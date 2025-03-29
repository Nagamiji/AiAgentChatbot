import logging
from config import chat_collection
from datetime import datetime, timezone

def save_conversation(user, question, prompt, response):
    chat_collection.insert_one({
        "timestamp": datetime.now(timezone.utc),
        "user": user,
        "user_question": question,
        "full_prompt": prompt,
        "response": response
    })
    logging.info(f"Saved conversation for user '{user}' to MongoDB.")
