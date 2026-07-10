import os
from flask import Flask, request, abort
import google.generativeai as genai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE Credentials
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# Gemini API Configuration
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-3-flash-preview",
    system_instruction="""
    မင်းရဲ့နာမည်က Shine's Bot ဖြစ်ပြီး Shine Wonna ရဲ့ ကိုယ်ရေးကိုယ်တာ AI လက်ထောက် ဖြစ်တယ်။ 
    တခြားသူတွေ လာမေးရင် ယဉ်ယဉ်ကျေးကျေးနဲ့ မင်းက ဘယ်သူ့ရဲ့ လက်ထောက်ဖြစ်ကြောင်း အရင်မိတ်ဆက်ပါ။ 
    ပြီးရင် Shine Wonna က လက်ရှိမှာ [ဥပမာ- အလုပ်ကိစ္စတစ်ခုနဲ့အပြင်ကိုရောက်နေပါတယ်။အလုပ်ကိစ္စရှိရင်ပြောထားပေးလို့ရပါတယ်။] ဆိုတာကို လိုအပ်သလို အကျဉ်းချုပ် ပြန်ပြောပြပေးပါ။ 
    မြန်မာလို ယဉ်ကျေးပျူငှာစွာ တုံ့ပြန်ပေးပါ။
    """
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # Gemini AI ဆီက စာသားတောင်းဆိုခြင်း
        response = model.generate_content(user_message)
        reply_text = response.text
    except Exception as e:
        reply_text = f"Gemini Error: {str(e)}"
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
