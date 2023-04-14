import os
from slack_sdk import WebClient
from slack_bolt import App
import openai

# APIキーの設定
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Slackアプリの設定
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# デバッグ用
@app.message(":wave:")
def say_hello(message, say):
    user = message['user']
    say(f"Hi there, <@{user}>!")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

thread_histories = {}

@app.event("app_mention")
def handle_mentions(event, say):
    text = event["text"]
    thread_ts = event["ts"]

    history = thread_histories.get(thread_ts, [])
    history.append({"role": "user", "content": text})

    # メンションされたテキストをChatGPTに送信
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history
    )

    # ChatGPTからの応答をSlackに送信
    message = response.choices[0]["message"]["content"]
    say(message, thread_ts=thread_ts)

    history.append({"role": "assistant", "content": message})
    thread_histories[thread_ts] = history

def is_reply_to_chatgpt_bot(channel_id, thread_ts):
    try:
        result = slack_client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        for message in result["messages"]:
            if os.environ.get("SLACK_BOT_ID") in message:
                return True
    except SlackApiError as e:
        print(f"Error: {e}")
    return False

@app.event("message")
def handle_thread_replies(body, event, say):
    if "thread_ts" not in event or "subtype" in event:
        return

    text = event["text"]
    thread_ts = event["thread_ts"]
    channel_id = event["channel"]

    if not is_reply_to_chatgpt_bot(channel_id, thread_ts):
        return
    
    history = thread_histories.get(thread_ts, [])
    history.append({"role": "user", "content": text})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history
    )

    message = response.choices[0]["message"]["content"]
    say(message, thread_ts=thread_ts)

    history.append({"role": "assistant", "content": message})
    thread_histories[thread_ts] = history

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
