import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google import genai

app = FastAPI()

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    return PlainTextResponse("Bot running")

@app.get("/")
async def root():
    return {"ok": True}

def get_ai(text):
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=text
    )
    return resp.text

def send_msg(user_id, text):
    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {"recipient": {"id": user_id}, "message": {"text": text[:1900]}}
    requests.post(url, params=params, json=data)

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and event["message"].get("text"):
                    user_text = event["message"]["text"]
                    sender = event["sender"]["id"]
                    try:
                        ai_text = get_ai(user_text)
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                        ai_text = "AI একটু ব্যস্ত, ১ মিনিট পর আবার বলুন।"
                    send_msg(sender, ai_text)
    return {"status": "ok"}
