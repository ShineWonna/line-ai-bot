import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# Environment Variables များမှတစ်ဆင့် Key များကို ခေါ်ယူခြင်း
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    
    try:
        # OpenAI GPT-4o-mini မော်ဒယ်ကို လှမ်းခေါ်ခြင်း
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_text}]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"Error: {str(e)}"

    # LINE App ထဲသို့ ပြန်စာပို့ပေးခြင်း
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))

if __name__ == "__main__":
    app.run(port=5000)
