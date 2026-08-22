# 🎤 CHURN PREDICTION DISCOVERY - EXECUTION CHECKLIST

**Goal:** 50 customer interviews in 90 days → Clear PMF signal  
**Timeline:** Week 1-4 = Discovery, Week 5-8 = Validation, Week 9-12 = MVP  
**Time Commitment:** 5-8 hours/week (achievable alongside building)

---

## ⚡ WEEK 1: RAPID LAUNCH (Start TODAY)

### Monday (Day 1)
- [ ] 9:00am - Read CHURN_PREDICTION_PLAYBOOK.md (30 min)
- [ ] 9:30am - Open LinkedIn, create "target list" spreadsheet
- [ ] 10:00am - Search: "VP Customer Success" + "SaaS" + "$100M-1B revenue"
- [ ] 12:00pm - Find 15 people, copy name + email + company
- [ ] 1:00pm LUNCH
- [ ] 2:00pm - Repeat search with "Head of Retention" + "Director of CS"
- [ ] 4:00pm - Have 30 names (add notes: company, pain points from LinkedIn)

**Deliverable:** `target_list_week1.csv` with 30 people

### Tuesday (Day 2)
- [ ] 9:00am - Open `cold_email_sender.py` (created below)
- [ ] 9:30am - Write 3 variations of cold email
- [ ] 10:30am - Test with 3 founders/friends (ask for feedback)
- [ ] 11:30am - Refine based on feedback
- [ ] 1:00pm LUNCH
- [ ] 2:00pm - Set up Calendly link (free tier)
- [ ] 2:30pm - Add calendar link to email template
- [ ] 3:00pm - Test email send (send to yourself)

**Deliverable:** Polished cold email template + Calendly link live

### Wednesday (Day 3)
- [ ] 9:00am - Send 10 cold emails manually (personalize each)
  - Change: "[Company]" to actual company name
  - Change: "[Name]" to actual first name
  - Add: 1-2 sentence about their company (shows research)
- [ ] 11:00am - Send next 10 emails
- [ ] 1:00pm LUNCH
- [ ] 2:00pm - Send final 10 emails
- [ ] 3:00pm - Log in spreadsheet: sent to [name], company, date
- [ ] 4:00pm - Set up Gmail filter: "Label: ForecastX Replies"

**Deliverable:** 30 cold emails sent ✅

### Thursday (Day 4)
- [ ] 9:00am - Check replies (expect: 1-2 by Thursday)
- [ ] 10:00am - Schedule any replies that came in
- [ ] 11:00am - Send 10 more cold emails to new list
- [ ] 1:00pm LUNCH
- [ ] 2:00pm - Research 10 more prospects on LinkedIn
- [ ] 3:00pm - Send 10 more emails
- [ ] 4:00pm - Total sent: 50 emails

**Deliverable:** 50 cold emails sent + calendars started filling up

### Friday (Day 5)
- [ ] 9:00am - Prep for interviews (review CUSTOMER_INTERVIEW_TEMPLATE.md)
- [ ] 10:00am - Print 5 copies of interview questions
- [ ] 11:00am - Set up Zoom/Cal.com for calls
- [ ] 1:00pm LUNCH
- [ ] 2:00pm - Do first 2 customer interviews (30 min each)
- [ ] 3:30pm - Fill out interview summary (INTERVIEW_TRACKING_SHEET.md)
- [ ] 4:00pm - Send follow-up emails (offer early access)

**Deliverable:** 2 interviews done + summaries filled ✅

**WEEK 1 RESULT:**
- ✅ 50 cold emails sent
- ✅ 2-3 interviews scheduled/completed
- ✅ First data points on problem
- ✅ Confidence: 40% (only 2 interviews, but pattern emerging)

---

## 📈 WEEK 2-3: VOLUME (Scale to 10 interviews)

### Daily Ritual (30 min/day)
```
9:00am: Check email replies
9:15am: Schedule anyone who replied
9:30am: Send 5-10 new cold emails
10:00am: Done
```

### Interview Schedule (2 per day)
```
Tuesday:  9:00am interview + 10:00am interview
Wednesday: 2:00pm interview + 3:00pm interview
Thursday:  10:00am interview + 11:00am interview
Friday:    2:00pm interview + 3:00pm interview
```

### End of Week Ritual (Friday, 4pm)
```
Review all 5 interviews:
- Do they describe same problem?
- What exact words do they use?
- What budget do they mention?
- Who's the decision maker?

Fill out INTERVIEW_TRACKING_SHEET.md

Calculate pattern score: ___% mention same problem
```

