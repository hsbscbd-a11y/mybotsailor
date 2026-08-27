import os, requests, asyncio
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
    return PlainTextResponse("ok", status_code=403)

@app.get("/")
async def root(): 
    return {"status": "BRIS is running"}

def get_ai_sync(user_text: str):
    page_info = """
    তুমি BRIS (Business Research & Intelligent System) এর AI। NexMind AI Labs এর প্রোডাক্ট।
    কাজ: Business Lead খোঁজা, SMS, Bot।
    সবসময় বাংলায় ছোট উত্তর দিবে।
    """
    prompt = f"{page_info}\nUser: {user_text}"

    # BRIS Auto-Model Selector - একটা Fail করলে আরেকটা চলবে
    # BRIS Auto-Model Selector - Google এর নতুন মডেল অনুযায়ী
    MODELS_TO_TRY = [
        "gemini-3.6-flash",          # Google এখন এটাই ব্যবহার করতে বলছে
        "gemini-3.5-flash-lite",     # Lite ভার্সন
        "gemini-2.5-flash",          # Backup
    ]

    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            print(f"Trying model: {model_name}")
            r = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            print(f"SUCCESS with {model_name}")
            return r.text
        except Exception as e:
            print(f"FAILED {model_name}: {e}")
            last_error = e
            continue
    
    raise last_error

async def get_ai(text):
    return await asyncio.to_thread(get_ai_sync, text)

def send_msg(uid, txt):
    requests.post("https://graph.facebook.com/v20.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={"recipient": {"id": uid}, "message": {"text": txt[:1900]}},
        timeout=10
    )

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for ev in entry.get("messaging", []):
                if "message" in ev and ev["message"].get("text"):
                    try:
                        reply = await get_ai(ev["message"]["text"])
                    except Exception as e:
                        print(f"ALL MODELS FAILED: {e}")
                        reply = "আমি একটু টেকনিক্যাল সমস্যায় আছি, ১ মিনিট পর আবার বলুন, আমি আছি! 🙏"
                    send_msg(ev["sender"]["id"], reply)
    return {"status": "ok"}
