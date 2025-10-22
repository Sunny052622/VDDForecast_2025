# Comprehensive Sales Analysis Report
## VDD Forecast 2025 - Executive Summary

**Analysis Period:** February 1, 2025 - October 21, 2025 (263 days)  
**Analyst:** Senior Data Analyst AI  
**Date Generated:** October 22, 2025

---

## Executive Summary

This comprehensive analysis processed **31,497 successful transactions** across **17,674 unique orders**, generating insights into sales performance, customer behavior, product popularity, and future revenue projections.

### Key Highlights
- **Total Revenue:** ₹3,483,297.00
- **Average Order Value:** ₹197.09
- **Total Items Sold:** 34,145 units
- **Forecasted 30-Day Revenue:** ₹359,286.55

---

## 1. Overall Business Performance

### Primary KPIs

| Metric | Value |
|--------|-------|
| Total Revenue | ₹3,483,297.00 |
| Total Orders | 17,674 |
| Average Order Value | ₹197.09 |
| Total Items Sold | 34,145 units |
| Analysis Period | 263 days |
| Average Daily Revenue | ₹13,244.48 |

---

## 2. Sales Channel Analysis

### Channel Distribution

**In-Shop (78.8% of revenue)**
- Revenue: ₹2,745,873.10
- Average Order Value: ₹199.16
- Primary sales driver

**Delivery/Swiggy (21.2% of revenue)**
- Revenue: ₹737,423.90
- Average Order Value: ₹189.72
- Lower AOV suggests price-sensitive customers

### Strategic Insights
1. In-shop customers spend ₹9.44 more per order on average
2. Delivery channel represents growth opportunity (currently 21.2%)
3. Consider delivery-exclusive promotions to increase channel penetration

---

## 3. Category & Product Performance

### Top 10 Categories by Revenue

| Rank | Category | Revenue | % of Total |
|------|----------|---------|-----------|
| 1 | Momo | ₹1,888,503.17 | 54.2% |
| 2 | Noodles | ₹254,590.68 | 7.3% |
| 3 | Laphing | ₹232,563.60 | 6.7% |
| 4 | Chicken Starter | ₹200,000.52 | 5.7% |
| 5 | Thukpa | ₹183,414.07 | 5.3% |
| 6 | Noodle/Rice Combo | ₹142,523.05 | 4.1% |
| 7 | Veg Starters | ₹115,698.06 | 3.3% |
| 8 | Dumpling | ₹91,688.67 | 2.6% |
| 9 | Cigar Roll | ₹73,688.97 | 2.1% |
| 10 | Frankie | ₹52,497.53 | 1.5% |

**Key Finding:** Momos dominate revenue, generating over half of total sales (54.2%)

### Top 10 Items by Revenue

| Rank | Item | Revenue |
|------|------|---------|
| 1 | Chicken Steam Momo | ₹243,901.16 |
| 2 | Chicken Jhol Momo | ₹187,681.37 |
| 3 | Veg Steam Momo | ₹171,052.55 |
| 4 | Chicken Kothey Momo | ₹162,881.64 |
| 5 | Veg Jhol Momo | ₹130,688.68 |
| 6 | Thupka (Chicken) | ₹109,370.91 |
| 7 | Chicken Laphing | ₹107,056.64 |
| 8 | Veg Laphing | ₹103,001.14 |
| 9 | Veg Kothey Momo | ₹101,128.92 |
| 10 | Chicken Teekho Momo | ₹98,188.33 |

### Top 10 Items by Quantity (Critical for Inventory)

| Rank | Item | Units Sold |
|------|------|------------|
| 1 | Chicken Steam Momo | 2,944 |
| 2 | Veg Steam Momo | 2,271 |
| 3 | Chicken Jhol Momo | 1,843 |
| 4 | Chicken Kothey Momo | 1,767 |
| 5 | Veg Laphing | 1,590 |
| 6 | Veg Jhol Momo | 1,533 |
| 7 | Chicken Laphing | 1,424 |
| 8 | Veg Kothey Momo | 1,314 |
| 9 | Chicken Teekho Momo | 1,074 |
| 10 | Mineral Water | 986 |

**Key Insight:** There's strong alignment between revenue and quantity top 10 (9 items appear in both lists). The exceptions are:
- **Thupka (Chicken)** - High revenue, lower volume (premium pricing)
- **Mineral Water** - High volume, low revenue (low-margin item)

