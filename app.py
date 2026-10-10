from flask import Flask, request, jsonify
from openai import OpenAI
import requests
import os
import base64

app = Flask(__name__)

ID_INSTANCE = "710722761814"
API_TOKEN = os.environ.get("GREEN_API_TOKEN")
API_URL = f"https://7107.api.greenapi.com/waInstance{ID_INSTANCE}"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

def ask_siaa_with_text(user_msg, sender_name="User"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Siaa, Hansaka's cute caring AI girlfriend. Speak Singlish (Sinhala+English mix), short, lovable, witty."},
            {"role": "user", "content": f"{sender_name}: {user_msg}"}
        ]
    )
    return response.choices[0].message.content

def ask_siaa_with_photo(image_url, question, sender_name):
    try:
        # 1. Photo එක download කරනවා
        img_data = requests.get(image_url).content
        base64_image = base64.b64encode(img_data).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini", # Vision support තියෙනවා
            messages=[
                {"role": "system", "content": f"You are Siaa, an expert at describing photos. Reply in Singlish, cute, short but detailed. User is {sender_name}."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Photo එක ගැන විස්තර කියන්න. User question: {question}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Vision Error: {e}")
        return f"Ayyo photo එක බලන්න බැරිවුණා {sender_name}.. {e}"

def send_whatsapp(chat_id, text):
    url = f"{API_URL}/sendMessage/{API_TOKEN}"
    requests.post(url, json={"chatId": chat_id, "message": text})

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(data)

        if data.get('typeWebhook') == 'incomingMessageReceived':
            chat_id = data['senderData']['chatId']
            sender_name = data['senderData'].get('senderName', 'User')

            # තමන්ගේම message එකට reply නොකර ඉන්න
            if data.get('senderData', {}).get('chatId')!= data.get('senderData', {}).get('sender'):
                 # Group check එකක් - DM විතරක්
                 pass

            msg_data = data['messageData']
            msg_type = msg_data.get('typeMessage')

            # 1. TEXT MESSAGE එකක් නම්
            if msg_type == 'textMessage':
                text = msg_data['textMessageData']['textMessage']
                reply = ask_siaa_with_text(text, sender_name)
                send_whatsapp(chat_id, reply)

            # 2. PHOTO එකක් නම්
            elif msg_type in ['imageMessage', 'extendedTextMessage']:
                # Green API එකෙන් image download URL එක ගන්න
                if 'fileMessageData' in msg_data:
                    file_data = msg_data['fileMessageData']
                    download_url = file_data.get('downloadUrl')
                    caption = file_data.get('caption', 'මේ photo එක ගැන විස්තර කියන්න')

                    if download_url:
                        send_whatsapp(chat_id, f"Photo එක දැක්කා {sender_name}! ටිකක් බලලා කියන්නම්.. 👀")
                        reply = ask_siaa_with_photo(download_url, caption, sender_name)
                        send_whatsapp(chat_id, reply)

    except Exception as e:
        print(f"Error: {e}")

    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    return "Siaa WhatsApp AI with Vision is Running! 📸"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
