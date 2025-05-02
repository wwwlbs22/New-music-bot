import logging
from telethon.tl.types import DocumentAttributeImageSize

from pyrogram import Client

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

# Create a logger object
logger = logging.getLogger("pyrogram")

import sys
import asyncio
from pytgcalls import filters as call_filters
import os
from tools import *
from config import *
from fonts import *
from pyrogram import enums
from pyrogram import Client, filters
from pytgcalls.types import ChatUpdate
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatType, ChatMemberStatus
import importlib
from telethon import  Button
from pyrogram.errors.exceptions import InviteHashExpired , ChannelPrivate ,GroupcallForbidden, AccessTokenExpired, UserDeactivated
from pyrogram.errors.exceptions import SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, SessionRevoked, AuthTokenExpired, AuthKeyDuplicated
from pytgcalls.exceptions import NotInCallError
import time
import queue
import certifi
import datetime
import random
from pytgcalls.exceptions import (
    NoActiveGroupCall,
)
import base64
import subprocess
import re
import json
from pytgcalls import idle, PyTgCalls
from pytgcalls.types import AudioQuality
from pytgcalls.types import MediaStream
from pytgcalls.types import VideoQuality
from telethon import TelegramClient, events, errors
import yt_dlp
# Define the main bot client (app)
import random
import string

cache_dir = f"{ggg}/cache"
os.makedirs(cache_dir, exist_ok=True)

async def remove_active_chat(user_client, chat_id):
    if chat_id in active[user_client.me.username]:
        active[user_client.me.username].remove(chat_id)
    chat_dir = f"{ggg}/user_{user_client.me.id}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)
    clear_directory(chat_dir)


def storre_user(user_id, timestamp):
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"timestamp": timestamp}},
        upsert=True
    )

import asyncio
import logging
from typing import Optional
from pyrogram import Client





from telethon import TelegramClient, events
import asyncio
import traceback
import os
    # Start Telethon monitor bot

from pyrogram.enums import ChatMemberStatus, ChatType





from pyrogram import Client, filters
import asyncio
import datetime
from pyrogram import enums










from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Store temporary format selections
stored_format = {}



from typing import Dict, List, Optional, Tuple, NamedTuple

class BotStats(NamedTuple):
    """Container for bot statistics including identification info."""
    bot_id: int
    username: str
    count: int


async def get_chat_info(client: Client, chat_id: int) -> Tuple[Optional[enums.ChatType], Optional[int]]:
    """Get chat type and members count safely with error handling."""
    try:
        chat = await client.get_chat(chat_id)
        members_count = await client.get_chat_members_count(chat_id) if not chat.type ==enums.ChatType.PRIVATE else 0
        return chat.type, members_count
    except FloodWait as e:
        print(f"Rate limited! Sleeping for {e.value} seconds.")
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"Error getting chat info for {chat_id}: {str(e)}")
        return None, None

async def get_client_stats(client: Client) -> Optional[Dict[str, int]]:
    """Gets statistics for a single client instance."""
    stats = {
        'private': 0,
        'groups': 0,
        'admin': 0
    }

    user_data = collection.find_one({"user_id": client.me.id})
    if not user_data:
        return None

    users: List[int] = user_data.get('users', [])

    # Process chats in batches to avoid overwhelming the server
    BATCH_SIZE = 50
    for i in range(0, len(users), BATCH_SIZE):
        batch = users[i:i + BATCH_SIZE]
        chat_infos = await asyncio.gather(
            *[get_chat_info(client, chat_id) for chat_id in batch],
            return_exceptions=True
        )

        for j, chat_info in enumerate(chat_infos):
            if not isinstance(chat_info, tuple) or chat_info[0] is None:
                continue
                
            chat_type, members_count = chat_info

            if chat_type == enums.ChatType.PRIVATE:
                stats['private'] += 1
            elif chat_type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                # Skip both counts if member count is less than 60
                if members_count is None or members_count < 60:
                    continue
                    
                # Count group
                stats['groups'] += 1
                
                # Check for admin status
                try:
                    member = await client.get_chat_member(batch[j], client.me.id)
                    if member.status in (
                        enums.ChatMemberStatus.OWNER,
                        enums.ChatMemberStatus.ADMINISTRATOR
                    ):
                        stats['admin'] += 1
                except Exception as e:
                    print(f"Error checking admin status in {batch[j]}: {str(e)}")

    return stats


from telethon import events
from telethon.tl.types import User




def currently_playing(user_client, message):
    song_queue = queues.get(f"dic_{user_client.me.id}")
    try:
        if len(song_queue[message.chat.id]) <=1:
           return False
        return True
    except KeyError:
        True


import datetime
from pyrogram import filters




def format_duration(duration):
  hours = duration // 3600
  minutes = (duration % 3600) // 60
  seconds = duration % 60

  if hours > 0:
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
  elif minutes > 0:
    return f"{minutes:02d}:{seconds:02d}"
  else:
    return f"{seconds:02d}"