---

## 4. Time-Based Performance Patterns

### Monthly Trend
- Analysis covers 9 months (Feb - Oct 2025)
- Detailed monthly revenue trends show seasonal patterns
- See visualization: `01_time_channel_analysis.png`

### Day of Week Performance
- Revenue patterns vary significantly by day
- Identify peak days for staffing optimization

### Hourly Performance
- Clear peak hours identified in analysis
- Use for:
  - Optimal staff scheduling
  - Targeted promotions during slow hours
  - Inventory preparation timing

---

## 5. Market Basket Analysis

### Overview
- Analyzed **17,674 transactions** across **140 unique items**
- Identified **51 frequent itemsets**
- Generated **20 association rules**

### Top 5 Product Associations (Cross-Selling Opportunities)

| If Customer Buys... | They're Likely to Buy... | Lift | Confidence |
|---------------------|--------------------------|------|------------|
| Veg Laphing | Veg Kothey Momo | 1.97x | 13.5% |
| Veg Kothey Momo | Veg Laphing | 1.97x | 16.1% |
| Veg Laphing | Veg Jhol Momo | 1.95x | 16.0% |
| Veg Jhol Momo | Veg Laphing | 1.95x | 16.0% |
| Chicken Jhol Momo | Chicken Laphing | 1.68x | 12.5% |

### Actionable Insights
1. **Create Combo Deals:** Package Veg Laphing + Veg Kothey Momo together
2. **Staff Training:** Suggest Veg Jhol Momo when customers order Veg Laphing
3. **Menu Placement:** Position related items near each other on menu
4. **Upselling Script:** "Customers who ordered X often enjoy Y as well"

---

## 6. Sales Forecasting (30-Day Projection)

### Model Details
- **Model Type:** SARIMA(1,1,1)(1,1,1,7)
- **Forecast Period:** October 22 - November 20, 2025
- **Model Performance:** AIC: 4647.75, BIC: 4665.27

### Forecast Summary

| Metric | Value |
|--------|-------|
| Total 30-Day Forecasted Revenue | ₹359,286.55 |
| Average Daily Forecast | ₹11,976.22 |
| Current Average Daily Revenue | ₹13,244.48 |
| Projected Variance | -9.6% |

### First 7 Days Detailed Forecast

| Date | Forecast | Lower CI | Upper CI |
|------|----------|----------|----------|
| Oct 22 | ₹12,207.99 | ₹4,886.76 | ₹19,529.22 |
| Oct 23 | ₹10,217.99 | ₹2,564.68 | ₹17,871.30 |
| Oct 24 | ₹13,630.67 | ₹5,896.60 | ₹21,364.74 |
| Oct 25 | ₹14,756.94 | ₹6,974.04 | ₹22,539.84 |
| Oct 26 | ₹16,093.77 | ₹8,268.12 | ₹23,919.43 |
| Oct 27 | ₹7,218.73 | ₹-648.25 | ₹15,085.70 |
| Oct 28 | ₹11,094.50 | ₹3,186.68 | ₹19,002.32 |

### Statistical Notes
- **ADF Test Result:** p-value = 0.2218 (non-stationary series)
- Model includes weekly seasonality component
- Wide confidence intervals reflect inherent variability in daily sales

---

## 7. Strategic Recommendations

### Immediate Actions (0-30 Days)

#### 1. Inventory Management
- **Action:** Stock based on quantity analysis, not revenue
- **Priority Items:** 
  - Chicken Steam Momo (2,944 units/9 months ≈ 327 units/month)
  - Veg Steam Momo (252 units/month)
  - Focus on top 10 quantity items
- **Impact:** Reduce stockouts of high-volume items

#### 2. Cross-Selling Program
- **Action:** Implement suggested pairings from basket analysis
- **Implementation:**
  - Train staff on top 5 associations
  - Create combo deals (Veg Laphing + Veg Kothey Momo)
  - Update POS system with cross-sell prompts
- **Expected Impact:** 5-10% increase in AOV

#### 3. Channel Strategy
- **In-Shop (78.8%):**
  - Maintain quality and service standards
  - Consider loyalty program for repeat customers
- **Delivery (21.2%):**
  - Promotional campaigns to increase penetration
  - Target 25% revenue share in next quarter
  - Optimize delivery menu (high-margin, travel-well items)

### Medium-Term Initiatives (30-90 Days)

