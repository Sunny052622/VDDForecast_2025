"""
Comprehensive Sales Analysis Script
Senior Data Analyst Report
Author: AI Data Analyst
Date: October 22, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import datetime, timedelta
from mlxtend.frequent_patterns import apriori, association_rules
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import matplotlib.dates as mdates
import sys
import io

# Set UTF-8 encoding for output to handle special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("="*80)
print("COMPREHENSIVE SALES ANALYSIS")
print("="*80)
print("\n")

# ============================================================================
# PART 1: DATA INGESTION & PREPARATION (THE "RULES ENGINE")
# ============================================================================

print("PART 1: DATA INGESTION & PREPARATION")
print("-" * 80)

# Load Data
print("\n1.1 Loading Data...")
df_sales = pd.read_excel('data.xlsx', sheet_name='SalesData')
df_name_ref = pd.read_excel('data.xlsx', sheet_name='nameRef')
df_combo_ref = pd.read_excel('data.xlsx', sheet_name='comboRef')

print(f"   [+] SalesData loaded: {df_sales.shape[0]:,} rows, {df_sales.shape[1]} columns")
print(f"   [+] nameRef loaded: {df_name_ref.shape[0]:,} rows, {df_name_ref.shape[1]} columns")
print(f"   [+] comboRef loaded: {df_combo_ref.shape[0]:,} rows, {df_combo_ref.shape[1]} columns")

# Clean df_sales
print("\n1.2 Cleaning Sales Data...")

# Filter for successful transactions only
df_sales = df_sales[df_sales['Status'] == 'Success'].copy()
print(f"   [+] Filtered for successful transactions: {df_sales.shape[0]:,} rows")

# Convert Date and Timestamp to datetime
df_sales['Date'] = pd.to_datetime(df_sales['Date'], errors='coerce')
df_sales['Timestamp'] = pd.to_datetime(df_sales['Timestamp'], errors='coerce')

# Convert numeric columns
numeric_cols = ['Price', 'Qty.', 'Sub Total', 'Discount', 'Tax', 'Final Total']
for col in numeric_cols:
    df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce')

print(f"   [+] Converted Date, Timestamp, and numeric columns")

# Create time-based features
df_sales['Year'] = df_sales['Date'].dt.year
df_sales['Month'] = df_sales['Date'].dt.month
df_sales['Month-Year'] = df_sales['Date'].dt.to_period('M').astype(str)
df_sales['Week'] = df_sales['Date'].dt.isocalendar().week
df_sales['DayOfWeek'] = df_sales['Date'].dt.day_name()
df_sales['Hour'] = df_sales['Timestamp'].dt.hour

print(f"   [+] Created time-based features: Year, Month, Month-Year, Week, DayOfWeek, Hour")

# Standardize Order Type - Create Sales Channel
df_sales['Sales Channel'] = df_sales['Area'].apply(
    lambda x: 'Delivery' if x == 'Swiggy' else 'In-Shop'
)
print(f"   [+] Created Sales Channel: Delivery vs In-Shop")

# ============================================================================
# PART 1B: CREATE TWO SEPARATE ANALYSIS DATAFRAMES
# ============================================================================

print("\n1.3 Creating Two Analysis DataFrames...")

# -----------------------------------------------------------------------------
# A. df_revenue_analysis (For Revenue & Sales Analysis)
# -----------------------------------------------------------------------------
print("\n   A. Creating df_revenue_analysis (Revenue Analysis - As Sold)...")

# Standardize column names in df_name_ref for easier merging
df_name_ref_clean = df_name_ref[['Item', 'Real Name', 'Parent', 'Sub Category']].copy()
df_name_ref_clean.columns = ['Item Name', 'Real Item Name', 'Parent Category', 'Sub Category']
df_name_ref_clean = df_name_ref_clean.drop_duplicates(subset=['Item Name'])

# Merge df_sales with df_name_ref to get standardized names and categories
df_revenue_analysis = df_sales.merge(
    df_name_ref_clean,
    on='Item Name',
    how='left'
)

# Fill missing values with original item name if not found in reference
df_revenue_analysis['Real Item Name'] = df_revenue_analysis['Real Item Name'].fillna(df_revenue_analysis['Item Name'])
df_revenue_analysis['Parent Category'] = df_revenue_analysis['Parent Category'].fillna('Unknown')
df_revenue_analysis['Sub Category'] = df_revenue_analysis['Sub Category'].fillna('Unknown')

print(f"      [+] df_revenue_analysis created: {df_revenue_analysis.shape[0]:,} rows")
print(f"      [+] This DataFrame preserves combos as sold for revenue calculations")

# -----------------------------------------------------------------------------
# B. df_quantity_analysis (For Item Quantity & Ingredient-Level Analysis)
# -----------------------------------------------------------------------------
print("\n   B. Creating df_quantity_analysis (Quantity Analysis - Component Level)...")

# Prepare combo reference data
df_combo_ref_clean = df_combo_ref[['Item Name', 'Real Item Name']].copy()

# Get list of combo items
combo_items = df_combo_ref_clean['Item Name'].unique()

# Step 1: Isolate non-combo items
df_non_combo = df_sales[~df_sales['Item Name'].isin(combo_items)].copy()

# Merge non-combo items with name reference
df_non_combo_merged = df_non_combo.merge(
    df_name_ref_clean,
    on='Item Name',
    how='left'
)

# Fill missing values
df_non_combo_merged['Real Item Name'] = df_non_combo_merged['Real Item Name'].fillna(df_non_combo_merged['Item Name'])
df_non_combo_merged['Parent Category'] = df_non_combo_merged['Parent Category'].fillna('Unknown')
df_non_combo_merged['Sub Category'] = df_non_combo_merged['Sub Category'].fillna('Unknown')

print(f"      Step 1: Non-combo items isolated: {df_non_combo_merged.shape[0]:,} rows")

# Step 2 & 3: Isolate combo items and explode them
df_combo = df_sales[df_sales['Item Name'].isin(combo_items)].copy()
print(f"      Step 2: Combo items isolated: {df_combo.shape[0]:,} rows")

# Step 4: For each combo sale, explode into component items
combo_exploded_list = []

for idx, row in df_combo.iterrows():
    combo_name = row['Item Name']
    combo_qty = row['Qty.']
    
    # Get all component items for this combo
    components = df_combo_ref_clean[df_combo_ref_clean['Item Name'] == combo_name]
    
    for _, component in components.iterrows():
        # Create a new row for each component
        new_row = row.copy()
        new_row['Real Item Name'] = component['Real Item Name']
        new_row['Component Qty'] = combo_qty * 1  # Assuming base quantity is 1 for each component
        combo_exploded_list.append(new_row)

if combo_exploded_list:
    df_combo_exploded = pd.DataFrame(combo_exploded_list)
    
    # Update Qty. to reflect component quantity
    df_combo_exploded['Qty.'] = df_combo_exploded['Component Qty']
    
    # Remove existing category columns if they exist
    if 'Parent Category' in df_combo_exploded.columns:
        df_combo_exploded = df_combo_exploded.drop(columns=['Parent Category', 'Sub Category'], errors='ignore')
    
    # Merge with name reference to get categories for component items
    df_combo_exploded = df_combo_exploded.merge(
        df_name_ref_clean[['Real Item Name', 'Parent Category', 'Sub Category']].drop_duplicates(subset=['Real Item Name']),
        on='Real Item Name',
        how='left'
    )
    
    # Fill missing values
    df_combo_exploded['Parent Category'] = df_combo_exploded['Parent Category'].fillna('Unknown')
    df_combo_exploded['Sub Category'] = df_combo_exploded['Sub Category'].fillna('Unknown')
    
    # Clean up Component Qty column
    df_combo_exploded = df_combo_exploded.drop(columns=['Component Qty'], errors='ignore')
    
    print(f"      Step 4: Combos exploded into components: {df_combo_exploded.shape[0]:,} rows")
else:
    df_combo_exploded = pd.DataFrame()
    print(f"      Step 4: No combos to explode")

# Step 5: Combine non-combo and exploded combo items
if not df_combo_exploded.empty:
    df_quantity_analysis = pd.concat([df_non_combo_merged, df_combo_exploded], ignore_index=True)
else:
    df_quantity_analysis = df_non_combo_merged.copy()

print(f"      Step 5: df_quantity_analysis created: {df_quantity_analysis.shape[0]:,} rows")
print(f"      [+] This DataFrame shows component-level quantities for inventory analysis")

print("\n[+] Data Preparation Complete!\n")

# ============================================================================
# PART 2: DETAILED ANALYSIS & VISUALIZATION
# ============================================================================

print("="*80)
print("PART 2: DETAILED ANALYSIS & VISUALIZATION")
print("="*80)

# Create output directory for plots
import os
if not os.path.exists('analysis_outputs'):
    os.makedirs('analysis_outputs')

# ============================================================================
# 1. OVERALL BUSINESS KPIs
# ============================================================================

print("\n1. OVERALL BUSINESS KPIs")
print("-" * 80)

total_revenue = df_revenue_analysis['Final Total'].sum()
total_orders = df_revenue_analysis['Invoice No.'].nunique()
overall_aov = total_revenue / total_orders if total_orders > 0 else 0
total_items_sold = df_revenue_analysis['Qty.'].sum()

print(f"\n   Total Revenue:           ₹{total_revenue:,.2f}")
print(f"   Total Unique Orders:     {total_orders:,}")
print(f"   Average Order Value:     ₹{overall_aov:,.2f}")
print(f"   Total Items Sold:        {total_items_sold:,.0f}")

# ============================================================================
# 2. SALES PERFORMANCE BY CHANNEL & TIME
# ============================================================================

print("\n\n2. SALES PERFORMANCE BY CHANNEL & TIME")
print("-" * 80)

# By Channel
print("\n   2.1 Performance by Sales Channel:")
channel_revenue = df_revenue_analysis.groupby('Sales Channel')['Final Total'].sum().sort_values(ascending=False)
channel_pct = (channel_revenue / total_revenue * 100).round(2)

for channel in channel_revenue.index:
    print(f"      {channel:12} - Revenue: ₹{channel_revenue[channel]:,.2f} ({channel_pct[channel]:.2f}%)")

# AOV by Channel
channel_aov = df_revenue_analysis.groupby('Sales Channel').apply(
    lambda x: x['Final Total'].sum() / x['Invoice No.'].nunique()
).sort_values(ascending=False)

print(f"\n   2.2 Average Order Value by Channel:")
for channel in channel_aov.index:
    print(f"      {channel:12} - AOV: ₹{channel_aov[channel]:,.2f}")

# By Time
print("\n   2.3 Time-Based Analysis:")

# Monthly Revenue Trend
monthly_revenue = df_revenue_analysis.groupby('Month-Year')['Final Total'].sum().sort_index()
print(f"      [+] Monthly trend calculated for {len(monthly_revenue)} months")

# Revenue by Day of Week
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_revenue = df_revenue_analysis.groupby('DayOfWeek')['Final Total'].sum()
dow_revenue = dow_revenue.reindex(day_order)

# Revenue by Hour
hourly_revenue = df_revenue_analysis.groupby('Hour')['Final Total'].sum()

# Create Time-Based Visualizations
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Monthly Revenue Trend
ax1 = axes[0, 0]
monthly_revenue.plot(kind='line', ax=ax1, marker='o', color='#2E86AB', linewidth=2)
ax1.set_title('Monthly Revenue Trend', fontsize=14, fontweight='bold')
ax1.set_xlabel('Month-Year', fontsize=12)
ax1.set_ylabel('Revenue (₹)', fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)
for label in ax1.get_xticklabels():
    label.set_ha('right')

# Plot 2: Revenue by Day of Week
ax2 = axes[0, 1]
dow_revenue.plot(kind='bar', ax=ax2, color='#A23B72')
ax2.set_title('Revenue by Day of Week', fontsize=14, fontweight='bold')
ax2.set_xlabel('Day of Week', fontsize=12)
ax2.set_ylabel('Revenue (₹)', fontsize=12)
ax2.tick_params(axis='x', rotation=45)
ax2.grid(True, alpha=0.3, axis='y')

# Plot 3: Revenue by Hour of Day
ax3 = axes[1, 0]
hourly_revenue.plot(kind='bar', ax=ax3, color='#F18F01')
ax3.set_title('Revenue by Hour of Day', fontsize=14, fontweight='bold')
ax3.set_xlabel('Hour', fontsize=12)
ax3.set_ylabel('Revenue (₹)', fontsize=12)
ax3.grid(True, alpha=0.3, axis='y')

# Plot 4: Channel Distribution
ax4 = axes[1, 1]
colors = ['#06A77D', '#D4A373']
ax4.pie(channel_revenue.values, labels=channel_revenue.index, autopct='%1.1f%%',
        startangle=90, colors=colors, textprops={'fontsize': 12, 'fontweight': 'bold'})
ax4.set_title('Revenue Distribution by Sales Channel', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('analysis_outputs/01_time_channel_analysis.png', dpi=300, bbox_inches='tight')
print(f"      [+] Time & Channel visualizations saved")
plt.close()

# ============================================================================
# 3. CATEGORY & PRODUCT PERFORMANCE
# ============================================================================

print("\n\n3. CATEGORY & PRODUCT PERFORMANCE")
print("-" * 80)

# Revenue Analysis
print("\n   3.1 Revenue Analysis (from df_revenue_analysis):")

# Revenue by Parent Category
category_revenue = df_revenue_analysis.groupby('Parent Category')['Final Total'].sum().sort_values(ascending=False)
print(f"\n      Revenue by Parent Category:")
for i, (cat, rev) in enumerate(category_revenue.head(10).items(), 1):
    pct = (rev / total_revenue * 100)
    print(f"      {i:2}. {cat:20} - ₹{rev:,.2f} ({pct:.1f}%)")

# Top 10 Items by Revenue
top_revenue_items = df_revenue_analysis.groupby('Real Item Name')['Final Total'].sum().sort_values(ascending=False).head(10)
print(f"\n      Top 10 Items by Revenue:")
for i, (item, rev) in enumerate(top_revenue_items.items(), 1):
    print(f"      {i:2}. {item:30} - ₹{rev:,.2f}")

# Quantity Analysis
print("\n   3.2 Quantity Analysis (from df_quantity_analysis):")

# Top 10 Items by Quantity
top_qty_items = df_quantity_analysis.groupby('Real Item Name')['Qty.'].sum().sort_values(ascending=False).head(10)
print(f"\n      Top 10 Items by Quantity (Component Level - Critical for Inventory):")
for i, (item, qty) in enumerate(top_qty_items.items(), 1):
    print(f"      {i:2}. {item:30} - {qty:,.0f} units")

# Comparison Insight
print(f"\n   3.3 Revenue vs Quantity Comparison Insights:")
top_rev_set = set(top_revenue_items.index)
top_qty_set = set(top_qty_items.index)
common_items = top_rev_set & top_qty_set
only_revenue = top_rev_set - top_qty_set
only_quantity = top_qty_set - top_rev_set

print(f"      [+] Items in BOTH top 10 lists: {len(common_items)}")
if common_items:
    for item in common_items:
        print(f"         - {item}")

print(f"\n      [+] Items ONLY in top revenue (high price/margin items): {len(only_revenue)}")
if only_revenue:
    for item in only_revenue:
        print(f"         - {item}")

print(f"\n      [+] Items ONLY in top quantity (high volume/low price items): {len(only_quantity)}")
if only_quantity:
    for item in only_quantity:
        print(f"         - {item}")

# Create Category & Product Visualizations
fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Plot 1: Revenue by Category (Pie Chart)
ax1 = axes[0, 0]
top_categories = category_revenue.head(8)
other_revenue = category_revenue[8:].sum() if len(category_revenue) > 8 else 0
if other_revenue > 0:
    plot_data = pd.concat([top_categories, pd.Series({'Other': other_revenue})])
else:
    plot_data = top_categories

colors_palette = plt.cm.Set3(range(len(plot_data)))
ax1.pie(plot_data.values, labels=plot_data.index, autopct='%1.1f%%',
        startangle=90, colors=colors_palette, textprops={'fontsize': 9})
ax1.set_title('Revenue Distribution by Parent Category', fontsize=14, fontweight='bold')

# Plot 2: Top 10 Items by Revenue
ax2 = axes[0, 1]
top_revenue_items.sort_values().plot(kind='barh', ax=ax2, color='#06A77D')
ax2.set_title('Top 10 Items by Revenue', fontsize=14, fontweight='bold')
ax2.set_xlabel('Revenue (₹)', fontsize=12)
ax2.set_ylabel('Item Name', fontsize=12)
ax2.grid(True, alpha=0.3, axis='x')

# Plot 3: Top 10 Items by Quantity
ax3 = axes[1, 0]
top_qty_items.sort_values().plot(kind='barh', ax=ax3, color='#D62828')
ax3.set_title('Top 10 Items by Quantity (Component Level)', fontsize=14, fontweight='bold')
ax3.set_xlabel('Quantity Sold', fontsize=12)
ax3.set_ylabel('Item Name', fontsize=12)
ax3.grid(True, alpha=0.3, axis='x')

# Plot 4: Category Performance Matrix (Revenue vs Quantity)
ax4 = axes[1, 1]
category_metrics = pd.DataFrame({
    'Revenue': df_revenue_analysis.groupby('Parent Category')['Final Total'].sum(),
    'Quantity': df_quantity_analysis.groupby('Parent Category')['Qty.'].sum()
})
category_metrics = category_metrics.nlargest(10, 'Revenue')

x = np.arange(len(category_metrics))
width = 0.35

ax4_twin = ax4.twinx()
bars1 = ax4.bar(x - width/2, category_metrics['Revenue'], width, label='Revenue (₹)', color='#2E86AB')
bars2 = ax4_twin.bar(x + width/2, category_metrics['Quantity'], width, label='Quantity', color='#F18F01')

ax4.set_xlabel('Category', fontsize=12)
ax4.set_ylabel('Revenue (₹)', fontsize=12, color='#2E86AB')
ax4_twin.set_ylabel('Quantity', fontsize=12, color='#F18F01')
ax4.set_title('Top Categories: Revenue vs Quantity', fontsize=14, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(category_metrics.index, rotation=45, ha='right', fontsize=9)
ax4.tick_params(axis='y', labelcolor='#2E86AB')
ax4_twin.tick_params(axis='y', labelcolor='#F18F01')
ax4.grid(True, alpha=0.3, axis='y')

# Combine legends
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.tight_layout()
plt.savefig('analysis_outputs/02_category_product_performance.png', dpi=300, bbox_inches='tight')
print(f"\n      [+] Category & Product visualizations saved")
plt.close()

# ============================================================================
# 4. BASKET ANALYSIS
# ============================================================================

print("\n\n4. BASKET ANALYSIS (Market Basket Analysis)")
print("-" * 80)

# Prepare transaction data for basket analysis
print("\n   4.1 Preparing basket data...")

# Group by Invoice No. and create a list of items per transaction
basket_df = df_revenue_analysis.groupby(['Invoice No.', 'Real Item Name'])['Qty.'].sum().unstack(fill_value=0)

# Convert to binary (1 if item was purchased, 0 otherwise)
basket_binary = basket_df.applymap(lambda x: 1 if x > 0 else 0)

print(f"      [+] Created transaction matrix: {basket_binary.shape[0]:,} transactions × {basket_binary.shape[1]} unique items")

# Apply Apriori algorithm
print("\n   4.2 Running Apriori algorithm to find frequent itemsets...")
min_support = 0.01  # Items appearing in at least 1% of transactions

try:
    frequent_itemsets = apriori(basket_binary, min_support=min_support, use_colnames=True)
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
    
    print(f"      [+] Found {len(frequent_itemsets):,} frequent itemsets")
    print(f"      [+] Itemset sizes: {frequent_itemsets['length'].value_counts().sort_index().to_dict()}")
    
    # Generate association rules
    print("\n   4.3 Generating association rules...")
    
    if len(frequent_itemsets[frequent_itemsets['length'] >= 2]) > 0:
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
        rules = rules.sort_values('lift', ascending=False)
        
        print(f"      [+] Generated {len(rules):,} association rules")
        
        # Display top 5 rules by lift
        print(f"\n   4.4 Top 5 Association Rules (by Lift):")
        print(f"      {'#':3} {'Antecedent (If)':<30} {'Consequent (Then)':<30} {'Support':<10} {'Confidence':<12} {'Lift':<8}")
        print(f"      {'-'*3} {'-'*30} {'-'*30} {'-'*10} {'-'*12} {'-'*8}")
        
        for idx, row in rules.head(5).iterrows():
            antecedent = ', '.join(list(row['antecedents']))[:28]
            consequent = ', '.join(list(row['consequents']))[:28]
            support = f"{row['support']:.4f}"
            confidence = f"{row['confidence']:.4f}"
            lift = f"{row['lift']:.2f}"
            print(f"      {idx+1:3} {antecedent:<30} {consequent:<30} {support:<10} {confidence:<12} {lift:<8}")
        
        # Create Basket Analysis Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Top 15 Most Frequent Items
        ax1 = axes[0, 0]
        item_frequency = basket_binary.sum().sort_values(ascending=False).head(15)
        item_frequency_pct = (item_frequency / len(basket_binary) * 100)
        item_frequency_pct.sort_values().plot(kind='barh', ax=ax1, color='#2E86AB')
        ax1.set_title('Top 15 Most Frequently Purchased Items', fontsize=14, fontweight='bold')
        ax1.set_xlabel('% of Transactions', fontsize=12)
        ax1.set_ylabel('Item Name', fontsize=12)
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Plot 2: Support vs Confidence for Top Rules
        ax2 = axes[0, 1]
        top_rules = rules.head(20)
        scatter = ax2.scatter(top_rules['support'], top_rules['confidence'], 
                             s=top_rules['lift']*50, c=top_rules['lift'], 
                             cmap='YlOrRd', alpha=0.6, edgecolors='black', linewidth=0.5)
        ax2.set_title('Association Rules: Support vs Confidence', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Support', fontsize=12)
        ax2.set_ylabel('Confidence', fontsize=12)
        ax2.grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=ax2)
        cbar.set_label('Lift', fontsize=10)
        
        # Plot 3: Top Rules by Lift
        ax3 = axes[1, 0]
        top_lift_rules = rules.head(10).copy()
        top_lift_rules['rule'] = top_lift_rules.apply(
            lambda x: f"{list(x['antecedents'])[0][:15]} -> {list(x['consequents'])[0][:15]}", axis=1
        )
        top_lift_rules.set_index('rule')['lift'].sort_values().plot(kind='barh', ax=ax3, color='#D62828')
        ax3.set_title('Top 10 Association Rules by Lift', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Lift', fontsize=12)
        ax3.set_ylabel('Rule (If -> Then)', fontsize=12)
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Plot 4: Itemset Length Distribution
        ax4 = axes[1, 1]
        itemset_dist = frequent_itemsets['length'].value_counts().sort_index()
        ax4.bar(itemset_dist.index, itemset_dist.values, color='#06A77D', edgecolor='black', linewidth=0.5)
        ax4.set_title('Distribution of Frequent Itemset Sizes', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Number of Items in Itemset', fontsize=12)
        ax4.set_ylabel('Count', fontsize=12)
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('analysis_outputs/03_basket_analysis.png', dpi=300, bbox_inches='tight')
        print(f"\n      [+] Basket Analysis visualizations saved")
        plt.close()
        
    else:
        print("      [!] Not enough frequent itemsets with 2+ items to generate rules")
        rules = pd.DataFrame()
        
except Exception as e:
    print(f"      [!] Basket analysis error: {str(e)}")
    print(f"      [!] Try adjusting min_support parameter or checking data quality")
    rules = pd.DataFrame()

# ============================================================================
# 5. SALES FORECASTING
# ============================================================================

print("\n\n5. SALES FORECASTING (30-Day Revenue Forecast)")
print("-" * 80)

# Create daily revenue DataFrame
print("\n   5.1 Preparing daily revenue data...")
daily_revenue = df_revenue_analysis.groupby('Date')['Final Total'].sum().sort_index()
daily_revenue = daily_revenue.asfreq('D', fill_value=0)  # Fill missing dates with 0

print(f"      [+] Daily revenue data: {len(daily_revenue)} days")
print(f"      [+] Date range: {daily_revenue.index.min().strftime('%Y-%m-%d')} to {daily_revenue.index.max().strftime('%Y-%m-%d')}")
print(f"      [+] Mean daily revenue: ₹{daily_revenue.mean():,.2f}")

# Check for stationarity using Augmented Dickey-Fuller test
print("\n   5.2 Testing for stationarity (ADF Test)...")
adf_result = adfuller(daily_revenue.dropna())
print(f"      ADF Statistic: {adf_result[0]:.4f}")
print(f"      p-value: {adf_result[1]:.4f}")

if adf_result[1] < 0.05:
    print(f"      [+] Series is stationary (p-value < 0.05)")
else:
    print(f"      [!] Series is non-stationary (p-value >= 0.05)")
    print(f"      -> Differencing may improve forecast accuracy")

# Build SARIMA model
print("\n   5.3 Building SARIMA forecast model...")

try:
    # Use a simple SARIMA model with seasonal component
    # Parameters: (p,d,q) x (P,D,Q,s)
    # For daily data with potential weekly seasonality
    model = SARIMAX(daily_revenue, 
                    order=(1, 1, 1),  # ARIMA order
                    seasonal_order=(1, 1, 1, 7),  # Seasonal order (weekly pattern)
                    enforce_stationarity=False,
                    enforce_invertibility=False)
    
    results = model.fit(disp=False)
    print(f"      [+] SARIMA model fitted successfully")
    print(f"      [+] AIC: {results.aic:.2f}")
    print(f"      [+] BIC: {results.bic:.2f}")
    
    # Forecast next 30 days
    print("\n   5.4 Generating 30-day forecast...")
    forecast_steps = 30
    forecast = results.get_forecast(steps=forecast_steps)
    forecast_df = forecast.summary_frame()
    
    # Create forecast dates
    last_date = daily_revenue.index.max()
    forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_steps, freq='D')
    forecast_df.index = forecast_dates
    
    # Calculate total forecasted revenue
    total_forecast_revenue = forecast_df['mean'].sum()
    avg_daily_forecast = forecast_df['mean'].mean()
    
    print(f"      [+] Forecast generated for {forecast_steps} days")
    print(f"      [+] Total forecasted revenue (30 days): ₹{total_forecast_revenue:,.2f}")
    print(f"      [+] Average daily forecasted revenue: ₹{avg_daily_forecast:,.2f}")
    
    # Create Forecast Visualization
    fig, axes = plt.subplots(2, 1, figsize=(16, 12))
    
    # Plot 1: Full Historical + Forecast
    ax1 = axes[0]
    
    # Plot historical data
    ax1.plot(daily_revenue.index, daily_revenue.values, label='Historical', color='#2E86AB', linewidth=2)
    
    # Plot forecast
    ax1.plot(forecast_df.index, forecast_df['mean'], label='Forecast', color='#D62828', linewidth=2, linestyle='--')
    
    # Plot confidence intervals
    ax1.fill_between(forecast_df.index, 
                     forecast_df['mean_ci_lower'], 
                     forecast_df['mean_ci_upper'], 
                     color='#D62828', alpha=0.2, label='95% Confidence Interval')
    
    ax1.set_title('Sales Forecast: Historical Data + 30-Day Prediction', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Daily Revenue (₹)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Zoomed in on Recent + Forecast
    ax2 = axes[1]
    
    # Last 60 days of historical + forecast
    recent_days = 60
    recent_data = daily_revenue.tail(recent_days)
    
    ax2.plot(recent_data.index, recent_data.values, label='Recent Historical', color='#2E86AB', linewidth=2, marker='o', markersize=3)
    ax2.plot(forecast_df.index, forecast_df['mean'], label='Forecast', color='#D62828', linewidth=2, linestyle='--', marker='s', markersize=4)
    ax2.fill_between(forecast_df.index, 
                     forecast_df['mean_ci_lower'], 
                     forecast_df['mean_ci_upper'], 
                     color='#D62828', alpha=0.2, label='95% Confidence Interval')
    
    ax2.set_title(f'Detailed View: Last {recent_days} Days + 30-Day Forecast', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Daily Revenue (₹)', fontsize=12)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('analysis_outputs/04_sales_forecast.png', dpi=300, bbox_inches='tight')
    print(f"\n      [+] Forecast visualizations saved")
    plt.close()
    
    # Print forecast summary table
    print("\n   5.5 Detailed Forecast (First 10 Days):")
    print(f"      {'Date':<12} {'Forecasted Revenue':<20} {'Lower CI':<15} {'Upper CI':<15}")
    print(f"      {'-'*12} {'-'*20} {'-'*15} {'-'*15}")
    for date, row in forecast_df.head(10).iterrows():
        print(f"      {date.strftime('%Y-%m-%d'):<12} ₹{row['mean']:>15,.2f}   ₹{row['mean_ci_lower']:>11,.2f}   ₹{row['mean_ci_upper']:>11,.2f}")
    
except Exception as e:
    print(f"      [!] Forecasting error: {str(e)}")
    print(f"      [!] This may be due to insufficient data or model parameters")

# ============================================================================
# FINAL SUMMARY REPORT
# ============================================================================

print("\n\n")
print("="*80)
print("COMPREHENSIVE ANALYSIS SUMMARY REPORT")
print("="*80)

print(f"""
============================================================================
                         KEY BUSINESS INSIGHTS                              
