import sys
import os

# Add project root to sys.path so we can import config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import openai
import logging
from dotenv import load_dotenv
from config import DB_CONFIG

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- 🛒 PRODUCTS ---
products = [
    (1001, 'Wireless Mouse', 'High precision wireless mouse with ergonomic design.'),
    (1002, 'Mechanical Keyboard', 'RGB backlit mechanical keyboard with blue switches.'),
    (1003, 'Laptop Stand', 'Adjustable aluminum laptop stand for better airflow.'),
    (1004, 'USB-C Charger', '65W USB-C fast charger for laptops and phones.'),
    (1005, 'Monitor Arm', 'Dual monitor adjustable arm for ergonomic setups.'),
    (1006, 'Webcam', '1080p HD webcam with noise-canceling microphone.'),
    (1007, 'Noise-Canceling Headphones', 'Over-ear headphones with active noise cancellation.'),
    (1008, 'Smart Desk Lamp', 'LED lamp with touch control and USB charging port.'),
    (1009, 'Ergonomic Chair', 'Adjustable office chair with lumbar support.'),
    (1010, 'Wireless Presenter', 'Presentation clicker with laser pointer.')
]

# --- 📦 ORDERS ---
orders = [
    (1010, 'Sophia', 'Johnson', '2024-11-12', 159.99, 'Delivered', [1001, 1002]),
    (1011, 'Jackson', 'Lee', '2024-11-13', 89.50, 'Pending', [1003]),
    (1012, 'Olivia', 'Martinez', '2024-11-14', 299.00, 'Shipped', [1005, 1006]),
    (1013, 'Ethan', 'Wong', '2024-11-15', 134.25, 'Processing', [1007]),
    (1014, 'Isabella', 'Patel', '2024-11-16', 189.99, 'Delivered', [1008, 1010]),
    (1015, 'Lucas', 'Nguyen', '2024-11-17', 499.00, 'Pending', [1009]),
    (1016, 'Mia', 'Kim', '2024-11-18', 210.00, 'Shipped', [1004, 1002, 1006]),
    (1017, 'Aiden', 'Garcia', '2024-11-19', 275.75, 'Delivered', [1001, 1007]),
    (1018, 'Ella', 'Rodriguez', '2024-11-20', 120.50, 'Pending', [1003, 1008]),
    (1019, 'Liam', 'Hernandez', '2024-11-21', 139.99, 'Processing', [1005, 1010])
]

# --- 🤖 RAG FAQS ---
rag_data = [
    "How do I apply a discount code?",
    "Is in-store pickup available?",
    "How long does shipping take?",
    "What are the current products in stock?",
    "How can I track my order?",
    "Can I return a product if I don’t like it?",
    "Do you offer free shipping?",
    "Where can I find my invoice?",
    "Can I change my delivery address after ordering?",
    "Are your products under warranty?",
    "How do I contact customer support?",
    "Do you ship internationally?",
    "How to cancel an order before it ships?",
    "Can I get notified when an item is back in stock?"
]

# --- Insert Logic ---

def insert_products(cur):
    cur.executemany(
        "INSERT INTO products (productid, name, description) VALUES (%s, %s, %s) ON CONFLICT (productid) DO NOTHING;",
        products
    )

def insert_orders(cur):
    for order in orders:
        try:
            cur.execute(
                "INSERT INTO orders (ordernumber, customerfirstname, customerlastname, date, price, status, productidsordered) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (ordernumber) DO NOTHING;",
                (order[0], order[1], order[2], order[3], order[4], order[5], order[6])
            )
        except Exception as e:
            logging.warning(f"Order insert failed: {e}")

def insert_rag(cur):
    for question in rag_data:
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=question
            )
            embedding = response['data'][0]['embedding']
            answer = f"This is the answer to: {question}"
            cur.execute(
                "INSERT INTO rag (question, answer, embedding) VALUES (%s, %s, %s);",
                (question, answer, embedding)
            )
        except Exception as e:
            logging.error(f"Failed to insert RAG for '{question}': {e}")

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_products(cur)
    insert_orders(cur)
    insert_rag(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Data inserted successfully.")

if __name__ == "__main__":
    main()
