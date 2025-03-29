from services.chat_agent import handle_chat

if __name__ == "__main__":
    username = input("👤 Enter your name: ")

    while True:
        question = input("\n🧠 Ask your AI Agent (type 'exit' to quit):\n> ")
        if question.lower() in ['exit', 'quit']:
            break

        save = input("💾 Save to MongoDB? (y/n): ").strip().lower() == 'y'
        handle_chat(question, user=username, save_to_db=save)
