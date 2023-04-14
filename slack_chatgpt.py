import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import openai

# APIキーの設定
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Slackアプリの設定
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message(":wave:")
def say_hello(message, say):
    user = message['user']
    say(f"Hi there, <@{user}>!")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

@app.event("app_mention")
def handle_mentions(event, say):
    text = event["text"]

    # メンションされたテキストをChatGPTに送信
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": text}
        ]
    )

    # ChatGPTからの応答をSlackに送信
    message = response.choices[0]["message"]["content"]
    say(message)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

