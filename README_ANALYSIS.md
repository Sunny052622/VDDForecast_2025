# Sales Analysis - Quick Start Guide

## 📊 What Was Delivered

### 1. **Complete Python Script** 
**File:** `sales_analysis.py`
- Fully executable, production-ready code
- Handles all data processing, analysis, and visualization
- Well-commented and structured
- Can be re-run anytime with updated data

### 2. **Comprehensive Analysis Report**
**File:** `ANALYSIS_SUMMARY_REPORT.md`
- Executive summary of all findings
- Detailed insights and recommendations
- Tables with key metrics
- Strategic action items

### 3. **Four Professional Visualizations**
**Folder:** `analysis_outputs/`
- `01_time_channel_analysis.png` - Time trends and channel distribution
- `02_category_product_performance.png` - Product and category insights
- `03_basket_analysis.png` - Market basket and association rules
- `04_sales_forecast.png` - 30-day revenue forecast

---

## 🎯 Key Findings at a Glance

### Business Performance
- **Revenue:** ₹3.48 Million (9 months)
- **Orders:** 17,674
- **AOV:** ₹197.09
- **Forecasted Next 30 Days:** ₹359,286.55

### Top Insights
1. **Momos dominate:** 54% of all revenue
2. **In-shop is primary channel:** 78.8% vs 21.2% delivery
3. **Top seller:** Chicken Steam Momo (₹243K revenue, 2,944 units)
4. **Strong associations:** Veg Laphing + Veg Kothey Momo (1.97x lift)

---

## 🚀 How to Re-Run the Analysis

### Option 1: Run the Complete Analysis
```bash
python sales_analysis.py
```
This will:
- Process all data from `data.xlsx`
- Generate new visualizations
- Print comprehensive report to console

### Option 2: Update Data and Re-Analyze
1. Update your `data.xlsx` file with new data
2. Ensure three sheets exist: `SalesData`, `nameRef`, `comboRef`
3. Run: `python sales_analysis.py`
4. Check `analysis_outputs/` for new charts

---

## 📁 File Structure

```
VDDForecast_2025/
│
├── data.xlsx                          # Your source data (3 sheets)
├── sales_analysis.py                  # Main analysis script
├── ANALYSIS_SUMMARY_REPORT.md         # Detailed written report
├── README_ANALYSIS.md                 # This file
│
└── analysis_outputs/                  # Generated visualizations
    ├── 01_time_channel_analysis.png
    ├── 02_category_product_performance.png
    ├── 03_basket_analysis.png
    └── 04_sales_forecast.png
```

---

## 🔍 Understanding the Analysis

### Part 1: Data Preparation (The "Rules Engine")
The script creates TWO separate analysis DataFrames:

1. **df_revenue_analysis** (31,497 rows)
   - Items as sold (combos intact)
   - Used for: Revenue, AOV, sales metrics
   - Example: "Veggie Combo" counts as one item

2. **df_quantity_analysis** (31,917 rows)
   - Component-level (combos exploded)
   - Used for: Inventory, ingredient planning
   - Example: "Veggie Combo" split into "Veg Momo" + "Coke"

**Why two DataFrames?**
- Revenue must be calculated on what was sold
- Inventory must be planned for what was actually consumed

### Part 2: Five Major Analyses

1. **Overall Business KPIs**
   - Revenue, orders, AOV, items sold

2. **Sales Performance by Channel & Time**
   - In-Shop vs Delivery
   - Monthly trends
   - Day of week patterns
   - Hourly patterns

3. **Category & Product Performance**
   - Top categories by revenue
   - Top 10 items by revenue
   - Top 10 items by quantity (for inventory)
   - Comparison insights

4. **Basket Analysis**
   - Frequent itemsets (Apriori algorithm)
   - Association rules
   - Cross-selling opportunities
   - Top 5 product pairings by lift

5. **Sales Forecasting**
   - SARIMA model (weekly seasonality)
   - 30-day forecast
   - Confidence intervals
   - Stationarity testing

---

## 📈 Key Metrics Explained

### AOV (Average Order Value)
```
Total Revenue ÷ Number of Orders = ₹197.09
```
**Why it matters:** Tracks customer spending behavior

### Lift (Association Rules)
```
Lift = 1.97 means customers are 97% MORE likely 
to buy item B when they buy item A
```
**Why it matters:** Identifies cross-selling opportunities

