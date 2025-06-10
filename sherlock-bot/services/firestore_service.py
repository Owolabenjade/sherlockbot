# Import all functions from firebase_service
from .firebase_service import save_review_result, get_review, get_user_session, update_user_session

# Re-export for backward compatibility
__all__ = ['save_review_result', 'get_review', 'get_user_session', 'update_user_session']