async def run_user(user_id):
    reload_all_plugins()
    user_data = user_sessions.find_one({"user_id": user_id})
    user_session_string = user_data.get("string_session")
    user_bot_token = user_data.get("bot_token")
    
    try:
        # Create and start the user client using the bot token
        user_client = Client(
            f"{generate_client_id()}",
            api_id=API_ID,
            api_hash=API_HASH,workers=5,
            bot_token=user_bot_token,
            plugins=dict(root="plugins",include=["bots"]),
            in_memory=True, sleep_threshold=32,
        )
        await user_client.start()
        client_name = f"{user_client.me.first_name} {user_client.me.last_name or ''}".strip()
        logger.info(f"Bot authorized successfully! 🎉 Authorized as: {client_name}")
        clients[user_id] = user_client
        owners[user_client.me.id] = user_id
        

    except (SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, 
            SessionRevoked, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired, 
            UserDeactivated) as e:
        try:
            user_client = clients.get(user_id)
            await user_client.stop(block=False)
        except:
            pass
        user_sessions.delete_one({"user_id": user_id})
        if user_id in clients:
            clients.pop(user_id)
            
    except AttributeError:
        logger.info("The object is None; it doesn't have an 'id' attribute.")
        
    except Exception as e:
        try:
            user_client = clients.get(user_id)
            await user_client.stop(block=False)
        except:
            pass
        try:
            await app.send_message(user_id, f"Error starting your music: {e}")
        except:
            pass
            
        # Notify admins about the error
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass
                        
        if user_id in clients:
            clients.pop(user_id)
        return

    try:
        # Create and start the session client
        session_client = Client(
            f"user_{user_id}_session",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=user_session_string,
            in_memory=True, no_updates=True, sleep_threshold=32
        )
        auth = await session_client.connect()
        if not auth:
            try:
                user_client = clients.get(user_id)
                await user_client.stop(block=False)
            except:
                pass
            await app.send_message(user_id, f"Client is not authorized for {user_id}. Please authorize first.")
            await session_client.disconnect()
            user_sessions.delete_one({"user_id": user_id})
            return

        await session_client.disconnect()
        call_py = PyTgCalls(session_client)
        call_py.add_handler(end, call_filters.stream_end())
        call_py.add_handler(hd_stream_closed_kicked, call_filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT) | call_filters.chat_update(ChatUpdate.Status.KICKED))
        await call_py.start()
        await asyncio.sleep(2)
        clients[f"{user_id}_session"] = session_client
        songs_client[session_client.me.id] = call_py
        client_name = f'{session_client.me.first_name if session_client.me else ""} {session_client.me.last_name or "" if session_client.me else ""}'.strip()
        user_client = clients.get(user_id)
        await app.send_message(user_id, f"Your music bot rebooted successfully 🎉 bot as: @{user_client.me.username}\nAssistant as: {client_name}")
        logger.info(f"Username authorized successfully! 🎉 Authorized as: {client_name}")

        try:
            await session_client.join_chat("sheepra_cutie")
            await session_client.join_chat("nub_coder_s")
            await session_client.join_chat("nub_coder_updates")
        except:
            pass

        connector[user_client.me.username] = user_id
        queues[f"dic_{user_client.me.id}"] = {}
        linkage[session_client.me.id] = user_client
        active[user_client.me.username] = []

    except (SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, 
            SessionRevoked, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired, 
            UserDeactivated) as e:
        user_sessions.delete_one({"user_id": user_id})
        try:
            user_client = clients.get(user_id)
            await user_client.stop(block=False)
        except:
            pass
        if user_id in clients:
            clients.pop(user_id)
            
    except AttributeError:
        logger.info("The object is None; it doesn't have an 'id' attribute.")
        
    except Exception as e:
        try:
            user_client = clients.get(user_id)
            await user_client.stop(block=False)
        except:
            pass
        try:
            await app.send_message(user_id, f"Error starting your music: {e}")
        except:
            pass
            
        # Notify admins about the error
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass
                        
        if user_id in clients:
            clients.pop(user_id)







def set_gvar(user_id, key, value):
    set_user_data(user_id, key, value)

def get_user_data(user_id, key):
    user_data = user_sessions.find_one({"user_id": user_id})
    if user_data and key in user_data:
        return user_data[key]
    return None

def set_user_data(user_id, key, value):
    user_sessions.update_one({"user_id": user_id}, {"$set": {key: value}}, upsert=True)

def gvarstatus(user_id, key):
    return get_user_data(user_id, key)

def unset_user_data(user_id, key):
     user_sessions.update_one({"user_id": user_id}, {"$unset": {key: ''}}, upsert=True)


def rename_file(old_name, new_name):
    try:
        # Rename the file
        os.rename(old_name, new_name)

        # Get the absolute path of the renamed file
        new_file_path = os.path.abspath(new_name)
        logger.info(f'File renamed from {old_name} to {new_name}')
        return new_file_path  # Return the new file location
    except FileNotFoundError:
        logger.info(f'The file {old_name} does not exist.')
    except FileExistsError:
        logger.info(f'The file {new_name} already exists.')
    except Exception as e:
        logger.info(f'An error occurred: {e}')
import magic

mime = magic.Magic(mime=True)


import psutil
import os



from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType




from telethon import events
import os
import sys




create_custom_filter = filters.create(lambda _, __, message: any(m.is_self for m in (message.new_chat_members if message.new_chat_members else [])))





bot.start(bot_token=BOT_TOKEN)
bot.loop.run_until_complete(run_all_clients())
import time
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
bot.run_until_disconnected()
