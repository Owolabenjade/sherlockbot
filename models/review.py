# models/review.py - Review model
import uuid
from datetime import datetime
from firebase_admin import firestore
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

class Review:
    """Review model class for database operations"""
    
    @classmethod
    def get_by_id(cls, review_id):
        """
        Get review by ID
        
        Args:
            review_id (str): Review ID
            
        Returns:
            dict: Review data
        """
        try:
            db = firestore.client()
            review_doc = db.collection('reviews').document(review_id).get()
            
            if review_doc.exists:
                review_data = review_doc.to_dict()
                review_data['id'] = review_id
                return review_data
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting review {review_id}: {str(e)}")
            return None
    
    @classmethod
    def get_by_user(cls, user_id):
        """
        Get reviews by user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: Review data
        """
        try:
            db = firestore.client()
            reviews = []
            
            reviews_ref = db.collection('reviews').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            for review_doc in reviews_ref.stream():
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                reviews.append(review_data)
            
            return reviews
        
        except Exception as e:
            logger.error(f"Error getting reviews for user {user_id}: {str(e)}")
            return []
    
    @classmethod
    def get_count(cls):
        """
        Get total review count
        
        Returns:
            int: Review count
        """
        try:
            db = firestore.client()
            reviews_ref = db.collection('reviews')
            return len(list(reviews_ref.stream()))
        
        except Exception as e:
            logger.error(f"Error getting review count: {str(e)}")
            return 0
    
    @classmethod
    def get_count_by_type(cls, review_type):
        """
        Get review count by type
        
        Args:
            review_type (str): Review type
            
        Returns:
            int: Review count
        """
        try:
            db = firestore.client()
            reviews_ref = db.collection('reviews').where('review_type', '==', review_type)
            return len(list(reviews_ref.stream()))
        
        except Exception as e:
            logger.error(f"Error getting review count by type {review_type}: {str(e)}")
            return 0
    
    @classmethod
    def get_recent(cls, limit=10):
        """
        Get recent reviews
        
        Args:
            limit (int): Maximum number of reviews to return
            
        Returns:
            list: Recent reviews
        """
        try:
            db = firestore.client()
            reviews = []
            
            # Get reviews sorted by timestamp
            reviews_ref = db.collection('reviews').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            for review_doc in reviews_ref.stream():
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                reviews.append(review_data)
            
            return reviews
        
        except Exception as e:
            logger.error(f"Error getting recent reviews: {str(e)}")
            return []
    
    @classmethod
    def get_paginated(cls, page=1, per_page=20):
        """
        Get paginated reviews
        
        Args:
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (reviews, total_count)
        """
        try:
            db = firestore.client()
            
            # Get total count
            total = cls.get_count()
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get reviews with pagination
            reviews_ref = db.collection('reviews').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(per_page).offset(offset)
            
            reviews = []
            for review_doc in reviews_ref.stream():
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                reviews.append(review_data)
            
            return reviews, total
        
        except Exception as e:
            logger.error(f"Error getting paginated reviews: {str(e)}")
            return [], 0
    
    @classmethod
    def get_by_type(cls, review_type, page=1, per_page=20):
        """
        Get reviews by type
        
        Args:
            review_type (str): Review type
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (reviews, total_count)
        """
        try:
            db = firestore.client()
            
            # Get total count for this type
            total = cls.get_count_by_type(review_type)
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get reviews with pagination
            reviews_ref = db.collection('reviews').where('review_type', '==', review_type).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(per_page).offset(offset)
            
            reviews = []
            for review_doc in reviews_ref.stream():
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                reviews.append(review_data)
            
            return reviews, total
        
        except Exception as e:
            logger.error(f"Error getting reviews by type {review_type}: {str(e)}")
            return [], 0
    
    @classmethod
    def search(cls, query, page=1, per_page=20):
        """
        Search reviews
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (reviews, total_count)
        """
        try:
            db = firestore.client()
            reviews = []
            
            # Get all reviews (Firestore doesn't support text search)
            reviews_ref = db.collection('reviews').stream()
            
            for review_doc in reviews_ref:
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                
                # Filter reviews manually
                if query.lower() in str(review_data).lower():
                    reviews.append(review_data)
            
            # Sort by timestamp
            reviews.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Calculate total
            total = len(reviews)
            
            # Paginate results
            start = (page - 1) * per_page
            end = start + per_page
            reviews = reviews[start:end]
            
            return reviews, total
        
        except Exception as e:
            logger.error(f"Error searching reviews: {str(e)}")
            return [], 0
    
    @classmethod
    def get_stats(cls, start_date, end_date, interval='day'):
        """
        Get review statistics
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            interval (str): Interval (hour, day, month)
            
        Returns:
            dict: Review statistics
        """
        try:
            db = firestore.client()
            
            # Convert dates to strings
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            
            # Get reviews in date range
            reviews_ref = db.collection('reviews').where('timestamp', '>=', start_str).where('timestamp', '<=', end_str).stream()
            
            reviews = []
            for review_doc in reviews_ref:
                review_data = review_doc.to_dict()
                review_data['id'] = review_doc.id
                reviews.append(review_data)
            
            # Group by interval and type
            grouped = {
                'basic': {},
                'advanced': {}
            }
            
            for review in reviews:
                timestamp = review.get('timestamp')
                review_type = review.get('review_type', 'basic')
                
                if not timestamp:
                    continue
                
                review_date = datetime.fromisoformat(timestamp)
                
                # Format key based on interval
                if interval == 'hour':
                    key = review_date.strftime('%Y-%m-%d %H:00')
                elif interval == 'day':
                    key = review_date.strftime('%Y-%m-%d')
                elif interval == 'month':
                    key = review_date.strftime('%Y-%m')
                else:
                    key = review_date.strftime('%Y-%m-%d')
                
                if key not in grouped[review_type]:
                    grouped[review_type][key] = 0
                
                grouped[review_type][key] += 1
            
            # Get all keys
            all_keys = set()
            for review_type in grouped:
                all_keys.update(grouped[review_type].keys())
            
            # Sort keys
            labels = sorted(all_keys)
            
            # Build datasets
            datasets = []
            
            for review_type in ['basic', 'advanced']:
                data = [grouped[review_type].get(key, 0) for key in labels]
                
                datasets.append({
                    'label': f"{review_type.capitalize()} Reviews",
                    'data': data,
                    'total': sum(data)
                })
            
            return {
                'labels': labels,
                'datasets': datasets,
                'total': sum(datasets[0]['total'] + datasets[1]['total'])
            }
        
        except Exception as e:
            logger.error(f"Error getting review stats: {str(e)}")
            return {
                'labels': [],
                'datasets': [],
                'total': 0
            }

    @classmethod
    def save(cls, review_data):
        """
        Save review to database
        
        Args:
            review_data (dict): Review data
            
        Returns:
            str: Review ID
        """
        try:
            db = firestore.client()
            
            # Generate ID
            review_id = str(uuid.uuid4())
            
            # Add timestamp if not present
            if 'timestamp' not in review_data:
                review_data['timestamp'] = datetime.now().isoformat()
            
            # Save to database
            db.collection('reviews').document(review_id).set(review_data)
            
            return review_id
        
        except Exception as e:
            logger.error(f"Error saving review: {str(e)}")
            return None