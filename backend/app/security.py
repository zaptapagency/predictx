"""
Security & Compliance Implementation
- Data encryption (at-rest, in-transit)
- Audit logging
- GDPR/CCPA compliance
"""

from cryptography.fernet import Fernet
from sqlalchemy import Column, String, DateTime, Integer, Text
from datetime import datetime
import json
import os
from app.utils.time import utcnow

# ============================================================================
# DATA ENCRYPTION (At-Rest)
# ============================================================================

class EncryptionManager:
    """Encrypts/decrypts sensitive data (PII, API keys)"""

    def __init__(self, key: str = None):
        """Initialize with encryption key from env"""
        if not key:
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                raise ValueError("ENCRYPTION_KEY not set in environment")
        self.cipher = Fernet(key.encode())

    def encrypt(self, data: str) -> str:
        """Encrypt data to store in database"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data retrieved from database"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


# ============================================================================
# AUDIT LOGGING (Track who accessed what, when)
# ============================================================================

class AuditLog(Base):
    """Audit log for compliance (GDPR, SOC 2)"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    action = Column(String)  # 'login', 'api_key_created', 'data_export', 'admin_access'
    resource_type = Column(String)  # 'user', 'prediction', 'api_key'
    resource_id = Column(String)  # ID of the resource (user_id, prediction_id, etc)
    status = Column(String)  # 'success', 'failure'
    ip_address = Column(String)
    user_agent = Column(String)
    request_data = Column(Text)  # JSON of what was requested
    response_status = Column(Integer)  # HTTP status code
    timestamp = Column(DateTime, default=utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id} at {self.timestamp}>"


# ============================================================================
# AUDIT LOGGING FUNCTIONS
# ============================================================================

def log_audit(
    db,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: str,
    status: str = "success",
    ip_address: str = None,
    user_agent: str = None,
    request_data: dict = None,
    response_status: int = 200
):
    """Log action to audit trail (for compliance)"""

    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        ip_address=ip_address,
        user_agent=user_agent,
        request_data=json.dumps(request_data) if request_data else None,
        response_status=response_status,
        timestamp=utcnow()
    )
    db.add(audit)
    db.commit()
    return audit


# ============================================================================
# GDPR COMPLIANCE
# ============================================================================

def delete_user_data(db, user_id: int):
    """Delete all user data on request (GDPR right to be forgotten)"""

    # Log the deletion request
    log_audit(
        db, user_id,
        action='user_data_deletion_requested',
        resource_type='user',
        resource_id=str(user_id)
    )

    # Delete user's data
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # Delete: predictions, api keys, subscriptions, audit logs
    db.query(Prediction).filter(Prediction.user_id == user_id).delete()
    db.query(APIKey).filter(APIKey.user_id == user_id).delete()
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    db.query(Invoice).filter(Invoice.user_id == user_id).delete()
    db.query(UsageLog).filter(UsageLog.user_id == user_id).delete()

    # Delete user account
    db.delete(user)
    db.commit()

    return True


# ============================================================================
# DATA RESIDENCY (Store data in specific region)
# ============================================================================

class DataResidency:
    """Store user data in specific geographic region"""

    REGIONS = {
        'us': 'postgresql://...',  # US data center
        'eu': 'postgresql://...',  # EU data center (GDPR compliant)
        'asia': 'postgresql://...',  # Asia data center
    }

    @staticmethod
    def get_database_url(user_region: str = 'us'):
        """Get appropriate database URL based on user's region"""
        return DataResidency.REGIONS.get(user_region, DataResidency.REGIONS['us'])


# ============================================================================
# HIPAA COMPLIANCE (For healthcare use cases)
# ============================================================================

class HIPAACompliance:
    """Healthcare data protection (HIPAA)"""

    @staticmethod
    def encrypt_pii(data: str) -> str:
        """HIPAA requires encryption of PHI (Protected Health Information)"""
        manager = EncryptionManager()
        return manager.encrypt(data)

    @staticmethod
    def log_healthcare_access(db, user_id: int, patient_id: str, action: str):
        """Log all healthcare data access (HIPAA audit trail)"""
        log_audit(
            db, user_id,
            action=f'hipaa_{action}',
            resource_type='patient',
            resource_id=patient_id
        )


# ============================================================================
# CCPA COMPLIANCE (California Consumer Privacy Act)
# ============================================================================

class CCPACompliance:
    """California privacy law requirements"""

    PERSONAL_DATA_TYPES = [
        'email', 'name', 'phone', 'address',
        'billing_address', 'ip_address', 'user_agent'
    ]

    @staticmethod
    def get_user_personal_data(db, user_id: int) -> dict:
        """Export all personal data user (CCPA right to know)"""
        user = db.query(User).filter(User.id == user_id).first()

        return {
            'email': user.email,
            'name': user.name,
            'company': user.organization.name if user.organization else None,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'predictions_count': len(user.predictions),
            'subscriptions': [
                {
                    'tier': sub.tier,
                    'status': sub.status,
                    'started_at': sub.started_at.isoformat(),
                }
                for sub in user.subscriptions
            ]
        }


# ============================================================================
# EXAMPLE: Add to FastAPI routes
# ============================================================================

"""
# In backend/app/api/compliance.py

from fastapi import APIRouter, Depends, HTTPException
from app.security import delete_user_data, CCPACompliance, log_audit

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

@router.post("/data/export")
def export_user_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''Export all personal data (CCPA compliance)'''

    data = CCPACompliance.get_user_personal_data(db, user.id)
    log_audit(db, user.id, 'data_export_requested', 'user', str(user.id))

    return {
        'status': 'success',
        'data': data,
        'export_date': utcnow().isoformat()
    }

@router.post("/data/delete")
def request_data_deletion(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''Delete all user data (GDPR/CCPA right to be forgotten)'''

    delete_user_data(db, user.id)

    return {
        'status': 'success',
        'message': 'Your data will be deleted within 30 days'
    }
"""
