# 💰 PRICING STRATEGY - LIGHTGBM OPTIMIZATION

**Goal:** Find optimal price that maximizes ARR  
**Method:** Test with customers, optimize based on response  
**Timeline:** Week 1-4 of customer discovery

---

## 🎯 PRICING TIERS (Test these with interviews)

### Tier 1: FREE (Activation driver)
```
- 5 predictions/month
- Basic accuracy (standard model)
- CSV export
- Goal: Get users to experience value
- Expected conversion: 5-10% to paid
```

### Tier 2: PRO (Main revenue)
```
- Unlimited predictions
- Advanced accuracy (+20% better)
- API access
- CSV + JSON export
- Integrations: Stripe, Salesforce, HubSpot
- Custom models (industry-specific)
- Email support
- Price: TEST $49, $79, $99, $149/month
```

### Tier 3: ENTERPRISE (Land deals)
```
- Custom features
- Dedicated account manager
- SLA guarantee (99.9% uptime)
- Custom integrations
- Data residency (EU/APAC)
- SSO (SAML)
- Price: Custom (test $5K-50K/month)
```

---

## 📊 PRICING TEST FRAMEWORK

### Test with Each Customer Interview

**Question 1: Budget**
```
"How much budget do you have for [solving this] this year?"
```
Track: Budget availability

**Question 2: Price Sensitivity**
```
"Would you pay $49/month for this solution?"
If YES:
  "Would you pay $99/month?"
If NO:
  "Would you pay $29/month?"
```
Track: Willingness at different price points

**Question 3: Value Extraction**
```
"If this saved you [X hours/week], what's that worth?"
Calculate: Annual hours × hourly rate = annual value
Target price: 1/3 of annual value
```

**Question 4: Competitive Pricing**
```
"What are you currently paying for [competitor solution]?"
Track: Existing spend on similar tools
```

---

## 🧮 FORMULA: Calculate Price

**After 10 interviews, calculate optimal price:**

```
Annual Cost of Problem = Hours/week × 50 weeks/year × Hourly rate

Example for Churn:
- CSM currently spends 5 hours/week identifying churn risks
- 5 hours × 50 weeks × $75/hour = $18,750/year cost
- Min price: $18,750 × 0.33 = $6,250/year = $521/month
- Max price: $18,750 × 0.67 = $12,500/year = $1,042/month
- Recommended: $750/month

If 10 interviews show:
- Min: $210/month
- Max: $5,000/month
- Median: $750/month
- → Price at $749/month

Our pricing: $49, $99, $299 may be too LOW!
Should test: $299, $799, $2,999
```

---

## A/B TEST PRICING (After MVP)

Once you have 10 beta users, test:

```
Group A: Show $49/month
Group B: Show $99/month
Group C: Show $199/month

Metric: Conversion rate (% who upgrade)

Expected outcome:
$49: 15% conversion
$99: 10% conversion
$199: 5% conversion

Goal: Find price that maximizes revenue
(Price × Conversion Rate) = Revenue per user
```

---

## 💵 REVENUE PROJECTIONS (Based on testing)

### Conservative (Based on $99/month tier)

```
Month 1: 5 paying customers = $495 MRR
Month 2: 15 customers = $1,485 MRR
Month 3: 30 customers = $2,970 MRR
Month 4: 50 customers = $4,950 MRR
Month 5: 75 customers = $7,425 MRR
Month 6: 100 customers = $9,900 MRR = $118,800 ARR

Year 1 target: $100-150K ARR (30-50 paying customers)
```

### Aggressive (If we're underpriced, should be $499/month)

```
Month 1: 5 customers = $2,495 MRR
Month 2: 15 customers = $7,485 MRR
Month 3: 30 customers = $14,970 MRR
Month 4: 50 customers = $24,950 MRR
Month 5: 75 customers = $37,425 MRR
Month 6: 100 customers = $49,900 MRR = $598,800 ARR

Year 1 target: $500K-750K ARR (100 paying customers)
```