============================================================================

1. OVERALL PERFORMANCE
   * Total Revenue:           ₹{total_revenue:,.2f}
   * Total Orders:            {total_orders:,}
   * Average Order Value:     ₹{overall_aov:,.2f}
   * Total Items Sold:        {total_items_sold:,.0f}

2. SALES CHANNEL INSIGHTS
""")

for channel in channel_revenue.index:
    print(f"   * {channel}:")
    print(f"     - Revenue: ₹{channel_revenue[channel]:,.2f} ({channel_pct[channel]:.1f}%)")
    print(f"     - AOV: ₹{channel_aov[channel]:,.2f}")

print(f"""
3. TOP PERFORMERS
   
   Top 3 Revenue-Generating Items:
""")
for i, (item, rev) in enumerate(top_revenue_items.head(3).items(), 1):
    print(f"   {i}. {item} - ₹{rev:,.2f}")

print(f"""
   Top 3 Most-Sold Items (by Quantity - Critical for Inventory):
""")
for i, (item, qty) in enumerate(top_qty_items.head(3).items(), 1):
    print(f"   {i}. {item} - {qty:,.0f} units")

print(f"""
4. CATEGORY PERFORMANCE
   
   Top 3 Categories by Revenue:
""")
for i, (cat, rev) in enumerate(category_revenue.head(3).items(), 1):
    pct = (rev / total_revenue * 100)
    print(f"   {i}. {cat} - ₹{rev:,.2f} ({pct:.1f}%)")

if not rules.empty:
    print(f"""
