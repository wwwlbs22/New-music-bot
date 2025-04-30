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
def generate_client_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

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




def is_admin(user_id):
    admin_file = f"{ggg}/admin.txt"
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if user_id in admin_ids:
                return True

from telethon import TelegramClient, events
import asyncio
import traceback
import os



from telethon import events
import subprocess
import os

# This function will execute git commands and return the output
import subprocess

async def execute_git_commands():
    commands = [
        "git reset --hard",
        "git stash",
        "git pull",
        "pip install -r requirements.txt"
    ]

    results = []
    for cmd in commands:
        try:
            # Execute the command and capture output
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # Format the result
            if process.returncode == 0:
                if stdout.strip():
                    results.append(f"$ {cmd}\n{stdout}")
                else:
                    results.append(f"$ {cmd}\n(Command executed successfully)")
            else:
                results.append(f"$ {cmd}\nError: {stderr}")

        except Exception as e:
            results.append(f"$ {cmd}\nException: {str(e)}")

    return "\n\n".join(results)


@bot.on(events.NewMessage(pattern=r'^/pull$'))
async def pull_handler(event):
    user_id = event.sender_id
    # Check if the user is an admin by comparing their user ID with the ones in >
    admin_file = f"{ggg}/admin.txt"
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if user_id not in admin_ids:
                return
    # Send a message to indicate the pull is starting
    message = await event.respond("🔄 Executing git commands...")
    
    # Execute the git commands
    result = await execute_git_commands()
    
    # Edit the original message with the results
    await message.edit(f"```\n{result}\n```")

# Example of how to register this handler with your bot


async def is_connected(client):
    """Check if client is properly connected"""
    try:
        return await client.get_me() is not None
    except Exception as e:
        logger.info(f"Connection check failed: {str(e)}")
        return False



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

def get_format_keyboard(current_format: int):
    """Generate format selection keyboard with current selection marked"""
    keyboard = []  # Create 4 rows of buttons

    # Create buttons for numbers 1 to 15
    for i in range(0, 16, 4):
        row = []
        for j in range(1, 5):
            num = i + j
            # Mark selected format with brackets
            text = f"[{num}]" if num == current_format else str(num)
            row.append(InlineKeyboardButton(text, callback_data=f"format_{num}"))
        keyboard.append(row)

    # Add the last button for '16' and 'Done' in the last row
    keyboard.append([InlineKeyboardButton("Done ✅", callback_data="format_done")])

    return InlineKeyboardMarkup(keyboard)

def format_message(format_num: int):
    """Generate preview message showing current format"""
    queue_preview = queue_styles[format_num].format(superscript("MUSIC"), superscript("Sample Title"), "3:45", "1")
    play_preview = play_styles[format_num].format(superscript("MUSIC"), superscript("Sample Title"), "3:45", "User")
    
    return (
        "Selected format:\n"
        "───────────────\n"
        f"<blockquote>Queue Format:</blockquote>\n{queue_preview}\n\n"
        f"<blockquote>Play Format:</blockquote>\n{play_preview}"
    )



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

# Add to existing imports

# Add new handler for tracking played songs




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



def reload_all_plugins():
    # Reload plugins from the current directory
    current_dir_plugins = ['tools', 'fonts']
    for plugin_name in current_dir_plugins:
        try:
            module = importlib.import_module(plugin_name)
            importlib.reload(module)
            logger.info(f"Reloaded plugin: {plugin_name}")
        except Exception as e:
            logger.info(f"Failed to reload plugin {plugin_name}: {e}")

    # Original plugin directory reload
    plugin_dir = "plugins"
    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and not file.startswith("*"):  # Ignore *init_>
            module_name = file[:-3]  # Remove .py extension
            try:
                module = importlib.import_module(f"{plugin_dir}.{module_name}")
                importlib.reload(module)  # Reload the module
                logger.info(f"Reloaded plugin: {module_name}")
            except Exception as e:
                logger.info(f"Failed to reload plugin {module_name}: {e}")


