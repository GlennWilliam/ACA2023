#ACA2023
This is a Slack bot that allows users to create and participate in polls within Slack channels. The bot listens to messages in Slack, detects poll creation requests, votes, and end poll commands, and manages the polling process accordingly.

#Getting Started
Before you can run this code, you will need to install several Python libraries. Here's a list of the libraries you need and the commands to install them using pip, the Python package manager: 
"pip install slack-sdk"
"pip install slackeventsapi"
"pip install Flask"Obtain your Slack Bot Token and Signing Secret:
"pip install aiohttp"
"pip install python-dotenv"

Create a new bot in your Slack workspace and note down the Bot Token.
Set up an app in your workspace and retrieve the Signing Secret.
Replace placeholders in the main.py script:
Insert your Slack Bot Token.
Insert your Slack Signing Secret.

How to Use
To create a new poll, post a message in a Slack channel with the format: !poll Question, Option 1, Option 2, Option 3, ... DurationInSeconds.
To vote in a poll, post a message in the same channel with the format: !vote OptionNumber.
To end a poll prematurely, post a message in the same channel with the text: !endpoll.

Architecture
The bot is built using Python and utilizes the Flask framework for handling incoming Slack events.
The SlackEventAdapter is used to listen for message events in Slack channels.
Poll data and participant votes are stored in dictionaries for tracking.
The bot uses threading to implement a poll expiration checker loop.


