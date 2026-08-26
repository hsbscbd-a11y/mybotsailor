import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

def get_gemini_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return "দুঃখিত, আমি এখন উত্তর দিতে পারছি না।"

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    print(r.status_code, r.text)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    if message_text:
                        ai_reply = get_gemini_response(message_text)
                        send_message(sender_id, ai_reply)
    return "ok", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
