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
    if request.query_params.get("hub.mode") == "subscribe":
        if request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
            return PlainTextResponse(content=request.query_params.get("hub.challenge"))
    return PlainTextResponse("Bot running")

@app.get("/")
async def root():
    return {"status": "ok"}

def get_gemini_response(user_message):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_message
        )
        return response.text[:1900]
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return f"AI Error: {e}"

def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    r = requests.post(url, params=params, json=payload)
    print(f"FB Send: {r.status_code} {r.text}")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for ev in entry.get("messaging", []):
                if "message" in ev and ev["message"].get("text"):
                    get_gemini_response(ev["message"]["text"])
                    send_message(ev["sender"]["id"], get_gemini_response(ev["message"]["text"]))
    return {"status": "ok"}
