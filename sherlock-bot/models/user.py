# models/user.py - User model
from datetime import datetime
from firebase_admin import firestore
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

class User:
    """User model class for database operations"""
    
    @classmethod
    def get_by_id(cls, user_id):
        """
        Get user by ID
        
        Args:
            user_id (str): User ID (phone number)
            
        Returns:
            dict: User data
        """
        try:
            db = firestore.client()
            user_doc = db.collection('sessions').document(user_id).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['id'] = user_id
                return user_data
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    @classmethod
    def get_count(cls):
        """
        Get total user count
        
        Returns:
            int: User count
        """
        try:
            db = firestore.client()
            users_ref = db.collection('sessions')
            return len(list(users_ref.stream()))
        
        except Exception as e:
            logger.error(f"Error getting user count: {str(e)}")
            return 0
    
    @classmethod
    def get_recent(cls, limit=10):
        """
        Get recent users
        
        Args:
            limit (int): Maximum number of users to return
            
        Returns:
            list: Recent users
        """
        try:
            db = firestore.client()
            users = []
            
            # Get users sorted by created_at
            users_ref = db.collection('sessions').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            for user_doc in users_ref.stream():
                user_data = user_doc.to_dict()
                user_data['id'] = user_doc.id
                users.append(user_data)
            
            return users
        
        except Exception as e:
            logger.error(f"Error getting recent users: {str(e)}")
            return []
    
    @classmethod
    def get_paginated(cls, page=1, per_page=20):
        """
        Get paginated users
        
        Args:
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (users, total_count)
        """
        try:
            db = firestore.client()
            
            # Get total count
            total = cls.get_count()
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get users with pagination
            users_ref = db.collection('sessions').order_by('created_at', direction=firestore.Query.DESCENDING).limit(per_page).offset(offset)
            
            users = []
            for user_doc in users_ref.stream():
                user_data = user_doc.to_dict()
                user_data['id'] = user_doc.id
                users.append(user_data)
            
            return users, total
        
        except Exception as e:
            logger.error(f"Error getting paginated users: {str(e)}")
            return [], 0
    
    @classmethod
    def search(cls, query, page=1, per_page=20):
        """
        Search users
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (users, total_count)
        """
        try:
            db = firestore.client()
            users = []
            
            # Get all users (Firestore doesn't support text search)
            users_ref = db.collection('sessions').stream()
            
            for user_doc in users_ref:
                user_data = user_doc.to_dict()
                user_data['id'] = user_doc.id
                
                # Filter users manually
                if query.lower() in user_doc.id.lower() or query.lower() in str(user_data).lower():
                    users.append(user_data)
            
            # Sort by created_at
            users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Calculate total
            total = len(users)
            
            # Paginate results
            start = (page - 1) * per_page
            end = start + per_page
            users = users[start:end]
            
            return users, total
        
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return [], 0
    
    @classmethod
    def get_stats(cls, start_date, end_date, interval='day'):
        """
        Get user statistics
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            interval (str): Interval (hour, day, month)
            
        Returns:
            dict: User statistics
        """
        try:
            db = firestore.client()
            
            # Convert dates to strings
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            
            # Get users in date range
            users_ref = db.collection('sessions').where('created_at', '>=', start_str).where('created_at', '<=', end_str).stream()
            
            users = []
            for user_doc in users_ref:
                user_data = user_doc.to_dict()
                user_data['id'] = user_doc.id
                users.append(user_data)
            
            # Group by interval
            grouped = {}
            
            for user in users:
                created_at = user.get('created_at')
                if not created_at:
                    continue
                
                created_date = datetime.fromisoformat(created_at)
                
                # Format key based on interval
                if interval == 'hour':
                    key = created_date.strftime('%Y-%m-%d %H:00')
                elif interval == 'day':
                    key = created_date.strftime('%Y-%m-%d')
                elif interval == 'month':
                    key = created_date.strftime('%Y-%m')
                else:
                    key = created_date.strftime('%Y-%m-%d')
                
                if key not in grouped:
                    grouped[key] = 0
                
                grouped[key] += 1
            
            # Format for chart
            labels = sorted(grouped.keys())
            values = [grouped[key] for key in labels]
            
            return {
                'labels': labels,
                'values': values,
                'total': sum(values)
            }
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                'labels': [],
                'values': [],
                'total': 0
            }