5. BASKET ANALYSIS INSIGHTS
   
   * Found {len(frequent_itemsets):,} frequent itemsets
   * Generated {len(rules):,} association rules
   
   Top 3 Product Associations (for cross-selling):
""")
    for idx, row in rules.head(3).iterrows():
        antecedent = ', '.join(list(row['antecedents']))
        consequent = ', '.join(list(row['consequents']))
        print(f"   * If customer buys '{antecedent}'")
        print(f"     -> They're {row['lift']:.2f}x more likely to buy '{consequent}'")
        print(f"     (Confidence: {row['confidence']:.1%})\n")

try:
    print(f"""
6. SALES FORECAST
   
   * Forecast Period: {forecast_dates[0].strftime('%Y-%m-%d')} to {forecast_dates[-1].strftime('%Y-%m-%d')}
   * Total Forecasted Revenue (30 days): ₹{total_forecast_revenue:,.2f}
   * Average Daily Forecast: ₹{avg_daily_forecast:,.2f}
   * Model: SARIMA(1,1,1)(1,1,1,7)
   
   First 7 Days Forecast:
""")
    for date, row in forecast_df.head(7).iterrows():
        print(f"   * {date.strftime('%Y-%m-%d')}: ₹{row['mean']:,.2f} (CI: ₹{row['mean_ci_lower']:,.2f} - ₹{row['mean_ci_upper']:,.2f})")
except:
    print("\n6. SALES FORECAST\n   * Forecast not available")

print(f"""
============================================================================
                        STRATEGIC RECOMMENDATIONS                           