**WEEK 2-3 RESULT:**
- ✅ 10 interviews total
- ✅ Problem pattern emerging (70%+ describe same issue?)
- ✅ Average pain level: ___/10
- ✅ Average budget: $___/month

---

## 🎯 WEEK 4: VALIDATION

- [ ] Do 5 more interviews (total: 15)
- [ ] Analyze: Do 70%+ describe identical problem?
- [ ] If YES → Problem is clear, move to Week 5 validation
- [ ] If NO → Interview different vertical (fraud? forecasting?)
- [ ] Create "Problem Statement" document (1 page)
  - Who: [Exact persona]
  - What: [Problem in their words]
  - Why: [$X cost/year]
  - Proof: [# interviews, % validation]

**RED FLAGS (Pivot if you see):**
- ❌ Every customer describes different problem
- ❌ Problem not in top 3 priorities
- ❌ Avg pain level <6/10
- ❌ No one has budget for solution

**GREEN FLAGS (Keep going):**
- ✅ 70%+ describe same problem (word-for-word)
- ✅ Avg pain level 7+/10
- ✅ 60%+ have budget
- ✅ Urgency: 70%+ want to solve in next 3 months

**WEEK 4 RESULT:**
- ✅ 15 interviews total
- ✅ Clear problem statement
- ✅ Confidence: 70% (pattern is real)
- ✅ GO DECISION: Build MVP or PIVOT decision

---

## 💰 WEEK 5-8: VALIDATION PHASE

Continue same ritual but focus on:
- [ ] Pricing: "What would you pay for a solution?"
- [ ] Urgency: "When could you start using this?"
- [ ] Commitment: "Would you beta test this?"

**Target:** 20 total interviews + 5 beta commitments

---

## 🏗️ WEEK 9-12: BUILD & SELL

- [ ] Build MVP (3 must-have features only)
- [ ] Deploy to 5 beta users
- [ ] Collect feedback + iterate
- [ ] Get first 3-5 paying customers ($2-5K/month each)

---

## 📊 TRACKING TEMPLATE

Use this spreadsheet:

```
Column A: Date
Column B: Customer Name
Column C: Title
Column D: Company
Column E: Problem Clarity (1-10)
Column F: Pain Level (1-10)
Column G: Budget (1-10)
Column H: Would Buy? (YES/MAYBE/NO)
Column I: Decision Timeline (weeks)
Column J: Referrals (names)
Column K: Notes
```

Copy this template 50 times (one row per interview).

Update weekly: Calculate avg on columns E-G

---

## 🎤 PRE-INTERVIEW CHECKLIST

Before every call:
- [ ] Research their company (2 min on LinkedIn)
- [ ] Write down their title
- [ ] Turn off Slack
- [ ] Have questions printed (CUSTOMER_INTERVIEW_TEMPLATE.md)
- [ ] Test Zoom audio
- [ ] Ask permission to record
- [ ] Take notes on EXACT words (not interpretation)

---

## 🚨 WEEKLY GO/NO-GO DECISION

**Every Friday at 4pm, ask yourself:**

After 5 interviews:
- Can I write the problem in 1 sentence?
- Do 70%+ describe the same problem?
- If NO → Change approach, test different persona

After 10 interviews:
- Do 70%+ describe identical problem?
- Is avg pain level 7+?
- If NO → This vertical doesn't work, pivot

After 15 interviews:
- Do 80%+ say same problem?
- Do 60%+ have budget?
- If NO → Market is too small, pivot

After 20 interviews:
- Ready to build MVP?
- Have 5 beta commitments?
- If YES → Start building

---

## ✅ SUCCESS CHECKLIST

By end of Week 4:
- [ ] 15 interviews completed
- [ ] Clear problem statement (1 page)
- [ ] Pattern identified (70%+ same problem)
- [ ] Average budget: $___/month
- [ ] Decision: GO or PIVOT?

By end of Week 8:
- [ ] 20 interviews completed
- [ ] MVP scope defined
- [ ] 5 beta users committed
- [ ] Pricing strategy: $___/month

By end of Week 12:
- [ ] 50 interviews completed
- [ ] MVP deployed
- [ ] 15+ beta users testing
- [ ] 3-5 paying customers
- [ ] PMF validated or pivot decision made

---

**NOW CLOSE THIS AND GO SEND YOUR FIRST 5 COLD EMAILS.** 🚀

Seriously. Stop reading. Open Gmail. Send emails.

Your first customer interview is 3 days away.
