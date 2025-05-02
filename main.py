import logging
from telethon.tl.types import DocumentAttributeImageSize
from pyrogram import Client
import sys
import asyncio
import os
import time
import queue
import datetime
import random
import base64
import subprocess
import re
import json
import certifi
from typing import Optional, Dict, List, Tuple, NamedTuple

# Third-party libraries
from pytgcalls import filters as call_filters
from pytgcalls import idle, PyTgCalls
from pytgcalls.types import AudioQuality, MediaStream, VideoQuality, ChatUpdate
from pytgcalls.exceptions import NoActiveGroupCall, NotInCallError
from telethon import TelegramClient, events, errors, Button
import yt_dlp
import magic
import psutil


# Local modules
from tools import *  # Assuming these are utility functions
from config import *
from fonts import *

# Pyrogram and Telethon imports
from pyrogram import enums, filters
from pyrogram import Client
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatType, ChatMemberStatus
import importlib
from telethon import  Button
from pyrogram.errors.exceptions import InviteHashExpired , ChannelPrivate ,GroupcallForbidden, AccessTokenExpired, UserDeactivated
from pyrogram.errors.exceptions import SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, SessionRevoked, AuthTokenExpired, AuthKeyDuplicated
import random
import string
# Set up logging
def setup_logger():
    """Configures the logger for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
    )
    return logging.getLogger("pyrogram")


# Initialize the logger
logger = setup_logger()


# Define the cache directory
def setup_cache_directory():
    """Creates the cache directory if it does not exist."""
    cache_dir = f"{ggg}/cache"
    os.makedirs(cache_dir, exist_ok=True)

setup_cache_directory()

# Chat management functions
async def remove_active_chat(user_client, chat_id):
    """Removes a chat from the active list and clears its directory."""
    if chat_id in active[user_client.me.username]:
        active[user_client.me.username].remove(chat_id)
    chat_dir = f"{ggg}/user_{user_client.me.id}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)
    clear_directory(chat_dir)

# Database management functions
def store_user(user_id, timestamp):
    """Stores or updates user information in the database."""
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"timestamp": timestamp}},
        upsert=True
    )

import asyncio
# Chat info and stats functions
from pyrogram.enums import ChatMemberStatus, ChatType

class BotStats(NamedTuple):
    """Container for bot statistics including identification info."""
    bot_id: int
    username: str
    count: int




# Inline keyboard and format selection functions
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Store temporary format selections
stored_format = {}


async def get_chat_info(client: Client, chat_id: int) -> Tuple[Optional[enums.ChatType], Optional[int]]:
    """Retrieves the chat type and member count for a given chat ID.
    Handles potential errors like FloodWait."""
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
    """Collects statistics about a client's interactions, such as private chats, groups,
    and admin status in groups."""
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
                
            chat_type, members_count  = chat_info

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

# Song queue management functions
def currently_playing(user_client, message):
    """Checks if a song is currently playing in a specific chat."""
    song_queue = queues.get(f"dic_{user_client.me.id}")
    try:
        if len(song_queue[message.chat.id]) <=1:
           return False
        return True
    except KeyError:
        return True


# Utility functions

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


# Main user management functions
async def run_user(user_id):
    """Starts and manages both the user bot client and the session client.
    Handles authentication, error management, and setup of necessary handlers."""
    
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

# Global variable management functions
def set_gvar(user_id, key, value):
    """Sets a global variable for a specific user."""
    set_user_data(user_id, key, value)

def get_user_data(user_id, key):
    """Retrieves a global variable for a specific user."""
    user_data = user_sessions.find_one({"user_id": user_id})
    if user_data and key in user_data:
        return user_data[key]
    return None

def set_user_data(user_id, key, value):
    user_sessions.update_one({"user_id": user_id}, {"$set": {key: value}}, upsert=True)

def gvarstatus(user_id, key):
    return get_user_data(user_id, key)
def unset_user_data(user_id, key):
    """Unsets (removes) a global variable for a specific user."""
     user_sessions.update_one({"user_id": user_id}, {"$unset": {key: ''}}, upsert=True)

# File and Mime type management functions
def rename_file(old_name, new_name):
    """Renames a file and logs the operation. Handles common errors such as
    FileNotFound and FileExistsError."""
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
