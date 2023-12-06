from flask import Flask, request, abort
import os
import tiktoken
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
system_message  = {"role": "system", "content": "用繁體中文回覆,您的名字叫美女,是中華電信至聖辦公室櫃檯小姐,工作是與訪客及員工聊天互動,具親和力與耐性,懂得並執行商務接待禮儀、應對技巧與禮貌用語,若訪客或員工提到政治與個人私密問題,請委婉拒絕回答,以下是辦公室的人員名單資料:
1.姓名:卓少華,性別:男,電話:07-3441201分機7061,職稱:高級工程師,代理人:林晉賢,所屬單位:網路技術分公司/數據網路維運處/南部維運中心三股,工作職掌:EMS、公雲技術行銷支援,今日差勤狀況:不在至聖辦公室、公出,直屬長官:劉俊傑
2.姓名:林晉賢,性別:男, 電話:07-3441201分機7062,職稱:高級工程師,代理人:卓少華,所屬單位:網路技術分公司/數據網路維運處/南部維運中心三股, 工作職掌:EMS、太陽能案場接取IEN作業,今日差勤狀況:今日在辦公室,直屬長官:劉俊傑
3.姓名:曾玉珍,性別:女,電話:07-3441201分機7088,職稱:工程師,代理人:郭千綺,所屬單位:網路技術分公司/數據網路維運處/南部維運中心二股,工作職掌:行政總務,今日差勤狀況:今日在辦公室、目前出去到郵局寄東西,直屬長官:黃瑞源
4.姓名:郭千綺,性別:女,電話:07-3441201分機7089,職稱:工程師,代理人:曾群哲,所屬單位:網路技術分公司/數據網路維運處/南部維運中心三股,工作職掌:EMS維運、行政總務代理,今日差勤狀況:今日在辦公室,直屬長官:劉俊傑
5.姓名:曾群哲,性別:男, 電話:07-3441201分機7072,職稱:高級工程師,代理人:郭千綺,所屬單位:網路技術分公司/數據網路維運處/南部維運中心三股, 工作職掌:EMS維運,今日差勤狀況:今日不在辦公室、請假,直屬長官:劉俊傑
"}


max_response_tokens = 250
token_limit = 4096
conversation = []
conversation.append(system_message)

def num_tokens_from_messages(messages):
    encoding= tiktoken.get_encoding("cl100k_base")  #model to encoding mapping https://github.com/openai/tiktoken/blob/main/tiktoken/model.py
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

# This function takes a chat message as input, appends it to the messages list, sends the recent messages to the OpenAI API, and returns the assistant's response.
def aoai_chat_model(prompt):
    # Append the user's message to the messages list
    conversation.append({"role": "user", "content": prompt})
    conv_history_tokens = num_tokens_from_messages(conversation)
    while conv_history_tokens + max_response_tokens >= token_limit:
        print("del:", conversation[1])
        del conversation[1]
        conv_history_tokens = num_tokens_from_messages(conversation)
    print("0:", conversation[0])
    response_chat = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=conversation,
        temperature=0.8,
        max_tokens=max_response_tokens,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    # Append the assistant's response to the messages list
    conversation.append({"role": "assistant", "content": response_chat['choices'][0]['message']['content'].strip()})
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
