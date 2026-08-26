import os, requests
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
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=request.query_params.get("hub.challenge"))
    return PlainTextResponse("ok")

@app.get("/")
async def root(): return {"ok": True}

def get_ai(text):
    # একটার পর একটা ট্রাই করবে, যেটা কাজ করে সেটা নেবে
    for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]:
        try:
            resp = client.models.generate_content(model=model_name, contents=text)
            print(f"SUCCESS with {model_name}")
            return resp.text
        except Exception as e:
            print(f"FAILED {model_name}: {e}")
            continue
    return "AI Key বা Model এ সমস্যা হচ্ছে, Log দেখুন।"

def send_msg(uid, txt):
    requests.post("https://graph.facebook.com/v20.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={"recipient": {"id": uid}, "message": {"text": txt[:1900]}})

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for ev in entry.get("messaging", []):
                if "message" in ev and ev["message"].get("text"):
                    reply = get_ai(ev["message"]["text"])
                    send_msg(ev["sender"]["id"], reply)
    return {"status": "ok"}
