"""
Pre-built Playbook Templates
Ready-to-use playbooks for common use cases across industries
"""

PLAYBOOK_TEMPLATES = [
    {
        "name": "High-Value Customer Churn Prevention",
        "slug": "churn-prevention-high-value",
        "description": "Identifies high-value customers at risk of churning and triggers automated retention workflow. Proven to save $100K+ per customer saved.",
        "category": "churn",
        "use_case": "churn-prediction",
        "industry": "SaaS",
        "price_monthly": 79.00,
        "price_yearly": 799.00,
        "free": False,
        "icon": "🛡️",
        "tags": ["proven", "automated", "high-roi", "bestseller"],
        "success_rate": 0.78,
        "typical_roi": 6.5,
        "setup_time_minutes": 15,
        "configuration": {
            "trigger": "churn_risk_score > 0.8 AND mrr > 5000",
            "conditions": [
                "Usage declined 40%+ in last 30 days",
                "Support tickets increased 300%",
                "No login in 15+ days",
                "Payment failed",
                "New procurement contact"
            ],
            "actions": [
                {
                    "type": "email",
                    "template": "retention_offer",
                    "delay_hours": 0,
                    "personalization": ["company_name", "executive_name", "revenue_at_risk"]
                },
                {
                    "type": "slack_alert",
                    "channel": "cs-critical-alerts",
                    "message": "🚨 {company} at high churn risk (${revenue} MRR)"
                },
                {
                    "type": "create_task",
                    "system": "salesforce",
                    "task_type": "Executive Call - Churn Prevention",
                    "priority": "High",
                    "assignee_role": "VP Customer Success"
                },
                {
                    "type": "webhook",
                    "url": "https://customer.example.com/api/alerts/churn",
                    "method": "POST"
                }
            ],
            "schedule": "daily",
            "follow_up": {
                "day_1": "Send email",
                "day_3": "Slack reminder if no action",
                "day_7": "Executive call"
            }
        },
        "playbook_type": "retention",
        "best_for": ["SaaS", "Subscription", "Enterprise Software"],
        "typical_users": ["VP Customer Success", "CS Manager", "CEO"],
        "expected_outcomes": {
            "prevented_churn": "70-80% of targeted customers",
            "revenue_saved": "$50K-$500K per customer",
            "time_to_save": "14-30 days",
            "cost_of_execution": "$500-2000 per customer"
        }
    },

    {
        "name": "Lead Scoring & Conversion Acceleration",
        "slug": "lead-scoring-conversion",
        "description": "Scores incoming leads by conversion probability and routes high-quality leads to sales immediately. Increases close rate by 35-45%.",
        "category": "lead-scoring",
        "use_case": "lead-scoring",
        "industry": "SaaS",
        "price_monthly": 49.00,
        "price_yearly": 499.00,
        "free": False,
        "icon": "🎯",
        "tags": ["sales", "automated", "real-time", "high-conversion"],
        "success_rate": 0.82,
        "typical_roi": 4.2,
        "setup_time_minutes": 20,
        "configuration": {
            "trigger": "lead_conversion_score > 0.7",
            "signals": [
                "Company size (100-5000 employees)",
                "Industry match",
                "Email engagement (opens, clicks)",
                "Website behavior (pages visited, time spent)",
                "Competitor search",
                "LinkedIn profile similarity to ideal customer",
                "Email domain quality",
                "Budget size indicators"
            ],
            "actions": [
                {
                    "type": "email",
                    "template": "high_intent_welcome",
                    "priority": "high"
                },
                {
                    "type": "slack_alert",
                    "channel": "sales-hot-leads",
                    "message": "🔥 HIGH-QUALITY LEAD: {company} ({score}% conversion probability)"
                },
                {
                    "type": "assign_to_salesforce",
                    "assignment_rule": "round_robin",
                    "notify": True
                },
                {
                    "type": "calendar_invitation",
                    "meeting_type": "Discovery Call",
                    "duration_minutes": 30,
                    "suggested_time": "next_business_day"
                }
            ],
            "schedule": "real-time",
            "scoring_model": "gradient_boosting",
            "features": 25
        },
        "playbook_type": "sales_acceleration",
        "best_for": ["SaaS", "Enterprise Software", "B2B Services"],
        "typical_users": ["VP Sales", "Sales Manager", "SDR Lead"],
        "expected_outcomes": {
            "higher_quality_leads": "35-45% increase in conversion rate",
            "faster_sales_cycle": "20% shorter deal duration",
            "higher_deal_value": "$5K-20K average deal size",
            "sales_productivity": "60% more qualified meetings per rep"
        }
    },

    {
        "name": "Expansion Opportunity Detector",
        "slug": "expansion-opportunity",
        "description": "Identifies existing customers ready for upsell/cross-sell and triggers expansion workflow. Average expansion value $15K-50K per customer.",
        "category": "expansion",
        "use_case": "expansion-opportunity",
        "industry": "SaaS",
        "price_monthly": 69.00,
        "price_yearly": 699.00,
        "free": False,
        "icon": "📈",
        "tags": ["expansion", "upsell", "revenue-growth", "automated"],
        "success_rate": 0.65,
        "typical_roi": 3.8,
        "setup_time_minutes": 25,
        "configuration": {
            "trigger": "expansion_opportunity_score > 0.75",
            "signals": [
                "Usage at 80%+ of plan limits",
                "Added new team members (+50%)",
                "Active in 90%+ of features",
                "High engagement (daily active users)",
                "Approaching renewal date",
                "Customer satisfaction (NPS > 50)",
                "High product adoption rate",
                "Growing organization size"
            ],
            "actions": [
                {
                    "type": "email",
                    "template": "expansion_opportunity",
                    "personalization": ["current_usage", "available_features", "savings"]
                },
                {
                    "type": "slack_alert",
                    "channel": "expansion-targets",
                    "message": "💰 EXPANSION READY: {company} - ${opportunity_value} potential"
                },
                {
                    "type": "assign_to_cs",
                    "role": "CS Manager",
                    "action": "Schedule expansion call"
                },
                {
                    "type": "create_salesforce_task",
                    "task": "Expansion Proposal - {feature_gap}"
                }
            ],
            "schedule": "weekly",
            "opportunity_calculator": "usage_forecast_model"
        },
        "playbook_type": "revenue_growth",
        "best_for": ["SaaS", "Subscription", "Enterprise Software"],
        "typical_users": ["VP Customer Success", "Account Executive", "CS Manager"],
        "expected_outcomes": {
            "expansion_rate": "35-50% of identified customers expand",
            "average_expansion_value": "$15K-50K per customer",
            "revenue_impact": "$300K-2M per year for 100-customer base",
            "customer_lifetime_value": "40-60% increase"
        }
    },

    {
        "name": "Fraud & Risk Detection Real-Time",
        "slug": "fraud-detection-realtime",
        "description": "Real-time fraud detection across transactions, accounts, and behavior. Blocks 98%+ of fraud attempts with <0.1% false positive rate.",
        "category": "fraud",
        "use_case": "fraud-detection",
        "industry": "Fintech",
        "price_monthly": 149.00,
        "price_yearly": 1499.00,
        "free": False,
        "icon": "🚨",
        "tags": ["fraud", "security", "real-time", "critical"],
        "success_rate": 0.98,
        "typical_roi": 8.2,
        "setup_time_minutes": 30,
        "configuration": {
            "trigger": "fraud_risk_score > 0.9",
            "signals": [
                "Transaction amount anomaly (>3σ from average)",
                "Geographic impossibility (impossible travel)",
                "New payment method",
                "Multiple failed transactions",
                "Velocity abuse (10+ transactions in 5 min)",
                "Behavioral deviation",
                "Device fingerprint mismatch",
                "IP address flagged",
                "Email/phone verification failed",
                "Machine learning ensemble score"
            ],
            "actions": [
                {
                    "type": "block_transaction",
                    "immediate": True
                },
                {
                    "type": "alert_security_team",
                    "priority": "critical",
                    "method": ["slack", "email", "sms"]
                },
                {
                    "type": "request_verification",
                    "method": "2fa_challenge",
                    "timeout_seconds": 300
                },
                {
                    "type": "quarantine_account",
                    "duration_hours": 24,
                    "manual_review": True
                },
                {
                    "type": "log_incident",
                    "system": "security_hub",
                    "severity": "critical"
                }
            ],
            "schedule": "real-time",
            "ml_model": "gradient_boosting_ensemble",
            "features": 50,
            "latency_ms": "<100ms"
        },
        "playbook_type": "security",
        "best_for": ["Fintech", "Payment Processing", "Banking", "Insurance"],
        "typical_users": ["Chief Risk Officer", "VP Fraud", "Security Team"],
        "expected_outcomes": {
            "fraud_prevention": "98%+ of fraud attempts blocked",
            "false_positive_rate": "<0.1% (minimal legitimate customer friction)",
            "fraud_loss_prevented": "$1M-50M+ per year",
            "compliance_improvement": "SOC 2, PCI-DSS ready"
        }
    },

    {
        "name": "Demand Forecasting & Inventory Optimization",
        "slug": "demand-forecasting-inventory",
        "description": "Predicts demand 30-90 days ahead to optimize inventory and prevent stockouts. Reduces inventory waste by 25-40%.",
        "category": "forecasting",
        "use_case": "demand-forecasting",
        "industry": "E-commerce",
        "price_monthly": 59.00,
        "price_yearly": 599.00,
        "free": False,
        "icon": "📊",
        "tags": ["forecasting", "inventory", "supply-chain", "cost-savings"],
        "success_rate": 0.89,
        "typical_roi": 3.2,
        "setup_time_minutes": 20,
        "configuration": {
            "trigger": "continuous_daily_forecast",
            "signals": [
                "Historical sales data (24 months)",
                "Seasonality patterns",
                "Trend analysis",
                "Weather data (temperature, rainfall)",
                "Marketing campaigns",
                "Competitor activity",
                "Macro trends (inflation, employment)",
                "Social media sentiment",
                "Google Trends data",
                "Industry benchmarks"
            ],
            "actions": [
                {
                    "type": "update_inventory_forecast",
                    "system": "erp",
                    "frequency": "daily"
                },
                {
                    "type": "purchase_order_recommendation",
                    "alert_procurement": True,
                    "lead_time_days": 30
                },
                {
                    "type": "slack_alert",
                    "channel": "supply-chain",
                    "message": "📦 FORECAST: {product} demand {direction} {percent}% next month"
                },
                {
                    "type": "pricing_adjustment",
                    "trigger": "high_demand",
                    "increase_percent": 5
                },
                {
                    "type": "marketing_spend",
                    "adjust_budget": "based_on_forecast"
                }
            ],
            "schedule": "daily",
            "forecast_horizon_days": 90,
            "ml_model": "prophet_ensemble",
            "confidence_intervals": ["50%", "80%", "95%"]
        },
        "playbook_type": "supply_chain",
        "best_for": ["E-commerce", "Retail", "Manufacturing", "Supply Chain"],
        "typical_users": ["VP Supply Chain", "Inventory Manager", "CFO"],
        "expected_outcomes": {
            "inventory_reduction": "25-40% less waste",
            "stockout_prevention": "95%+ fulfillment rate",
            "working_capital_improvement": "$500K-5M+ freed up",
            "customer_satisfaction": "Faster delivery, better availability"
        }
    },

    {
        "name": "Customer Health Score & Proactive Support",
        "slug": "customer-health-proactive",
        "description": "Continuously monitors customer health and alerts support team to issues before customers complain. Improves NPS by 15-25 points.",
        "category": "retention",
        "use_case": "customer-health",
        "industry": "SaaS",
        "price_monthly": 59.00,
        "price_yearly": 599.00,
        "free": False,
        "icon": "❤️",
        "tags": ["health", "proactive", "support", "retention"],
        "success_rate": 0.72,
        "typical_roi": 2.8,
        "setup_time_minutes": 15,
        "configuration": {
            "trigger": "health_score < 50",
            "signals": [
                "Feature usage frequency",
                "Support ticket sentiment",
                "Response time to emails",
                "NPS score",
                "API error rates",
                "Login frequency",
                "Time to value (days)",
                "Onboarding completion %",
                "Training completion %",
                "Account expansion velocity"
            ],
            "actions": [
                {
                    "type": "assign_to_cs",
                    "role": "CSM",
                    "priority": "high",
                    "message": "Customer health declined. Schedule check-in."
                },
                {
                    "type": "email",
                    "template": "we_noticed",
                    "message": "We noticed you might be struggling. How can we help?"
                },
                {
                    "type": "slack_alert",
                    "channel": "cs-watch",
                    "message": "⚠️ {company} health score: {score} - may need support"
                },
                {
                    "type": "send_resources",
                    "content": "tutorials, guides, knowledge base articles"
                },
                {
                    "type": "schedule_call",
                    "type": "success_consultation",
                    "priority": "high"
                }
            ],
            "schedule": "weekly",
            "scoring_model": "weighted_ensemble"
        },
        "playbook_type": "customer_success",
        "best_for": ["SaaS", "Enterprise Software", "B2B Services"],
        "typical_users": ["VP Customer Success", "CSM", "Support Manager"],
        "expected_outcomes": {
            "nps_improvement": "15-25 point increase",
            "support_efficiency": "30% fewer urgent tickets",
            "proactive_resolution": "Issues fixed before escalation",
            "retention_rate": "35-50% reduction in churn"
        }
    },

    {
        "name": "Employee Turnover Risk & Retention",
        "slug": "employee-retention-risk",
        "description": "Identifies employees at risk of leaving and triggers retention workflow. Save $50K-200K per key employee retained.",
        "category": "retention",
        "use_case": "employee-turnover",
        "industry": "Enterprise",
        "price_monthly": 69.00,
        "price_yearly": 699.00,
        "free": False,
        "icon": "👥",
        "tags": ["hr", "retention", "employees", "cost-savings"],
        "success_rate": 0.68,
        "typical_roi": 5.2,
        "setup_time_minutes": 25,
        "configuration": {
            "trigger": "turnover_risk_score > 0.7",
            "signals": [
                "Job search activity detected",
                "LinkedIn profile update frequency",
                "Decreased performance rating",
                "Negative sentiment in communications",
                "Increased absences",
                "Reduced collaboration",
                "Skipped meetings",
                "Reduced slack activity",
                "External networking activity",
                "Salary market rate vs. actual"
            ],
            "actions": [
                {
                    "type": "alert_manager",
                    "priority": "high",
                    "message": "Employee at retention risk. Consider proactive conversation."
                },
                {
                    "type": "hr_intervention",
                    "actions": [
                        "Schedule 1:1 with manager",
                        "Review compensation",
                        "Discuss career development",
                        "Offer growth opportunity"
                    ]
                },
                {
                    "type": "send_career_development",
                    "content": "training, certifications, growth paths"
                },
                {
                    "type": "compensation_adjustment",
                    "recommend_raise_percent": 10
                },
                {
                    "type": "slack_alert",
                    "channel": "hr-critical",
                    "message": "🚨 KEY EMPLOYEE: {name} showing turnover signals"
                }
            ],
            "schedule": "monthly",
            "scoring_model": "gradient_boosting"
        },
        "playbook_type": "human_resources",
        "best_for": ["Enterprise", "Technology", "Finance", "Healthcare"],
        "typical_users": ["VP HR", "CHO", "Department Manager"],
        "expected_outcomes": {
            "retention_rate": "68% of flagged employees stay",
            "cost_savings": "$50K-200K per key employee retained",
            "productivity_maintenance": "Avoid onboarding/training costs",
            "team_morale": "Proactive support improves engagement"
        }
    },

    {
        "name": "Price Elasticity & Revenue Optimization",
        "slug": "price-elasticity-optimization",
        "description": "Dynamically optimizes pricing based on demand, competition, and customer willingness to pay. Increases revenue 8-15% without volume loss.",
        "category": "pricing",
        "use_case": "price-optimization",
        "industry": "E-commerce",
        "price_monthly": 79.00,
        "price_yearly": 799.00,
        "free": False,
        "icon": "💰",
        "tags": ["pricing", "revenue", "optimization", "automation"],
        "success_rate": 0.75,
        "typical_roi": 4.5,
        "setup_time_minutes": 30,
        "configuration": {
            "trigger": "daily_price_optimization",
            "signals": [
                "Current price vs market",
                "Demand volume",
                "Inventory level",
                "Competitor pricing",
                "Customer segment willingness to pay",
                "Profit margin target",
                "Elasticity coefficient",
                "Seasonality",
                "Macro trends",
                "Customer lifetime value"
            ],
            "actions": [
                {
                    "type": "update_pricing",
                    "products": "dynamic_segment",
                    "frequency": "daily",
                    "max_change_percent": 15
                },
                {
                    "type": "segment_pricing",
                    "segments": [
                        "new_customer (discount 10%)",
                        "loyal_customer (standard)",
                        "high_value (premium)",
                        "price_sensitive (volume)"
                    ]
                },
                {
                    "type": "a_b_test_price",
                    "variants": 3,
                    "duration_days": 7
                },
                {
                    "type": "alert_merchandising",
                    "message": "Price updated: {product} ${old_price} → ${new_price}"
                }
            ],
            "schedule": "daily",
            "optimization_algorithm": "reinforcement_learning",
            "revenue_target": "maximize_profit"
        },
        "playbook_type": "revenue_optimization",
        "best_for": ["E-commerce", "SaaS", "Retail", "Subscription"],
        "typical_users": ["VP Revenue", "Pricing Manager", "CFO"],
        "expected_outcomes": {
            "revenue_increase": "8-15% without volume loss",
            "profit_improvement": "15-25% depending on elasticity",
            "customer_satisfaction": "Maintained or improved",
            "competitive_advantage": "Dynamic pricing vs. static competitors"
        }
    },

    {
        "name": "Product Launch Success Predictor",
        "slug": "product-launch-success",
        "description": "Predicts new product/feature success before launch and optimizes go-to-market strategy. Increases launch ROI by 40-60%.",
        "category": "product",
        "use_case": "product-success",
        "industry": "SaaS",
        "price_monthly": 79.00,
        "price_yearly": 799.00,
        "free": False,
        "icon": "🚀",
        "tags": ["product", "launch", "strategy", "optimization"],
        "success_rate": 0.71,
        "typical_roi": 3.5,
        "setup_time_minutes": 25,
        "configuration": {
            "trigger": "pre_launch_analysis",
            "signals": [
                "Market size & growth",
                "Competitive landscape",
                "Customer feedback/demand",
                "Beta user engagement",
                "Feature adoption in beta",
                "Customer willingness to pay",
                "Go-to-market readiness",
                "Sales team preparedness",
                "Marketing campaign quality",
                "Support team readiness"
            ],
            "actions": [
                {
                    "type": "launch_success_score",
                    "predict": "success_probability",
                    "confidence": "80%+"
                },
                {
                    "type": "identify_gaps",
                    "areas": [
                        "market_awareness",
                        "sales_enablement",
                        "support_readiness",
                        "pricing_optimization",
                        "competitive_positioning"
                    ]
                },
                {
                    "type": "optimize_gtm",
                    "recommendations": [
                        "target_segment",
                        "messaging",
                        "pricing",
                        "launch_date",
                        "marketing_spend"
                    ]
                },
                {
                    "type": "alert_leadership",
                    "message": "Launch success predicted at {score}%. Consider adjustments in {areas}."
                }
            ],
            "schedule": "one_time_pre_launch",
            "ml_model": "ensemble_classifier"
        },
        "playbook_type": "product_strategy",
        "best_for": ["SaaS", "Tech", "Enterprise Software"],
        "typical_users": ["VP Product", "Chief Product Officer", "VP Go-to-Market"],
        "expected_outcomes": {
            "launch_success_rate": "71% probability of success",
            "roi_improvement": "40-60% better launch ROI",
            "time_to_profitability": "30-40% faster",
            "customer_adoption": "Better targeting = faster adoption"
        }
    },

    {
        "name": "Patient Readmission Risk Prevention",
        "slug": "readmission-risk-prevention",
        "description": "Identifies high-risk patients likely to readmit and triggers preventive care. Reduces readmission rates by 25-35%.",
        "category": "retention",
        "use_case": "readmission-prediction",
        "industry": "Healthcare",
        "price_monthly": 99.00,
        "price_yearly": 999.00,
        "free": False,
        "icon": "⚕️",
        "tags": ["healthcare", "clinical", "prevention", "outcomes"],
        "success_rate": 0.81,
        "typical_roi": 6.8,
        "setup_time_minutes": 30,
        "configuration": {
            "trigger": "readmission_risk > 0.7",
            "signals": [
                "Age and comorbidities",
                "Length of stay",
                "Admission type (emergency vs planned)",
                "Discharge disposition",
                "Medication compliance",
                "Social determinants of health",
                "Transportation barriers",
                "Previous readmissions",
                "Lab value trends",
                "Functional status"
            ],
            "actions": [
                {
                    "type": "alert_care_team",
                    "priority": "high",
                    "message": "Patient at high readmission risk ({score}%). Coordinate discharge."
                },
                {
                    "type": "schedule_followup",
                    "timing": "within_48_hours",
                    "type": "nurse_call_or_visit"
                },
                {
                    "type": "medication_reconciliation",
                    "action": "verify_prescriptions",
                    "contact": "pharmacy"
                },
                {
                    "type": "send_patient_resources",
                    "content": "discharge_instructions, symptom_monitoring, emergency_resources"
                },
                {
                    "type": "create_care_plan",
                    "focus_areas": [
                        "medication_adherence",
                        "follow_up_appointments",
                        "dietary_needs",
                        "activity_restrictions"
                    ]
                }
            ],
            "schedule": "at_discharge",
            "ml_model": "gradient_boosting",
            "clinical_validation": True
        },
        "playbook_type": "clinical_outcomes",
        "best_for": ["Healthcare Systems", "Hospitals", "Primary Care"],
        "typical_users": ["Chief Medical Officer", "Care Coordinator", "Discharge Planner"],
        "expected_outcomes": {
            "readmission_reduction": "25-35% reduction in 30-day readmissions",
            "quality_improvement": "Better HCAHPS scores",
            "cost_savings": "$15K-30K per readmission prevented",
            "patient_outcomes": "Better recovery and satisfaction"
        }
    },

    {
        "name": "Support Ticket Escalation Prevention",
        "slug": "support-escalation-prevention",
        "description": "Predicts support tickets that will escalate and routes to senior team proactively. Resolves 60-70% of issues before escalation.",
        "category": "support",
        "use_case": "support-escalation",
        "industry": "SaaS",
        "price_monthly": 49.00,
        "price_yearly": 499.00,
        "free": False,
        "icon": "🎧",
        "tags": ["support", "escalation", "automation", "efficiency"],
        "success_rate": 0.67,
        "typical_roi": 2.5,
        "setup_time_minutes": 15,
        "configuration": {
            "trigger": "escalation_risk > 0.75",
            "signals": [
                "Ticket sentiment (NLP)",
                "Response time delays",
                "First response time",
                "Customer VIP status",
                "Ticket priority",
                "Related recent tickets",
                "Customer lifetime value",
                "Previous escalations",
                "Keywords (urgent, critical)",
                "Resolution time trend"
            ],
            "actions": [
                {
                    "type": "assign_to_senior_agent",
                    "immediately": True,
                    "message": "High escalation risk ticket"
                },
                {
                    "type": "send_resources",
                    "type": "knowledge_base_articles",
                    "relevant_to": "ticket_issue"
                },
                {
                    "type": "schedule_priority_response",
                    "sla_minutes": 30
                },
                {
                    "type": "alert_manager",
                    "message": "Ticket at escalation risk - suggest proactive follow-up"
                },
                {
                    "type": "auto_draft_response",
                    "template": "relevant_solution",
                    "require_review": True
                }
            ],
            "schedule": "real-time",
            "ml_model": "text_classification"
        },
        "playbook_type": "customer_support",
        "best_for": ["SaaS", "Enterprise Software", "Tech Support"],
        "typical_users": ["Head of Support", "Support Manager", "QA Lead"],
        "expected_outcomes": {
            "escalation_prevention": "60-70% of high-risk tickets prevented",
            "csat_improvement": "Better customer satisfaction",
            "support_efficiency": "30% fewer escalations",
            "agent_stress": "Reduced workload for senior team"
        }
    }
]


