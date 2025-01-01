from flask import Flask, request, abort
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)

# LINEのアクセストークンとチャネルシークレット
LINE_ACCESS_TOKEN = 'UH9/CGcVZt4bnQKn3DX72uPH1i6AC0uKxSEWa2divzG7kyK3MfkOl1kc2K7bKhbbw0oIWnAk2K+/Mq/GJIq6RcBKBCPK025VD0S7ZPazgxcEI+fbA/ceLzDWorMGUFUPyaAyB/voU2GTKn23KUw8gwdB04t89/1O/w1cDnyilFU='  # ここにLINEのアクセストークンを設定
LINE_CHANNEL_SECRET = '43ef859f4196c303b24b94f6052c4fa3'  # ここにLINEのチャネルシークレットを設定

# ユーザーの設定した通貨と価格を保存する辞書
user_settings = {}


# メッセージ受信のエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)

    # リクエストの検証（セキュリティ）
    if not verify_signature(body, request.headers['X-Line-Signature']):
        abort(400)

    # メッセージの内容を解析
    events = parse_events(body)
    for event in events:
        if event["type"] == "message":
            message = event["message"]["text"]
            user_id = event["source"]["userId"]

            if message == "価格通知設定":
                send_reply(user_id, "通貨名を教えてください（例: BTC）")
                user_settings[user_id] = {"step": "currency"}
            elif user_id in user_settings:
                if user_settings[user_id]["step"] == "currency":
                    user_settings[user_id]["currency"] = message
                    send_reply(user_id, f"{message}の価格を設定してください（例: 5000000）")
                    user_settings[user_id]["step"] = "price"
                elif user_settings[user_id]["step"] == "price":
                    user_settings[user_id]["price"] = float(message)
                    send_reply(user_id, f"価格通知を設定しました！ {message}円になったらお知らせします。")
                    user_settings[user_id]["step"] = "complete"

                    # 通貨と価格を元に価格監視を開始
                    check_price(user_id)

    return "OK"


# Webhookで送信された署名を検証する関数
def verify_signature(body, signature):
    # シグネチャの検証を行うコード（省略）
    return True


# Webhookから送られたイベントデータを解析する関数
def parse_events(body):
    # ボディを解析してイベントリストを返すコード（省略）
    return []


# 通貨価格を取得してユーザーに通知する関数
def get_current_price(currency):
    # ここでビットバンクAPIなどを使って現在の価格を取得します
    # 仮に1000000円を返すようにしています
    return 1000000  # 実際にはAPIを使って価格を取得してください


# LINEにメッセージを送る関数
def send_line_notify(message, user_id):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response


# ユーザーに返信する関数
def send_reply(user_id, message):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response


# 価格が目標に達したかどうかをチェックする関数
def check_price(user_id):
    currency = user_settings[user_id]["currency"]
    target_price = user_settings[user_id]["price"]

    # 定期的に価格をチェック
    current_price = get_current_price(currency)  # 実際にはAPIを使って価格を取得
    print(f"Current price of {currency}: {current_price}円")

    if current_price >= target_price:
        send_line_notify(f"【お知らせ】{currency}が目標価格に達しました！現在の価格は{current_price}円です。", user_id)
    else:
        print(f"{currency}の価格が目標価格に達していません。")


# 定期的に価格をチェックするためにスケジューラーを設定
def start_price_check():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_price, 'interval', seconds=60)  # 60秒ごとに価格チェック
    scheduler.start()


if __name__ == "__main__":
    start_price_check()  # 価格監視を開始
    app.run(debug=True, port=5000)
