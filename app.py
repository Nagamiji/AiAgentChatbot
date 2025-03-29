from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import chat_collection
from bson import ObjectId
from services.chat_agent import handle_chat_api
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# 🔁 API endpoint for external use (e.g. Postman)
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    user = data.get('user', 'anonymous')
    question = data.get('question', '')
    save = data.get('save_to_db', True)

    if not question:
        return jsonify({"error": "Question is required"}), 400

    response, prompt = handle_chat_api(question, user=user, save_to_db=save)

    return jsonify({
        "response": response,
        "prompt": prompt,
        "status": "ok"
    })


# 📄 Homepage: Chat history viewer
@app.route('/')
def index():
    query = {}
    keyword = request.args.get('q')
    if keyword:
        query['conversation.text'] = {'$regex': keyword, '$options': 'i'}

    chats = chat_collection.find(query).sort("timestamp", -1)
    return render_template('index.html', chats=chats)


# 🔍 View single saved chat
@app.route('/chat/<chat_id>')
def view_chat(chat_id):
    chat = chat_collection.find_one({'_id': ObjectId(chat_id)})
    return render_template('chat.html', chat=chat)


# 🧼 Optional route: manually clear chat session
@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    session.pop('conversation', None)
    session.pop('chat_mode', None)
    return redirect(url_for('chat_ui'))


# 🖥️ Web Chat UI (Temporary vs Normal mode logic)
@app.route('/chat-ui', methods=['GET', 'POST'])
def chat_ui():
    # ✅ Clear temporary session if refreshed
    if request.method == 'GET':
        if session.get('chat_mode') == 'temp' and 'conversation' in session:
            session.pop('conversation', None)
            session.pop('chat_mode', None)
            return redirect(url_for('chat_ui'))  # Clean reload

    # 🛠️ Ensure conversation is initialized
    if 'conversation' not in session:
        session['conversation'] = []

    if request.method == 'POST':
        user_input = request.form['user_input']
        chat_mode = request.form.get('chat_mode', 'normal')  # fallback default
        save_to_db = chat_mode != 'temp'

        session['chat_mode'] = chat_mode
        user = "web-user"
        response, prompt = handle_chat_api(user_input, user=user, save_to_db=save_to_db)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

        session.modified = True
        return redirect(url_for('chat_ui'))

    return render_template('chat_ui.html', conversation=session.get('conversation', []))


# 🔧 App launcher
if __name__ == '__main__':
    app.run(debug=True)
