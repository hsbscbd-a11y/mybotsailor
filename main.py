from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import os
import requests

app = FastAPI()

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

@app.get("/")
def home():
    return {"message": "Bot is Running with FastAPI!"}

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    else:
        return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text", "")
                    
                    # Auto Reply
                    reply_text = f"You said: {message_text}"
                    send_message(sender_id, reply_text)
                    
    return {"status": "ok"}

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, json=payload)
