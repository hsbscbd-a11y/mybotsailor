import os, requests, asyncio
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google import genai

app = FastAPI()

PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Client একবারই বানাও
client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/webhook")
async def verify(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=request.query_params.get("hub.challenge"))
    return PlainTextResponse("ok", status_code=403)

@app.get("/")
async def root(): 
    return {"status": "BRIS is running", "ok": True}

# --- BRIS AI CORE ---
def get_ai_sync(user_text: str):
    page_info = """
    তুমি BRIS (Business Research & Intelligent System) এর অফিসিয়াল AI।
    BRIS হলো NexMind AI Labs এর একটি প্রোডাক্ট।
    - BRIS কি করে? Business এর জন্য Lead খুঁজে আনে, SMS পাঠায়, অটো রিপ্লাই দেয়, অর্ডার নেয়।
    - NexMind AI Labs কি? বাংলাদেশি AI স্টার্টআপ, আমরা Facebook Bot, Automation, BRIS নিয়ে কাজ করি।
    - সবসময় বাংলায়, বন্ধুত্বপূর্ণ ভাবে কথা বলবে।
    - উত্তর ছোট ও স্মার্ট রাখবে।
    """

    full_prompt = f"{page_info}\n\nইউজারের প্রশ্ন: {user_text}\n\nউত্তর দাও:"

    # সঠিক মডেল নাম ব্যবহার করো
    r = client.models.generate_content(
        model="gemini-2.0-flash",  # FIXED: 3.6-flash বলে কিছু নেই
        contents=full_prompt
    )
    return r.text

async def get_ai(text):
    # Async server যাতে Block না হয়, তাই thread এ চালাও
    return await asyncio.to_thread(get_ai_sync, text)

def send_msg(uid, txt):
    if not PAGE_ACCESS_TOKEN:
        print("ERROR: PAGE_ACCESS_TOKEN missing")
        return
    try:
        requests.post("https://graph.facebook.com/v20.0/me/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={"recipient": {"id": uid}, "message": {"text": txt[:1900]}},
            timeout=10
        )
    except Exception as e:
        print(f"FB Send Error: {e}")

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("Incoming:", body)

    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for ev in entry.get("messaging", []):
                if "message" in ev and ev["message"].get("text"):
                    user_text = ev["message"]["text"]
                    sender_id = ev["sender"]["id"]
                    
                    try:
                        print(f"User {sender_id}: {user_text}")
                        reply = await get_ai(user_text)
                        print(f"AI Reply: {reply}")
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                        # ইউজারকে কখনো Error দেখাবে না, সুন্দর রিপ্লাই দিবে
                        reply = "আমি একটু ব্যস্ত ছিলাম, এখন ফ্রি আছি। আবার বলুন প্লিজ! 🙏"
                    
                    send_msg(sender_id, reply)
    return {"status": "ok"}
