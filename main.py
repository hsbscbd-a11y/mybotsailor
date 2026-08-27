import os
import requests
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google import genai

app = FastAPI()

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    return PlainTextResponse("Verification failed", status_code=403)

@app.get("/")
async def root():
    return {"status": "BRIS is Live - Gemini 3.6 Flash"}

# --- BRIS AI ---
def get_ai_sync(user_text: str):
    prompt = f"""
    তুমি BRIS (Business Research & Intelligent System) এর অফিসিয়াল AI Assistant।
    BRIS হলো NexMind AI Labs এর একটি প্রোডাক্ট যা Business এর জন্য Lead খুঁজে, SMS পাঠায়, অটো রিপ্লাই দেয়।
    NexMind AI Labs বাংলাদেশি AI স্টার্টআপ, Facebook Bot, Automation নিয়ে কাজ করে।
    সবসময় বাংলায়, বন্ধুত্বপূর্ণ ও ছোট উত্তর দিবে।

    User Question: {user_text}
    """

    # Google এখন শুধু এই ২টা মডেল Allow করছে (তোমার Logs অনুযায়ী)
    MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]

    last_error = None
    for model_name in MODELS:
        try:
            print(f"Trying model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            print(f"SUCCESS with {model_name}")
            return response.text
        except Exception as e:
            print(f"FAILED {model_name}: {e}")
            last_error = e
            continue
    
    # সব মডেল Fail করলে Error Raise করবে
    raise last_error

async def get_ai(text: str):
    return await asyncio.to_thread(get_ai_sync, text)

def send_msg(recipient_id: str, text: str):
    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text[:1900]}
    }
    try:
        requests.post(url, params=params, json=data, timeout=15)
    except Exception as e:
        print(f"FB Send Error: {e}")

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print(f"Incoming: {body}")

    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and event["message"].get("text"):
                    user_msg = event["message"]["text"]
                    sender_id = event["sender"]["id"]
                    print(f"User {sender_id}: {user_msg}")

                    try:
                        ai_reply = await get_ai(user_msg)
                    except Exception as e:
                        print(f"FINAL ERROR: {e}")
                        ai_reply = "আমি একটু টেকনিক্যাল আপডেটে আছি, ১ মিনিট পর আবার বলুন প্লিজ! 🙏"

                    send_msg(sender_id, ai_reply)

    return {"status": "ok"}
