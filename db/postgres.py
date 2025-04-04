import psycopg2
import re
import openai
import time
import logging
from config import DB_CONFIG

# -----------------------------
# 🔧 Utility: DB connection
# -----------------------------
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# -----------------------------
# 🤖 FAQ (RAG-based) Search
# -----------------------------
def search_faq(question, top_k=1):
    """
    Performs semantic search on the RAG table using OpenAI embeddings.
    Returns top-k most similar FAQs.
    """
    start = time.time()
    try:
        embedding = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=question
        )['data'][0]['embedding']
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return []

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT question, answer
                    FROM rag
                    ORDER BY embedding <-> %s::vector
                    LIMIT %s;
                """, (embedding, top_k))
                results = cur.fetchall()
    except Exception as e:
        logging.error(f"FAQ search failed: {e}")
        results = []

    if results:
        logging.info(f"✅ Found {len(results)} FAQ match(es).")
    else:
        logging.warning("❌ No FAQ matches found.")

    return results

# -----------------------------
# 📦 Order Search by Order #
# -----------------------------
def search_orders(question):
    """
    Extracts order number from question and returns order details if found.
    """
    match = re.search(r"order\s*(\d+)", question, re.IGNORECASE)
    if not match:
        logging.info("No order ID found in question.")
        return None

    order_id = int(match.group(1))
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM orders WHERE ordernumber = %s;", (order_id,))
                order = cur.fetchone()
    except Exception as e:
        logging.error(f"Order query failed: {e}")
        order = None

    if order:
        logging.info(f"✅ Order found: #{order_id}")
    else:
        logging.warning(f"❌ No order found for ID: {order_id}")

    return order

# -----------------------------
# 🔍 Product Search (by ID or name)
# -----------------------------
def search_products(question):
    """
    Tries to find a product either by ID in the question or fuzzy name matching.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                match = re.search(r"product\s*(\d+)", question, re.IGNORECASE)
                if match:
                    product_id = int(match.group(1))
                    cur.execute("SELECT productid, name, description FROM products WHERE productid = %s;", (product_id,))
                    product = cur.fetchone()
                    log_msg = f"Product found by ID: {product_id}" if product else f"No product found by ID: {product_id}"
                else:
                    cur.execute("""
                        SELECT productid, name, description
                        FROM products
                        ORDER BY similarity(name, %s) DESC
                        LIMIT 1;
                    """, (question,))
                    product = cur.fetchone()
                    log_msg = f"Product found by name match." if product else "No product found by name."
    except Exception as e:
        logging.error(f"Product search failed: {e}")
        product = None
        log_msg = "Product search error."

    logging.info(log_msg) if product else logging.warning(log_msg)
    return product

# -----------------------------
# 📋 Get All Products (In Stock)
# -----------------------------
def get_all_products():
    """
    Returns all products currently stored in the database.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT productid, name, description FROM products;")
                products = cur.fetchall()
    except Exception as e:
        logging.error(f"Failed to retrieve all products: {e}")
        products = []

    return products