#### 4. Operational Efficiency
- **Peak Hour Optimization:**
  - Use hourly analysis to schedule staff
  - Pre-prep ingredients before peak times
  - Implement express service during rush hours

- **Slow Period Strategy:**
  - Happy hour promotions
  - Targeted digital marketing
  - Test new menu items

#### 5. Product Portfolio Optimization
- **Star Products (High Revenue + High Volume):**
  - Maintain quality consistency
  - Never compromise on availability
  - Consider slight price increases (test elasticity)

- **Cash Cows (High Revenue, Lower Volume):**
  - Thupka (Chicken) - maintain premium positioning
  - Protect margins, increase awareness

- **Volume Drivers (High Volume, Lower Revenue):**
  - Mineral Water - ensure availability as complement item
  - Consider bundling with main items

#### 6. Menu Engineering
- **Remove/Replace:** Items not in top 30 by revenue or quantity
- **Promote:** Items with high margins that are near top 10
- **Test:** New variations of best-sellers (e.g., new momo flavors)

### Long-Term Strategy (90+ Days)

#### 7. Forecasting & Planning
- **Monthly Review:**
  - Compare actual vs. forecast
  - Refine model parameters
  - Adjust inventory planning

- **Seasonal Preparation:**
  - Build forecasts for special events
  - Plan inventory for festivals/holidays
  - Adjust staffing models

#### 8. Data-Driven Culture
- **Implement:**
  - Daily sales dashboard
  - Weekly performance reviews
  - Monthly strategic planning sessions
- **Track:**
  - KPIs vs. targets
  - New product performance
  - Cross-selling success rates

---

## 8. Technical Notes

### Data Quality
- **Total Transactions Analyzed:** 31,497
- **Data Completeness:** 100% (all successful transactions)
- **Time Period:** 263 days (Feb 1 - Oct 21, 2025)

### Methodology
1. **Data Preparation:**
   - Two-DataFrame approach for accuracy
   - Revenue analysis: Items as sold (combos intact)
   - Quantity analysis: Component-level (combos exploded)

2. **Statistical Techniques:**
   - Time series decomposition
   - SARIMA forecasting with weekly seasonality
   - Apriori algorithm (min support = 1%)
   - Association rules (min lift = 1.0)

3. **Visualizations:**
   - 4 comprehensive visualization sets
   - All charts saved in high resolution (300 DPI)
   - Located in `analysis_outputs/` directory

---

## 9. Visualization Guide

### File 1: `01_time_channel_analysis.png`
- Monthly revenue trend line chart
- Revenue by day of week bar chart
- Revenue by hour of day bar chart
- Sales channel distribution pie chart

### File 2: `02_category_product_performance.png`
- Revenue distribution by category (pie chart)
- Top 10 items by revenue (horizontal bar)
- Top 10 items by quantity (horizontal bar)
- Category performance matrix (revenue vs. quantity)

### File 3: `03_basket_analysis.png`
- Top 15 most frequently purchased items
- Association rules: support vs. confidence scatter plot
- Top 10 rules by lift
- Itemset length distribution

### File 4: `04_sales_forecast.png`
- Full historical data + 30-day forecast with confidence intervals
- Detailed view: Last 60 days + forecast

---

## 10. Conclusion

This analysis reveals a healthy business with clear strengths:

✅ **Strong Core Products:** Momos drive 54% of revenue  
✅ **Stable Customer Base:** 17,674 orders over 9 months  
✅ **Consistent AOV:** ₹197.09 across channels  
✅ **Clear Patterns:** Strong product associations for cross-selling  

### Areas for Improvement:
⚠️ **Delivery Channel:** Only 21% of revenue - growth opportunity  
⚠️ **Forecast Trend:** Slight decline projected (-9.6%) - requires attention  
⚠️ **Product Concentration:** Heavy reliance on momos - diversification needed  

### Next Steps:
1. Implement cross-selling program immediately
2. Launch delivery channel growth campaign
3. Monitor forecast vs. actuals weekly
4. Review and optimize menu quarterly
5. Develop seasonal promotions based on patterns

---

**For Questions or Further Analysis:**
Contact: Senior Data Analyst
Files: All code available in `sales_analysis.py`
Visualizations: Located in `analysis_outputs/` directory

---

*Report Generated: October 22, 2025*  
*Analysis Period: February 1 - October 21, 2025*  
*Data Source: data.xlsx (SalesData, nameRef, comboRef sheets)*


