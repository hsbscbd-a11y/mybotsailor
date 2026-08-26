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

import time
from google.genai import errors

def get_ai(text):
    page_info = """
    তুমি NexMind AI Labs এর অফিসিয়াল AI অ্যাসিস্ট্যান্ট।
    NexMind AI Labs এর মালিক হচ্ছেন হাসান মাহমুদ।
    তার স্ত্রী হচ্ছেন রুমি হাসান। তিনি গার্মেন্টসে জব করে তার স্বামীকে অনেক হেল্প করেছেন।
    তার স্বামী তার স্ত্রীর এই ত্যাগ ও সম্মান রাখতে একদিন এই AI দিয়ে বড় কিছু করে দেখাবে, ইনশাআল্লাহ।
    তুমি সবসময় বাংলায় ভদ্রভাবে উত্তর দেবে।
    """
    full_prompt = f"{page_info}\n\nপ্রশ্ন: {text}"

    try:
        r = client.models.generate_content(model="gemini-3.6-flash", contents=full_prompt)
        return r.text
    except Exception as e:
        # যদি কোটা শেষ হয়
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("Quota sesh, 1 min wait")
            return "আমাদের AI এখন একটু ব্যস্ত আছে, দয়া করে ১ মিনিট পর আবার মেসেজ করুন। 🙏"
        else:
            print(f"Error: {e}")
            return "দুঃখিত, একটু সমস্যা হচ্ছে, একটু পর আবার চেষ্টা করুন।"

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
