import os
import requests
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, User

# Database create
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- SECURE ENV VARIABLES (Render থেকে আসবে) ---
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mybotsailor_verify_123")

GRAPH_API_VERSION = "v21.0"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"status": "MyBotSailor is Running!"}

# 1. Login URL generate
@app.get("/auth/login")
def auth_login():
    auth_url = f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=pages_show_list,pages_messaging,pages_manage_metadata,pages_read_engagement&response_type=code"
    return {"auth_url": auth_url}

# 2. OAuth Callback - User er Page Token Save hobe
@app.get("/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    # Code -> Long Lived Token
    token_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token?client_id={APP_ID}&client_secret={APP_SECRET}&redirect_uri={REDIRECT_URI}&code={code}"
    r = requests.get(token_url).json()
    
    if "access_token" not in r:
        return {"error": r}

    user_access_token = r["access_token"]

    # Get User's Pages
    pages_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts?access_token={user_access_token}"
    pages_data = requests.get(pages_url).json()

    for page in pages_data.get("data", []):
        page_id = page["id"]
        page_token = page["access_token"]
        page_name = page["name"]
        
        # Save to DB
        existing_user = db.query(User).filter(User.page_id == page_id).first()
        if not existing_user:
            new_user = User(page_id=page_id, page_access_token=page_token, page_name=page_name)
            db.add(new_user)
        else:
            existing_user.page_access_token = page_token
            existing_user.page_name = page_name
        db.commit()

    return HTMLResponse("<h1>Success! Your Page Connected to MyBotSailor. You can close this window.</h1>")

# 3. Webhook Verification (Meta theke asbe)
@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return HTMLResponse(content=challenge)
    return HTMLResponse(content="Verification Failed", status_code=403)

# 4. Webhook - Message Receive & Auto Reply
@app.post("/webhook")
async def webhook_handler(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                if "message" in messaging:
                    sender_id = messaging["sender"]["id"]
                    recipient_id = messaging["recipient"]["id"]
                    message_text = messaging["message"].get("text", "")

                    # Find page owner from DB
                    user = db.query(User).filter(User.page_id == recipient_id).first()
                    if user and message_text:
                        # Echo Reply
                        reply_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/messages?access_token={user.page_access_token}"
                        payload = {
                            "recipient": {"id": sender_id},
                            "message": {"text": f"Echo: {message_text}"}
                        }
                        requests.post(reply_url, json=payload)
    return {"status": "ok"}
