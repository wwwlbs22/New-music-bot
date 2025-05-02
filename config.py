import random
import string
import os
import time
import pymongo
from telethon import TelegramClient, events, Button
from pyrogram import Client, filters
from thumbnails import *
from fonts import *

# Use getenv for all sensitive/configurable values
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("SESSION_STR", "")
GROUP = os.getenv("GROUP", "nub_coder_s")
CHANNEL = os.getenv("CHANNEL", "nub_coders_updates")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
mongodb = os.getenv("MONGODB_URI", "")

# Working directory
ggg = os.getcwd()

# Initialize data structures
temporary = {}
active = {}
playing = {}
queues = {}
clients = {}
played = {}
linkage = {}
conversations = {}
connector = {}
songs_client = {}
owners = {}
spam_chats = []
broadcasts = {}
broadcast_message = {}

# Track start time
StartTime = time.time()

# Set up MongoDB connection
mongo_client = pymongo.MongoClient(mongodb)
db = mongo_client['voice']
user_sessions = db['user_sessions']
collection = db["users"]
