# routes/admin_routes.py - Admin dashboard routes
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime, timedelta
from models.user import User
from models.review import Review
from models.payment import Payment
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

# Create blueprint
admin_bp = Blueprint('admin', __name__)

def login_required(f):
    """
    Login required decorator
    
    Args:
        f: Function to decorate
        
    Returns:
        Function: Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def index():
    """
    Admin index/redirect to dashboard
    
    Returns:
        Redirect: To dashboard or login
    """
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login
    
    Returns:
        Template: Login page or redirect to dashboard
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_login_time'] = datetime.now().isoformat()
            
            next_page = request.args.get('next', url_for('admin.dashboard'))
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """
    Admin logout
    
    Returns:
        Redirect: To login page
    """
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_login_time', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Admin dashboard
    
    Returns:
        Template: Dashboard page
    """
    # Get stats
    user_count = User.get_count()
    review_count = Review.get_count()
    basic_review_count = Review.get_count_by_type('basic')
    advanced_review_count = Review.get_count_by_type('advanced')
    payment_count = Payment.get_count()
    payment_total = Payment.get_total_amount()
    
    # Get recent reviews
    recent_reviews = Review.get_recent(5)
    
    # Get recent users
    recent_users = User.get_recent(5)
    
    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        review_count=review_count,
        basic_review_count=basic_review_count,
        advanced_review_count=advanced_review_count,
        payment_count=payment_count,
        payment_total=payment_total,
        recent_reviews=recent_reviews,
        recent_users=recent_users
    )

@admin_bp.route('/users')
@login_required
def users():
    """
    Admin users list
    
    Returns:
        Template: Users page
    """
    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '')
    
    # Get users
    if search:
        users, total = User.search(search, page, per_page)
    else:
        users, total = User.get_paginated(page, per_page)
    
    return render_template(
        'admin/users.html',
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        total_pages=(total + per_page - 1) // per_page
    )

@admin_bp.route('/reviews')
@login_required
def reviews():
    """
    Admin reviews list
    
    Returns:
        Template: Reviews page
    """
    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    review_type = request.args.get('type', '')
    search = request.args.get('search', '')
    
    # Get reviews
    if search:
        reviews, total = Review.search(search, page, per_page)
    elif review_type:
        reviews, total = Review.get_by_type(review_type, page, per_page)
    else:
        reviews, total = Review.get_paginated(page, per_page)
    
    return render_template(
        'admin/reviews.html',
        reviews=reviews,
        total=total,
        page=page,
        per_page=per_page,
        review_type=review_type,
        search=search,
        total_pages=(total + per_page - 1) // per_page
    )

@admin_bp.route('/payments')
@login_required
def payments():
    """
    Admin payments list
    
    Returns:
        Template: Payments page
    """
    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '')
    
    # Get payments
    if search:
        payments, total = Payment.search(search, page, per_page)
    else:
        payments, total = Payment.get_paginated(page, per_page)
    
    return render_template(
        'admin/payments.html',
        payments=payments,
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        total_pages=(total + per_page - 1) // per_page
    )

@admin_bp.route('/user/<user_id>')
@login_required
def user_detail(user_id):
    """
    Admin user detail
    
    Args:
        user_id (str): User ID
    
    Returns:
        Template: User detail page
    """
    # Get user
    user = User.get_by_id(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))
    
    # Get user reviews
    reviews = Review.get_by_user(user_id)
    
    # Get user payments
    payments = Payment.get_by_user(user_id)
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        reviews=reviews,
        payments=payments
    )

@admin_bp.route('/review/<review_id>')
@login_required
def review_detail(review_id):
    """
    Admin review detail
    
    Args:
        review_id (str): Review ID
    
    Returns:
        Template: Review detail page
    """
    # Get review
    review = Review.get_by_id(review_id)
    
    if not review:
        flash('Review not found', 'error')
        return redirect(url_for('admin.reviews'))
    
    # Get user
    user = User.get_by_id(review.get('user_id'))
    
    return render_template(
        'admin/review_detail.html',
        review=review,
        user=user
    )

@admin_bp.route('/stats')
@login_required
def stats():
    """
    Admin statistics
    
    Returns:
        Template: Stats page
    """
    # Get date range
    date_range = request.args.get('range', 'week')
    
    # Set date range
    end_date = datetime.now()
    
    if date_range == 'day':
        start_date = end_date - timedelta(days=1)
        interval = 'hour'
    elif date_range == 'week':
        start_date = end_date - timedelta(days=7)
        interval = 'day'
    elif date_range == 'month':
        start_date = end_date - timedelta(days=30)
        interval = 'day'
    elif date_range == 'year':
        start_date = end_date - timedelta(days=365)
        interval = 'month'
    else:
        start_date = end_date - timedelta(days=7)
        interval = 'day'
    
    # Get stats
    review_stats = Review.get_stats(start_date, end_date, interval)
    payment_stats = Payment.get_stats(start_date, end_date, interval)
    user_stats = User.get_stats(start_date, end_date, interval)
    
    return render_template(
        'admin/stats.html',
        date_range=date_range,
        review_stats=review_stats,
        payment_stats=payment_stats,
        user_stats=user_stats
    )