============================================================================

1. INVENTORY MANAGEMENT
   * Focus on top quantity items for inventory planning
   * These differ from top revenue items, indicating volume vs. value distinction

2. CROSS-SELLING OPPORTUNITIES
   * Use association rules to create combo deals
   * Train staff on high-lift product pairings

3. OPERATIONAL EFFICIENCY
   * Peak hours identified in hourly revenue chart
   * Optimize staffing during high-revenue periods
   * Consider promotions during low-traffic hours

4. CHANNEL STRATEGY
   * {channel_revenue.index[0]} is the dominant channel ({channel_pct.iloc[0]:.1f}%)
   * AOV differences suggest different customer behaviors per channel

5. FORECASTING & PLANNING
   * Use 30-day forecast for inventory and staff planning
   * Monitor actual vs. forecast to refine model

============================================================================
                           OUTPUT FILES GENERATED                           
============================================================================

All visualizations saved in 'analysis_outputs/' directory:

   1. 01_time_channel_analysis.png
      - Monthly revenue trend
      - Revenue by day of week
      - Revenue by hour of day
      - Channel distribution

   2. 02_category_product_performance.png
      - Revenue by category (pie chart)
      - Top 10 items by revenue
      - Top 10 items by quantity
      - Category performance matrix

   3. 03_basket_analysis.png
      - Most frequently purchased items
      - Association rules visualization
      - Top rules by lift
      - Itemset distribution

   4. 04_sales_forecast.png
      - Full historical data + 30-day forecast
      - Detailed recent view with confidence intervals

============================================================================
                            ANALYSIS COMPLETE                               
============================================================================

Thank you for using this comprehensive sales analysis system.
For questions or further analysis, please consult your data analyst.

""")

print("="*80)
print("Script execution completed successfully!")
print("="*80)

