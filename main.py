import os
import asyncio
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn

# --- Configuration ---
# Use environment variables for production, fallback to defaults for local dev
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8306417982:AAG_iTJsRV3aMviAqrV1gOk5ecICNPh4fg0")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8203104058")

# Log configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ptb_application.initialize()
    await ptb_application.start()
    await ptb_application.updater.start_polling() 
    logger.info("Telegram Bot Started and Polling...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Telegram Bot...")
    try:
        if ptb_application.updater.running:
            await ptb_application.updater.stop()
        if ptb_application.running:
            await ptb_application.stop()
        await ptb_application.shutdown()
        logger.info("Telegram Bot Shutdown Complete.")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Telegram Bot Setup ---
# Build the application
ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# State Management
class ChatSession:
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.step = "init"
        self.user_info = {}
        self.admin_connected = False

    async def send_text(self, text: str):
        try:
            await self.websocket.send_json({"type": "message", "content": text, "sender": "agent"})
        except Exception as e:
            logger.error(f"Error sending to {self.client_id}: {e}")

sessions: Dict[str, ChatSession] = {}
# Mapping Telegram Message ID -> Client ID (for checking replies)
# When we forward a msg to Admin, we store the ID of that msg.
# If Admin replies to it, we know who they are talking to.
msg_id_to_client: Dict[int, str] = {}
admin_active_session: Optional[str] = None


# --- Telegram Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Future Growth Support Bot Ready.\nCreate a web session to test.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Reply to a message to speak to that specific user.\nOr simply type to speak to the last active user.')

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_active_session
    
    # Security check: Only talk to the Admin
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID):
        return

    msg_text = update.message.text
    target_client_id = None

    # 1. Check if this is a reply to a specific forwarded message
    if update.message.reply_to_message:
        reply_id = update.message.reply_to_message.message_id
        if reply_id in msg_id_to_client:
            target_client_id = msg_id_to_client[reply_id]
            # Update active session to this user for convenience
            admin_active_session = target_client_id

    # 2. If not a reply (or mapping lost), use the globally active session
    if not target_client_id:
        target_client_id = admin_active_session

    # 3. Send logic
    if target_client_id and target_client_id in sessions:
        session = sessions[target_client_id]
        await session.send_text(msg_text)
        # Verify receipt to admin (optional, can be noisy)
        # await update.message.set_reaction("👍") 
    else:
        if target_client_id:
             await update.message.reply_text("Session disconnected or expired.")
        else:
             await update.message.reply_text("No active chat. waiting for customers...")

ptb_application.add_handler(CommandHandler("start", start_command))
ptb_application.add_handler(CommandHandler("help", help_command))
ptb_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))


# --- FastAPI Routes ---


# GET Routes
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/products", response_class=HTMLResponse)
async def get_products(request: Request):
    return templates.TemplateResponse("products.html", {"request": request})

@app.get("/performance", response_class=HTMLResponse)
async def get_performance(request: Request):
    return templates.TemplateResponse("performance.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def get_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def get_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def get_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


# WebSocket Route
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    global admin_active_session
    await websocket.accept()
    
    session = ChatSession(websocket, client_id)
    sessions[client_id] = session
    
    # "Customer clicks support Chat button -> Window pops up -> System says: Welcome..."
    # We also reset the step to init.
    session.step = "awaiting_inquiry"
    await session.send_text("Welcome to the support Chat. My name is Oliver, what can I help you out with today?")
    
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                continue

            # Process logic
            # IF admin connected, bridge directly
            if session.admin_connected:
                if ADMIN_CHAT_ID:
                    try:
                        # Forward to Telegram
                        msg = await ptb_application.bot.send_message(
                            chat_id=ADMIN_CHAT_ID,
                            text=f"[{client_id}]: {content}"
                        )
                        # Store ID for 'Reply' functionality
                        msg_id_to_client[msg.message_id] = client_id
                        admin_active_session = client_id
                    except Exception as e:
                        logger.error(f"Telegram send error: {e}")
                continue

            # OLIVER BOT LOGIC (Pre-Admin)
            if session.step == "awaiting_inquiry":
                session.user_info["inquiry"] = content
                await session.send_text("Thank you. Please tell me your name and email in case the chat gets disconnected.")
                session.step = "awaiting_contact"

            elif session.step == "awaiting_contact":
                session.user_info["contact"] = content
                await session.send_text("Great! Lastly, what is your phone number? [We will give you a call shortly]\n*No charge to your phone Bill*")
                session.step = "awaiting_phone"

            elif session.step == "awaiting_phone":
                session.user_info["phone"] = content
                await session.send_text("Redirecting to next available agent! Your queue is being filtered the order it came in, Thank you.")
                
                # Notify Admin
                details = (
                    f"🚨 **New Support Request**\n"
                    f"Processing Order: #00{len(sessions)}\n"
                    f"**Client:** {session.user_info.get('contact')}\n"
                    f"**Phone:** {session.user_info.get('phone')}\n"
                    f"**Inquiry:** {session.user_info.get('inquiry')}\n\n"
                    f"System: Client marked as active. Reply to chat."
                )
                
                if ADMIN_CHAT_ID:
                    try:
                        msg = await ptb_application.bot.send_message(
                            chat_id=ADMIN_CHAT_ID, 
                            text=details, 
                            parse_mode="Markdown"
                        )
                        msg_id_to_client[msg.message_id] = client_id
                        admin_active_session = client_id
                        session.admin_connected = True
                    except Exception as e:
                        logger.error(f"Telegram error: {e}")
                        
                session.step = "connected"

    except WebSocketDisconnect:
        del sessions[client_id]
        if admin_active_session == client_id:
            admin_active_session = None
        if ADMIN_CHAT_ID and session.admin_connected:
            await ptb_application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Client {client_id} disconnected.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
