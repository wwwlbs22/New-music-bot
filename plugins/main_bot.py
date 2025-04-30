import logging
from pyrogram import Client, filters

# Get the logger
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
from functools import wraps
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


# Auth handler


async def remove_active_chat(user_client, chat_id):
    if chat_id in active[user_client.me.username]:
        active[user_client.me.username].remove(chat_id)



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

def single_app_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update):
                user_client = apps.get('app')
                if user_client and user_client.is_connected:
                    if user_client.name != client.name:
                        return await client.stop(block=False)
                    logger.info("Stopping bot")
                return await func(client, update)
        return wrapper
    return decorator



async def maintain_connection(user_id: int, client: Client, is_bot: bool = False, 
                            check_interval: int = 60, retry_delay: int = 60, 
                            max_retries: int = 3) -> None:
    """
    Maintains connection for both bot and session clients with proper validation.
    
    Args:
        user_id: Telegram user ID
        client: The Pyrogram Client instance to maintain
        is_bot: Whether this is a bot client (True) or session client (False)
        check_interval: Time between connection checks in seconds
        retry_delay: Time to wait between retry attempts in seconds
        max_retries: Maximum number of consecutive retry attempts
    """
    consecutive_failures = 0
    
    while True:
        try:
            # First check if user_id exists in clients dict
            if user_id not in clients:
                logger.info(f"User {user_id} not found in clients dictionary. Stopping maintenance.")
                break

            # Get the appropriate client for comparison
            if is_bot:
                stored_client = clients.get(user_id)
                if not stored_client or stored_client.name != client.name:
                    logger.info(f"Bot client mismatch for user {user_id}. Stopping maintenance.")
                    break
            else:
                stored_client = clients.get(f"{user_id}_session")
                if not stored_client or stored_client.name != client.name:
                    logger.info(f"Session client mismatch for user {user_id}. Stopping maintenance.")
                    break

            # Connection check
            try:
                await client.get_me()
                logger.info(f"Connection check successful for {'bot' if is_bot else 'session'} client of user {user_id}")
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures = 0
                logger.info(f"Connection check failed, attempting to reconnect: {str(e)}")
                
                # Stop client
                try:
                    await client.stop(block=False)
                except Exception as e:
                    logger.info(f"Error stopping client: {e}")
                
                await asyncio.sleep(8)
                # Attempt to reconnect
                try:
                    await client.start()
                    # Verify connection
                    await client.get_me()
                    logger.info(f"Successfully reconnected {'bot' if is_bot else 'session'} client for user {user_id}")
                    consecutive_failures = 0
                except Exception as e:
                    raise ConnectionError(f"Failed to verify connection: {e}")

            await asyncio.sleep(check_interval)
            
        except Exception as e:
            if str(e) == 'Client is already connected':
                  continue
            consecutive_failures += 1
            logger.info(f"Connection maintenance failed (attempt {consecutive_failures}) for user {user_id}: {str(e)}")
            
            # If max retries reached, try to notify admins
            if consecutive_failures >= max_retries:
                logger.info(f"Maximum retry attempts ({max_retries}) reached for user {user_id}")
                
                # Try to notify admins
                admin_file = f"{ggg}/admin.txt"
                if os.path.exists(admin_file):
                    with open(admin_file, "r") as file:
                        admin_ids = [int(line.strip()) for line in file.readlines()]
                        for admin_id in admin_ids:
                            try:
                                await app.send_message(
                                    admin_id, 
                                    f"Connection maintenance failed for user {user_id} "
                                    f"({'bot' if is_bot else 'session'} client): {str(e)}"
                                )
                            except Exception:
                                pass
                
                # Try to notify user
                try:
                    await bot.send_message(
                        user_id,
                        f"Connection maintenance failed for your {user_id} "
                        f"{'bot' if is_bot else 'session'} client:\n{str(e)}"
                    )
                except Exception:
                    pass
                
                await asyncio.sleep(retry_delay * 2)
                consecutive_failures = 0
            else:
                await asyncio.sleep(retry_delay)



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


