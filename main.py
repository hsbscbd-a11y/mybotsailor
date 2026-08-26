import os
import requests
from fastapi import FastAPI, Request
import google.generativeai as genai

app = FastAPI()

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.get("/")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and challenge:
        if token != VERIFY_TOKEN:
            return {"error": "Verification token mismatch"}
        return int(challenge)
    return {"message": "Hello world - FastAPI Bot is running"}

def get_gemini_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "দুঃখিত, আমি এখন উত্তর দিতে পারছি না।"

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, json=data)
    print(r.status_code, r.text)

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    if message_text:
                        ai_reply = get_gemini_response(message_text)
                        send_message(sender_id, ai_reply)
    return {"status": "ok"}
