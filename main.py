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
    page_info = """
    তুমি NexMind AI Labs এর অফিসিয়াল AI অ্যাসিস্ট্যান্ট।
    NexMind AI Labs কি?
    - এটি একটি বাংলাদেশি AI স্টার্টআপ
    - আমরা AI টুলস, Facebook Bot, Automation নিয়ে কাজ করি
    - আমাদের সার্ভিস: AI Chatbot বানানো, পেজ অটোমেশন, AI ভিডিও
    - যোগাযোগ: Facebook পেজে মেসেজ করুন
    - ব্যবহারকারীর সাথে সবসময় বাংলায় সুন্দরভাবে কথা বলবে
    """

    full_prompt = f"{page_info}\n\nইউজারের প্রশ্ন: {text}\n\nউত্তর বাংলায় দাও:"

    r = client.models.generate_content(model="gemini-3.6-flash", contents=full_prompt)
    print("SUCCESS with gemini-3.6-flash")
    return r.text

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
                    try:
                        reply = get_ai(ev["message"]["text"])
                    except Exception as e:
                        reply = f"Error: {e} - Render Logs দেখুন"
                        print(reply)
                    send_msg(ev["sender"]["id"], reply)
    return {"status": "ok"}