def reload_config():
    # Reload plugins from the current directory
    current_dir_plugins = ['config']
    for plugin_name in current_dir_plugins:
        try:
            module = importlib.import_module(plugin_name)
            importlib.reload(module)
            logger.info(f"Reloaded plugin: {plugin_name}")
        except Exception as e:
            logger.info(f"Failed to reload plugin {plugin_name}: {e}")

    # Original plugin directory reload

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





async def run_user_client(user_id):
    reload_all_plugins()
    user_data = user_sessions.find_one({"user_id": user_id})
    user_session_string = user_data.get("string_session")
    user_bot_token = user_data.get("bot_token")
    drem = is_dremium(user_id)
    prem = is_premium(user_id)
    if not prem:
        return
    await asyncio.sleep(delay=random.randint(5, 200))
    try:
        # Create and start the user client using the bot token
        user_client = Client(
            f"{generate_client_id()}",
            api_id=API_ID,
            api_hash=API_HASH,workers=5,
            bot_token=user_bot_token, 
plugins=dict(root="plugins",include=["bots"]),in_memory=True,
    sleep_threshold=30,  # Increased from default 10
        )
        await user_client.start()
        client_name = f"{user_client.me.first_name} {user_client.me.last_name or ''}".strip()
        logger.info(f"Bot authorized successfully! 🎉 Authorized as: {client_name}")
        clients[user_id] = user_client
        owners[user_client.me.id] = user_id
        
    except (SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, SessionRevoked, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired, UserDeactivated):
        user_sessions.delete_one({"user_id": user_id})
        if user_id in clients:
            clients.pop(user_id)
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass
    except Exception as e:
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass

    try:
        # Create and start the session client
        session_client = Client(
            f"user_{user_id}_session",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=user_session_string,
in_memory=True, no_updates=True, sleep_threshold=32)
        auth = await session_client.connect()
        if not auth:
            try:
                      user_client = clients.get(user_id)
                      await user_client.stop(block=False)
            except:
                    pass
            logger.info(f"Client is not authorized for {user_id}. Please authorize first.")
            await session_client.stop(block=False)
            user_sessions.delete_one({"user_id": user_id})
            return
        await session_client.disconnect()
        call_py = PyTgCalls(session_client)
        clients[f"{user_id}_session"] = session_client
        call_py.add_handler(end, call_filters.stream_end())
        call_py.add_handler(hd_stream_closed_kicked, call_filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT) | call_filters.chat_update(ChatUpdate.Status.KICKED))
        await call_py.start()
        await asyncio.sleep(2)
        songs_client[session_client.me.id] = call_py
        client_name = f'{session_client.me.first_name if session_client.me else ""} {session_client.me.last_name or "" if session_client.me else ""}'.strip()
        logger.info(f"Username authorized successfully! 🎉 Authorized as: {client_name}")
        try:
                   await session_client.join_chat("sheepra_cutie")
                   await session_client.join_chat("nub_coder_s")
                   await session_client.join_chat("nub_coder_updates")
        except:
                   pass
        # Add to connector dictionary
        connector[user_client.me.username] = user_id
        queues[f"dic_{user_client.me.id}"] = {}
        linkage[session_client.me.id] = user_client
        active[user_client.me.username] = []
        
        # Add play handler to user_client using MessageHandler
    except AttributeError:
        logger.info("The object is None; it doesn't have an 'id' attribute.")
    except (SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered, SessionRevoked, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired, UserDeactivated) as e:
        try:
                      user_client = clients.get(user_id)
                      await user_client.stop(block=False)
        except:
                    pass
        user_sessions.delete_one({"user_id": user_id})
        if user_id in clients:
            clients.pop(user_id)
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass
    except Exception as e:
        logger.info(e)
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
            with open(admin_file, "r") as file:
                admin_ids = [int(line.strip()) for line in file.readlines()]
                for admin_id in admin_ids:
                    try:
                        await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")
                    except:
                        pass
        try:
                             await bot.send_message(user_id,f"Error starting your client:\n{e}")
        except:
                                pass




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
