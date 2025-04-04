import os
from dotenv import load_dotenv
from pymongo import MongoClient
import openai
import logging

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler()
    ]
)

# ✅ Load .env
load_dotenv()

# ✅ OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ PostgreSQL config
DB_CONFIG = {
    "host": "localhost",
    "port": 5444,
    "database": "postgres",
    "user": "postgres",
    "password": "Tt501007"
}

# ✅ MongoDB config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["chatBotConversation"]

# Define collections for both chats and users
chat_collection = mongo_db["chat"]
user_collection = mongo_db["users"]  # Add this line to define user_collection