### Confidence
```
Confidence = 16.1% means in 16.1% of cases where 
customers buy item A, they also buy item B
```
**Why it matters:** Shows reliability of the association

### SARIMA Model
```
SARIMA(1,1,1)(1,1,1,7)
- (1,1,1): ARIMA components (trend)
- (1,1,1,7): Seasonal components (weekly pattern)
```
**Why it matters:** Captures both trends and weekly patterns

---

## 🎓 Technical Details

### Required Python Libraries
- pandas (data manipulation)
- numpy (numerical operations)
- matplotlib (visualization)
- seaborn (advanced visualization)
- mlxtend (market basket analysis)
- statsmodels (time series forecasting)
- openpyxl (Excel file handling)

All installed automatically when you ran the script.

### Data Processing Rules Implemented
✅ Filter for Status == 'Success' only
✅ Convert dates and numeric fields properly
✅ Create time-based features (Year, Month, Week, DayOfWeek, Hour)
✅ Standardize sales channels (Swiggy = Delivery, others = In-Shop)
✅ Merge with reference data for standardized names
✅ Explode combos for quantity analysis
✅ Handle missing values appropriately

---

## 💡 Quick Wins from This Analysis

### Implement These TODAY:
1. **Cross-Sell Training:** Teach staff the top 5 associations
2. **Menu Placement:** Put Veg Laphing near Veg Kothey Momo on menu
3. **Inventory Focus:** Prioritize top 10 quantity items

### Implement This WEEK:
1. **Combo Deal:** Create "Veg Laphing + Veg Kothey Momo" combo
2. **Peak Hour Prep:** Use hourly chart to optimize prep schedules
3. **Delivery Promotion:** Launch campaign to grow delivery from 21% to 25%

### Implement This MONTH:
1. **Weekly Forecast Reviews:** Track actual vs predicted
2. **Menu Engineering:** Review items not in top 30
3. **Staff Optimization:** Schedule based on hourly patterns

---

## 🔄 Updating the Analysis

### When to Re-Run:
- **Weekly:** For updated forecasts
- **Monthly:** For trend analysis
- **Quarterly:** For strategic review
- **Ad-hoc:** After major changes (menu, pricing, marketing)

### What Changes Might Be Needed:
If your data structure changes, update these sections:
- Line 40-42: Sheet names
- Line 98-100: Column name mappings
- Line 568-571: SARIMA parameters (if forecast quality is poor)

---

## 📞 Support & Questions

### If Script Fails:
1. Check that `data.xlsx` exists in same folder
2. Verify three sheets: `SalesData`, `nameRef`, `comboRef`
3. Ensure Python libraries are installed
4. Check Python version (requires 3.7+)

### If Results Look Wrong:
1. Verify data quality in Excel file
2. Check for duplicate rows
3. Ensure Status column has 'Success' for valid transactions
4. Verify date formats are consistent

### If Forecast Seems Off:
- Normal! Forecasts have wide confidence intervals
- Monitor actual vs predicted over time
- May need to adjust SARIMA parameters
- Consider external factors (holidays, events)

---

## 🎉 Success Criteria

You've successfully completed the analysis if:
- ✅ All 4 visualizations generated in `analysis_outputs/`
- ✅ Console shows "Script execution completed successfully!"
- ✅ No error messages during execution
- ✅ Charts look reasonable and match your business knowledge
- ✅ Forecast values are in expected range

---

## 📊 Example Use Cases

### Scenario 1: Weekly Review Meeting
**What to share:**
- Key metrics from console output
- `01_time_channel_analysis.png` for trends
- Top 10 products by revenue
- Forecast for next week

### Scenario 2: Inventory Planning
**What to use:**
- Top 10 items by QUANTITY (not revenue!)
- These numbers are component-level
- Multiply by growth factor for buffer stock

### Scenario 3: Menu Planning
**What to analyze:**
- Items ONLY in top revenue = premium items
- Items ONLY in top quantity = volume items
- Items in NEITHER = candidates for removal

### Scenario 4: Marketing Campaign
**What to leverage:**
- Basket analysis for bundle creation
- Day/hour patterns for promotion timing
- Channel AOV differences for targeting

---

**Questions?** Review `sales_analysis.py` - it's fully commented!

**Need modifications?** The code is structured for easy customization.

**Want deeper insights?** Re-run with different parameters or add new analyses.

---

*Happy Analyzing! 🚀*


