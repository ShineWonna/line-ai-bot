import logging
import os

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.genai as genai
load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# LINE setup
line_bot_api = MessagingApi(require_env("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(require_env("LINE_CHANNEL_SECRET"))

# Gemini setup
genai.configure(api_key=require_env("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    if not signature or not body or not body.strip():
        abort(400)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception:
        logger.exception("Failed to verify or handle LINE webhook request")
        abort(500)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if not getattr(event, "reply_token", None):
        logger.warning("Ignoring LINE event without reply token")
        return

    message = getattr(event, "message", None)
    user_text = getattr(message, "text", "") if message is not None else ""
    if not user_text or not user_text.strip():
        logger.info("Ignoring non-text or empty message event")
        return

    try:
        response = model.generate_content(user_text)
        reply_text = getattr(response, "text", None) or getattr(response, "output_text", None)
        if not reply_text:
            reply_text = str(response)
    except Exception:
        logger.exception("Gemini response generation failed")
        reply_text = "Sorry, I couldn't generate a response right now."

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception:
        logger.exception("Failed to send LINE reply")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
