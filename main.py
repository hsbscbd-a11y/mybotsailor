from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import PageToken

# খাতা বানানো নিশ্চিত করা
Base.metadata.create_all(bind=engine)

app = FastAPI()

# #TODO: এখানে তোমার Facebook App এর ID আর Secret বসাবে
APP_ID = "1386633599573638"
APP_SECRET = "58ce66dbaf1b03c83488f92be8f66afb"
# তোমার Ngrok URL টা এখানে বসাবে, যেমন https://xxxx.ngrok-free.app
REDIRECT_URI = "https://YOUR_NGROK_URL/auth/callback"

VERIFY_TOKEN = "mybotsailor_verify_123"

# 1. হোম পেজ - এখানে Connect Button থাকবে
@app.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <html>
        <body style="text-align:center; margin-top:100px; font-family: sans-serif;">
            <h1>MyBotSailor - SaaS</h1>
            <h3>Phase 2 Running...</h3>
            <a href="/auth/facebook" style="background-color:#1877F2; color:white; padding:15px 25px; text-decoration:none; border-radius:5px; font-weight:bold;">
                Connect with Facebook
            </a>
        </body>
    </html>
    """

# 2. Facebook Login এ পাঠানো
@app.get("/auth/facebook")
def auth_facebook():
    fb_auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=pages_show_list,pages_messaging,pages_manage_metadata&response_type=code"
    return RedirectResponse(fb_auth_url)

# 3. Facebook থেকে ফিরে আসার পর
@app.get("/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    # Code দিয়ে Access Token নেওয়া
    token_url = f"https://graph.facebook.com/v19.0/oauth/access_token?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&client_secret={APP_SECRET}&code={code}"
    token_res = requests.get(token_url).json()
    user_token = token_res.get("access_token")

    if not user_token:
        return {"error": "Failed to get user token", "details": token_res}

    # User Token দিয়ে তার সব Page বের করা
    pages_url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}"
    pages_res = requests.get(pages_url).json()
    
    saved_pages = []
    for page in pages_res.get("data", []):
        # খাতায় Save করা
        db_page = PageToken(
            page_id=page["id"],
            page_name=page["name"],
            access_token=page["access_token"]
        )
        db.merge(db_page) # থাকলে Update, না থাকলে Insert
        saved_pages.append(page["name"])
    
    db.commit()

    return HTMLResponse(f"<h1>Success!</h1><p>Saved Pages: {', '.join(saved_pages)}</p><p>Check your mybotsailor.db file</p>")

# 4. Webhook (আগের মতোই থাকবে, এখন খাতা থেকে Token নিবে)
@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return "Verification failed"

@app.post("/webhook")
async def webhook_handler(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            if "message" in msg:
                sender_id = msg["sender"]["id"]
                page_id = msg["recipient"]["id"]
                text = msg["message"].get("text", "")
                
                # খাতা থেকে ওই পেজের চাবি বের করা
                page_data = db.query(PageToken).filter(PageToken.page_id == page_id).first()
                if page_data:
                    page_token = page_data.access_token
                    # Reply পাঠানো
                    reply_url = f"https://graph.facebook.com/v19.0/me/messages?access_token={page_token}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": f"You said: {text} [From SaaS Bot]"}
                    }
                    requests.post(reply_url, json=payload)
    return {"status": "ok"}