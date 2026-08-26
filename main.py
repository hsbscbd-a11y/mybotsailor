import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import google.generativeai as genai

app = FastAPI()

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Facebook Verify এর জন্য
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and challenge:
        if token != VERIFY_TOKEN:
            return PlainTextResponse("Verification token mismatch", status_code=403)
        return PlainTextResponse(content=challenge)
    return PlainTextResponse("Bot is running")

# Check করার জন্য root
@app.get("/")
async def root():
    return {"status": "Bot is running - FastAPI"}

def get_gemini_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text[:1900]
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "দুঃখিত, এখন উত্তর দিতে পারছি না।"

def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    r = requests.post(url, params=params, json=payload)
    print(f"Send status: {r.status_code}")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for msg in entry.get("messaging", []):
                if "message" in msg and msg["message"].get("text"):
                    sender = msg["sender"]["id"]
                    text = msg["message"]["text"]
                    ai_reply = get_gemini_response(text)
                    send_message(sender, ai_reply)
    return {"status": "ok"}
