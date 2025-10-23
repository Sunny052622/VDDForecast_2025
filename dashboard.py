"""
Interactive Sales Analysis Dashboard
Built with Streamlit
Supports local Excel and Google Sheets data sources
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import warnings
import os

warnings.filterwarnings('ignore')

# Try importing Google Sheets libraries
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="VDD Sales Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 48px;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load from Google Sheets
def load_from_google_sheets():
    """Load data from Google Sheets using service account credentials"""
    try:
        # Define the scope for Google Sheets API
        scope = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # Get credentials from Streamlit secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        
        # Authorize and open the spreadsheet
        client = gspread.authorize(credentials)
        
        # Get spreadsheet URL from secrets
        spreadsheet_url = st.secrets["gsheet"]["spreadsheet_url"]
        spreadsheet = client.open_by_url(spreadsheet_url)
        
        # Load each sheet
        df_sales = pd.DataFrame(spreadsheet.worksheet('SalesData').get_all_records())
        df_name_ref = pd.DataFrame(spreadsheet.worksheet('nameRef').get_all_records())
        df_combo_ref = pd.DataFrame(spreadsheet.worksheet('comboRef').get_all_records())
        
        return df_sales, df_name_ref, df_combo_ref, None
        
    except Exception as e:
        return None, None, None, str(e)


# Helper function to load from local Excel
def load_from_excel():
    """Load data from local Excel file"""
    try:
        df_sales = pd.read_excel('data.xlsx', sheet_name='SalesData')
        df_name_ref = pd.read_excel('data.xlsx', sheet_name='nameRef')
        df_combo_ref = pd.read_excel('data.xlsx', sheet_name='comboRef')
        return df_sales, df_name_ref, df_combo_ref, None
    except Exception as e:
        return None, None, None, str(e)


# Data loading function with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes to allow fresh data updates
def load_data(use_google_sheets=True):
    """Load and prepare data - handles both revenue and quantity analysis
    
    Args:
        use_google_sheets: If True, tries to load from Google Sheets first, falls back to Excel
    """
    try:
        # Try loading from Google Sheets if enabled and available
        if use_google_sheets and GSHEETS_AVAILABLE and "gcp_service_account" in st.secrets:
            df_sales, df_name_ref, df_combo_ref, error = load_from_google_sheets()
            if df_sales is not None:
                st.sidebar.success("📊 Data loaded from Google Sheets")
            else:
                st.sidebar.warning(f"⚠️ Google Sheets error: {error}. Using local file...")
                df_sales, df_name_ref, df_combo_ref, error = load_from_excel()
        else:
            # Load from local Excel file
            df_sales, df_name_ref, df_combo_ref, error = load_from_excel()
            if df_sales is not None:
                st.sidebar.info("📁 Data loaded from local Excel file")
        
        if df_sales is None:
            raise Exception(error or "Failed to load data from any source")
        
        # Clean df_sales
        df_sales = df_sales[df_sales['Status'] == 'Success'].copy()
        df_sales['Date'] = pd.to_datetime(df_sales['Date'], errors='coerce')
        df_sales['Timestamp'] = pd.to_datetime(df_sales['Timestamp'], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['Price', 'Qty.', 'Sub Total', 'Discount', 'Tax', 'Final Total']
        for col in numeric_cols:
            df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce')
        
        # Create time-based features
        df_sales['Year'] = df_sales['Date'].dt.year
        df_sales['Month'] = df_sales['Date'].dt.month
        df_sales['Month-Year'] = df_sales['Date'].dt.to_period('M').astype(str)
        df_sales['Week'] = df_sales['Date'].dt.isocalendar().week
        df_sales['DayOfWeek'] = df_sales['Date'].dt.day_name()
        df_sales['Hour'] = df_sales['Timestamp'].dt.hour
        
        # Use the new Online/Offline column if it exists, otherwise derive from Area
        if 'Online / Offline' in df_sales.columns:
            df_sales['Sales Channel'] = df_sales['Online / Offline']
        else:
            df_sales['Sales Channel'] = df_sales['Area'].apply(
                lambda x: 'Delivery' if x == 'Swiggy' else 'In-Shop'
            )
        
        # Prepare name reference
        df_name_ref_clean = df_name_ref[['Item', 'Real Name', 'Parent', 'Sub Category']].copy()
        df_name_ref_clean.columns = ['Item Name', 'Real Item Name', 'Parent Category', 'Sub Category']
        df_name_ref_clean = df_name_ref_clean.drop_duplicates(subset=['Item Name'])
        
        # Prepare combo reference
        df_combo_ref_clean = df_combo_ref[['Item Name', 'Real Item Name', 'Category', 'Sub Category']].copy()
        
        # Ensure Outlet column exists and has no nulls
        if 'Outlet' not in df_sales.columns:
            df_sales['Outlet'] = 'Unknown'
        df_sales['Outlet'] = df_sales['Outlet'].fillna('Unknown')
        
        # Create revenue analysis DataFrame (as-sold)
        df_revenue_analysis = df_sales.merge(
            df_name_ref_clean,
            on='Item Name',
            how='left'
        )
        df_revenue_analysis['Real Item Name'] = df_revenue_analysis['Real Item Name'].fillna(df_revenue_analysis['Item Name'])
        df_revenue_analysis['Parent Category'] = df_revenue_analysis['Parent Category'].fillna('Unknown')
        df_revenue_analysis['Sub Category'] = df_revenue_analysis['Sub Category'].fillna('Unknown').astype(str)
        
        # Create quantity analysis DataFrame (combos exploded)
        combo_items = df_combo_ref_clean['Item Name'].unique()
        
        # Non-combo items
        df_non_combo = df_sales[~df_sales['Item Name'].isin(combo_items)].copy()
        df_non_combo_merged = df_non_combo.merge(df_name_ref_clean, on='Item Name', how='left')
        df_non_combo_merged['Real Item Name'] = df_non_combo_merged['Real Item Name'].fillna(df_non_combo_merged['Item Name'])
        df_non_combo_merged['Parent Category'] = df_non_combo_merged['Parent Category'].fillna('Unknown')
        df_non_combo_merged['Sub Category'] = df_non_combo_merged['Sub Category'].fillna('Unknown').astype(str)
        
        # Combo items - explode into components
        df_combo = df_sales[df_sales['Item Name'].isin(combo_items)].copy()
        combo_exploded_list = []
        
        for idx, row in df_combo.iterrows():
            combo_name = row['Item Name']
            combo_qty = row['Qty.']
            components = df_combo_ref_clean[df_combo_ref_clean['Item Name'] == combo_name]
            
            for _, component in components.iterrows():
                new_row = row.copy()
                new_row['Real Item Name'] = component['Real Item Name']
                new_row['Qty.'] = combo_qty * 1
                
                # Look up category and sub-category from nameRef based on Real Item Name
                matching_name = df_name_ref_clean[df_name_ref_clean['Real Item Name'] == component['Real Item Name']]
                if len(matching_name) > 0:
                    new_row['Parent Category'] = matching_name.iloc[0]['Parent Category']
                    new_row['Sub Category'] = matching_name.iloc[0]['Sub Category']
                else:
                    # Fallback to comboRef if not found in nameRef
                    new_row['Parent Category'] = component['Category']
                    new_row['Sub Category'] = component['Sub Category'] if pd.notna(component['Sub Category']) else component['Real Item Name']
                
                combo_exploded_list.append(new_row)
        
        if combo_exploded_list:
            df_combo_exploded = pd.DataFrame(combo_exploded_list)
            df_quantity_analysis = pd.concat([df_non_combo_merged, df_combo_exploded], ignore_index=True)
        else:
            df_quantity_analysis = df_non_combo_merged.copy()
        
        # Clean up sub-category column
        df_quantity_analysis['Sub Category'] = df_quantity_analysis['Sub Category'].fillna('Unknown').astype(str)
        
        return df_revenue_analysis, df_quantity_analysis
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

# Add data source toggle in sidebar
st.sidebar.markdown("# ⚙️ Settings")

# Refresh button
if st.sidebar.button("🔄 Refresh Data", help="Clear cache and reload data"):
    st.cache_data.clear()
    st.rerun()

# Data source info
with st.sidebar.expander("📊 Data Source Info", expanded=False):
    if GSHEETS_AVAILABLE and "gcp_service_account" in st.secrets:
        st.write("✅ Google Sheets: Enabled")
        if "gsheet" in st.secrets:
            st.write(f"📝 Spreadsheet connected")
    else:
        st.write("📁 Using local Excel file")
    
    st.caption("Data refreshes every 5 minutes automatically")

st.sidebar.markdown("---")

# Load data
with st.spinner("Loading data..."):
    # Try Google Sheets if available, otherwise use Excel
    use_gsheets = GSHEETS_AVAILABLE and "gcp_service_account" in st.secrets
    df_revenue, df_quantity = load_data(use_google_sheets=use_gsheets)

if df_revenue is None or df_quantity is None:
    st.error("Failed to load data. Please check data.xlsx file or Google Sheets connection.")
    st.stop()

# Sidebar filters
st.sidebar.markdown("# 🎛️ Filters")
st.sidebar.markdown("---")

# Outlet filter (NEW)
outlet_values = df_revenue['Outlet'].dropna().unique().tolist()
outlet_values = [str(o) for o in outlet_values if o not in ['', 'nan', 'None']]
outlets = ['All'] + sorted(outlet_values)
selected_outlet = st.sidebar.selectbox("🏪 Select Outlet", outlets, key='sidebar_outlet_filter')

# Date range filter
min_date = df_revenue['Date'].min().date()
max_date = df_revenue['Date'].max().date()

date_range = st.sidebar.date_input(
    "📅 Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Channel filter (Online/Offline)
channel_values = df_revenue['Sales Channel'].dropna().unique().tolist()
channels = ['All'] + sorted([str(c) for c in channel_values if c not in ['', 'nan', 'None']])
selected_channel = st.sidebar.selectbox("🌐 Online / Offline", channels)

# Category filter
categories = ['All'] + sorted(df_revenue['Parent Category'].unique().tolist())
selected_category = st.sidebar.selectbox("📦 Select Category", categories)

# Apply filters
df_filtered = df_revenue.copy()

try:
    if selected_outlet != 'All':
        df_filtered = df_filtered[df_filtered['Outlet'] == selected_outlet]
    
    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['Date'].dt.date >= date_range[0]) &
            (df_filtered['Date'].dt.date <= date_range[1])
        ]

    if selected_channel != 'All':
        df_filtered = df_filtered[df_filtered['Sales Channel'] == selected_channel]

    if selected_category != 'All':
        df_filtered = df_filtered[df_filtered['Parent Category'] == selected_category]
        
except Exception as e:
    st.error(f"Filter error: {str(e)}")
    df_filtered = df_revenue.copy()

# Check if filtered data is empty
if len(df_filtered) == 0:
    st.warning("⚠️ No data matches the selected filters. Please adjust your filters.")
    st.stop()

# Main dashboard
st.markdown('<p class="main-header">📊 VDD Sales Analysis Dashboard</p>', unsafe_allow_html=True)

# Summary metrics row
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered['Final Total'].sum()
total_orders = df_filtered['Invoice No.'].nunique()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
total_items = df_filtered['Qty.'].sum()

with col1:
    st.metric(
        label="💰 Total Revenue",
        value=f"₹{total_revenue:,.0f}",
        delta=f"{(total_revenue/df_revenue['Final Total'].sum()*100):.1f}% of total"
    )

with col2:
    st.metric(
        label="🛍️ Total Orders",
        value=f"{total_orders:,}",
        delta=f"{(total_orders/df_revenue['Invoice No.'].nunique()*100):.1f}% of total"
    )

with col3:
    st.metric(
        label="📈 Average Order Value",
        value=f"₹{avg_order_value:,.2f}"
    )

with col4:
    st.metric(
        label="📦 Items Sold",
        value=f"{total_items:,.0f}"
    )

st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📈 Overview", 
    "🏆 Top Products", 
    "⏰ Time Analysis", 
    "💰 Net Revenue & Discounts",
    "📊 Trends Analysis",
    "🔗 Basket Analysis",
    "🔮 Revenue Forecast",
    "📦 Weekly Unit Forecast",
    "📱 Send Targets"
])

# TAB 1: Overview
with tab1:
    st.markdown("### 📊 Sales Channel Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        channel_revenue = df_filtered.groupby('Sales Channel')['Final Total'].sum()
        
        fig = go.Figure(data=[go.Pie(
            labels=channel_revenue.index,
            values=channel_revenue.values,
            hole=0.4,
            marker_colors=['#06A77D', '#D4A373']
        )])
        fig.update_layout(title="Revenue by Sales Channel", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        channel_aov = df_filtered.groupby('Sales Channel').apply(
            lambda x: x['Final Total'].sum() / x['Invoice No.'].nunique()
        ).reset_index()
        channel_aov.columns = ['Sales Channel', 'AOV']
        
        fig = go.Figure(data=[go.Bar(
            x=channel_aov['Sales Channel'],
            y=channel_aov['AOV'],
            marker_color=['#06A77D', '#D4A373'],
            text=channel_aov['AOV'].round(2),
            textposition='auto'
        )])
        fig.update_layout(
            title="Average Order Value by Channel",
            xaxis_title="Sales Channel",
            yaxis_title="AOV (₹)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📦 Category Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_revenue = df_filtered.groupby('Parent Category')['Final Total'].sum().sort_values(ascending=False).head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=category_revenue.values,
            y=category_revenue.index,
            orientation='h',
            marker_color='#2E86AB',
            text=[f"₹{v:,.0f}" for v in category_revenue.values],
            textposition='auto'
        )])
        fig.update_layout(
            title="Top 10 Categories by Revenue",
            xaxis_title="Revenue (₹)",
            yaxis_title="Category",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        category_qty = df_filtered.groupby('Parent Category')['Qty.'].sum().sort_values(ascending=False).head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=category_qty.values,
            y=category_qty.index,
            orientation='h',
            marker_color='#D62828',
            text=[f"{v:,.0f}" for v in category_qty.values],
            textposition='auto'
        )])
        fig.update_layout(
            title="Top 10 Categories by Quantity",
            xaxis_title="Quantity Sold",
            yaxis_title="Category",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: Top Products
with tab2:
    st.markdown("### 🏆 Product Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Top 15 Products by Revenue")
        top_revenue = df_filtered.groupby('Real Item Name')['Final Total'].sum().sort_values(ascending=False).head(15)
        
        fig = go.Figure(data=[go.Bar(
            x=top_revenue.values,
            y=top_revenue.index,
            orientation='h',
            marker_color='#06A77D',
            text=[f"₹{v:,.0f}" for v in top_revenue.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Revenue (₹)", yaxis_title="Product", height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        revenue_df = top_revenue.reset_index()
        revenue_df.columns = ['Product', 'Revenue']
        revenue_df['Revenue'] = revenue_df['Revenue'].apply(lambda x: f"₹{x:,.2f}")
        revenue_df.insert(0, 'Rank', range(1, len(revenue_df) + 1))
        st.dataframe(revenue_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 📦 Top 15 Products by Quantity")
        top_qty = df_filtered.groupby('Real Item Name')['Qty.'].sum().sort_values(ascending=False).head(15)
        
        fig = go.Figure(data=[go.Bar(
            x=top_qty.values,
            y=top_qty.index,
            orientation='h',
            marker_color='#F18F01',
            text=[f"{v:,.0f}" for v in top_qty.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Quantity Sold", yaxis_title="Product", height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        qty_df = top_qty.reset_index()
        qty_df.columns = ['Product', 'Quantity']
        qty_df['Quantity'] = qty_df['Quantity'].apply(lambda x: f"{x:,.0f}")
        qty_df.insert(0, 'Rank', range(1, len(qty_df) + 1))
        st.dataframe(qty_df, use_container_width=True, hide_index=True)

# TAB 3: Time Analysis
with tab3:
    st.markdown("### ⏰ Time-Based Performance")
    
    # Add category filters for timeline
    st.markdown("#### 🎛️ Timeline Filters")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        timeline_parents = ['All'] + sorted([str(p) for p in df_filtered['Parent Category'].dropna().unique() if p not in ['Unknown', '']])
        selected_timeline_parent = st.selectbox("Parent Category", timeline_parents, key='timeline_parent')
    
    with col_f2:
        if selected_timeline_parent != 'All':
            filtered_for_timeline = df_filtered[df_filtered['Parent Category'] == selected_timeline_parent]
            timeline_subs = ['All'] + sorted([str(s) for s in filtered_for_timeline['Sub Category'].dropna().unique() if s not in ['Unknown', '']])
        else:
            timeline_subs = ['All']
        selected_timeline_sub = st.selectbox("Sub Category", timeline_subs, key='timeline_sub')
    
    with col_f3:
        if selected_timeline_sub != 'All':
            filtered_for_items = df_filtered[df_filtered['Sub Category'] == selected_timeline_sub]
        elif selected_timeline_parent != 'All':
            filtered_for_items = df_filtered[df_filtered['Parent Category'] == selected_timeline_parent]
        else:
            filtered_for_items = df_filtered
        
        timeline_items = ['All'] + sorted([str(i) for i in filtered_for_items['Real Item Name'].dropna().unique()][:50])
        selected_timeline_item = st.selectbox("Real Item Name (Top 50)", timeline_items, key='timeline_item')
    
    # Apply timeline filters
    df_timeline = df_filtered.copy()
    if selected_timeline_parent != 'All':
        df_timeline = df_timeline[df_timeline['Parent Category'] == selected_timeline_parent]
    if selected_timeline_sub != 'All':
        df_timeline = df_timeline[df_timeline['Sub Category'] == selected_timeline_sub]
    if selected_timeline_item != 'All':
        df_timeline = df_timeline[df_timeline['Real Item Name'] == selected_timeline_item]
    
    st.markdown("---")
    
    # Timeline charts
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("#### 📊 Timeline: Revenue Trend")
        timeline_rev = df_timeline.groupby('Month-Year')['Final Total'].sum().reset_index()
        timeline_rev.columns = ['Month', 'Revenue']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timeline_rev['Month'],
            y=timeline_rev['Revenue'],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(46, 134, 171, 0.2)'
        ))
        fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (₹)", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_t2:
        st.markdown("#### 📦 Timeline: Units Sold Trend")
        timeline_qty = df_timeline.groupby('Month-Year')['Qty.'].sum().reset_index()
        timeline_qty.columns = ['Month', 'Units']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timeline_qty['Month'],
            y=timeline_qty['Units'],
            mode='lines+markers',
            name='Units',
            line=dict(color='#D62828', width=3),
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(214, 40, 40, 0.2)'
        ))
        fig.update_layout(xaxis_title="Month", yaxis_title="Units Sold", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Add Week of Month calculation
    df_timeline['Week_of_Month'] = df_timeline['Date'].apply(
        lambda x: (x.day - 1) // 7 + 1 if pd.notna(x) else None
    )
    df_timeline['Week_of_Month'] = df_timeline['Week_of_Month'].apply(
        lambda x: f"Week {int(x)}" if pd.notna(x) and x <= 5 else "Week 4+" if pd.notna(x) else None
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📆 Revenue by Day of Week")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_revenue = df_timeline.groupby('DayOfWeek')['Final Total'].sum().reindex(day_order, fill_value=0)
        
        fig = go.Figure(data=[go.Bar(
            x=dow_revenue.index,
            y=dow_revenue.values,
            marker_color='#A23B72',
            text=[f"₹{v:,.0f}" for v in dow_revenue.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Day of Week", yaxis_title="Revenue (₹)", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📅 Revenue by Week of Month")
        st.caption("📊 For Staffing Planning")
        week_of_month_revenue = df_timeline.groupby('Week_of_Month')['Final Total'].sum().reindex(
            ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 4+'], fill_value=0
        )
        
        fig = go.Figure(data=[go.Bar(
            x=week_of_month_revenue.index,
            y=week_of_month_revenue.values,
            marker_color='#06A77D',
            text=[f"₹{v:,.0f}" for v in week_of_month_revenue.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Week of Month", yaxis_title="Revenue (₹)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Add insight
        max_week = week_of_month_revenue.idxmax()
        min_week = week_of_month_revenue.idxmin()
        max_val = week_of_month_revenue.max()
        min_val = week_of_month_revenue.min()
        variance = ((max_val - min_val) / min_val * 100) if min_val > 0 else 0
        
        st.info(f"""
        **Staffing Insight:**
        
        🔼 Highest: **{max_week}** (₹{max_val:,.0f})
        🔽 Lowest: **{min_week}** (₹{min_val:,.0f})
        📊 Variance: **{variance:.1f}%**
        
        💡 Plan {variance:.0f}% more staff for {max_week}
        """)
    
    with col3:
        st.markdown("#### ⏰ Revenue by Hour of Day")
        hourly_revenue = df_timeline.groupby('Hour')['Final Total'].sum()
        
        fig = go.Figure(data=[go.Bar(
            x=hourly_revenue.index,
            y=hourly_revenue.values,
            marker_color='#F18F01',
            text=[f"₹{v:,.0f}" for v in hourly_revenue.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Revenue (₹)", height=400)
        st.plotly_chart(fig, use_container_width=True)

# TAB 4: Net Revenue & Discounts
with tab4:
    st.markdown("### 💰 Net Revenue & Discount Analysis")
    
    # Calculate net metrics
    total_gross = df_filtered['Sub Total'].sum()
    total_discount = df_filtered['Discount'].sum()
    total_tax = df_filtered['Tax'].sum()
    total_net = df_filtered['Final Total'].sum()
    
    discount_rate = (total_discount / total_gross * 100) if total_gross > 0 else 0
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gross Revenue", f"₹{total_gross:,.0f}")
    with col2:
        st.metric("Total Discounts", f"₹{total_discount:,.0f}", delta=f"-{discount_rate:.1f}%")
    with col3:
        st.metric("Total Tax", f"₹{total_tax:,.0f}")
    with col4:
        st.metric("Net Revenue", f"₹{total_net:,.0f}")
    
    st.markdown("---")
    
    # Discount analysis by channel
    st.markdown("### 📊 Discount Analysis by Sales Channel")
    
    channel_discount = df_filtered.groupby('Sales Channel').agg({
        'Sub Total': 'sum',
        'Discount': 'sum',
        'Final Total': 'sum',
        'Invoice No.': 'nunique'
    }).reset_index()
    
    channel_discount['Discount %'] = (channel_discount['Discount'] / channel_discount['Sub Total'] * 100).round(2)
    channel_discount['Net AOV'] = (channel_discount['Final Total'] / channel_discount['Invoice No.']).round(2)
    channel_discount['Gross AOV'] = (channel_discount['Sub Total'] / channel_discount['Invoice No.']).round(2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💸 Discount % by Channel")
        fig = go.Figure(data=[go.Bar(
            x=channel_discount['Sales Channel'],
            y=channel_discount['Discount %'],
            marker_color=['#06A77D', '#D4A373'],
            text=channel_discount['Discount %'].round(1),
            texttemplate='%{text}%',
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="Sales Channel", yaxis_title="Discount %", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Gross AOV vs Net AOV by Channel")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Gross AOV',
            x=channel_discount['Sales Channel'],
            y=channel_discount['Gross AOV'],
            text=channel_discount['Gross AOV'].round(0),
            textposition='auto',
            marker_color='#A8DADC'
        ))
        fig.add_trace(go.Bar(
            name='Net AOV',
            x=channel_discount['Sales Channel'],
            y=channel_discount['Net AOV'],
            text=channel_discount['Net AOV'].round(0),
            textposition='auto',
            marker_color='#457B9D'
        ))
        fig.update_layout(
            xaxis_title="Sales Channel",
            yaxis_title="AOV (₹)",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.markdown("### 📋 Detailed Discount Metrics by Channel")
    
    channel_display = channel_discount[['Sales Channel', 'Sub Total', 'Discount', 'Discount %', 'Final Total', 'Gross AOV', 'Net AOV']].copy()
    channel_display.columns = ['Channel', 'Gross Revenue', 'Total Discount', 'Discount %', 'Net Revenue', 'Gross AOV', 'Net AOV']
    channel_display['Gross Revenue'] = channel_display['Gross Revenue'].apply(lambda x: f"₹{x:,.0f}")
    channel_display['Total Discount'] = channel_display['Total Discount'].apply(lambda x: f"₹{x:,.0f}")
    channel_display['Net Revenue'] = channel_display['Net Revenue'].apply(lambda x: f"₹{x:,.0f}")
    channel_display['Gross AOV'] = channel_display['Gross AOV'].apply(lambda x: f"₹{x:,.2f}")
    channel_display['Net AOV'] = channel_display['Net AOV'].apply(lambda x: f"₹{x:,.2f}")
    
    st.dataframe(channel_display, use_container_width=True, hide_index=True)
    
    # Monthly discount trend
    st.markdown("---")
    st.markdown("### 📈 Monthly Discount Trends")
    
    monthly_discount = df_filtered.groupby('Month-Year').agg({
        'Sub Total': 'sum',
        'Discount': 'sum',
        'Final Total': 'sum'
    }).reset_index()
    monthly_discount['Discount %'] = (monthly_discount['Discount'] / monthly_discount['Sub Total'] * 100).round(2)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(name='Discount Amount', x=monthly_discount['Month-Year'], y=monthly_discount['Discount'],
               marker_color='#E63946'),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(name='Discount %', x=monthly_discount['Month-Year'], y=monthly_discount['Discount %'],
                   mode='lines+markers', line=dict(color='#F18F01', width=3), marker=dict(size=8)),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Discount Amount (₹)", secondary_y=False)
    fig.update_yaxes(title_text="Discount %", secondary_y=True)
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Discount insights
    st.markdown("---")
    st.markdown("### 💡 Key Discount Insights")
    
    # Find highest discount channel
    max_discount_channel = channel_discount.loc[channel_discount['Discount %'].idxmax(), 'Sales Channel']
    max_discount_pct = channel_discount['Discount %'].max()
    
    col_i1, col_i2, col_i3 = st.columns(3)
    
    with col_i1:
        st.info(f"""
        **Highest Discount Channel**
        
        {max_discount_channel} offers the highest average discount at {max_discount_pct:.1f}%
        """)
    
    with col_i2:
        net_impact = total_discount / total_net * 100
        st.warning(f"""
        **Discount Impact**
        
        Discounts represent {net_impact:.1f}% of net revenue
        """)
    
    with col_i3:
        aov_diff = channel_discount['Gross AOV'].max() - channel_discount['Net AOV'].max()
        st.success(f"""
        **AOV Impact**
        
        Max AOV reduced by ₹{aov_diff:.2f} due to discounts
        """)

# TAB 5: Trends Analysis
with tab5:
    st.markdown("### 📊 Detailed Trends Analysis")
    st.info("📈 Month-on-month analysis of units sold and net revenue with advanced filtering")
    
    # Smart cascading filters
    st.markdown("#### 🎛️ Trend Filters")
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        st.markdown("**Online/Offline**")
        channel_options = ['All'] + sorted([str(c) for c in df_revenue['Sales Channel'].dropna().unique()])
        selected_trend_channel = st.selectbox(
            "Select Channel",
            channel_options,
            key='trend_channel',
            help="Filter by online or offline sales"
        )
    
    with col_f2:
        st.markdown("**Outlet**")
        # Filter outlets based on channel if needed
        if selected_trend_channel != 'All':
            filtered_outlets = df_revenue[df_revenue['Sales Channel'] == selected_trend_channel]
        else:
            filtered_outlets = df_revenue
        
        outlet_options = ['All'] + sorted([str(o) for o in filtered_outlets['Outlet'].dropna().unique()])
        selected_trend_outlet = st.selectbox(
            "Select Outlet",
            outlet_options,
            key='trend_outlet',
            help="Filter by specific outlet"
        )
    
    with col_f3:
        st.markdown("**Parent Category**")
        parent_options = ['All'] + sorted([str(p) for p in df_quantity['Parent Category'].dropna().unique() if p not in ['Unknown', '']])
        selected_trend_parents = st.multiselect(
            "Select Categories",
            parent_options,
            default=None,
            key='trend_parent',
            help="Select one or more parent categories"
        )
    
    with col_f4:
        st.markdown("**Sub Category**")
        # Filter based on selected parents
        if selected_trend_parents:
            filtered_for_subs = df_quantity[df_quantity['Parent Category'].isin(selected_trend_parents)]
        else:
            filtered_for_subs = df_quantity
        
        sub_options = ['All'] + sorted([str(s) for s in filtered_for_subs['Sub Category'].dropna().unique() if s not in ['Unknown', '']])
        selected_trend_subs = st.multiselect(
            "Select Sub Categories",
            sub_options,
            default=None,
            key='trend_sub',
            help="Auto-filtered by parent. Select one or more"
        )
    
    with col_f5:
        st.markdown("**Real Item Name**")
        # Filter based on selected sub-categories
        if selected_trend_subs:
            filtered_for_items_trend = df_quantity[df_quantity['Sub Category'].isin(selected_trend_subs)]
        elif selected_trend_parents:
            filtered_for_items_trend = df_quantity[df_quantity['Parent Category'].isin(selected_trend_parents)]
        else:
            filtered_for_items_trend = df_quantity
        
        item_options = ['All'] + sorted([str(i) for i in filtered_for_items_trend['Real Item Name'].dropna().unique()][:100])
        selected_trend_items = st.multiselect(
            "Select Items (Top 100)",
            item_options,
            default=None,
            key='trend_items',
            help="Auto-filtered. Select specific items"
        )
    
    # Apply all filters
    df_trends = df_revenue.copy()  # Use df_revenue for revenue, df_quantity for units
    df_trends_qty = df_quantity.copy()
    
    if selected_trend_channel != 'All':
        df_trends = df_trends[df_trends['Sales Channel'] == selected_trend_channel]
        df_trends_qty = df_trends_qty[df_trends_qty['Sales Channel'] == selected_trend_channel]
    
    if selected_trend_outlet != 'All':
        df_trends = df_trends[df_trends['Outlet'] == selected_trend_outlet]
        df_trends_qty = df_trends_qty[df_trends_qty['Outlet'] == selected_trend_outlet]
    
    if selected_trend_parents:
        df_trends = df_trends[df_trends['Parent Category'].isin(selected_trend_parents)]
        df_trends_qty = df_trends_qty[df_trends_qty['Parent Category'].isin(selected_trend_parents)]
    
    if selected_trend_subs:
        df_trends = df_trends[df_trends['Sub Category'].isin(selected_trend_subs)]
        df_trends_qty = df_trends_qty[df_trends_qty['Sub Category'].isin(selected_trend_subs)]
    
    if selected_trend_items:
        df_trends = df_trends[df_trends['Real Item Name'].isin(selected_trend_items)]
        df_trends_qty = df_trends_qty[df_trends_qty['Real Item Name'].isin(selected_trend_items)]
    
    if len(df_trends) > 0:
        st.markdown("---")
        
        # Calculate monthly metrics
        monthly_metrics = df_trends.groupby('Month-Year').agg({
            'Sub Total': 'sum',
            'Tax': 'sum',
            'Final Total': 'sum'
        }).reset_index()
        monthly_metrics.columns = ['Month', 'Gross Revenue', 'Tax', 'Net Sales (After Tax)']
        
        monthly_units = df_trends_qty.groupby('Month-Year')['Qty.'].sum().reset_index()
        monthly_units.columns = ['Month', 'Units Sold']
        
        # Merge
        monthly_combined = monthly_metrics.merge(monthly_units, on='Month', how='left')
        
        # Display charts
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("### 📦 Month-on-Month Units Sold")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_combined['Month'],
                y=monthly_combined['Units Sold'],
                marker_color='#2E86AB',
                text=monthly_combined['Units Sold'].round(0),
                textposition='auto',
                name='Units'
            ))
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Units Sold",
                height=450,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
        
        with col_c2:
            st.markdown("### 💰 Month-on-Month Net Sales (After Tax)")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_combined['Month'],
                y=monthly_combined['Net Sales (After Tax)'],
                marker_color='#06A77D',
                text=[f"₹{v:,.0f}" for v in monthly_combined['Net Sales (After Tax)']],
                textposition='auto',
                name='Net Sales'
            ))
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Net Sales (₹)",
                height=450,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
        
        # Combined dual-axis chart
        st.markdown("---")
        st.markdown("### 📊 Combined Trend: Units vs Revenue")
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                name='Units Sold',
                x=monthly_combined['Month'],
                y=monthly_combined['Units Sold'],
                marker_color='rgba(46, 134, 171, 0.7)',
                yaxis='y',
                offsetgroup=1
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                name='Net Sales',
                x=monthly_combined['Month'],
                y=monthly_combined['Net Sales (After Tax)'],
                mode='lines+markers',
                line=dict(color='#06A77D', width=3),
                marker=dict(size=10),
                yaxis='y2'
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Units Sold", secondary_y=False)
        fig.update_yaxes(title_text="Net Sales (₹)", secondary_y=True)
        fig.update_layout(height=450, hovermode='x unified')
        
        st.plotly_chart(fig, width='stretch')
        
        # Insights section
        st.markdown("---")
        st.markdown("### 💡 Trend Insights")
        
        # Calculate growth rates
        if len(monthly_combined) >= 2:
            # Month-on-month growth
            monthly_combined['Units Growth %'] = monthly_combined['Units Sold'].pct_change() * 100
            monthly_combined['Revenue Growth %'] = monthly_combined['Net Sales (After Tax)'].pct_change() * 100
            
            # Latest month stats
            latest_month = monthly_combined.iloc[-1]
            previous_month = monthly_combined.iloc[-2] if len(monthly_combined) >= 2 else None
            
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            
            with col_i1:
                units_growth = latest_month['Units Growth %']
                st.metric(
                    "Latest Units Growth",
                    f"{latest_month['Units Sold']:,.0f}",
                    delta=f"{units_growth:+.1f}% MoM"
                )
            
            with col_i2:
                revenue_growth = latest_month['Revenue Growth %']
                st.metric(
                    "Latest Revenue Growth",
                    f"₹{latest_month['Net Sales (After Tax)']:,.0f}",
                    delta=f"{revenue_growth:+.1f}% MoM"
                )
            
            with col_i3:
                avg_units = monthly_combined['Units Sold'].mean()
                latest_vs_avg = ((latest_month['Units Sold'] - avg_units) / avg_units * 100)
                st.metric(
                    "Avg Monthly Units",
                    f"{avg_units:,.0f}",
                    delta=f"{latest_vs_avg:+.1f}% vs avg"
                )
            
            with col_i4:
                avg_revenue = monthly_combined['Net Sales (After Tax)'].mean()
                latest_rev_vs_avg = ((latest_month['Net Sales (After Tax)'] - avg_revenue) / avg_revenue * 100)
                st.metric(
                    "Avg Monthly Revenue",
                    f"₹{avg_revenue:,.0f}",
                    delta=f"{latest_rev_vs_avg:+.1f}% vs avg"
                )
            
            # Detailed insights
            st.markdown("---")
            
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                # Best and worst months
                best_month_units = monthly_combined.loc[monthly_combined['Units Sold'].idxmax()]
                worst_month_units = monthly_combined.loc[monthly_combined['Units Sold'].idxmin()]
                
                st.success(f"""
                **Units Performance**
                
                🔼 Best Month: **{best_month_units['Month']}** ({best_month_units['Units Sold']:,.0f} units)
                🔽 Worst Month: **{worst_month_units['Month']}** ({worst_month_units['Units Sold']:,.0f} units)
                📊 Range: {((best_month_units['Units Sold'] - worst_month_units['Units Sold']) / worst_month_units['Units Sold'] * 100):.1f}% variance
                """)
            
            with col_insight2:
                best_month_rev = monthly_combined.loc[monthly_combined['Net Sales (After Tax)'].idxmax()]
                worst_month_rev = monthly_combined.loc[monthly_combined['Net Sales (After Tax)'].idxmin()]
                
                st.info(f"""
                **Revenue Performance**
                
                🔼 Best Month: **{best_month_rev['Month']}** (₹{best_month_rev['Net Sales (After Tax)']:,.0f})
                🔽 Worst Month: **{worst_month_rev['Month']}** (₹{worst_month_rev['Net Sales (After Tax)']:,.0f})
                📊 Range: {((best_month_rev['Net Sales (After Tax)'] - worst_month_rev['Net Sales (After Tax)']) / worst_month_rev['Net Sales (After Tax)'] * 100):.1f}% variance
                """)
            
            # Trend direction
            st.markdown("---")
            
            # Calculate overall trend (first 3 months vs last 3 months)
            if len(monthly_combined) >= 6:
                first_3_units = monthly_combined.head(3)['Units Sold'].mean()
                last_3_units = monthly_combined.tail(3)['Units Sold'].mean()
                units_trend = ((last_3_units - first_3_units) / first_3_units * 100)
                
                first_3_revenue = monthly_combined.head(3)['Net Sales (After Tax)'].mean()
                last_3_revenue = monthly_combined.tail(3)['Net Sales (After Tax)'].mean()
                revenue_trend = ((last_3_revenue - first_3_revenue) / first_3_revenue * 100)
                
                col_trend1, col_trend2 = st.columns(2)
                
                with col_trend1:
                    trend_icon = "📈" if units_trend > 0 else "📉" if units_trend < 0 else "➡️"
                    trend_color = "success" if units_trend > 5 else "error" if units_trend < -5 else "info"
                    
                    if trend_color == "success":
                        st.success(f"""
                        {trend_icon} **Overall Units Trend: {units_trend:+.1f}%**
                        
                        First 3 months avg: {first_3_units:,.0f} units
                        Last 3 months avg: {last_3_units:,.0f} units
                        
                        Trend: **Growing** 🚀
                        """)
                    elif trend_color == "error":
                        st.error(f"""
                        {trend_icon} **Overall Units Trend: {units_trend:+.1f}%**
                        
                        First 3 months avg: {first_3_units:,.0f} units
                        Last 3 months avg: {last_3_units:,.0f} units
                        
                        Trend: **Declining** ⚠️
                        """)
                    else:
                        st.info(f"""
                        {trend_icon} **Overall Units Trend: {units_trend:+.1f}%**
                        
                        First 3 months avg: {first_3_units:,.0f} units
                        Last 3 months avg: {last_3_units:,.0f} units
                        
                        Trend: **Stable**
                        """)
                
                with col_trend2:
                    rev_trend_icon = "📈" if revenue_trend > 0 else "📉" if revenue_trend < 0 else "➡️"
                    rev_trend_color = "success" if revenue_trend > 5 else "error" if revenue_trend < -5 else "info"
                    
                    if rev_trend_color == "success":
                        st.success(f"""
                        {rev_trend_icon} **Overall Revenue Trend: {revenue_trend:+.1f}%**
                        
                        First 3 months avg: ₹{first_3_revenue:,.0f}
                        Last 3 months avg: ₹{last_3_revenue:,.0f}
                        
                        Trend: **Growing** 🚀
                        """)
                    elif rev_trend_color == "error":
                        st.error(f"""
                        {rev_trend_icon} **Overall Revenue Trend: {revenue_trend:+.1f}%**
                        
                        First 3 months avg: ₹{first_3_revenue:,.0f}
                        Last 3 months avg: ₹{last_3_revenue:,.0f}
                        
                        Trend: **Declining** ⚠️
                        """)
                    else:
                        st.info(f"""
                        {rev_trend_icon} **Overall Revenue Trend: {revenue_trend:+.1f}%**
                        
                        First 3 months avg: ₹{first_3_revenue:,.0f}
                        Last 3 months avg: ₹{last_3_revenue:,.0f}
                        
                        Trend: **Stable**
                        """)
            
            # Detailed monthly table
            st.markdown("---")
            st.markdown("### 📋 Detailed Monthly Data")
            
            display_monthly = monthly_combined[['Month', 'Units Sold', 'Gross Revenue', 'Tax', 'Net Sales (After Tax)', 'Units Growth %', 'Revenue Growth %']].copy()
            display_monthly['Gross Revenue'] = display_monthly['Gross Revenue'].apply(lambda x: f"₹{x:,.0f}")
            display_monthly['Tax'] = display_monthly['Tax'].apply(lambda x: f"₹{x:,.0f}")
            display_monthly['Net Sales (After Tax)'] = display_monthly['Net Sales (After Tax)'].apply(lambda x: f"₹{x:,.0f}")
            display_monthly['Units Sold'] = display_monthly['Units Sold'].apply(lambda x: f"{x:,.0f}")
            display_monthly['Units Growth %'] = display_monthly['Units Growth %'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")
            display_monthly['Revenue Growth %'] = display_monthly['Revenue Growth %'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")
            
            st.dataframe(display_monthly, width='stretch', hide_index=True)
            
            # Download option
            csv_trends = monthly_combined.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Trends Data (CSV)",
                data=csv_trends,
                file_name="monthly_trends_analysis.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No data available for selected filters. Please adjust your selection.")
    else:
        st.warning("⚠️ No data available. Please adjust filters.")

# TAB 6: Basket Analysis  
with tab6:
    st.markdown("### 🔗 Market Basket Analysis")
    
    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        
        # Prepare transaction data
        basket_df = df_filtered.groupby(['Invoice No.', 'Real Item Name'])['Qty.'].sum().unstack(fill_value=0)
        basket_binary = basket_df.map(lambda x: 1 if x > 0 else 0)
        
        st.markdown("#### 🔝 Most Frequently Purchased Items")
        item_frequency = basket_binary.sum().sort_values(ascending=False).head(20)
        item_frequency_pct = (item_frequency / len(basket_binary) * 100)
        
        fig = go.Figure(data=[go.Bar(
            x=item_frequency_pct.values,
            y=item_frequency_pct.index,
            orientation='h',
            marker_color='#2E86AB',
            text=[f"{v:.1f}%" for v in item_frequency_pct.values],
            textposition='auto'
        )])
        fig.update_layout(xaxis_title="% of Transactions", yaxis_title="Item", height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Association rules
        frequent_itemsets = apriori(basket_binary, min_support=0.01, use_colnames=True)
        
        if len(frequent_itemsets) > 0:
            frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
            
            if len(frequent_itemsets[frequent_itemsets['length'] >= 2]) > 0:
                rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
                rules = rules.sort_values('lift', ascending=False)
                
                st.markdown("#### 🔗 Top Association Rules")
                
                top_rules = rules.head(10).copy()
                top_rules['rule'] = top_rules.apply(
                    lambda x: f"{list(x['antecedents'])[0][:20]} -> {list(x['consequents'])[0][:20]}", 
                    axis=1
                )
                
                fig = go.Figure(data=[go.Bar(
                    x=top_rules['lift'],
                    y=top_rules['rule'],
                    orientation='h',
                    marker_color='#D62828',
                    text=top_rules['lift'].round(2),
                    textposition='auto'
                )])
                fig.update_layout(
                    title="Top 10 Association Rules by Lift",
                    xaxis_title="Lift",
                    yaxis_title="Rule (If -> Then)",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("#### 📋 Detailed Association Rules")
                rules_display = rules.head(20).copy()
                rules_display['Antecedent'] = rules_display['antecedents'].apply(lambda x: ', '.join(list(x)))
                rules_display['Consequent'] = rules_display['consequents'].apply(lambda x: ', '.join(list(x)))
                rules_display = rules_display[['Antecedent', 'Consequent', 'support', 'confidence', 'lift']]
                rules_display.columns = ['If Customer Buys', 'Then They May Buy', 'Support', 'Confidence', 'Lift']
                rules_display['Support'] = rules_display['Support'].apply(lambda x: f"{x:.4f}")
                rules_display['Confidence'] = rules_display['Confidence'].apply(lambda x: f"{x:.2%}")
                rules_display['Lift'] = rules_display['Lift'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(rules_display, use_container_width=True, hide_index=True)
            else:
                st.warning("Not enough frequent itemsets with 2+ items found.")
        else:
            st.warning("No frequent itemsets found with current support threshold.")
    
    except Exception as e:
        st.error(f"Error in basket analysis: {str(e)}")

# TAB 7: Revenue Forecast
with tab7:
    st.markdown("### 🔮 Revenue Forecast")
    
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        
        daily_revenue = df_revenue.groupby('Date')['Final Total'].sum().sort_index()
        daily_revenue = daily_revenue.asfreq('D', fill_value=0)
        
        st.markdown("#### 📈 Historical Daily Revenue")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_revenue.index,
            y=daily_revenue.values,
            mode='lines',
            name='Daily Revenue',
            line=dict(color='#2E86AB', width=2)
        ))
        fig.update_layout(xaxis_title="Date", yaxis_title="Revenue (₹)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30, step=1)
        
        if st.button("🔮 Generate Forecast", type="primary"):
            with st.spinner("Building forecast model..."):
                try:
                    model = SARIMAX(
                        daily_revenue,
                        order=(1, 1, 1),
                        seasonal_order=(1, 1, 1, 7),
                        enforce_stationarity=False,
                        enforce_invertibility=False
                    )
                    results = model.fit(disp=False)
                    
                    forecast = results.get_forecast(steps=forecast_days)
                    forecast_df = forecast.summary_frame()
                    
                    last_date = daily_revenue.index.max()
                    forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days, freq='D')
                    forecast_df.index = forecast_dates
                    
                    st.markdown("#### 🔮 Forecast Results")
                    
                    fig = go.Figure()
                    
                    recent_data = daily_revenue.tail(60)
                    fig.add_trace(go.Scatter(
                        x=recent_data.index,
                        y=recent_data.values,
                        mode='lines',
                        name='Historical',
                        line=dict(color='#2E86AB', width=2)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=forecast_df.index,
                        y=forecast_df['mean'],
                        mode='lines',
                        name='Forecast',
                        line=dict(color='#D62828', width=2, dash='dash')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=forecast_df.index.tolist() + forecast_df.index.tolist()[::-1],
                        y=forecast_df['mean_ci_upper'].tolist() + forecast_df['mean_ci_lower'].tolist()[::-1],
                        fill='toself',
                        fillcolor='rgba(214, 40, 40, 0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        name='95% Confidence Interval',
                        showlegend=True
                    ))
                    
                    fig.update_layout(xaxis_title="Date", yaxis_title="Daily Revenue (₹)", height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Forecasted Revenue", f"₹{forecast_df['mean'].sum():,.0f}")
                    
                    with col2:
                        st.metric("Average Daily Forecast", f"₹{forecast_df['mean'].mean():,.0f}")
                    
                    with col3:
                        current_avg = daily_revenue.tail(30).mean()
                        forecast_avg = forecast_df['mean'].mean()
                        change = ((forecast_avg - current_avg) / current_avg * 100)
                        st.metric("Forecast vs Current", f"{change:+.1f}%")
                    
                    st.success(f"✅ Forecast generated successfully for {forecast_days} days!")
                    
                except Exception as e:
                    st.error(f"Error generating forecast: {str(e)}")
        
    except Exception as e:
        st.error(f"Error in forecast tab: {str(e)}")

# TAB 8: Weekly Unit Forecast
with tab8:
    st.markdown("### 📦 Weekly Unit Forecast")
    st.info("📊 Select filters and click Submit to generate Week 1 & Week 2 unit forecasts")
    
    # Calculate historical average units by day of week for categories
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Create clean filter interface
    st.markdown("#### 🎛️ Forecast Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 1. Outlet Type filter
        st.markdown("**1️⃣ Outlet Type**")
        outlet_values = df_revenue['Outlet'].dropna().unique().tolist()
        outlet_list = sorted([str(o) for o in outlet_values if o not in ['', 'nan', 'None']])
        outlet_options = ['All'] + outlet_list
        selected_outlets = st.selectbox(
            "Select Outlet",
            outlet_options,
            help="Choose which outlet to forecast",
            key='wf_outlet'
        )
    
    with col2:
        # 2. Parent Category filter - multi-select
        st.markdown("**2️⃣ Parent Category**")
        parent_cat_vals = df_revenue['Parent Category'].dropna().unique().tolist()
        parent_categories = sorted([str(p) for p in parent_cat_vals if p not in ['Unknown', '', 'nan', 'None']])
        
        selected_parents = st.multiselect(
            "Select Parent Categories",
            parent_categories,
            default=None,
            help="Select one or more parent categories (leave empty for all)",
            key='wf_parent'
        )
    
    with col3:
        # 3. Sub Category filter - cascading from parent, multi-select
        st.markdown("**3️⃣ Sub Category**")
        
        # Filter sub-categories based on selected parents
        if selected_parents:
            filtered_for_sub = df_revenue[df_revenue['Parent Category'].isin(selected_parents)]
        else:
            filtered_for_sub = df_revenue
        
        available_subcats = filtered_for_sub['Sub Category'].dropna().unique().tolist()
        available_subcats = sorted([str(s) for s in available_subcats if s not in ['Unknown', '', 'nan', 'None']])
        
        selected_subcats = st.multiselect(
            "Select Sub Categories",
            available_subcats,
            default=None,
            help="Auto-filtered by parent category. Select one or more (leave empty for all)",
            key='wf_subcat'
        )
    
    with col4:
        # 4. Real Item Name filter - cascading from sub-category, multi-select
        st.markdown("**4️⃣ Real Item Name**")
        
        # Filter items based on selected sub-categories
        if selected_subcats:
            filtered_for_items = df_revenue[df_revenue['Sub Category'].isin(selected_subcats)]
        elif selected_parents:
            filtered_for_items = df_revenue[df_revenue['Parent Category'].isin(selected_parents)]
        else:
            filtered_for_items = df_revenue
        
        available_items = filtered_for_items['Real Item Name'].dropna().unique().tolist()
        available_items = sorted([str(i) for i in available_items if i not in ['Unknown', '', 'nan', 'None']])
        
        selected_items = st.multiselect(
            "Select Real Item Names",
            available_items,
            default=None,
            help="Auto-filtered by sub-category. Select specific items (leave empty for all)",
            key='wf_items'
        )
    
    # Forecast adjustment factor with info button
    st.markdown("---")
    col_slider, col_info = st.columns([4, 1])
    
    with col_slider:
        growth_factor = st.slider(
            "📈 Forecast Adjustment Factor (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5,
            help="Adjust forecast up or down based on expected growth/decline",
            key='wf_growth'
        )
    
    with col_info:
        st.markdown("")
        st.markdown("")
        with st.expander("ℹ️ What is this?"):
            st.markdown("""
            **Forecast Adjustment Factor**
            
            Use this to adjust the historical average forecasts:
            
            - **0%** = Use pure historical averages
            - **+20%** = Increase forecast by 20% (e.g., expecting festival season)
            - **-15%** = Decrease forecast by 15% (e.g., expecting slowdown)
            
            **When to adjust:**
            - Upcoming festivals/holidays
            - Marketing campaigns planned
            - New menu items launching
            - Seasonal changes
            - Competitor activity
            
            The adjustment applies to all forecasted values.
            """)
    
    # Submit button
    st.markdown("")
    if st.button("🚀 Submit & Generate Forecast", type="primary", use_container_width=True):
        with st.spinner("Generating weekly unit forecasts..."):
            try:
                # Filter data based on selections (use QUANTITY data for accurate unit counts)
                df_forecast_data = df_quantity.copy()
                
                # Apply outlet filter
                if selected_outlets != 'All':
                    df_forecast_data = df_forecast_data[df_forecast_data['Outlet'] == selected_outlets]
                    outlet_label = selected_outlets
                else:
                    outlet_label = "All Outlets"
                
                # Apply parent category filter
                if selected_parents:
                    df_forecast_data = df_forecast_data[df_forecast_data['Parent Category'].isin(selected_parents)]
                    parent_label = ', '.join(selected_parents) if len(selected_parents) <= 3 else f"{len(selected_parents)} categories"
                else:
                    parent_label = "All Categories"
                
                # Apply sub-category filter
                if selected_subcats:
                    df_forecast_data = df_forecast_data[df_forecast_data['Sub Category'].isin(selected_subcats)]
                    subcat_label = ', '.join(selected_subcats) if len(selected_subcats) <= 3 else f"{len(selected_subcats)} sub-categories"
                else:
                    subcat_label = "All Sub-Categories"
                
                # Apply real item name filter
                if selected_items:
                    df_forecast_data = df_forecast_data[df_forecast_data['Real Item Name'].isin(selected_items)]
                    item_label = ', '.join(selected_items) if len(selected_items) <= 3 else f"{len(selected_items)} items"
                    group_col = 'Real Item Name'
                elif selected_subcats:
                    # Group by real item name if sub-category is selected
                    group_col = 'Real Item Name'
                    item_label = "All Items"
                elif selected_parents:
                    # Group by sub-category if only parent is selected
                    group_col = 'Sub Category'
                    item_label = "All Items"
                else:
                    # Default to parent category if nothing specific selected
                    group_col = 'Parent Category'
                    item_label = "All Items"
                
                # Check if we have data
                if len(df_forecast_data) == 0:
                    st.warning("⚠️ No data available for the selected filters. Please adjust your selection.")
                    st.stop()
                
                # Calculate CORRECT average units per day of week per category/sub-category
                # IMPORTANT: Handle items with different launch dates (not sold from Feb)
                
                # Step 1: Find first sale date for each item/category
                first_sale_dates = df_forecast_data.groupby(group_col)['Date'].min().to_dict()
                
                # Step 2: Calculate average ONLY from launch date onwards for each item
                dow_averages_list = []
                
                for item_name, launch_date in first_sale_dates.items():
                    # Filter to only data from this item's launch date onwards
                    item_data = df_forecast_data[
                        (df_forecast_data[group_col] == item_name) & 
                        (df_forecast_data['Date'] >= launch_date)
                    ].copy()
                    
                    # Sum quantity per day
                    daily_totals = item_data.groupby(['Date', 'DayOfWeek'])['Qty.'].sum().reset_index()
                    
                    # Calculate average per day of week (only for days AFTER launch)
                    dow_avg = daily_totals.groupby('DayOfWeek')['Qty.'].mean()
                    
                    # Add item name to the series
                    for dow in dow_avg.index:
                        dow_averages_list.append({
                            group_col: item_name,
                            'DayOfWeek': dow,
                            'Avg_Qty': dow_avg[dow],
                            'Launch_Date': launch_date,
                            'Days_in_Market': (df_forecast_data['Date'].max() - launch_date).days
                        })
                
                # Convert to DataFrame
                dow_category_avg_df = pd.DataFrame(dow_averages_list)
                
                # Pivot to get days as columns
                dow_category_avg = dow_category_avg_df.pivot(index=group_col, columns='DayOfWeek', values='Avg_Qty')
                dow_category_avg = dow_category_avg.reindex(columns=day_order, fill_value=0)
                
                # Check if pivot produced data
                if len(dow_category_avg) == 0:
                    st.warning("⚠️ No forecast data available. Try different filters.")
                    st.stop()
                
                # Show calculation methodology
                with st.expander("📊 View Calculation Details"):
                    st.markdown(f"""
                    **Forecast Calculation Method:**
                    
                    1. **Data Filtered:** {len(df_forecast_data):,} transactions
                    2. **Grouping Level:** {group_col}
                    3. **Calculation Method:**
                       - For each item/category, find its FIRST SALE DATE (launch date)
                       - Calculate averages ONLY from launch date onwards
                       - This handles new items launched in April, May, or June
                       - Sum all units sold per day (by {group_col})
                       - Average those daily totals by day of week
                    
                    4. **Overall Date Range:** {df_forecast_data['Date'].min().strftime('%Y-%m-%d')} to {df_forecast_data['Date'].max().strftime('%Y-%m-%d')}
                    5. **Total Items/Categories:** {len(first_sale_dates)}
                    6. **Adjustment Applied:** {growth_factor:+d}%
                    """)
                    
                    st.markdown("**Item Launch Dates (First Sale):**")
                    launch_info = pd.DataFrame([
                        {
                            'Item/Category': k,
                            'Launch Date': v.strftime('%Y-%m-%d'),
                            'Days in Market': (df_forecast_data['Date'].max() - v).days
                        }
                        for k, v in first_sale_dates.items()
                    ]).sort_values('Launch Date')
                    st.dataframe(launch_info, use_container_width=True, hide_index=True)
                    
                    st.info("""
                    ℹ️ **Why this matters:** Items launched in April/May/June won't have their averages 
                    diluted by zero-sales months (Feb/Mar). Each item's forecast is based only on 
                    the period it was actually available for sale.
                    """)
                
                # Apply growth factor adjustment
                adjustment = 1 + (growth_factor / 100)
                dow_category_forecast = dow_category_avg * adjustment
                
                # Create Week 1 and Week 2 forecasts with date ranges
                # Calculate next Monday as Week 1 start
                today = pd.Timestamp.now()
                days_until_monday = (7 - today.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7  # If today is Monday, start from next Monday
                
                week1_start = today + pd.Timedelta(days=days_until_monday)
                week1_end = week1_start + pd.Timedelta(days=6)
                week2_start = week1_end + pd.Timedelta(days=1)
                week2_end = week2_start + pd.Timedelta(days=6)
                
                week1_forecast = dow_category_forecast.copy()
                week2_forecast = dow_category_forecast.copy()
                
                # Build forecast title
                forecast_title = f"{outlet_label}"
                if parent_label != "All Categories":
                    forecast_title += f" | {parent_label}"
                if selected_subcats:
                    forecast_title += f" | {subcat_label}"
                if selected_items:
                    forecast_title += f" | {item_label}"
                
                # Display summary
                st.markdown("---")
                st.success(f"✅ Forecast Generated: {forecast_title}")
                
                # Show filter summary
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                with col_sum1:
                    st.metric("🏪 Outlet", outlet_label)
                with col_sum2:
                    st.metric("📦 Parent", parent_label)
                with col_sum3:
                    st.metric("🎯 Sub Category", subcat_label)
                with col_sum4:
                    st.metric("🍜 Item", item_label)
                
                # Display forecasts
                st.markdown("---")
                st.markdown(f"### 📅 Week 1: {week1_start.strftime('%b %d')} - {week1_end.strftime('%b %d, %Y')} (Monday-Sunday)")
                
                # Week 1 table (clean format)
                week1_display = week1_forecast.round(0).copy()
                week1_display['Total'] = week1_display.sum(axis=1)
                
                # Add launch date info for context
                week1_display['Launch Date'] = week1_display.index.map(first_sale_dates)
                week1_display['Days in Market'] = week1_display['Launch Date'].apply(
                    lambda x: (df_forecast_data['Date'].max() - x).days
                )
                
                # Mark new items (launched in last 90 days)
                week1_display['Status'] = week1_display['Days in Market'].apply(
                    lambda x: '🆕 New' if x < 90 else '✓'
                )
                
                # Reorder columns
                cols_order = ['Status', 'Days in Market', 'Launch Date'] + day_order + ['Total']
                week1_display = week1_display[cols_order]
                week1_display = week1_display.sort_values('Total', ascending=False)
                
                # Format launch date
                week1_display['Launch Date'] = week1_display['Launch Date'].dt.strftime('%Y-%m-%d')
                
                # Rename day columns to include dates for Week 1
                week1_dates = pd.date_range(week1_start, periods=7, freq='D')
                col_mapping = {day: f"{day}\n({week1_dates[i].strftime('%b %d')})" 
                              for i, day in enumerate(day_order)}
                week1_display_with_dates = week1_display.rename(columns=col_mapping)
                
                st.dataframe(
                    week1_display_with_dates.style.format({
                        'Days in Market': '{:.0f}',
                        **{col: '{:.0f}' for col in week1_display_with_dates.columns if col not in ['Status', 'Launch Date', 'Days in Market']}
                    }).background_gradient(cmap='Blues', subset=[c for c in week1_display_with_dates.columns if c not in ['Total', 'Status', 'Launch Date', 'Days in Market']]),
                    use_container_width=True
                )
                
                # Download button for Week 1
                csv1 = week1_display.to_csv()
                filename_base = f"{outlet_label}_{parent_label}".replace(' ', '_').replace(',', '').replace('|', '_')
                st.download_button(
                    label="⬇️ Download Week 1 Forecast (CSV)",
                    data=csv1,
                    file_name=f"week1_forecast_{filename_base}.csv",
                    mime="text/csv"
                )
                
                st.markdown("---")
                st.markdown(f"### 📅 Week 2: {week2_start.strftime('%b %d')} - {week2_end.strftime('%b %d, %Y')} (Monday-Sunday)")
                
                # Week 2 table (clean format)
                week2_display = week2_forecast.round(0).copy()
                week2_display['Total'] = week2_display.sum(axis=1)
                
                # Add launch date info for context (same as Week 1)
                week2_display['Launch Date'] = week2_display.index.map(first_sale_dates)
                week2_display['Days in Market'] = week2_display['Launch Date'].apply(
                    lambda x: (df_forecast_data['Date'].max() - x).days
                )
                week2_display['Status'] = week2_display['Days in Market'].apply(
                    lambda x: '🆕 New' if x < 90 else '✓'
                )
                
                # Reorder columns
                cols_order = ['Status', 'Days in Market', 'Launch Date'] + day_order + ['Total']
                week2_display = week2_display[cols_order]
                week2_display = week2_display.sort_values('Total', ascending=False)
                
                # Format launch date
                week2_display['Launch Date'] = week2_display['Launch Date'].dt.strftime('%Y-%m-%d')
                
                # Rename day columns to include dates for Week 2
                week2_dates = pd.date_range(week2_start, periods=7, freq='D')
                col_mapping2 = {day: f"{day}\n({week2_dates[i].strftime('%b %d')})" 
                               for i, day in enumerate(day_order)}
                week2_display_with_dates = week2_display.rename(columns=col_mapping2)
                
                st.dataframe(
                    week2_display_with_dates.style.format({
                        'Days in Market': '{:.0f}',
                        **{col: '{:.0f}' for col in week2_display_with_dates.columns if col not in ['Status', 'Launch Date', 'Days in Market']}
                    }).background_gradient(cmap='Greens', subset=[c for c in week2_display_with_dates.columns if c not in ['Total', 'Status', 'Launch Date', 'Days in Market']]),
                    use_container_width=True
                )
                
                # Download button for Week 2
                csv2 = week2_display.to_csv()
                st.download_button(
                    label="⬇️ Download Week 2 Forecast (CSV)",
                    data=csv2,
                    file_name=f"week2_forecast_{filename_base}.csv",
                    mime="text/csv"
                )
                
                # Combined 2-week summary
                st.markdown("---")
                st.markdown("### 📊 2-Week Summary")
                
                combined_summary = pd.DataFrame({
                    'Week 1 Total': week1_display['Total'],
                    'Week 2 Total': week2_display['Total']
                })
                combined_summary['2-Week Total'] = combined_summary['Week 1 Total'] + combined_summary['Week 2 Total']
                combined_summary = combined_summary.sort_values('2-Week Total', ascending=False)
                
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(
                    name='Week 1',
                    x=combined_summary.index[:15],
                    y=combined_summary['Week 1 Total'][:15],
                    text=combined_summary['Week 1 Total'][:15].round(0),
                    textposition='auto'
                ))
                fig3.add_trace(go.Bar(
                    name='Week 2',
                    x=combined_summary.index[:15],
                    y=combined_summary['Week 2 Total'][:15],
                    text=combined_summary['Week 2 Total'][:15].round(0),
                    textposition='auto'
                ))
                
                fig3.update_layout(
                    title=f"2-Week Comparison",
                    xaxis_title=group_col,
                    yaxis_title="Total Units",
                    barmode='group',
                    height=500
                )
                st.plotly_chart(fig3, use_container_width=True)
                
                # Download combined summary
                csv_combined = combined_summary.to_csv()
                st.download_button(
                    label="⬇️ Download 2-Week Summary (CSV)",
                    data=csv_combined,
                    file_name=f"2week_summary_{filename_base}.csv",
                    mime="text/csv"
                )
                
                # Methodology note
                with st.expander("ℹ️ Forecast Methodology"):
                    st.markdown("""
                    **How the forecast is calculated:**
                    
                    1. **Historical Averaging**: We calculate the average units sold per day of week for each category/item based on all historical data.
                    
                    2. **Weekly Pattern Recognition**: The forecast recognizes that different days have different demand patterns (e.g., weekends might be busier).
                    
                    3. **Adjustment Factor**: You can apply a growth/decline factor to adjust forecasts based on expected business changes.
                    
                    4. **Week 1 & Week 2**: Both weeks use the same daily patterns, assuming regular weekly cycles.
                    
                    **Use this forecast for:**
                    - Inventory planning
                    - Staff scheduling
                    - Ingredient procurement
                    - Production planning
                    
                    **Note**: Actual demand may vary due to holidays, promotions, weather, etc. Monitor and adjust as needed!
                    """)
                
            except Exception as e:
                st.error(f"Error generating forecast: {str(e)}")
                st.info("Please ensure you have sufficient historical data for accurate forecasts.")

# TAB 9: Send Targets (WhatsApp-Friendly Format)
with tab9:
    st.markdown("### 📱 Send Targets - WhatsApp Format")
    st.info("📊 Quick forecast view for sharing via WhatsApp/messaging")
    
    # Adjustment slider at top
    st.markdown("#### 📈 Set Forecast Adjustment")
    
    col_adj, col_info2 = st.columns([4, 1])
    
    with col_adj:
        target_adjustment = st.slider(
            "Forecast Adjustment Factor (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5,
            help="Adjust forecast up or down for targets",
            key='target_adjustment'
        )
    
    with col_info2:
        st.markdown("")
        st.markdown("")
        with st.expander("ℹ️ Help"):
            st.markdown("""
            **Adjustment Examples:**
            - **+20%** = Festival/promotion week
            - **0%** = Normal week (historical average)
            - **-15%** = Expected slowdown
            """)
    
    if st.button("🚀 Generate Targets Table", type="primary", use_container_width=True):
        with st.spinner("Generating targets..."):
            try:
                # Define the specific sub-categories to show (exact names from data)
                target_subcategories = [
                    'Chicken Momo', 'Veg Momo', 'Mutton Momo', 'Prawn Dumpling',
                    'Veg Laphing', 'Chicken Laphing', 'Mutton Laphing',
                    'Chicken Cigar Roll', 'Veg Cigar Roll', 'Himalayan Momo',
                    'Veg Frankie', 'Chicken Frankie', 'Mutton Frankie ',  # Note: trailing space
                    'Chicken Wonton', 'Prawn Wonton ', 'Veg Wonton',  # Note: Prawn has trailing space
                    'Chicken Sha-Phaley', 'Mutton Sha-Phaley'
                ]
                
                # Calculate next two weeks' date ranges
                today = pd.Timestamp.now()
                days_until_monday = (7 - today.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                
                week1_start = today + pd.Timedelta(days=days_until_monday)
                week1_end = week1_start + pd.Timedelta(days=6)
                week2_start = week1_end + pd.Timedelta(days=1)
                week2_end = week2_start + pd.Timedelta(days=6)
                
                # Calculate forecasts by outlet and sub-category
                targets_data = []
                
                for subcat in target_subcategories:
                    row_data = {'Sub Category': subcat.strip()}  # Remove trailing spaces for display
                    
                    for outlet in ['KV', 'Patia']:
                        # Filter data for this outlet and sub-category (use QUANTITY analysis for accurate units)
                        df_target = df_quantity[
                            (df_quantity['Outlet'] == outlet) &
                            (df_quantity['Sub Category'] == subcat)
                        ].copy()
                        
                        if len(df_target) > 0:
                            # Find launch date for this sub-category at this outlet
                            launch_date = df_target['Date'].min()
                            
                            # Filter to only post-launch data
                            df_target = df_target[df_target['Date'] >= launch_date]
                            
                            # Calculate daily totals
                            daily_totals = df_target.groupby('Date')['Qty.'].sum().reset_index()
                            daily_totals['DayOfWeek'] = pd.to_datetime(daily_totals['Date']).dt.day_name()
                            
                            # Average by day of week
                            weekly_avg = daily_totals.groupby('DayOfWeek')['Qty.'].mean().sum()
                            
                            # Apply adjustment
                            adjusted_forecast = weekly_avg * (1 + target_adjustment / 100)
                            
                            row_data[f'{outlet}'] = int(round(adjusted_forecast))
                        else:
                            row_data[f'{outlet}'] = 0
                    
                    # Calculate total
                    row_data['Total'] = row_data.get('KV', 0) + row_data.get('Patia', 0)
                    
                    targets_data.append(row_data)
                
                # Create DataFrame
                targets_df = pd.DataFrame(targets_data)
                
                # Create display format with both weeks
                display_data = []
                for _, row in targets_df.iterrows():
                    display_data.append({
                        'Sub Category': row['Sub Category'],
                        'KV (W1)': row.get('KV', 0),
                        'Patia (W1)': row.get('Patia', 0),
                        'Total (W1)': row.get('Total', 0),
                        'KV (W2)': row.get('KV', 0),
                        'Patia (W2)': row.get('Patia', 0),
                        'Total (W2)': row.get('Total', 0)
                    })
                
                targets_display = pd.DataFrame(display_data)
                
                # Display header with date ranges
                st.markdown("---")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.markdown(f"### 📅 Week 1: {week1_start.strftime('%b %d')} - {week1_end.strftime('%b %d, %Y')}")
                with col_h2:
                    st.markdown(f"### 📅 Week 2: {week2_start.strftime('%b %d')} - {week2_end.strftime('%b %d, %Y')}")
                
                st.markdown("---")
                
                # Show the table
                st.markdown("#### 📊 Targets by Sub-Category & Outlet")
                st.dataframe(
                    targets_display.style.format({
                        'KV (W1)': '{:.0f}',
                        'Patia (W1)': '{:.0f}',
                        'Total (W1)': '{:.0f}',
                        'KV (W2)': '{:.0f}',
                        'Patia (W2)': '{:.0f}',
                        'Total (W2)': '{:.0f}'
                    }).background_gradient(cmap='YlGnBu', subset=['KV (W1)', 'Patia (W1)', 'Total (W1)', 'KV (W2)', 'Patia (W2)', 'Total (W2)']),
                    use_container_width=True,
                    hide_index=True
                )
                
                st.success(f"✅ Targets generated with {target_adjustment:+d}% adjustment")
                
                # Create WhatsApp-friendly text format
                st.markdown("---")
                st.markdown("### 📱 WhatsApp-Friendly Format (Click to Copy)")
                
                # Build text format
                whatsapp_text = f"""*WEEKLY TARGETS*
