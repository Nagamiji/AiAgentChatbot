def build_prompt(question, faq=None, order=None, product=None):
    """
    Builds a prompt dynamically based on available context.
    Returns a string for the language model.
    """
    question_lower = question.lower().strip()
    context_parts = []

    # ✅ Handle greetings separately
    greetings = ["hi", "hello", "hey", "who are you", "what are you"]
    if any(greet in question_lower for greet in greetings):
        return (
            "You are a friendly and conversational AI assistant. "
            "The user just greeted you, so respond warmly and naturally."
        )

    # ✅ Build context from data sources
    if faq:
        faq_q, faq_a = faq[0]
        context_parts.append(f"📚 FAQ Match:\nQ: {faq_q}\nA: {faq_a}")

    if order:
        context_parts.append(
            f"📦 Order Info:\n"
            f"Order ID: {order[0]}\n"
            f"Customer: {order[1]} {order[2]}\n"
            f"Date: {order[3]}\n"
            f"Price: ${order[4]}\n"
            f"Status: {order[5]}\n"
            f"Products: {order[6]}"
        )

    if product and len(product) >= 3:
        context_parts.append(
            f"🛒 Product Info:\n"
            f"Product ID: {product[0]}\n"
            f"Name: {product[1]}\n"
            f"Description: {product[2]}"
        )

    # ✅ Fall back message if no context
    if not context_parts:
        context_parts.append("No relevant FAQ, order, or product data found.")

    # ✅ Final prompt assembly
    return (
        "You are a helpful and knowledgeable AI assistant. "
        "Use the following context to answer the user's question:\n\n"
        f"{'\n\n'.join(context_parts)}\n\n"
        f"User question: {question}\n\n"
        "Respond in a clear and concise way."
    )
