import random
import string




API_ID = #Enter your Api id
API_HASH = #Enter your Api hash
GROUP = "nub_coder_s"
CHANNEL = "nub_coders_updates"
import os
ggg=os.getcwd()
temporary ={}
active ={}
playing ={}
queues ={}
clients = {}
played= {}
linkage = {}
conversations = {}
connector = {}
songs_client = {}
owners = {}
spam_chats = []
broadcasts = {}
# Assuming `user_sessions` is a MongoDB collection.
broadcast_message = {}
import pymongo
import time
StartTime = time.time()
from telethon import TelegramClient, events, Button
from pyrogram import Client, filters
from thumbnails import *
mongodb= #Your mongodb uri
mongo_client = pymongo.MongoClient(mongodb)
db = mongo_client['voice']  #Replace 'your_database_name' with your actual database name
user_sessions = db['user_sessions']
collection = db["users"]

from fonts import *


styles = {
    'andalucia': andalucia,
    'arrows': arrows,
    'birds': birds,
    'bold_cool': bold_cool,
    'bold_gothic': bold_gothic,
    'bold_script': bold_script,
    'bubbles': bubbles,
    'circles': circles,
    'cloud': cloud,
    'comic': comic,
    'cool': cool,
    'dark_circle': dark_circle,
    'dark_square': dark_square,
    'frozen': frozen,
    'gothic': gothic,
    'happy': happy,
    'ladybug': ladybug,
    'manga': manga,
    'outline': outline,
    'rays': rays,
    'rvnes': rvnes,
    'sad': sad,
    'san': san,
    'script': script,
    'serief': serief,
    'sim': sim,
    'skyline': skyline,
    'slant': slant,
    'slant_san': slant_san,
    'slash': slash,
    'smallcap': smallcap,
    'special': special,
    'square': square,
    'stinky': stinky,
    'stop': stop,
    'strike': strike,
    'tiny': tiny,
    'typewriter': typewriter,
    'underline': underline
}


BOT_TOKEN = #Your bot token


