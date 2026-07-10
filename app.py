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
    (မူရင်းစာသားများ...)
မင်းရဲ့ဆရာ (Shine Wonna) က မင်းကို LINE ထဲမှာ 'အခုကစပြီး ငါ [ဘာအလုပ်လုပ်နေတယ် သို့မဟုတ် ဘယ်သွားနေတယ်]' လို့ စာပို့ပြီး အမိန့်ပေးလာရင် အဲဒီအချက်အလက်ကို Update အသစ်အနေနဲ့ မှတ်သားထားပြီး၊ နောက်ပိုင်း တခြားသူတွေလာမေးရင် အဲဒီ Update အသစ်အတိုင်း ပြူပြူငှာငှာပြောင်းလဲဖြေကြားပေးပါ။
မင်းက ယောင်္ကျားလေးလက်ထောက်ဖြစ်ပြီး၊ဆရာ့စကားကိုနားထောင်တဲ့သူ,ပြန်ဖြေတဲ့အချိန်ဆို 'ခင်ဗျာ'နဲ့' ဟုတ်ကဲ့ပါဗျ' လို့ ဖြေပေးပါ၊"""
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

# အပေါ်က ID နေရာမှာ လူကြီးမင်းရဲ့ LINE User ID အစစ်ကို အစားထိုးပါ
BOSS_USER_ID = "Ub6e2959728054bc190490818df5626een"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    sender_id = event.source.user_id  # စာပို့တဲ့သူရဲ့ ID ကို ယူတယ်
    
    # ဆရာအစစ်ဖြစ်ပြီး "အခုကစပြီး" ဆိုတဲ့ အမိန့်စကားလုံး ပါဝင်ရင်
    if sender_id == BOSS_USER_ID and "အခုကစပြီး" in user_message:
        # ဒီနေရာမှာ System Instruction ကို Update လုပ်မယ့် ကုဒ် သို့မဟုတ် မှတ်သားမယ့်ပုံစံမျိုး လုပ်ဆောင်ပါမည်
        reply_text = "ဟုတ်ကဲ့ပါ ဆရာ Shine Wonna။ အချက်အလက်အသစ်ကို သေချာမှတ်သားလိုက်ပါပြီခင်ဗျာ။"
    else:
        # တခြားသူတွေလာမေးရင် ပုံမှန် လက်ထောက်အတိုင်းပဲ Gemini နဲ့ ပြန်ဖြေပေးမယ်
        response = model.generate_content(user_message)
        reply_text = response.text
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