def seed_playbook_templates(db_session, organization_id=1):
    """
    Seed database with default playbook templates
    Run once during setup

    Usage:
        from app.fixtures.playbook_templates import seed_playbook_templates
        seed_playbook_templates(db_session)
    """
    from app.db.marketplace_models import Playbook
    from datetime import datetime
    from uuid import uuid4

    system_user_id = 1  # System user ID for ForecastX playbooks

    for template in PLAYBOOK_TEMPLATES:
        # Check if already exists
        existing = db_session.query(Playbook).filter(
            Playbook.slug == template["slug"]
        ).first()

        if existing:
            continue

        playbook = Playbook(
            organization_id=organization_id,
            creator_id=system_user_id,
            name=template["name"],
            slug=template["slug"],
            description=template["description"],
            category=template["category"],
            use_case=template["use_case"],
            industry=template["industry"],
            price_monthly=template["price_monthly"],
            price_yearly=template.get("price_yearly"),
            free=template["free"],
            icon=template["icon"],
            tags=template.get("tags", []),
            configuration=template["configuration"],
            success_rate=template.get("success_rate"),
            typical_roi=template.get("typical_roi"),
            setup_time_minutes=template.get("setup_time_minutes"),
            status="published",
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        db_session.add(playbook)

    db_session.commit()
    return len(PLAYBOOK_TEMPLATES)
