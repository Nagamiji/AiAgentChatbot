from flask import Blueprint, request, render_template, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager, UserMixin
from config import user_collection  # Your MongoDB collection
from bson import ObjectId
from itsdangerous import URLSafeTimedSerializer as Serializer
import secrets
from datetime import timedelta

# Create the login manager instance
login_manager = LoginManager()

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Secret key for CSRF protection and token generation
SECRET_KEY = 'your-secret-key'  # Ensure to change this to a more secure key and store in env var

# User class with methods for login
class User(UserMixin):  # Inherit from UserMixin
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])  # MongoDB's _id field is typically an ObjectId
        self.username = user_doc['username']
        self.password = user_doc['password']
        self.role = user_doc.get('role', 'user')  # Default role is 'user'
        self._is_active = user_doc.get('is_active', True)  # Set directly as an attribute, no setter

    @property
    def is_active(self):
        """Override the default is_active property in Flask-Login."""
        return self._is_active

    @staticmethod
    def get_by_username(username):
        user_doc = user_collection.find_one({'username': username})
        return User(user_doc) if user_doc else None

    @staticmethod
    def get_by_id(user_id):
        user_doc = user_collection.find_one({'_id': ObjectId(user_id)})
        return User(user_doc) if user_doc else None

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return self.id

    def has_role(self, role):
        return self.role == role

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Register Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Default role is 'user'
        
        # Simple password strength validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long", "error")
            return redirect(url_for('auth.register'))
        
        # Hash the password using werkzeug's built-in function
        hashed_password = generate_password_hash(password)  # Use werkzeug's hashing function here

        # Check if username already exists
        if user_collection.find_one({'username': username}):
            flash("Username already exists. Please choose a different one.", "error")
            return redirect(url_for('auth.register'))

        # Insert new user into MongoDB with hashed password and role
        user_collection.insert_one({
            'username': username,
            'password': hashed_password,  # Store hashed password
            'role': role,  # Store the user role
            'is_active': True  # Default is_active value
        })
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('auth.login'))
    return render_template('register.html')

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)

        if user and user.check_password(password):
            login_user(user)
            
            # Set the session cookie securely
            session.permanent = True  # The session will expire based on the PERMANENT_SESSION_LIFETIME setting
            session['csrf_token'] = secrets.token_hex(16)  # CSRF Token generation

            # Redirect to the chat UI page after successful login
            return redirect(url_for('chat_ui'))  # Redirect to chat UI instead of dashboard

        flash("Invalid username or password", "error")  # Flash error message
    return render_template('login.html')


# Logout Route
@auth_bp.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

# Protecting routes with login_required
@auth_bp.route('/protected')
@login_required
def protected():
    return render_template('protected_page.html')  # Example of a protected page
