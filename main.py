from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import os
import requests

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Verification failed", status_code=403)

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    # তোমার Bot এর Logic এখানে থাকবে
    print(data)
    return {"status": "ok"}

@app.get("/")
async def home():
    return {"message": "Bot is Running with FastAPI!"}
