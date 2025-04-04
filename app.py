from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import chat_collection, user_collection
from bson import ObjectId
from services.chat_agent import handle_chat_api
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from flask import abort
from services.auth import auth_bp  # Import the auth blueprint
from datetime import timedelta

# Initialize Flask app
app = Flask(__name__)

# Set the session lifetime for the app globally
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)  # Set session timeout to 15 minutes

# Set up secret key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # Secure this key in production

# Configure Flask session management and cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Enable this in production with HTTPS
app.config['SESSION_PROTECTION'] = 'strong'

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# Register the auth blueprint only once here in app.py
app.register_blueprint(auth_bp, url_prefix='/auth')


# 📄 Homepage: Chat history viewer
@app.route('/')
@login_required
def index():
    query = {}
    keyword = request.args.get('q')
    if keyword:
        query['conversation.text'] = {'$regex': keyword, '$options': 'i'}

    chats = chat_collection.find(query).sort("timestamp", -1)
    return render_template('index.html', chats=chats)

# 🔍 View single saved chat
@app.route('/chat/<chat_id>')
@login_required
def view_chat(chat_id):
    chat = chat_collection.find_one({'_id': ObjectId(chat_id)})
    return render_template('chat.html', chat=chat)

# 🧼 Optional route: manually clear chat session
@app.route('/clear-chat', methods=['POST'])
@login_required
def clear_chat():
    session.pop('conversation', None)
    session.pop('chat_mode', None)
    return redirect(url_for('chat_ui'))

# 🖥️ Web Chat UI (Temporary vs Normal mode logic)
@app.route('/chat-ui', methods=['GET', 'POST'])
@login_required
def chat_ui():
    # ✅ Clear temporary session if refreshed (clear the session if in 'temp' mode)
    if request.method == 'GET':
        if session.get('chat_mode') == 'temp' and 'conversation' in session:
            # Clear the conversation if in 'temp' mode
            session.pop('conversation', None)
            session.pop('chat_mode', None)  # Clear the chat mode as well
            return redirect(url_for('chat_ui'))  # Redirect to reload the page cleanly

    # 🛠️ Ensure conversation is initialized (only if not already present in the session)
    if 'conversation' not in session:
        session['conversation'] = []

    # ✅ Handle form submission for chat
    if request.method == 'POST':
        user_input = request.form['user_input']
        chat_mode = request.form.get('chat_mode', 'normal')  # Default to 'normal' if not provided
        save_to_db = chat_mode != 'temp'  # If in 'temp' mode, do not save to DB

        # Store the current chat mode in the session
        session['chat_mode'] = chat_mode  # Keep track of the mode

        user = current_user.username  # Use the logged-in user’s name
        response, prompt = handle_chat_api(user_input, user=user, save_to_db=save_to_db)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append the user's input and AI response to the session conversation
        session['conversation'].append({
            'sender': 'You',
            'text': user_input,
            'timestamp': timestamp
        })

        session['conversation'].append({
            'sender': 'AI',
            'text': response,
            'timestamp': timestamp
        })

        # ✅ Save full session as one MongoDB document if in normal mode
        if save_to_db:
            chat_collection.insert_one({
                "user": user,
                "chat_mode": chat_mode,
                "conversation": session['conversation'],
                "timestamp": datetime.now()
            })

        session.modified = True  # Mark the session as modified
        return redirect(url_for('chat_ui'))  # Redirect to stay on the chat page

    return render_template('chat_ui.html', conversation=session.get('conversation', []))


def role_required(role):
    """
    A decorator to require the user to have a specific role (e.g., 'admin', 'moderator').
    """
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role):
                # If the user doesn't have the required role, abort with 403 Forbidden
                abort(403)
            return func(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/admin-retrieve-data', methods=['GET', 'POST'])
@role_required('admin')  # Only admins can access this route
def admin_retrieve_data():
    # Your logic to retrieve and display data
    return render_template('admin_data_page.html')


@app.route('/moderator-actions', methods=['GET', 'POST'])
@role_required('moderator')  # Only moderators can access this route
def moderator_actions():
    # Your logic for moderator actions
    return render_template('moderator_actions_page.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')  # Assuming you have a 'dashboard.html' file in your templates


# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from services.auth import User  # Import User here to avoid circular import
    return User.get_by_id(user_id)


# 🔧 App launcher
if __name__ == '__main__':
    app.run(debug=True)