*Week 1:* {week1_start.strftime('%b %d')} - {week1_end.strftime('%b %d, %Y')}
*Week 2:* {week2_start.strftime('%b %d')} - {week2_end.strftime('%b %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*WEEK 1*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Sub Category         KV    Patia  Total*
"""
                
                for _, row in targets_display.iterrows():
                    subcat = row['Sub Category'][:20].ljust(20)
                    kv = str(int(row['KV (W1)'])).rjust(5)
                    patia = str(int(row['Patia (W1)'])).rjust(6)
                    total = str(int(row['Total (W1)'])).rjust(6)
                    whatsapp_text += f"{subcat} {kv} {patia} {total}\n"
                
                whatsapp_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*WEEK 2*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Sub Category         KV    Patia  Total*
"""
                
                for _, row in targets_display.iterrows():
                    subcat = row['Sub Category'][:20].ljust(20)
                    kv = str(int(row['KV (W2)'])).rjust(5)
                    patia = str(int(row['Patia (W2)'])).rjust(6)
                    total = str(int(row['Total (W2)'])).rjust(6)
                    whatsapp_text += f"{subcat} {kv} {patia} {total}\n"
                
                # Add summary
                total_w1 = targets_display['Total (W1)'].sum()
                total_w2 = targets_display['Total (W2)'].sum()
                
                whatsapp_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*SUMMARY*

Week 1 Total: *{int(total_w1):,} units*
Week 2 Total: *{int(total_w2):,} units*
Grand Total: *{int(total_w1 + total_w2):,} units*

Adjustment Applied: {target_adjustment:+d}%
"""
                
                # Display in text area for easy copying
                st.text_area(
                    "Copy this text to send via WhatsApp:",
                    whatsapp_text,
                    height=400,
                    help="Click inside, press Ctrl+A to select all, then Ctrl+C to copy"
                )
                
                # Also provide CSV download
                st.markdown("---")
                st.markdown("### 📥 Download Options")
                
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    csv_targets = targets_display.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download as CSV",
                        data=csv_targets,
                        file_name=f"targets_week1_{week1_start.strftime('%Y%m%d')}_week2_{week2_start.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col_d2:
                    st.download_button(
                        label="📋 Download as Text",
                        data=whatsapp_text,
                        file_name=f"targets_whatsapp_{week1_start.strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
                # Add quick copy button hint
                st.info("""
                💡 **Quick Copy Tips:**
                - Click inside the text box above
                - Press **Ctrl+A** (Select All)
                - Press **Ctrl+C** (Copy)
                - Open WhatsApp and **Ctrl+V** (Paste)
                - The formatting will be preserved!
                """)
                
            except Exception as e:
                st.error(f"Error generating targets: {str(e)}")
                st.info("Please ensure data is available for all categories and outlets.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 20px;'>
    <p><strong>VDD Sales Analysis Dashboard</strong></p>
    <p>Built with ❤️ using Streamlit | Real-time data analysis and forecasting</p>
</div>
""", unsafe_allow_html=True)