**The truth:** You're probably underpriced. Test higher.

---

## 📈 PRICING STRATEGY BY VERTICAL

### Churn Prediction
```
TAM: $30B (churn problem affects all subscription businesses)
Customer: VP Customer Success at $10M-1B revenue SaaS
Annual spend: $18K-200K (1-3% of CS team budget)
Optimal price: $499-2,999/month
Expected LTV: $5,000-30,000 (multi-year)
```

### Fraud Detection
```
TAM: $50B (prevents revenue loss)
Customer: Risk/Compliance manager at fintech/e-commerce
Annual spend: $100K-500K (fraud is expensive)
Optimal price: $2,999-15,000/month
Expected LTV: $50,000-150,000
```

### Demand Forecasting
```
TAM: $20B (inventory is expensive)
Customer: Supply chain manager
Annual spend: $50K-300K (reduces inventory costs)
Optimal price: $999-5,000/month
Expected LTV: $20,000-80,000
```

---

## 🎯 PRICING DECISION TREE

```
Week 1-2: Customer interviews
  ↓
  Have you talked to 10 customers?
  
  YES → Week 3: Analyze pricing feedback
        Calculate: min, max, median price
        Recommended: Start at median price
        
  NO → Week 2-3: Keep interviewing
       Track pricing in every conversation
```

---

## ✅ PRICING VALIDATION CHECKLIST

- [ ] Interviewed 10+ customers about budget
- [ ] Calculated annual cost of problem
- [ ] Know: min price customers would accept
- [ ] Know: max price customers would reject
- [ ] Know: median price across segment
- [ ] Tested at least 2 price points with customers
- [ ] Understand: how price affects conversion
- [ ] Ready to test with real users

---

## 🚀 PRICING TIMELINE

| Week | Action | Metric |
|------|--------|--------|
| 1-4 | Interview 15 customers, ask about budget | Know min/max/median price |
| 5-8 | Interview 20 customers total, test $X vs $Y | Understand price elasticity |
| 9-10 | MVP ready, offer to 5 beta users at full price | Get first customers at real price |
| 11-12 | Measure: who converts at each price? | Optimize for revenue, not growth |

---

## 💡 PRICING PSYCHOLOGY

**Higher prices = Better customers (counterintuitive)**

```
At $29/month:
- Customers: Anyone experimenting
- Churn: 80% in first month
- LTV: $35 (1 month × $29)
- Problem: Not serious enough

At $299/month:
- Customers: Only those solving real problem
- Churn: 40% in first year
- LTV: $1,436 (4.8 months × $299)
- Benefit: Higher quality, lower churn

At $2,999/month:
- Customers: Enterprise solving mission-critical problem
- Churn: 15% per year
- LTV: $40,000+
- Benefit: Sustainable, profitable, focused
```

**Never discount below 30%.** If customers won't pay full price, they don't have a real problem.

---

## 🎯 PRICING STRATEGY BY STAGE

### Stage 1: PMF Validation (now)
```
Goal: Prove problem exists, people will pay
Pricing: At market rate (don't discount)
Focus: Conversion rate, not volume
Kill metric: If <30% say they'd pay, pivot
```

### Stage 2: Growth (after PMF)
```
Goal: Scale to $100K MRR
Pricing: Annual discount (15-20% for yearly)
Focus: CAC efficiency, LTV, payback
Kill metric: If LTV:CAC < 3:1, optimize or reduce price
```

### Stage 3: Scale (after $100K MRR)
```
Goal: Scale to $1M+ ARR
Pricing: Usage-based OR enterprise pricing
Focus: Land big deals, expand within accounts
Kill metric: If NRR < 110%, improve product
```

---

**DECISION**: Start interviews THIS WEEK tracking price in every conversation.
By Week 4, you'll know optimal price. Test it. Iterate.