async def check_clients(admin_id, status_msg):
    """Check and maintain all client connections with live updates"""
    report = []
    total_clients = int(len(clients)//2)
    processed = 0

    for user_id, client in list(clients.items()):
        if not str(user_id).isdigit():
            continue

        processed += 1
        emoji_status = ["✅", "✅", "✅"]  # 3 check system
        try:
            if not await is_connected(client):
                # First show checking status
                status_line = f"Client {user_id}: (⟳⟳⟳)"
                await status_msg.edit(f"{status_msg.text}\n{status_line}")
                await asyncio.sleep(0.2)
                
                # Then update with actual status
                emoji_status = await handle_disconnected_client(user_id, client, emoji_status)
                status_line = f"Client {user_id}: ({''.join(emoji_status)})"
            else:
                status_line = f"Client {user_id}: (✅✅✅)"
        
        except Exception as e:
            status_line = f"Client {user_id}: (❌❌❌) [Error: {str(e)}]"

        # Update progress with proper line breaks
        progress = f"{processed}" if total_clients > 0 else ""
        new_line = f"{progress} {status_line}"
        report.append(new_line)
        
        # Edit message with organized formatting
        await status_msg.edit(
            f"{status_msg.text.split('・')[0]}\n" +  # Keep original header
            "\n".join(report)  # New line-separated list
        )
        await asyncio.sleep(0.3)

    completion_text = "✅ Client check completed!"
    return f"\n\n{report}\n\n{completion_text}"


async def handle_disconnected_client(user_id, client, emoji_status):
    """Handle reconnection attempts and modify status emojis"""
    # First check: Normal connect
    try:
        await client.connect()
        if await is_connected(client):
            return emoji_status  # All checks passed
    except Exception:
        emoji_status[0] = "❌"

    # Second check: Restart
    try:
        await client.restart()
        if await is_connected(client):
            return emoji_status
    except Exception:
        emoji_status[1] = "❌"

    # Final check: Full reinitialization
    try:
        await restart_client(user_id)
        return emoji_status  # Keep existing status (some checks failed but operation succeeded)
    except Exception:
        emoji_status[2] = "❌"
        return emoji_status


async def is_connected(client):
    """Check if client is properly connected"""
    try:
        return await client.get_me() is not None
    except Exception as e:
        logger.info(f"Connection check failed: {str(e)}")
        return False




# Add this to your bot startup
    
    # Start Telethon monitor bot


from pyrogram.enums import ChatMemberStatus, ChatType

def get_user_id_by_client(user_id, client):
  for id in clients:
    if id == user_id:
      user_client = clients.get(user_id)
      if user_client.me.id == client.me.id:
          return client.me.id
  return False

def get_owner_id_by_client(client):
    """Returns the user ID associated with the given client object.  Returns None if not found."""
    try:
      for user_id, user_client in clients.items():
        if user_client.me and user_client.me.id == client.me.id:  #Directly compare client objects
            return user_id
    except:
      user_id = owners.get(client.me.id)
      return user_id

from pyrogram import Client, filters
import asyncio
import datetime
from pyrogram import enums





import ast
import traceback
import sys
import inspect
from io import StringIO
import contextlib
import html
import asyncio
import pyrogram
# Message templates with proper HTML escaping
RUNNING = "<b>Eval Expression:</b>\n<pre>{}</pre>\n<b>Running...</b>"
ERROR = "<b>Eval Expression:</b>\n<pre>{}</pre>\n<b>Error:</b>\n<pre>{}</pre>"
SUCCESS = "<b>Eval Expression:</b>\n<pre>{}</pre>\n<b>Success</b>"
RESULT = "<b>Eval Expression:</b>\n<pre>{}</pre>\n<b>Result:</b>\n<pre>{}</pre>"

@Client.on_message(filters.command('eval', prefixes='^'))
async def eval_expression(client, message):
    # Extract the raw text after the command prefix
    if not message.text or len(message.command) < 2:
        await message.reply("Please provide code to evaluate.")
        return

    # Get full text after command
    if " " in message.text:
        full_command = message.text.split(" ", 1)[1]
    else:
        full_command = ""

    # Handle code blocks if present
    if full_command.startswith("```python") and full_command.endswith("```"):
        code = full_command[10:-3].strip()
    elif full_command.startswith("```") and full_command.endswith("```"):
        code = full_command[3:-3].strip()
    else:
        code = full_command

    if not code:
        await message.reply("Please provide code to evaluate.")
        return

    # Send initial "running" message
    response_msg = await message.reply(RUNNING.format(html.escape(code)))

    # Prepare globals and locals for execution
    globals_dict = globals().copy()
    # Add important modules and client objects to globals
    globals_dict.update({
        'client': client,
        'message': message,
        'asyncio': asyncio,
        'inspect': inspect,
    })

    locals_dict = {}

    # Capture stdout and stderr
    stdout = StringIO()
    stderr = StringIO()

    try:
        # Wrap code in async function for execution
        wrapped_code = f"""
async def __async_exec_function():
    __result = None
{textwrap.indent(code, '    ')}
    return __result
"""

        # Execute the code
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(wrapped_code, globals_dict, locals_dict)
            result = await locals_dict['__async_exec_function']()

        # Collect output
        stdout_output = stdout.getvalue()
        stderr_output = stderr.getvalue()

        # Format the final output
        output = ""
        if stdout_output:
            output += f"STDOUT:\n{stdout_output}\n"
        if stderr_output:
            output += f"STDERR:\n{stderr_output}\n"
        if result is not None:
            output += f"RETURN:\n{result}"

        # Check if the output is empty
        if not output:
            try:
                await client.edit_message_text(
                    chat_id=response_msg.chat.id,
                    message_id=response_msg.id,
                    text=SUCCESS.format(html.escape(code))
                )
            except pyrogram.errors.exceptions.bad_request_400.MessageTooLong:
                # Even the code is too long for display
                await handle_long_message(client, response_msg, code, "Success, no output")
            return

        # Try to send the full result
        try:
            await client.edit_message_text(
                chat_id=response_msg.chat.id,
                message_id=response_msg.id,
                text=RESULT.format(html.escape(code), html.escape(output))
            )
        except pyrogram.errors.exceptions.bad_request_400.MessageTooLong:
            # Message is too long, handle it differently
            await handle_long_message(client, response_msg, code, output)

    except Exception as e:
        # Get full traceback for errors
        error_text = traceback.format_exc()
        try:
            await client.edit_message_text(
                chat_id=response_msg.chat.id,
                message_id=response_msg.id,
                text=ERROR.format(html.escape(code), html.escape(error_text))
            )
        except pyrogram.errors.exceptions.bad_request_400.MessageTooLong:
            # Error message is too long
            await handle_long_message(client, response_msg, code, error_text, is_error=True)


async def handle_long_message(client, original_msg, code, output, is_error=False):
    """Handle messages that are too long for Telegram's limits"""

    # First, try to split the message into chunks
    if len(output) < 50000:  # If output is reasonably small, split it
        try:
            # First, edit the original message to indicate multiple parts
            prefix = "<b>Error Output:</b>" if is_error else "<b>Result Output:</b>"
            await client.edit_message_text(
                chat_id=original_msg.chat.id,
                message_id=original_msg.id,
                text=f"<b>Eval Expression:</b>\n<pre>{html.escape(code[:500])}{'...' if len(code) > 500 else ''}</pre>\n{prefix} (Output too long, sending in parts)"
            )

            # Then send output in chunks
            MAX_LENGTH = 4000
            chunks = [output[i:i+MAX_LENGTH] for i in range(0, len(output), MAX_LENGTH)]

            for i, chunk in enumerate(chunks):
                await client.send_message(
                    chat_id=original_msg.chat.id,
                    text=f"<b>Part {i+1}/{len(chunks)}:</b>\n<pre>{html.escape(chunk)}</pre>"
                )

        except Exception as chunk_error:
            # If chunking fails, fall back to file upload
            await upload_as_file(client, original_msg, code, output, is_error)
    else:
        # If output is very large, go straight to file upload
        await upload_as_file(client, original_msg, code, output, is_error)

async def upload_as_file(client, original_msg, code, output, is_error=False):
    """Upload the output as a text file"""
    try:
        # Create a temporary file
        file_name = f"eval_{'error' if is_error else 'output'}_{int(time.time())}.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(f"Eval Expression:\n{code}\n\n")
            file.write(f"{'Error' if is_error else 'Result'}:\n{output}")

        # Edit message to indicate file upload
        await client.edit_message_text(
            chat_id=original_msg.chat.id,
            message_id=original_msg.id,
            text=f"<b>Eval Expression:</b>\n<pre>{html.escape(code[:500])}{'...' if len(code) > 500 else ''}</pre>\n<b>{'Error' if is_error else 'Result'} too large, uploading as file...</b>"
        )

        # Send the file
        await client.send_document(
            chat_id=original_msg.chat.id,
            document=file_name,
            caption=f"{'Error' if is_error else 'Result'} output for eval command"
        )

        # Clean up
        os.remove(file_name)

    except Exception as file_error:
        # Last resort if everything fails
        await client.edit_message_text(
            chat_id=original_msg.chat.id,
            message_id=original_msg.id,
            text=f"<b>Eval Expression:</b>\n<pre>{html.escape(code[:500])}{'...' if len(code) > 500 else ''}</pre>\n<b>Output too large to display and file upload failed:</b> {str(file_error)}"
        )


from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Store temporary format selections
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import math

# Store temporary format selections
stored_format = {}

def get_format_keyboard(current_format: int, total_styles: int):
    """Generate format selection keyboard with current selection marked"""
    keyboard = []
    buttons_per_row = 4  # Number of buttons per row
    
    # Calculate number of full rows and remaining buttons
    total_rows = math.ceil(total_styles / buttons_per_row)
    
    for row in range(total_rows):
        button_row = []
        start_num = row * buttons_per_row + 1
        
        # Calculate end number for this row
        end_num = min(start_num + buttons_per_row - 1, total_styles)
        
        for num in range(start_num, end_num + 1):
            # Mark selected format with brackets
            text = f"[{num}]" if num == current_format else str(num)
            button_row.append(
                InlineKeyboardButton(text, callback_data=f"format_{num}")
            )
            
        if button_row:  # Only add non-empty rows
            keyboard.append(button_row)
    
    # Add navigation and done buttons in the last row
    nav_row = []
    if total_styles > buttons_per_row:
        nav_row.extend([
            InlineKeyboardButton("⬅️ Prev", callback_data="format_prev"),
            InlineKeyboardButton("Next ➡️", callback_data="format_next")
        ])
    nav_row.append(InlineKeyboardButton("Done ✅", callback_data="format_done"))
    keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(keyboard)

def format_message(format_num: int):
    """Generate preview message showing current format"""
    queue_preview = queue_styles[format_num].format(
        superscript("MUSIC"), 
        superscript("Sample Title"), 
        "3:45", 
        "1"
    )
    play_preview = play_styles[format_num].format(
        superscript("MUSIC"), 
        superscript("Sample Title"), 
        "3:45", 
        "User"
    )

    return (
        f"Format Style #{format_num}\n"
        "───────────────\n"
        f"<blockquote>Queue Format:</blockquote>\n{queue_preview}\n\n"
        f"<blockquote>Play Format:</blockquote>\n{play_preview}\n\n"
    )


from typing import Dict, List, Optional, Tuple, NamedTuple
from pyrogram import Client, filters, enums
from pyrogram.types import Message, Chat
import asyncio

class BotStats(NamedTuple):
    """Container for bot statistics including identification info."""
    bot_id: int
    username: str
    count: int


async def get_chat_type(client: Client, chat_id: int) -> Optional[enums.ChatType]:
    """Get chat type safely with error handling."""
    try:
        chat = await client.get_chat(chat_id)
        return chat.type
    except FloodWait as e:
        logger.info(f"Rate limited! Sleeping for {e.value} seconds.")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.info(f"Error getting chat type for {chat_id}: {str(e)}")
        return None

async def get_client_stats(client: Client) -> Optional[Dict[str, int]]:
    """Gets statistics for a single client instance."""
    stats = {
        'private': 0,
        'groups': 0,
        'supergroups': 0,
        'channels': 0,
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
        chat_types = await asyncio.gather(
            *[get_chat_type(client, chat_id) for chat_id in batch],
            return_exceptions=True
        )
        
        for j, chat_type in enumerate(chat_types):
            if not isinstance(chat_type, enums.ChatType):
                continue

            if chat_type == enums.ChatType.PRIVATE:
                stats['private'] += 1
            elif chat_type == enums.ChatType.GROUP:
                stats['groups'] += 1
            elif chat_type == enums.ChatType.SUPERGROUP:
                stats['supergroups'] += 1
                try:
                    member = await client.get_chat_member(batch[j], client.me.id)
                    if member.status in (
                        enums.ChatMemberStatus.OWNER,
                        enums.ChatMemberStatus.ADMINISTRATOR
                    ):
                        stats['admin'] += 1
                except Exception as e:
                    logger.info(f"Error checking admin status in {batch[j]}: {str(e)}")
            elif chat_type == enums.ChatType.CHANNEL:
                stats['channels'] += 1

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

async def hd_stream_closed_kicked(client, update):
   logger.info(update)
   session_client = client._mtproto
   user_client = linkage.get(session_client.me.id)
   song_queue_key = f"dic_{user_client.me.id}"
   song_queue = queues.get(song_queue_key)
   try:
      await remove_active_chat(user_client, update.chat_id)
      song_queue[update.chat_id].clear()
      playing[update.chat_id].clear()
   except Exception as e:
      logger.info(e)

async def end(client, update):
  session_client = client._mtproto
  user_client = linkage.get(session_client.me.id)
  try:
        collection.update_one(
            {"user_id": user_client.me.id},
            {"$push": {'dates': datetime.datetime.now()}},
            upsert=True
        )
  except Exception as e:
        logger.info(f"Error saving playtime: {e}")

  if user_client is None:
    logger.info(f"User client not found for session: {session_client}")
    return

  song_queue_key = f"dic_{user_client.me.id}"
  logger.info(f"Song queue key: {song_queue_key}")
  song_queue = queues.get(song_queue_key)

  if song_queue is None:
    logger.info(f"Song queue not found for user: {user_client.me.id}")
    await client.leave_call(update.chat_id)
    await remove_active_chat(user_client, update.chat_id)
    return playing[update.chat_id].clear()

  try:
    if update.chat_id in song_queue and song_queue[update.chat_id]:
      next_song = song_queue[update.chat_id].pop(0)
      playing[update.chat_id] = next_song
      await join_call(next_song['message'], next_song['title'],
next_song['session'], next_song['yt_link'], next_song['chat'], next_song['by'], next_song['duration'], next_song['mode'], next_song['thumb'])
    else:
      logger.info(f"Song queue for chat {update.chat_id} is empty.")
      await client.leave_call(update.chat_id)
      await remove_active_chat(user_client, update.chat_id)
      playing[update.chat_id].clear()
  except Exception as e:
    logger.info(f"Error in end function: {e}")


from yt_dlp import YoutubeDL

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
async def join_call(message, title, user_client, youtube_link, chat, by, duration, mode, thumb):
    audio_flags = MediaStream.Flags.IGNORE if mode == "audio" else None
    song_queue = queues.get(f"dic_{user_client.me.id}")
    position = len(song_queue.get(message.chat.id)) if song_queue.get(message.chat.id) else 0

    try:

        bot_username = user_client.me.username
        session_client_id = connector.get(bot_username)

        if session_client_id is None:
            await message.edit("No session client connected. Please authorize first with /host.")
            return await remove_active_chat(user_client, message.chat.id)

        # Retrieve the session client from the clients dictionary
        session_client = clients.get(f"{session_client_id}_session")
        if not session_client:
            await message.edit("Session client not found. Please re-authorize with /host.")
            return await remove_active_chat(user_client, message.chat.id)

        call_py = songs_client.get(session_client.me.id)
        await call_py.play(
            chat.id,
            MediaStream(
                youtube_link,
                AudioQuality.STUDIO,
                VideoQuality.HD_720p,
                video_flags=audio_flags,
                ytdlp_parameters='--cookies cookies.txt',
            ),
        )
        played[message.chat.id] =time.time()
        owner_id = get_owner_id_by_client(user_client)
        # Creating the inline keyboard with buttons arranged in two rows
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="▷", callback_data="resume"),
                InlineKeyboardButton(text="II", callback_data="pause"),
                InlineKeyboardButton(text="‣‣I" if position <1 else f"‣‣I({position})", callback_data="skip"),
                InlineKeyboardButton(text="▢", callback_data="end"),
            ],
        [                                                                                           InlineKeyboardButton(
                text=f"{smallcap('Add to group')}", url=f"https://t.me/{user_client.me.username}?startgroup=true"
            ),
            InlineKeyboardButton(
                        text=f"{smallcap('ᴜᴘᴅᴀᴛᴇs')}", url= gvarstatus(owner_id, "support") or "https://t.me/nub_coder_updates"
            )
        ],
        ])
        sent_message = await user_client.send_photo(
            message.chat.id, thumb, play_styles[int(gvarstatus(owner_id, "format") or 11)].format(superscript(mode), 
f"[{superscript(title)}](https://t.me/{user_client.me.username}?start=vidid_{extract_video_id(youtube_link)})", superscript(duration), by.mention()),
            reply_markup=keyboard        )
        asyncio.create_task(autoleave_vc(user_client, call_py, sent_message, duration))
        asyncio.create_task(update_progress_button(sent_message, duration, call_py))
        try:
            await message.delete()
        except Exception as e:
            logger.info(e)
    except NoActiveGroupCall:
        await user_client.send_message(chat.id, "ERROR: No active group calls")
        return await remove_active_chat(user_client, message.chat.id)
    except GroupcallForbidden:
        await user_client.send_message(chat.id, "ERROR: Telegram internal server error")
        return await remove_active_chat(user_client, message.chat.id)
    except Exception as e:
        await user_client.send_message(chat.id, f"ERROR: {e}")
        return await remove_active_chat(user_client, message.chat.id)

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




