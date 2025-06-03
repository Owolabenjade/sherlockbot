# models/payment.py - Payment model
from datetime import datetime
from firebase_admin import firestore
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

class Payment:
    """Payment model class for database operations"""
    
    def __init__(self):
        """Initialize Payment model"""
        self.db = firestore.client()
    
    def save_feedback(self, reason, feedback_text):
        """
        Save payment feedback
        
        Args:
            reason (str): Cancellation reason
            feedback_text (str): Feedback text
            
        Returns:
            str: Feedback ID
        """
        try:
            # Create feedback document
            feedback_data = {
                'reason': reason,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to database
            feedback_ref = self.db.collection('payment_feedback').add(feedback_data)
            
            logger.info(f"Saved payment feedback: {feedback_ref.id}")
            
            return feedback_ref.id
        
        except Exception as e:
            logger.error(f"Error saving payment feedback: {str(e)}")
            return None
    
    @classmethod
    def get_count(cls):
        """
        Get total payment count
        
        Returns:
            int: Payment count
        """
        try:
            db = firestore.client()
            payments_ref = db.collection('payments')
            return len(list(payments_ref.stream()))
        
        except Exception as e:
            logger.error(f"Error getting payment count: {str(e)}")
            return 0
    
    @classmethod
    def get_total_amount(cls):
        """
        Get total payment amount
        
        Returns:
            float: Total amount
        """
        try:
            db = firestore.client()
            total = 0.0
            
            # Get all payments
            payments_ref = db.collection('payments').stream()
            
            for payment_doc in payments_ref:
                payment_data = payment_doc.to_dict()
                amount = payment_data.get('amount', 0)
                total += float(amount)
            
            return total
        
        except Exception as e:
            logger.error(f"Error getting total payment amount: {str(e)}")
            return 0.0
    
    @classmethod
    def get_by_user(cls, user_id):
        """
        Get payments by user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: Payment data
        """
        try:
            db = firestore.client()
            payments = []
            
            payments_ref = db.collection('payments').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            for payment_doc in payments_ref.stream():
                payment_data = payment_doc.to_dict()
                payment_data['id'] = payment_doc.id
                payments.append(payment_data)
            
            return payments
        
        except Exception as e:
            logger.error(f"Error getting payments for user {user_id}: {str(e)}")
            return []
    
    @classmethod
    def get_paginated(cls, page=1, per_page=20):
        """
        Get paginated payments
        
        Args:
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (payments, total_count)
        """
        try:
            db = firestore.client()
            
            # Get total count
            total = cls.get_count()
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get payments with pagination
            payments_ref = db.collection('payments').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(per_page).offset(offset)
            
            payments = []
            for payment_doc in payments_ref.stream():
                payment_data = payment_doc.to_dict()
                payment_data['id'] = payment_doc.id
                payments.append(payment_data)
            
            return payments, total
        
        except Exception as e:
            logger.error(f"Error getting paginated payments: {str(e)}")
            return [], 0
    
    @classmethod
    def search(cls, query, page=1, per_page=20):
        """
        Search payments
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (payments, total_count)
        """
        try:
            db = firestore.client()
            payments = []
            
            # Get all payments (Firestore doesn't support text search)
            payments_ref = db.collection('payments').stream()
            
            for payment_doc in payments_ref:
                payment_data = payment_doc.to_dict()
                payment_data['id'] = payment_doc.id
                
                # Filter payments manually
                if query.lower() in str(payment_data).lower():
                    payments.append(payment_data)
            
            # Sort by timestamp
            payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Calculate total
            total = len(payments)
            
            # Paginate results
            start = (page - 1) * per_page
            end = start + per_page
            payments = payments[start:end]
            
            return payments, total
        
        except Exception as e:
            logger.error(f"Error searching payments: {str(e)}")
            return [], 0
    
    @classmethod
    def get_stats(cls, start_date, end_date, interval='day'):
        """
        Get payment statistics
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            interval (str): Interval (hour, day, month)
            
        Returns:
            dict: Payment statistics
        """
        try:
            db = firestore.client()
            
            # Convert dates to strings
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            
            # Get payments in date range
            payments_ref = db.collection('payments').where('timestamp', '>=', start_str).where('timestamp', '<=', end_str).stream()
            
            payments = []
            for payment_doc in payments_ref:
                payment_data = payment_doc.to_dict()
                payment_data['id'] = payment_doc.id
                payments.append(payment_data)
            
            # Group by interval
            count_grouped = {}
            amount_grouped = {}
            
            for payment in payments:
                timestamp = payment.get('timestamp')
                amount = float(payment.get('amount', 0))
                
                if not timestamp:
                    continue
                
                payment_date = datetime.fromisoformat(timestamp)
                
                # Format key based on interval
                if interval == 'hour':
                    key = payment_date.strftime('%Y-%m-%d %H:00')
                elif interval == 'day':
                    key = payment_date.strftime('%Y-%m-%d')
                elif interval == 'month':
                    key = payment_date.strftime('%Y-%m')
                else:
                    key = payment_date.strftime('%Y-%m-%d')
                
                if key not in count_grouped:
                    count_grouped[key] = 0
                    amount_grouped[key] = 0.0
                
                count_grouped[key] += 1
                amount_grouped[key] += amount
            
            # Format for chart
            labels = sorted(count_grouped.keys())
            count_values = [count_grouped[key] for key in labels]
            amount_values = [amount_grouped[key] for key in labels]
            
            return {
                'labels': labels,
                'count': {
                    'values': count_values,
                    'total': sum(count_values)
                },
                'amount': {
                    'values': amount_values,
                    'total': sum(amount_values)
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            return {
                'labels': [],
                'count': {
                    'values': [],
                    'total': 0
                },
                'amount': {
                    'values': [],
                    'total': 0
                }
            }