import time
import os
from dotenv import load_dotenv
from threading import Thread
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from flask import Flask
from collections import Counter 

load_dotenv()  # Load variables from .env file

app = Flask(__name__)

# Set your Slack bot token here
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Set your signing secret from the Slack API here
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Initialize Slack clients
slack_client = WebClient(token=SLACK_BOT_TOKEN)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, '/slack/events', app)

# Dictionary to store poll data
polls = {}

# Dictionary to store vote limits
participant_votes = {}
MAX_VOTES_PER_PARTICIPANT = 2


# Event listener for message events
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    user_id = message.get("user")
    channel = message.get("channel")
    text = message.get("text")

    if user_id and channel and text:

        # Check if the message is a poll creation request
        if text.startswith("!poll"):
            options = text.split("!poll")[1].strip().split(",")

            if len(options) >= 3:  # Added poll duration check
                poll_question = options[0]
                poll_options = [option.strip() for option in options[1:-1]]  # Last option is duration
                poll_duration = int(options[-1])

                # Store the poll in the dictionary with duration
                polls[channel] = {
                    "active": True,
                    "question": poll_question,
                    "options": poll_options,
                    "votes": [],
                    "end_time": int(time.time()) + poll_duration # Calculate poll end time
                }

                # Post the poll question and options to the channel
                poll_message = f"📊 Poll: {poll_question}\n"
                for idx, option in enumerate(poll_options, start=1):
                    poll_message += f"{idx}. {option}\n"
                poll_message += f"Poll ends in {poll_duration} seconds."
                slack_client.chat_postMessage(channel=channel, text=poll_message)

    # Check if the message is a poll vote
    elif text.startswith("!vote"):
        selected_option = text.split("!vote")[1].strip()

        # Check if there's an active poll and the selected_option is a valid number
        if channel in polls and selected_option.isdigit():
            selected_option = int(selected_option)
            poll = polls[channel]

            # Check if the selected_option is within the valid range of options
            if 1 <= selected_option <= len(poll["options"]):
                # Check if the user has not reached the maximum vote limit
                if user_id not in participant_votes:
                    participant_votes[user_id] = []

                if len(participant_votes[user_id]) < MAX_VOTES_PER_PARTICIPANT:
                    user_vote = poll["options"][selected_option - 1]
                    
                    # Record the user's vote and update their remaining votes
                    polls[channel]["votes"].append({"user_id": user_id, "vote": user_vote})
                    participant_votes[user_id].append(selected_option)
                    remaining_votes = MAX_VOTES_PER_PARTICIPANT - len(participant_votes[user_id])
                    
                    # Construct and send a message confirming the vote and remaining votes
                    vote_message = f"🗳️ Your vote for '{user_vote}' has been recorded. " \
                                f"You have {remaining_votes} votes remaining."
                    slack_client.chat_postMessage(channel=channel, text=vote_message)
                    
                else:
                    # Notify the user if they've reached the maximum vote limit
                    slack_client.chat_postMessage(channel=channel, text="You have reached the maximum vote limit.")
            else:
                # Notify the user if they've provided an invalid option number
                slack_client.chat_postMessage(channel=channel, text="Invalid option. Please vote for a valid option.")
        else:
            # Notify the user if there's no active poll to vote on
            slack_client.chat_postMessage(channel=channel, text="No active poll to vote on.")


            
    # Check if the message is to end the current poll
    elif text.strip() == "!endpoll":
        if channel in polls and polls[channel]["active"]:
            # Set the poll as inactive
            polls[channel]["active"] = False
            
            # Calculate and display results
            poll = polls[channel]
            votes = Counter([vote["vote"] for vote in poll["votes"]])
            result_message = ""

            # Check if anyone has voted
            if not votes:
                result_message = "No votes were cast in this poll."
            else:
                for option, count in votes.items():
                    result_message += f"{option}: {count} votes\n"
            
            slack_client.chat_postMessage(channel=channel, text="🛑 Poll has ended. Final results:\n" + result_message)

            # Remove the poll data from the dictionary
            del polls[channel]

            del participant_votes[channel]

        else:
            slack_client.chat_postMessage(channel=channel, text="No active poll to end.")


# Poll expiration checker
def check_expired_polls():
    current_time = time.time()
    expired_channels = []

    for channel, poll in polls.items():
        if poll["end_time"] <= current_time:
            expired_channels.append(channel)

    for channel in expired_channels:
        if channel in polls and polls[channel]["active"]:
            poll = polls[channel]
            poll["active"] = False
            
            # Calculate and display results
            votes = Counter([vote["vote"] for vote in poll["votes"]])
            result_message = ""

            # Check if anyone has voted
            if not votes:
                result_message = "No votes were cast in this poll."
            else:
                for option, count in votes.items():
                    result_message += f"{option}: {count} votes\n"

            slack_client.chat_postMessage(channel=channel, text="🛑 Poll has ended. Final results:\n" + result_message)

            # Remove the poll data from the dictionary
            del polls[channel]
            del participant_votes[channel]

# Define a function to continuously check for expired polls
def poll_checker_loop():
    while True:
        check_expired_polls()  # Call the function to check for expired polls
        time.sleep(10)  # Wait for 10 seconds before checking again

# Start the Flask server to listen for Slack events
if __name__ == "__main__":
    # Create a thread to run the poll_checker_loop function concurrently
    poll_checker_thread = Thread(target=poll_checker_loop)
    poll_checker_thread.daemon = True  # Set the thread as a daemon to exit with the main program
    poll_checker_thread.start()  # Start the thread

    # Start the Flask app to listen for Slack events
    app.run(debug=True)  # Run the Flask app in debug mode
   
