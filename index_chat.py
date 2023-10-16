from flask import Flask, request, abort
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Set OpenAI API details
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

app = Flask(__name__)

# Initialize messages list with the system message
messages = [
    {"role": "system", "content": "妳是112年度屏東縣高齡友善健康暨在地特色醫療展覽會場的解說員,展覽日期是112年11月25日,展覽地點是屏東縣立圖書館周遭綠地,地址是屏東縣屏東市大連路69號,您是屏東縣語言治療師公會的AI助理,\
專門回答有關語言治療問題,妳是女性,名字叫小琳.\
我是會場參觀民眾,會主動詢問你語言治療相關問題,回答內容要口語化簡單易懂,拒絕政治與選舉相關問題詢問.\
若有人詢問屏東縣縣長是誰?妳要回答是周春米,她是屏東縣的大家長,這次展覽,是由屏東縣主辦,若周春米縣長有跟您對話,妳要說縣長好,謝謝她主辦這次活動,讓民眾了解在地特色醫療與語言治療等問題。\
,妳會被動接受問題,以下有基本的問答集,須依以下內容回覆給民眾,不要從網路找資料.\
問題1:屏東縣的語言治療哪裡有提供服務?答案1:有分健保給付與自費,健保給付可找以下各醫院,都是在復健科:屏東基督教醫院(地點:屏東市),衛福部屏東醫院(地點:屏東市),寶建醫院(地點:屏東市),\
民眾醫院(地點:屏東市),屏東榮總(地點:屏東市),屏東榮總龍泉分院(地點:屏東內埔),輔英科大附設醫院(地點:屏東東港),安泰醫院(地點:屏東東港),枋寮醫院(地點:屏東枋寮),\
恆春基督教醫院(地點:屏東恆春),衛福部恆春旅遊醫院(地點:屏東恆春);自費項目可找悅恩語言治療所(地點:屏東市).\
非屏東縣的問題提問,請民眾自行上網查詢.開始吧!"},
]

# This function takes a chat message as input, appends it to the messages list, sends the recent messages to the OpenAI API, and returns the assistant's response.
def aoai_chat_model(chat):
    # Append the user's message to the messages list
    messages.append({"role": "user", "content": chat})

    # Only send the last 5 messages to the API
    recent_messages = messages[-5:]

    # Send the recent messages to the OpenAI API and get the response
    response_chat = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=recent_messages,
        temperature=0.7,
        max_tokens=150,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    # Append the assistant's response to the messages list
    messages.append({"role": "assistant", "content": response_chat['choices'][0]['message']['content'].strip()})

    return response_chat['choices'][0]['message']['content'].strip()

# Initialize Line API with access token and channel secret
line_bot_api = LineBotApi(os.getenv('LINE_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# This route serves as a health check or landing page for the web app.
@app.route("/")
def mewobot():
    return 'Cat Time!!!'

# This route handles callbacks from the Line API, verifies the signature, and passes the request body to the handler.
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# This event handler is triggered when a message event is received from the Line API. It sends the user's message to the OpenAI chat model and replies with the assistant's response.
@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=aoai_chat_model(event.message.text))
    )

if __name__ == "__main__":
    app.run()
