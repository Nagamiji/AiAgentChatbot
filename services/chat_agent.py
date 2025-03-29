from db.postgres import (
    search_faq,
    search_orders,
    search_products,
    get_all_products
)
from llm.prompt_builder import build_prompt
from llm.ollama_client import ask_ollama as call_llm
from db.mongo_logger import save_conversation
from tabulate import tabulate
import logging

# -----------------------------
# 📊 Format Data as Text Table
# -----------------------------
def format_as_table(data, headers=("ID", "Name", "Description")):
    """
    Formats a list of tuples (like products) as a clean table string for CLI.
    """
    return tabulate(data, headers=headers, tablefmt="pretty")

# -----------------------------
# 🌐 Format Data as HTML Table
# -----------------------------
def format_as_html_table(data, headers=("ID", "Name", "Description")):
    html = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
    html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    for row in data:
        html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    html += "</table>"
    return html

# -----------------------------
# 🧠 Core Logic (shared)
# -----------------------------
def process_question(user_question, is_web=False):
    """
    Main logic flow: detects if the question needs special DB logic,
    otherwise goes through RAG + product/order search + LLM.
    `is_web=True` returns an HTML table when appropriate.
    """

    # 🛒 Special case: List products in stock
    if "products in stock" in user_question.lower() or "available products" in user_question.lower():
        logging.info("🔍 Detected product stock inquiry. Fetching product list...")
        products = get_all_products()

        if not products:
            return "Sorry, there are no products in stock right now.", "get_all_products()"

        if is_web:
            table = format_as_html_table(products, headers=["Product ID", "Name", "Description"])
            response = f"🛒 <b>Here are the products currently in stock:</b><br><br>{table}"
        else:
            table = format_as_table(products, headers=["Product ID", "Name", "Description"])
            response = f"🛒 Here are the products currently in stock:\n\n{table}"

        return response, "get_all_products()"

    # 🧠 Default: Search RAG + Orders + Products → LLM
    faq = search_faq(user_question)
    order = search_orders(user_question)
    product = search_products(user_question)

    prompt = build_prompt(user_question, faq, order, product)
    response = call_llm(prompt)

    return response, prompt

# -----------------------------
# 💬 CLI Chat Handler
# -----------------------------
def handle_chat(user_question, user="anonymous", save_to_db=True):
    """
    Processes user question from CLI/terminal.
    """
    response, prompt = process_question(user_question, is_web=False)

    if save_to_db:
        save_conversation(user, user_question, prompt, response)
        logging.info("📝 Conversation saved to MongoDB.")
    else:
        logging.info("🛑 MongoDB save skipped.")

    print("🤖 LLM Response:\n")
    print(response)

# -----------------------------
# 🌐 API Chat Handler
# -----------------------------
def handle_chat_api(user_question, user="anonymous", save_to_db=True):
    """
    Processes user question via API (e.g. from web frontend).
    Returns a web-friendly HTML response and raw prompt.
    """
    response, prompt = process_question(user_question, is_web=True)

    if save_to_db:
        save_conversation(user, user_question, prompt, response)
        logging.info(f"📩 Saved conversation for API user '{user}'.")
    else:
        logging.info(f"API call with no Mongo save for user '{user}'.")

    return response, prompt
