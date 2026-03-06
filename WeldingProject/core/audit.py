"""RBAC audit logging: record User_ID for every Sale, Transfer, Approval."""
from .models import AuditLog


def log_audit(user, action, object_type=None, object_id=None, outlet_id=None, details=None):
    """Record an audit entry. Every action (Sale, Stock Transfer, Approval) records who did it."""
    if details is None:
        details = {}
    AuditLog.objects.create(
        user_id=getattr(user, 'id', None) if user else None,
        action=action,
        object_type=object_type or '',
        object_id=object_id,
        outlet_id=outlet_id,
        details=details,
    )
