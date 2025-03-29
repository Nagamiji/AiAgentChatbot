import requests
import json
import logging

def ask_ollama(prompt):
    response_text = ""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": [{"role": "user", "content": prompt}]
            },
            stream=True
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"LLM server connection failed: {e}")
        return f"Error connecting to LLM server: {e}"

    if response.status_code == 200:
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        response_text += data["message"]["content"]
                except json.JSONDecodeError:
                    continue
        logging.info("LLM response successfully received.")
    else:
        err_msg = f"LLM request failed: {response.status_code} - {response.text}"
        logging.error(err_msg)
        response_text = f"Error: {response.status_code} - {response.text}"

    return response_text
