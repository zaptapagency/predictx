"""
ForecastX Marketplace API
- Browse & search playbooks
- Publish playbooks
- Purchase & install playbooks
- Creator dashboard & earnings
- Reviews & ratings
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import uuid

from app.db.models_saas import User, Organization
from app.db.marketplace_models import (
    Playbook, PlaybookReview, PlaybookPurchase, CreatorEarnings,
    PlaybookStatus
)
from app.services.email_service import EmailService
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])
email_service = EmailService()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PlaybookPublishRequest(BaseModel):
    name: str
    description: str
    category: str  # churn, expansion, fraud, etc
    use_case: str  # lead-scoring, churn-prediction, etc
    industry: str = None  # saas, ecommerce, fintech, etc
    price_monthly: float = 49.0
    price_yearly: float = None
    free: bool = False
    configuration: dict  # Playbook logic
    success_rate: float = None  # 0.78 = 78%
    typical_roi: float = None  # 5.6 = 560% ROI
    setup_time_minutes: int = None

class PlaybookListResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    category: str
    use_case: str
    industry: str
    price_monthly: float
    free: bool
    creator: dict  # {id, name, email}
    downloads: int
    active_users: int
    avg_rating: float
    review_count: int
    success_rate: float
    typical_roi: float
    setup_time_minutes: int
    icon: str
    thumbnail_url: str
    published_at: datetime

class PlaybookDetailResponse(PlaybookListResponse):
    configuration: dict
    tags: list
    created_at: datetime
    total_revenue: float
    total_purchases: int = None

class ReviewRequest(BaseModel):
    rating: int  # 1-5
    title: str = None
    review_text: str = None
    ease_of_setup: int = None  # 1-5
    roi_achieved: str = None  # exceeded, met, lower
    would_recommend: bool = True

# ============================================================================
# BROWSE MARKETPLACE
# ============================================================================

@router.get("/playbooks")
def browse_playbooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    category: str = Query(None),
    use_case: str = Query(None),
    industry: str = Query(None),
    sort: str = Query("popular"),  # popular, newest, highest-rated, trending
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Browse all published playbooks in marketplace
    Filters: category, use_case, industry
    Sort: popular, newest, highest-rated, trending
    """

    query = db.query(Playbook).filter(Playbook.status == PlaybookStatus.PUBLISHED)

    # Apply filters
    if category:
        query = query.filter(Playbook.category == category)
    if use_case:
        query = query.filter(Playbook.use_case == use_case)
    if industry:
        query = query.filter(Playbook.industry == industry)

    # Search
    if search:
        query = query.filter(
            (Playbook.name.ilike(f"%{search}%")) |
            (Playbook.description.ilike(f"%{search}%"))
        )

    # Sort
    if sort == "newest":
        query = query.order_by(desc(Playbook.published_at))
    elif sort == "highest-rated":
        query = query.order_by(desc(Playbook.avg_rating))
    elif sort == "trending":
        # Trending = high downloads in last 7 days (simplified)
        query = query.order_by(desc(Playbook.downloads))
    else:  # popular (default)
        query = query.order_by(desc(Playbook.downloads))

    total = query.count()
    playbooks = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "playbooks": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "category": p.category,
                "use_case": p.use_case,
                "industry": p.industry,
                "price_monthly": p.price_monthly,
                "free": p.free,
                "creator": {
                    "id": p.creator.id,
                    "name": p.creator.name,
                    "email": p.creator.email
                },
                "downloads": p.downloads,
                "active_users": p.active_users,
                "avg_rating": p.avg_rating,
                "review_count": p.review_count,
                "success_rate": p.success_rate,
                "typical_roi": p.typical_roi,
                "setup_time_minutes": p.setup_time_minutes,
                "icon": p.icon,
                "thumbnail_url": p.thumbnail_url,
                "published_at": p.published_at,
            }
            for p in playbooks
        ]
    }


# ============================================================================
# GET PLAYBOOK DETAILS
# ============================================================================