from telethon import events
import os



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




def is_premium(user_id):
    current_time = int(time.time())
    user_data = collection.find_one({"user_id": user_id})

    if user_data:
        stored_time = user_data.get("timestamp")
        if not stored_time:
          return True
        time_difference =  stored_time - current_time
        if time_difference > 0:
            return True
        return False
    return True




def is_dremium(user_id):
    current_time = int(time.time())
    user_data = collection.find_one({"user_id": user_id})
    if user_data:
        stored_time = user_data.get("timestamp")
        premium_by = user_data.get("premium_by")
        if not stored_time:
          storre_user(user_id, int(time.time()) + (2 * 24 * 60 * 60))
          return False
        if not premium_by:
            collection.update_one(
                {"user_id": user_id},
                {"$set": {"premium_by": "TRIAL"}},
                upsert=True
            )
        time_difference =  stored_time - current_time
        if time_difference > 0:
             return True
        return False
    return False




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






from telethon import events, Button
from telethon.tl.types import User


from telethon import events
import os
import sys




create_custom_filter = filters.create(lambda _, __, message: any(m.is_self for m in (message.new_chat_members if message.new_chat_members else [])))








from telethon.tl.types import DocumentAttributeImageSize




# Run the main function

# Entry point for the asyncio program

    #

import time
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
