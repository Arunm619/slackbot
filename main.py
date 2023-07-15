import logging

from slack_bolt import App
from slack_sdk.web import WebClient
import OnboardingTutorial
import ssl as ssl_lib
import certifi

token = "xoxb-5570314117252-5572669801606-7ATIHjgu7bzmMxFy0woT8eGw"
signing_secret = "9438d28b495b91a3ce49cf9428438f3c"
ml_model_url = "https://78e77af553e04e03a3.gradio.live/"
ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
app = App(token=token, signing_secret=signing_secret)
onboarding_tutorials_sent = {}

from gradio_client import Client
from slack_bolt import App


import random

def extract_text_before_question(text):
    question_index = text.find("Question")
    if question_index != -1:
        return text[:question_index]
    else:
        return text


def get_waiting_message():
    waiting_messages = [
        "Hang tight, I'm fetching the information for you!",
        "Just a moment, I'm working on finding the answer.",
        "Hold on, I'm digging into my vast database for your query.",
        "Patience is key! I'm gathering the data you need.",
        "Please wait while I fetch the relevant details for you.",
        "I'm on it! Just a few seconds while I retrieve the requested information.",
        "Processing your request, please bear with me.",
        "Sit tight, I'm working hard to provide you with the best response.",
        "Almost there! I'm gathering the necessary data to assist you.",
        "Just a little longer, I'm searching high and low to find the answer."
    ]
    return random.choice(waiting_messages)


def makeGradioCall(query):
    client = Client(ml_model_url)
    result = client.predict(
        query,  # str  in 'query' Textbox component
        api_name="/predict"
    )
    print(result)
    fine_tuned = extract_text_before_question(result)
    print(fine_tuned)
    return fine_tuned

def start_onboarding(user_id: str, channel: str, client: WebClient):
    # Create a new onboarding tutorial.
    onboarding_tutorial = OnboardingTutorial(channel)

    # Get the onboarding message payload
    message = onboarding_tutorial.get_message_payload()

    # Post the onboarding message in Slack
    response = client.chat_postMessage(**message)

    # Capture the timestamp of the message we've just posted so
    # we can use it to update the message after a user
    # has completed an onboarding task.
    onboarding_tutorial.timestamp = response["ts"]

    # Store the message sent in onboarding_tutorials_sent
    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial


# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the message callback to the 'message' event.
@app.event("message")
def message(event, client):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if not text:
        return start_onboarding(user_id, channel_id, client)


def answer_message(body: dict, client):
    """
    SlackAPI handler of message received.
    """

    print(body)

    ts = body['event']['ts']
    user = body['event']['user']

    message = body['event']['text']
    channel = body['event']['channel']

    client.chat_postMessage(channel=channel, thread_ts=ts, text=get_waiting_message())
    client.chat_postMessage(channel=channel, thread_ts=ts, text=makeGradioCall(message))


@app.event("app_mention")
def handle_app_mention_events(body, client):
    answer_message(body, client)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.start(3000)