@router.get("/playbooks/{playbook_slug}")
def get_playbook_detail(
    playbook_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed info about a playbook"""

    playbook = db.query(Playbook).filter(
        Playbook.slug == playbook_slug,
        Playbook.status == PlaybookStatus.PUBLISHED
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Check if current user has purchased
    has_purchased = db.query(PlaybookPurchase).filter(
        PlaybookPurchase.playbook_id == playbook.id,
        PlaybookPurchase.organization_id == current_user.organization_id,
        PlaybookPurchase.is_active == True
    ).first() is not None

    return {
        "id": playbook.id,
        "name": playbook.name,
        "slug": playbook.slug,
        "description": playbook.description,
        "category": playbook.category,
        "use_case": playbook.use_case,
        "industry": playbook.industry,
        "price_monthly": playbook.price_monthly,
        "price_yearly": playbook.price_yearly,
        "free": playbook.free,
        "creator": {
            "id": playbook.creator.id,
            "name": playbook.creator.name,
        },
        "configuration": playbook.configuration,
        "tags": playbook.tags or [],
        "downloads": playbook.downloads,
        "active_users": playbook.active_users,
        "avg_rating": playbook.avg_rating,
        "review_count": playbook.review_count,
        "success_rate": playbook.success_rate,
        "typical_roi": playbook.typical_roi,
        "setup_time_minutes": playbook.setup_time_minutes,
        "icon": playbook.icon,
        "thumbnail_url": playbook.thumbnail_url,
        "published_at": playbook.published_at,
        "total_revenue": playbook.total_revenue,
        "has_purchased": has_purchased,
        "reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "title": r.title,
                "review_text": r.review_text,
                "user_name": r.user.name,
                "ease_of_setup": r.ease_of_setup,
                "would_recommend": r.would_recommend,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at,
            }
            for r in db.query(PlaybookReview)
                .filter(PlaybookReview.playbook_id == playbook.id)
                .order_by(desc(PlaybookReview.helpful_count))
                .limit(10)
                .all()
        ]
    }


# ============================================================================
# PUBLISH PLAYBOOK (Create)
# ============================================================================

@router.post("/playbooks")
def publish_playbook(
    payload: PlaybookPublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish a new playbook to marketplace
    Creator becomes owner and earns 70% of revenue
    """

    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must be part of an organization")

    # Create slug from name
    slug = payload.name.lower().replace(" ", "-").replace("_", "-")[:50]

    # Check if slug already exists
    existing = db.query(Playbook).filter(Playbook.slug == slug).first()
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"

    playbook = Playbook(
        organization_id=current_user.organization_id,
        creator_id=current_user.id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        category=payload.category,
        use_case=payload.use_case,
        industry=payload.industry,
        price_monthly=payload.price_monthly,
        price_yearly=payload.price_yearly,
        free=payload.free,
        configuration=payload.configuration,
        success_rate=payload.success_rate,
        typical_roi=payload.typical_roi,
        setup_time_minutes=payload.setup_time_minutes,
        status=PlaybookStatus.PENDING_REVIEW,  # Auto-review or manual?
    )

    db.add(playbook)
    db.commit()
    db.refresh(playbook)

    return {
        "success": True,
        "playbook_id": playbook.id,
        "slug": playbook.slug,
        "status": playbook.status,
        "message": "Playbook submitted for review. We'll publish it within 24 hours."
    }


# ============================================================================
# PURCHASE PLAYBOOK
# ============================================================================

@router.post("/playbooks/{playbook_id}/purchase")
def purchase_playbook(
    playbook_id: int,
    license_type: str = Query("monthly"),  # monthly, yearly
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Purchase/subscribe to a playbook
    Handles payment via Stripe
    """

    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must be part of an organization")

    # Check if already purchased
    existing_purchase = db.query(PlaybookPurchase).filter(
        PlaybookPurchase.playbook_id == playbook_id,
        PlaybookPurchase.organization_id == current_user.organization_id,
        PlaybookPurchase.is_active == True
    ).first()

    if existing_purchase:
        raise HTTPException(status_code=400, detail="Already subscribed to this playbook")

    # Calculate price
    if playbook.free:
        price_paid = 0.0
    elif license_type == "yearly" and playbook.price_yearly:
        price_paid = playbook.price_yearly
    else:
        price_paid = playbook.price_monthly

    # TODO: Integrate with Stripe to actually charge
    # For now, simulate purchase

    purchase = PlaybookPurchase(
        playbook_id=playbook_id,
        organization_id=current_user.organization_id,
        purchased_by_id=current_user.id,
        license_type=license_type,
        price_paid=price_paid,
        is_active=True,
        started_at=datetime.utcnow(),
    )

    if license_type == "yearly":
        purchase.expires_at = datetime.utcnow() + timedelta(days=365)

    db.add(purchase)

    # Update playbook metrics
    playbook.downloads += 1
    playbook.active_users += 1
    playbook.total_revenue += price_paid

    db.commit()

    return {
        "success": True,
        "message": "Successfully subscribed to playbook",
        "playbook": playbook.name,
        "license_type": license_type,
        "price_paid": price_paid,
        "expires_at": purchase.expires_at,
    }


# ============================================================================
# LEAVE REVIEW
# ============================================================================

@router.post("/playbooks/{playbook_id}/reviews")
def leave_review(
    playbook_id: int,
    payload: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a review/rating for a playbook"""

    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Check if user has purchased playbook
    has_purchased = db.query(PlaybookPurchase).filter(
        PlaybookPurchase.playbook_id == playbook_id,
        PlaybookPurchase.organization_id == current_user.organization_id
    ).first()

    if not has_purchased:
        raise HTTPException(status_code=403, detail="Must purchase playbook to leave review")

    # Check if already reviewed
    existing_review = db.query(PlaybookReview).filter(
        PlaybookReview.playbook_id == playbook_id,
        PlaybookReview.user_id == current_user.id
    ).first()

    if existing_review:
        # Update existing review
        existing_review.rating = payload.rating
        existing_review.title = payload.title
        existing_review.review_text = payload.review_text
        existing_review.ease_of_setup = payload.ease_of_setup
        existing_review.roi_achieved = payload.roi_achieved
        existing_review.would_recommend = payload.would_recommend
    else:
        # Create new review
        review = PlaybookReview(
            playbook_id=playbook_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            rating=payload.rating,
            title=payload.title,
            review_text=payload.review_text,
            ease_of_setup=payload.ease_of_setup,
            roi_achieved=payload.roi_achieved,
            would_recommend=payload.would_recommend,
        )
        db.add(review)

    # Update playbook average rating
    all_reviews = db.query(PlaybookReview).filter(PlaybookReview.playbook_id == playbook_id).all()
    if all_reviews:
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        playbook.avg_rating = round(avg_rating, 2)
        playbook.review_count = len(all_reviews)

    db.commit()

    return {
        "success": True,
        "message": "Review submitted successfully",
        "playbook_rating": playbook.avg_rating,
    }


# ============================================================================
# CREATOR DASHBOARD
# ============================================================================

@router.get("/creator/dashboard")
def creator_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get creator dashboard with all their playbooks & earnings"""

    # Get all playbooks created by user
    playbooks = db.query(Playbook).filter(
        Playbook.creator_id == current_user.id
    ).all()

    if not playbooks:
        return {
            "playbooks": [],
            "total_earnings": 0.0,
            "total_purchases": 0,
            "total_active_users": 0,
        }

    playbook_ids = [p.id for p in playbooks]

    # Get earnings for current month
    current_month = datetime.utcnow().strftime("%Y-%m")
    earnings = db.query(CreatorEarnings).filter(
        CreatorEarnings.creator_id == current_user.id,
        CreatorEarnings.month == current_month
    ).first()

    # Get total purchases
    total_purchases = db.query(PlaybookPurchase).filter(
        PlaybookPurchase.playbook_id.in_(playbook_ids)
    ).count()

    return {
        "playbooks": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "status": p.status,
                "downloads": p.downloads,
                "active_users": p.active_users,
                "avg_rating": p.avg_rating,
                "review_count": p.review_count,
                "total_revenue": p.total_revenue,
                "price_monthly": p.price_monthly,
                "published_at": p.published_at,
            }
            for p in playbooks
        ],
        "earnings_this_month": {
            "total_revenue": earnings.total_revenue if earnings else 0.0,
            "creator_share": earnings.creator_share if earnings else 0.0,
            "forecastx_share": earnings.forecastx_share if earnings else 0.0,
            "active_subscriptions": earnings.active_subscriptions if earnings else 0,
        },
        "all_time_stats": {
            "total_earnings": sum(p.total_revenue for p in playbooks),
            "total_purchases": total_purchases,
            "total_active_users": sum(p.active_users for p in playbooks),
            "avg_rating": sum(p.avg_rating for p in playbooks) / len(playbooks) if playbooks else 0.0,
        }
    }


# ============================================================================
# CREATOR EARNINGS HISTORY
# ============================================================================

@router.get("/creator/earnings")
def creator_earnings(
    months: int = Query(12),  # Last N months
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get earnings history for creator"""

    earnings = db.query(CreatorEarnings).filter(
        CreatorEarnings.creator_id == current_user.id
    ).order_by(desc(CreatorEarnings.month)).limit(months).all()

    return {
        "earnings": [
            {
                "month": e.month,
                "total_revenue": e.total_revenue,
                "creator_share": e.creator_share,
                "forecastx_share": e.forecastx_share,
                "active_subscriptions": e.active_subscriptions,
                "churn_rate": f"{e.churn_of_purchases:.1f}%",
                "payout_status": e.payout_status,
                "payout_date": e.payout_date,
            }
            for e in earnings
        ]
    }


# ============================================================================
# MY PURCHASES
# ============================================================================

@router.get("/my-purchases")
def my_purchases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all playbooks purchased by user's organization"""

    if not current_user.organization_id:
        return {"purchases": []}

    purchases = db.query(PlaybookPurchase).filter(
        PlaybookPurchase.organization_id == current_user.organization_id,
        PlaybookPurchase.is_active == True
    ).all()

    return {
        "purchases": [
            {
                "playbook_id": p.playbook_id,
                "playbook_name": p.playbook.name,
                "creator": p.playbook.creator.name,
                "license_type": p.license_type,
                "price_paid": p.price_paid,
                "started_at": p.started_at,
                "expires_at": p.expires_at,
                "times_run": p.times_run,
                "last_used_at": p.last_used_at,
                "churn_saved": p.churn_saved,
                "customers_affected": p.customers_affected,
            }
            for p in purchases
        ]
    }


# ============================================================================
# MARKETPLACE STATS
# ============================================================================

@router.get("/stats")
def marketplace_stats(db: Session = Depends(get_db)):
    """Get overall marketplace statistics (public)"""

    total_playbooks = db.query(Playbook).filter(
        Playbook.status == PlaybookStatus.PUBLISHED
    ).count()

    total_creators = db.query(Playbook).filter(
        Playbook.status == PlaybookStatus.PUBLISHED
    ).distinct(Playbook.creator_id).count()

    total_purchases = db.query(PlaybookPurchase).count()

    total_revenue = db.query(func.sum(PlaybookPurchase.price_paid)).scalar() or 0.0

    # Top playbook
    top_playbook = db.query(Playbook).filter(
        Playbook.status == PlaybookStatus.PUBLISHED
    ).order_by(desc(Playbook.downloads)).first()

    return {
        "total_playbooks": total_playbooks,
        "total_creators": total_creators,
        "total_purchases": total_purchases,
        "total_revenue": total_revenue,
        "top_playbook": {
            "name": top_playbook.name,
            "downloads": top_playbook.downloads,
        } if top_playbook else None,
    }
