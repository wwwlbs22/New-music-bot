from pyrogram.errors import StickersetInvalid, YouBlockedUser
import logging
from pyrogram import Client, filters
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
# Get the logger
logger = logging.getLogger("pyrogram")
import inspect
import sys
import asyncio
import os
from tools import *
from fonts import *
from pyrogram import enums
from pyrogram import Client, filters,emoji
from pytgcalls.types import ChatUpdate
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors.exceptions import InviteHashExpired , ChannelPrivate ,GroupcallForbidden, UserBlocked, PeerIdInvalid, MessageDeleteForbidden
from pytgcalls.exceptions import NotInCallError
from config import *
import time
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAudio
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
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
from telethon import TelegramClient, events
import yt_dlp
import time

from functools import wraps
from pyrogram.types import CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus


def retry(max_retries=3, initial_delay=5, backoff=2, exceptions=(FloodWait, OSError)):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    wait = e.value if isinstance(e, FloodWait) else delay
                    logger.info(f"Retry {retries}/{max_retries} for {func.__name__} after {wait}s")
                    await asyncio.sleep(wait)
                    delay *= backoff
                except Exception as e:
                    logger.info(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise
            return await func(*args, **kwargs)
        return wrapper
    return decorator


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


def premium_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(user_client, update):
            try:
                owner_id = get_owner_id_by_client(user_client)
                
                if not is_premium(owner_id):
                    try:
                        owner = await user_client.get_users(owner_id)
                        owner_mention = f"@{owner.username}" if owner.username else f"[{owner.first_name}](tg://user?id={owner_id})"
                    except Exception:
                        owner_mention = f"[Owner](tg://user?id={owner_id})"
                    
                    await update.reply(f"⚠️ Trial period ended. Please contact {owner_mention} to restart the bot.")
                    
                    return await stop_user(owner_id)
                
                return await func(user_client, update)
            
            except Exception as e:
                return
        return wrapper
    return decorator

def admin_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(user_client, update):
            try:
                # Handle both callback query and regular message
                if isinstance(update, CallbackQuery):
                    chat_id = update.message.chat.id
                    reply_id = update.message.id
                    user_id = update.from_user.id if update.from_user else None
                    command = update.data
                else:
                    chat_id = update.chat.id
                    reply_id = update.id
                    user_id = update.from_user.id if update.from_user else None
                    command = update.command[0].lower()
                    
                # Check if user is trying to skip their own song
                is_song_owner = False
                if isinstance(update, CallbackQuery):
                    # For callback queries, check using update.message.chat
                    if update.message.chat.id in playing and playing[update.message.chat.id]:
                        current_song = playing[update.message.chat.id]
                        if user_id and command in ["skip", "cskip"] and current_song["by"].id == user_id:
                            is_song_owner = True
                else:
                    # For regular messages
                    if update.chat.id in playing and playing[update.chat.id]:
                        current_song = playing[update.chat.id]
                        if user_id and command in ["skip", "cskip"] and current_song["by"].id == user_id:
                            is_song_owner = True
                
                # Continue with original authorization checks if not song owner
                if not is_song_owner:
                    user_data = user_sessions.find_one({"user_id": get_owner_id_by_client(user_client)})
                    sudoers = user_data.get("SUDOERS", [])
                    
                    # Check admin status
                    is_admin = False
                    admin_file = f"{ggg}/admin.txt"
                    if os.path.exists(admin_file):
                        with open(admin_file, "r") as file:
                            admin_ids = [int(line.strip()) for line in file.readlines()]
                            is_admin = user_id in admin_ids
                    
                    # Check permissions
                    is_auth_user = False
                    auth_users = user_data.get('auth_users', {})
                    if isinstance(auth_users, dict) and str(chat_id) in auth_users:
                        is_auth_user = user_id in auth_users[str(chat_id)]
                        
                    if not isinstance(update, CallbackQuery):
                        if command and str(command).endswith('del'):
                            is_auth_user = False
                    
                    is_authorized = (
                        is_admin or get_user_id_by_client(user_id, user_client) or user_id in sudoers or is_auth_user)
                    
                    if not user_id:
                        linked_chat = await user_client.get_chat(chat_id)
                        if linked_chat.linked_chat and update.sender_chat.id == linked_chat.linked_chat.id:
                            return await func(user_client, update)
                        await update.reply("⚠️ Cannot verify admin status from unknown user.", reply_to_message_id=reply_id)
                        return
                    
                    chat_member = await user_client.get_chat_member(chat_id, user_id)
                    if not (chat_member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR) or is_authorized):
                        if isinstance(update, CallbackQuery):
                            await update.answer("⚠️ This action is restricted to admins only.", show_alert=True)
                        else:
                            await update.reply("⚠️ This command is restricted to admins only.", reply_to_message_id=reply_id)
                        return
                
                # If we get here, the user is either an admin or the song owner
                return await func(user_client, update)
                
            except Exception as e:
                error_msg = f"Error checking admin status: {str(e)}"
                return logger.info(error_msg)
        return wrapper
    return decorator


def single_client_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update):
                user_client = clients.get(get_owner_id_by_client(client))
                if user_client:
                    if user_client.name == client.name:
                        return await func(client, update)
                    logger.info("Stopping bot")
                return await client.stop(block=False)
        return wrapper
    return decorator
# Define the main bot client (app)
create_custom_filter = filters.create(lambda _, __, message: any(m.is_self for m in (message.new_chat_members if message.new_chat_members else [])))

# Auth handler

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



from functools import wraps
from typing import Tuple, Optional

# Example usage:
async def is_active_chat(user_client,chat_id):
    if chat_id not in active[user_client.me.username]:
        return False
    else:
        return True


async def add_active_chat(user_client,chat_id):
    if chat_id not in active[user_client.me.username]:
        active[user_client.me.username].append(chat_id)



@Client.on_message(filters.command("ac"))
@retry()

async def active_chats(client, message):
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
        is_admin or
        get_user_id_by_client(user_id, client) or
        (user_id in sudoers and premium_by == "PAID")
    )

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER/SUDOER'S COMMAND...**")

    active_chats_list = active.get(client.me.username, [])
    if active_chats_list:
        titles = []
        for chat_id in active_chats_list:
            try:
                chat = await client.get_chat(chat_id)
                title = f"• {chat.title}"
            except Exception as e:
                title = f"• [ID: {chat_id}] (Failed to fetch title)"
            titles.append(title)
        
        titles_str = '\n'.join(titles)
        reply_text = (
            f"<b>Active group calls:</b>\n"
            f"<blockquote expandable>{titles_str}</blockquote>\n"
            f"<b>Total:</b> {len(active_chats_list)}"
        )
    else:
        reply_text = "<b>Active Voice Chats:</b>\n<blockquote>No active group calls</blockquote>"

    await message.reply_text(reply_text)


async def remove_active_chat(user_client, chat_id):
    if chat_id in active[user_client.me.username]:
        active[user_client.me.username].remove(chat_id)
    chat_dir = f"{ggg}/user_{user_client.me.id}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)
    clear_directory(chat_dir)



@Client.on_message(filters.command("tagall") & filters.group)
@retry()

@admin_only()
async def mentionall(client, message):
    await message.delete()
    chat_id = message.chat.id
    direp = message.reply_to_message
    args = get_arg(message)
    if not direp and not args:
        return await message.reply("**Give a message or reply to any message!**")

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in client.get_chat_members(chat_id):
        if not chat_id in spam_chats:
            break
        usrnum += 1
        usrtxt += f"{usr.user.mention()}, "
        if usrnum == 5:
            if args:
                txt = f"<blockquote>{args}\n\n{usrtxt}</blockquote>"
                await client.send_message(chat_id, txt)
            elif direp:
                await direp.reply(f"<blockquote>{usrtxt}</blockquote>")
            await asyncio.sleep(5)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@Client.on_message(filters.command(["seek", "seekback"]))
@retry()

@admin_only()
async def seek_handler_func(user_client, message):
    try:
        await message.delete()
    except:
        pass
    # Check if user is banned
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})
    if message.from_user.id in busers:
        return

    try:
        # Get seek value from command
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await user_client.send_message(
                message.chat.id,
                "❌ Please specify the seek time in seconds.\nUsage: /seek (seconds)"
            )
            return

        try:
            seek_value = int(command_parts[1])
            if seek_value < 0:
                await user_client.send_message(
                    message.chat.id,
                    f"{upper_mono('❌ Seek time cannot be negative!')}"
                )
                return
        except ValueError:
            await user_client.send_message(
                message.chat.id,
                f"{upper_mono('❌ Please provide a valid number of seconds!')}"
            )
            return

        # Check if there's a song playing
        if message.chat.id in playing and playing[message.chat.id]:
            current_song = playing[message.chat.id]
            duration_str = str(current_song['duration'])

            # Convert HH:MM:SS to total seconds
            duration_seconds = sum(
                int(x) * 60 ** i
                for i, x in enumerate(reversed(duration_str.split(":")))
            )

            # Get session client
            bot_username = user_client.me.username
            session_client_id = connector.get(bot_username)
            if session_client_id is None:
                await user_client.send_message(
                    message.chat.id,
                    f"{upper_mono('No session client connected. Please authorize first with /host.')}"
                )
                return await remove_active_chat(user_client, message.chat.id)

            # Get call client
            session_client = clients.get(f"{session_client_id}_session")
            call_py = songs_client.get(session_client.me.id)

            # Check if bot is actually streaming by fetching elapsed time
            if message.chat.id not in played:
                await user_client.send_message(
                    message.chat.id,
                    f"{upper_mono('Assistant is not streaming anything!')}"
                )
                return

            played_in_seconds = int(time.time() - played[message.chat.id])

            # Check seek boundaries based on command
            command = command_parts[0].lower()
            if command == "/seek":
                # Check if seeking forward would exceed remaining duration
                remaining_duration = duration_seconds - played_in_seconds
                if seek_value > remaining_duration:
                    await user_client.send_message(
                        message.chat.id,
                        f"{upper_mono('❌ Cannot seek beyond the remaining duration!')}"
                    )
                    return
                total_seek = seek_value + played_in_seconds
            else:  # seekback
                # Check if seeking back would exceed played duration
                if seek_value > played_in_seconds:
                    await user_client.send_message(
                        message.chat.id,
                        f"{upper_mono('❌ Cannot seek back more than the played duration!')}"
                    )
                    return
                total_seek = played_in_seconds - seek_value

            # Set audio flags based on mode
            mode = current_song['mode']
            audio_flags = MediaStream.Flags.IGNORE if mode == "audio" else None

            # Seek to specified position
            to_seek = format_duration(total_seek)
            await call_py.play(
                message.chat.id,
                MediaStream(
                    current_song['yt_link'],
                    AudioQuality.STUDIO,
                    VideoQuality.HD_720p,
                    video_flags=audio_flags,
                    ytdlp_parameters='--cookies-from-browser chrome',
                    ffmpeg_parameters=f"-ss {to_seek} -to {duration_str}"
                ),
            )

            # Update played time based on command
            if command == "/seek":
                played[message.chat.id] -= seek_value
            else:  # seekback
                played[message.chat.id] += seek_value

            await user_client.send_message(
                message.chat.id,
                f"{upper_mono(f'Seeked to {to_seek}!')}\n\nʙʏ: {message.from_user.mention()}"
            )
        else:
            await user_client.send_message(
                message.chat.id,
                f"{upper_mono('Assistant is not streaming anything!')}"
            )
    except Exception as e:
        await user_client.send_message(
            message.chat.id,
            f"{upper_mono('❌ An error occurred:')} {str(e)}"
        )


@Client.on_message(filters.command("cancel") & filters.group)
@retry()

@admin_only()
async def cancel_spam(client, message):
    if not message.chat.id in spam_chats:
        return await message.reply("**Looks like there is no tagall here.**")
    else:
        try:
            spam_chats.remove(message.chat.id)
        except:
            pass
        return await message.reply("**Dismissing Mention.**")

@Client.on_message(filters.command("del") & filters.group)
@retry()

@admin_only()
async def delete_message_handler(client, message):
    # Check if the message is a reply
    if message.reply_to_message:
        try:
            # Delete the replied message
            await message.reply_to_message.delete()
            # Optionally, delete the command message as well
            await message.delete()
        except MessageDeleteForbidden:
              pass
        except Exception as e:
            await message.reply(f"Error deleting message: {str(e)}")
    else:
        await message.reply("**Please reply to a message to delete it.**")


@Client.on_message(filters.command("auth") & filters.group)
@retry()

@admin_only()
async def auth_user(client, message):
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    user_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = user_data.get("SUDOERS", [])
    
    # Check if user is admin

    
    chat_id = message.chat.id
    auth_users = user_data.get('auth_users', {})
    
    # Convert auth_users to dict if it's not already (for backward compatibility)
    if not isinstance(auth_users, dict):
        auth_users = {}
    
    # Initialize empty list for chat_id if it doesn't exist
    if str(chat_id) not in auth_users:
        auth_users[str(chat_id)] = []
    
    if message.reply_to_message:
        replied_message = message.reply_to_message
        if replied_message.from_user:
            replied_user_id = replied_message.from_user.id
            
            # Check if replied user is admin
            if os.path.exists(admin_file):
                with open(admin_file, "r") as file:
                    admin_ids = [int(line.strip()) for line in file.readlines()]
                    if replied_user_id in admin_ids:
                        return await message.reply(f"**Owner is already authorized everywhere.**")
            
            # Check if user can be authorized
            if (replied_user_id != message.chat.id and 
                not replied_message.from_user.is_self and 
                not get_user_id_by_client(replied_user_id, client)):
                
                # Check if user is already authorized in this chat
                if replied_user_id not in auth_users[str(chat_id)]:
                    auth_users[str(chat_id)].append(replied_user_id)
                    user_sessions.update_one(
                        {"user_id": get_owner_id_by_client(client)},
                        {"$set": {'auth_users': auth_users}},
                        upsert=True
                    )
                    await message.reply(f"User {replied_user_id} has been authorized in this chat.")
                else:
                    await message.reply(f"User {replied_user_id} is already authorized in this chat.")
            else:
                await message.reply("You cannot authorize yourself or an anonymous user.")
        else:
            await message.reply("The replied message is not from a user.")
    else:
        # If not a reply, check if a user ID is provided in the command
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                user_id_to_auth = int(command_parts[1])
                # Check if user is already authorized in this chat
                if user_id_to_auth not in auth_users[str(chat_id)]:
                    auth_users[str(chat_id)].append(user_id_to_auth)
                    user_sessions.update_one(
                        {"user_id": get_owner_id_by_client(client)},
                        {"$set": {'auth_users': auth_users}},
                        upsert=True
                    )
                    await message.reply(f"User {user_id_to_auth} has been authorized in this chat.")
                else:
                    await message.reply(f"User {user_id_to_auth} is already authorized in this chat.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")

@Client.on_message(filters.command("unauth") & filters.group)
@retry()

@admin_only()
async def unauth_user(client, message):
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    user_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})

    chat_id = message.chat.id
    auth_users = user_data.get('auth_users', {})
    
    # Convert auth_users to dict if it's not already (for backward compatibility)
    if not isinstance(auth_users, dict):
        auth_users = {}
    
    # Initialize empty list for chat_id if it doesn't exist
    if str(chat_id) not in auth_users:
        auth_users[str(chat_id)] = []
    
    if message.reply_to_message:
        replied_message = message.reply_to_message
        if replied_message.from_user:
            replied_user_id = replied_message.from_user.id
            
            # Check if replied user is admin
            if os.path.exists(admin_file):
                with open(admin_file, "r") as file:
                    admin_ids = [int(line.strip()) for line in file.readlines()]
                    if replied_user_id in admin_ids:
                        return await message.reply(f"**You can't remove authorization from owner.**")
            
            # Check if user can be unauthorized
            if replied_user_id in auth_users[str(chat_id)]:
                auth_users[str(chat_id)].remove(replied_user_id)
                user_sessions.update_one(
                    {"user_id": get_owner_id_by_client(client)},
                    {"$set": {'auth_users': auth_users}},
                    upsert=True
                )
                await message.reply(f"User {replied_user_id} has been removed from authorized users in this chat.")
            else:
                await message.reply(f"User {replied_user_id} is not authorized in this chat.")
        else:
            await message.reply("The replied message is not from a user.")
    else:
        # If not a reply, check if a user ID is provided in the command
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                user_id_to_unauth = int(command_parts[1])
                # Check if user is authorized in this chat
                if user_id_to_unauth in auth_users[str(chat_id)]:
                    auth_users[str(chat_id)].remove(user_id_to_unauth)
                    user_sessions.update_one(
                        {"user_id": get_owner_id_by_client(client)},
                        {"$set": {'auth_users': auth_users}},
                        upsert=True
                    )
                    await message.reply(f"User {user_id_to_unauth} has been removed from authorized users in this chat.")
                else:
                    await message.reply(f"User {user_id_to_unauth} is not authorized in this chat.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")

@Client.on_message(filters.command("block"))
@retry()

async def block_user(client, message):
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
        is_admin or
        get_user_id_by_client(user_id, client) or
        (user_id in sudoers and premium_by == "PAID")
    )

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER/SUDOER'S COMMAND...**")

    # Check if the message is a reply


    user_data = collection.find_one({"user_id": client.me.id})
    busers = user_data.get('busers', {}) if user_data else []
    if message.reply_to_message:
        replied_message = message.reply_to_message
        # If the replied message is from a user (and not from the bot itself)
        if replied_message.from_user:
            replied_user_id = replied_message.from_user.id
            admin_file = f"{ggg}/admin.txt"
            if os.path.exists(admin_file):
               with open(admin_file, "r") as file:
                 admin_ids = [int(line.strip()) for line in file.readlines()]
                 if replied_user_id in admin_ids:
                     return await message.reply(f"**MF\n\nYou can't block my owner.**")
            # Check if the replied user is the same as the current chat (group) id
            if replied_user_id != message.chat.id and not replied_message.from_user.is_self and not get_user_id_by_client(replied_user_id, client):
                if not replied_user_id in busers:
                    collection.update_one({"user_id": client.me.id},
                                        {"$push": {'busers': replied_user_id}},
                                        upsert=True)
                else:
                   return await message.reply(f"User {replied_user_id} already in the blocklist.")
                await message.reply(f"User {replied_user_id} has been added to blocklist.")
            else:
                await message.reply("You cannot block yourself or a anonymous user")
        else:
            await message.reply("The replied message is not from a user.")
    else:
        # If not a reply, check if a user ID is provided in the command
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                user_id = int(command_parts[1])
                # Block the user with the provided user ID
                if not user_id in busers:
                    collection.update_one({"user_id": client.me.id},
                                        {"$push": {'busers': user_id}},
                                        upsert=True
                                    )
                else:
                   return await message.reply(f"User {user_id} already in the blocklist.")
                await message.reply(f"User {user_id} has been added to blocklist.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")

# Start the bot

@Client.on_message(filters.command("unblock"))
@retry()

async def unblock_user(client, message):
    # Check if the message is a reply
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
        is_admin or
        get_user_id_by_client(user_id, client) or
        (user_id in sudoers and premium_by == "PAID")
    )

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER/SUDOER'S COMMAND...**")

    user_data = collection.find_one({"user_id": client.me.id})
    busers = user_data.get('busers', {}) if user_data else []
    if message.reply_to_message:
        replied_message = message.reply_to_message
        # If the replied message is from a user (and not from the bot itself)
        replied_user_id = replied_message.from_user.id
            # Check if the replied user is the same as the current chat (group) id
        if replied_user_id in busers:
               collection.update_one({"user_id": client.me.id},
                                        {"$pull": {'busers': replied_user_id}},
                                        upsert=True
                                    )
               await message.reply(f"User {replied_user_id} has been removed from blocklist.")
        else:
              return await message.reply(f"User {replied_user_id} not in the blocklist.")

    else:
        # If not a reply, check if a user ID is provided in the command
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                user_id = int(command_parts[1])
                # Block the user with the provided user ID
                if user_id in busers:
                    collection.update_one({"user_id": client.me.id},
                                        {"$pull": {'busers': user_id}},
                                        upsert=True
                                    )
                else:
                   return await message.reply(f"User {user_id} not in the blocklist.")
                await message.reply(f"User {user_id} has been removed from blocklist.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")


@Client.on_message(filters.command("sudolist"))
@retry()

async def show_sudo_list(client, message):
    # Check admin permissions
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    owner_id = get_owner_id_by_client(client)
    # Get premium status of the command sender
    premium_by = collection.find_one({"user_id": user_id}, {"premium_by": 1}).get("premium_by", "PAID")
    
    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions - must be admin/verified AND have PAID status
    is_authorized = is_admin or (get_user_id_by_client(user_id, client) and premium_by == "PAID")

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS PAID OWNER'S COMMAND...**")
    
    try:
        # Get all users who have SUDOERS field
        sudo_users = user_sessions.find_one({"user_id": owner_id}).get("SUDOERS", []) if user_sessions.find_one({"user_id": owner_id}) else []
        
        if not sudo_users:
            return await message.reply("No sudo users found in the database.")
        
        # Build the sudo list message
        sudo_list = ["**🔱 SUDO USERS LIST:**\n"]
        number = 1
        
        for user_id in sudo_users:
                try:
                    # Try to get user info from Telegram
                    user_info = await client.get_users(user_id)
                    user_mention = f"@{user_info.username}" if user_info.username else user_info.first_name
                    sudo_list.append(f"**{number}➤** {user_mention} [`{user_id}`]")
                except Exception:
                    # If can't get user info, just show the ID
                    sudo_list.append(f"**{number}➤** Unknown User [`{user_id}`]")
                number += 1
        
        # Add count at the bottom
        sudo_list.append(f"\n**Total SUDO Users:** `{number-1}`")
        
        # Send the message
        await message.reply("\n".join(sudo_list))
        
    except Exception as e:
        await message.reply(f"An error occurred while fetching sudo list: {str(e)}")


@Client.on_message(filters.command("addsudo"))
@retry()

async def add_to_sudo(client, message):
    # Check admin permissions
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id

    # Get premium status of the command sender
    owner_id = get_owner_id_by_client(client)
    premium_by = collection.find_one({"user_id": owner_id}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids
    
    is_authorized = is_admin or (get_user_id_by_client(user_id, client) and premium_by == "PAID")

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS PAID OWNER'S COMMAND...**")

    if message.reply_to_message:
        replied_message = message.reply_to_message
        if replied_message.from_user:
            replied_user_id = replied_message.from_user.id

            # Check if target user is already admin
            if os.path.exists(admin_file):
                with open(admin_file, "r") as file:
                    admin_ids = [int(line.strip()) for line in file.readlines()]
                    if replied_user_id in admin_ids:
                        return await message.reply(f"**This user is already an owner!**")

            # Check if trying to add self or bot
            if replied_user_id != message.chat.id and not replied_message.from_user.is_self:
                # Get current sudo users
                users_data = user_sessions.find_one({"user_id": owner_id})

                sudoers = users_data.get("SUDOERS", [])

                if replied_user_id not in sudoers:
                    # Add user to sudoers
                    user_sessions.update_one(
                        {"user_id": owner_id},
                        {"$push": {"SUDOERS": replied_user_id}},
                        upsert=True
                    )
                    await message.reply(f"User {replied_user_id} has been added to sudoers list.")
                else:
                    await message.reply(f"User {replied_user_id} is already in sudoers list.")
            else:
                await message.reply("You cannot add yourself or the bot to sudoers.")
        else:
            await message.reply("The replied message is not from a user.")
    else:
        # Handle command with user ID
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                target_user_id = int(command_parts[1])

                # Check if target user is already admin
                if os.path.exists(admin_file):
                    with open(admin_file, "r") as file:
                        admin_ids = [int(line.strip()) for line in file.readlines()]
                        if target_user_id in admin_ids:
                            return await message.reply(f"**This user is already an owner!**")

                # Get current sudo users
                users_data = user_sessions.find_one({"user_id": owner_id})

                sudoers = users_data.get("SUDOERS", [])

                if target_user_id not in sudoers:
                    # Add user to sudoers
                    user_sessions.update_one(
                        {"user_id": owner_id},
                        {"$push": {"SUDOERS": target_user_id}},
                        upsert=True
                    )
                    await message.reply(f"User {target_user_id} has been added to sudoers list.")
                else:
                    await message.reply(f"User {target_user_id} is already in sudoers list.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")

@Client.on_message(filters.command("rmsudo"))
@retry()

async def remove_from_sudo(client, message):
    # Check admin permissions
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions - only admin or verified users can remove from sudo
    owner_id = get_owner_id_by_client(client)
    is_authorized = is_admin or (user_id == owner_id)

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER'S COMMAND...**")

    # Handle reply to message
    if message.reply_to_message:
        replied_message = message.reply_to_message
        if replied_message.from_user:
            replied_user_id = replied_message.from_user.id

            # Check if target user is an admin
            if os.path.exists(admin_file):
                with open(admin_file, "r") as file:
                    admin_ids = [int(line.strip()) for line in file.readlines()]
                    if replied_user_id in admin_ids:
                        return await message.reply(f"**Cannot remove an owner from sudo list!**")

            # Check if trying to remove self or bot
            if replied_user_id != message.chat.id and not replied_message.from_user.is_self:
                # Get current sudo users
                users_data = user_sessions.find_one({"user_id": owner_id})
                if not users_data:
                    return await message.reply(f"User {replied_user_id} is not in the database.")

                sudoers = users_data.get("SUDOERS", [])

                if replied_user_id in sudoers:
                    # Remove user from sudoers
                    user_sessions.update_one(
                        {"user_id": owner_id},
                        {"$pull": {"SUDOERS": replied_user_id}}
                    )
                    await message.reply(f"User {replied_user_id} has been removed from sudoers list.")
                else:
                    await message.reply(f"User {replied_user_id} is not in sudoers list.")
            else:
                await message.reply("You cannot remove yourself or the bot from sudoers.")
        else:
            await message.reply("The replied message is not from a user.")
    else:
        # Handle command with user ID
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                target_user_id = int(command_parts[1])

                # Check if target user is an admin
                if os.path.exists(admin_file):
                    with open(admin_file, "r") as file:
                        admin_ids = [int(line.strip()) for line in file.readlines()]
                        if target_user_id in admin_ids:
                            return await message.reply(f"**Cannot remove an owner from sudo list!**")

                # Get current sudo users
                users_data = user_sessions.find_one({"user_id": owner_id})
                if not users_data:
                    return await message.reply(f"User {target_user_id} is not in the database.")

                sudoers = users_data.get("SUDOERS", [])

                if target_user_id in sudoers:
                    # Remove user from sudoers
                    user_sessions.update_one(
                        {"user_id": owner_id},
                        {"$pull": {"SUDOERS": target_user_id}}
                    )
                    await message.reply(f"User {target_user_id} has been removed from sudoers list.")
                else:
                    await message.reply(f"User {target_user_id} is not in sudoers list.")
            except ValueError:
                await message.reply("Please provide a valid user ID.")
        else:
            await message.reply("You need to reply to a message or provide a user ID.")





from pyrogram.types import Chat
from pyrogram.errors import ChatAdminRequired

async def get_chat_member_count(client, chat_id):
    try:
        return await client.get_chat_members_count(chat_id)
    except:
        return "Unknown"

async def send_log_message(client, log_group_id, message, is_private):
    try:
        if is_private:
            user = message.from_user
            log_text = (
                "📥 **New User Started Bot**\n\n"
                f"**User Details:**\n"
                f"• Name: {user.first_name}\n"
                f"• Username: @{user.username if user.username else 'None'}\n"
                f"• User ID: `{user.id}`\n"
                f"• Is Premium: {'Yes' if user.is_premium else 'No'}\n"
                f"• DC ID: {user.dc_id if user.dc_id else 'Unknown'}\n"
                f"• Language: {user.language_code if user.language_code else 'Unknown'}\n"
                f"• Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            try: invite_link = client.export_chat_invite_link(chat.id)
            except (TimeoutError, exceptions.bad_request_400.ChatAdminRequired, AttributeError): invite_link = "Don't have invite right"
            except Exception: invite_link = "Error while generating invite link"
            chat = message.chat
            members_count = await get_chat_member_count(client, chat.id)
            log_text = (
                "📥 **Bot Added to New Group**\n\n"
                f"**Group Details:**\n"
                f"• Name: {chat.title}\n"
                f"• Chat ID: `{chat.id}`\n"
                f"• Type: {chat.type}\n"
                f"• Members: {members_count}\n"
                f"• Username: @{chat.username if chat.username else invite_link}\n"
                f"• Added By: {message.from_user.mention if message.from_user else 'Unknown'}\n"
                f"• Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        await asyncio.sleep(2)
        await client.send_message(
            chat_id=int(log_group_id),
            text=log_text,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.info(f"Error sending log message: {str(e)}")



@Client.on_message(filters.command("start") | (filters.group & create_custom_filter))
@retry()

async def user_client_start_handler(client, message):
    user_id = message.chat.id
    user_data = collection.find_one({"user_id": client.me.id})
    is_private = message.chat.type == enums.ChatType.PRIVATE
    should_log = False
    if user_data:
        users = user_data.get('users', {})
        if not user_id in users:
                collection.update_one({"user_id": client.me.id},
                                        {"$push": {'users': user_id}},
                                        upsert=True
                                    )
                should_log = True
    else:
        collection.update_one({"user_id": client.me.id},
                                        {"$set": {'users': [user_id]}},
                                        upsert=True
                                    )
        should_log = True
    if should_log:
        owner_id = get_owner_id_by_client(client)
        log_group = gvarstatus(owner_id, "log_group")
        
        if log_group:
          try:
            await send_log_message(
                client=client,
                log_group_id=log_group,
                message=message,
                is_private=is_private
            )
          except Exception as e:
             logger.info(e)

    # Process video ID if provided in start command
    command_args = message.text.split() if message.text else "hh".split()
    if len(command_args) > 1 and '_' in command_args[1]:
        try:
            loading = await message.reply("Getting stream info! Please wait...")
            # Split the argument using underscore and get the video ID
            _, video_id = command_args[1].split('_', 1)
            
            # Get video details
            video_info = get_video_details(video_id)
            
            if isinstance(video_info, dict):
                # Format numbers
                views = format_number(video_info['view_count'])
                likes = format_number(video_info['like_count'])
                subs = format_number(video_info['subscriber_count'])
                
                # Create formatted message
                logger.info(video_info['thumbnail'])
                await loading.delete()
                caption = (
                    f"📝 **Title:** {video_info['title']}\n\n"
                    f"⏱ **Duration:** {video_info['duration']}\n"
                    f"👁 **Views:** {views}\n"
                    f"👍 **Likes:** {likes}\n"
                    f"📺 **Channel:** {video_info['channel_name']}\n"
                    f"👥 **Subscribers:** {subs}\n"
                    f"📅 **Upload Date:** {video_info['upload_date']}"
                )
                
                # Create inline keyboard with YouTube button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🎬 Stream on YouTube",
                        url=video_info['video_url']
                    )]
                ])
                
                # Send thumbnail as photo with caption and keyboard
                try:
                    return await message.reply_photo(
                        photo=video_info['thumbnail'],
                        caption=caption,
                        reply_markup=keyboard,
                        reply_to_message_id=message.id
                    )
                except Exception as e:
                    return await message.reply_text(
                        f"❌ Failed to send photo: {str(e)}\n\n{caption}",
                        reply_markup=keyboard,
                        reply_to_message_id=message.id
                    )
            else:
                return await message.reply_text(
                    f"❌ Error: {video_info}",
                    reply_to_message_id=message.id
                )
                
        except Exception as e:
            return await message.reply_text(
                f"❌ Error processing video ID: {str(e)}",
                reply_to_message_id=message.id
            )

    # Handle logging

    session_name = f'user_{client.me.id}'
    user_dir = f"{ggg}/{session_name}"
    os.makedirs(user_dir, exist_ok=True)
    editing = await message.reply("⚡")
    owner_id = get_owner_id_by_client(client)
    owner = await client.get_users(owner_id)
    ow_id = owner.id if owner.username else None

    buttons = [
   [InlineKeyboardButton("Aᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ", url=f"https://t.me/{client.me.username}?startgroup=true")],
   [InlineKeyboardButton("Hᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="commands_all")],
   [
       InlineKeyboardButton(
           "Cʀᴇᴀᴛᴏʀ",
           user_id=owner_id
       ) if ow_id else InlineKeyboardButton(
           "Cʀᴇᴀᴛᴏʀ",
           url=f"https://t.me/{app.me.username}"
       ),
       InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url=gvarstatus(owner_id, "support") or "https://t.me/nub_coder_updates")
   ],
]
    import psutil
    from random import choice
    uptime = await get_readable_time((time.time() - StartTime))
    start = datetime.datetime.now()

    
    
    # Get system resources
    try:
        cpu_cores = psutil.cpu_count() or "N/A"
        ram = psutil.virtual_memory()
        ram_total = f"{ram.total / (1024**3):.2f} GB"
        disk = psutil.disk_usage('/')
        disk_total = f"{disk.total / (1024**3):.2f} GB"
    except Exception as e:
        cpu_cores = "N/A"
        ram_total = "N/A"
        disk_total = "N/A"
    try:
       if not client.me.username in active:
          await message.reply(f"No assistant userbot detected\nstopping the bot😢😢")
          return await client.stop(block=False)
       photu = None
       async for photo in client.get_chat_photos(client.me.id):
           photu = photo.file_id

       # First try to get logo from user_dir
       logo_path_jpg = f"{user_dir}/logo.jpg"
       logo_path_mp4 = f"{user_dir}/logo.mp4"
       logo = None
       
       if os.path.exists(logo_path_mp4):
           logo = logo_path_mp4
       elif os.path.exists(logo_path_jpg):
           logo = logo_path_jpg
       else:
           logo = gvarstatus(owner_id, "LOGO") or (await client.download_media(client.me.photo.big_file_id, logo_path_jpg) if client.me.photo else "music.jpg")
       
       alive_logo = logo
       if type(logo) is bytes:
           alive_logo = logo_path_jpg
           with open(alive_logo, "wb") as fimage:
               fimage.write(base64.b64decode(logo))
           if 'video' in mime.from_file(alive_logo):
               alive_logo = rename_file(alive_logo, logo_path_mp4)




       greet_message = gvarstatus(owner_id, "WELCOME") or f"""
🎵 **{client.me.mention()}** 🎵
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

🎧 **Yᴏᴜʀ ᴍᴜꜱɪᴄᴀʟ ᴊᴏᴜʀɴᴇʏ ʙᴇɢɪɴꜱ ʜᴇʀᴇ**

🔧 **SYSTEM STATUS**
• **Uᴘᴛɪᴍᴇ** » `{uptime}`
• **CPU ᴄᴏʀᴇꜱ** » `{cpu_cores}`
• **RAM** » `{ram_total}`
• **Dɪꜱᴋ** » `{disk_total}`

✨ **Pʀᴇᴍɪᴜᴍ Fᴇᴀᴛᴜʀᴇꜱ**
**• 8D ꜱᴜʀʀᴏᴜɴᴅ ꜱᴏᴜɴᴅ + ʜɪ-ꜰɪ**
**• 4K ᴜʟᴛʀᴀ HD ꜱᴛʀᴇᴀᴍɪɴɢ**
**• 0.1ꜱ ʀᴇꜱᴘᴏɴꜱᴇ ᴛɪᴍᴇ**
**• 20+ ꜱᴍᴀʀᴛ ᴄᴏɴᴛʀᴏʟꜱ**

⚙️ **Pᴇʀꜰᴏʀᴍᴀɴᴄᴇ**
**• 24/7 ɴᴏɴꜱᴛᴏᴘ ᴘʟᴀʏʙᴀᴄᴋ**
**• 99.9% ᴜᴘᴛɪᴍᴇ ɢᴜᴀʀᴀɴᴛᴇᴇ**"""
       d_ata = collection.find_one({"user_id": owner_id})
       premium_by = d_ata.get("premium_by", "PAID")
       if premium_by in ("REFERRAL", "TRIAL"):
           greet_message += f"""\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ [⚡](http://t.me/{app.me.username}?start={owner_id})"""

       send = client.send_video if alive_logo.endswith(".mp4") else client.send_photo
       await editing.delete()
       await send(
                user_id ,
                alive_logo,
                caption=await format_welcome_message(client, greet_message, message.chat.id, message.from_user.mention() if message.chat.type == enums.ChatType.PRIVATE else message.chat.title )
,reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
      logger.info(e)

# Create an instance of the Update class
async def format_welcome_message(client, text, chat_id, user_or_chat_name):
    """Helper function to format welcome message with real data"""
    try:
        formatted_text = text.replace("{name}", user_or_chat_name)
        formatted_text = formatted_text.replace("{id}", str(chat_id))
        formatted_text = formatted_text.replace("{botname}", f"@{client.me.username}")
        return formatted_text
    except Exception as e:
        logging.error(f"Error formatting welcome message: {str(e)}")
        return text  # Return original text if formatting fails


@Client.on_callback_query(filters.regex(r"commands_(.*)"))
@retry()

async def commands_handler(client, callback_query):
    data = callback_query.data.split("_", 1)[1]  # Extract command type
    user_id = callback_query.from_user.id
    admin_file = f"{ggg}/admin.txt"

    # Check if the user is an admin or owner
    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if user_id in admin_ids or get_user_id_by_client(user_id, client):
                is_admin = True
    owner_id = get_owner_id_by_client(client)
    owner = await client.get_users(owner_id)
    ow_id = owner.id if owner.username else None
    
    # Define command categories with detailed descriptions
    playback_commands = """**🎵 PLAYBACK COMMANDS**
<blockquote>
**◾ /play or /vplay**
- Play audio or video from YouTube
- Usage: `/play [song name or URL]`
- Can also reply to audio/video file or YouTube link
- `/vplay` streams video with audio
- Adds to queue if something is already playing

**◾ /playforce or /vplayforce**
- Force play (interrupts current playback)
- Usage: `/playforce [query]` or reply to media
- Immediately stops current track and plays new one

**◾ /cplay or /cvplay**
- Play in linked channel (requires group-channel link)
- Usage: `/cplay [query]` or reply to media
- Only works in groups with linked broadcast channel

**◾ /pause**
- Pause current playback
- Usage: `/pause`

**◾ /resume**
- Resume paused playback
- Usage: `/resume`

**◾ /skip**
- Skip to next track in queue
- Usage: `/skip`
- If queue is empty, stops playback

**◾ /end**
- Stop playback and clear queue
- Usage: `/end`

**◾ /seek or /seekback**
- Jump forward/backward in track
- Usage: `/seek 30` or `/seekback 15`

**◾ /loop**
- Loop current track X times
- Usage: `/loop 3` (loops 3 times)
- Maximum 20 loops
</blockquote>
"""

    blocklist_commands = """**🚫 BLOCKLIST COMMANDS**
<blockquote>
**◾ /block**
- Block user from using bot
- Usage: `/block @spammer` or reply to a user
- Owner/sudo-only command

**◾ /unblock**
- Unblock user
- Usage: `/unblock @username` or reply to a user
- Owner/sudo-only command

**◾ /blocklist**
- View all blocked users
- Usage: `/blocklist`
</blockquote>
"""

    sudo_commands = """**🔑 SUDO COMMANDS**
<blockquote>
**◾ /addsudo**
- Add sudo user
- Usage: `/addsudo @username` or reply to a user
- Owner-only command
- Grants user admin privileges for the bot

**◾ /rmsudo**
- Remove sudo user
- Usage: `/rmsudo @username` or reply to a user
- Owner-only command
- Revokes sudo privileges from user

**◾ /sudolist**
- List all sudo users
- Usage: `/sudolist`
</blockquote>
"""

    broadcast_commands = """**📢 BROADCAST COMMANDS**
<blockquote>
**◾ /broadcast**
- Send message to all users
- Usage: Reply to a message and type `/broadcast`
- Sends copy of message to all users

**◾ /fbroadcast**
- Force broadcast message
- Usage: Reply to a message and type `/fbroadcast`
- Forwards original message to all users
- Owner/sudo-only command
</blockquote>
"""

    auth_commands = """**🔐 AUTH COMMANDS**
<blockquote>
**◾ /auth**
- Authorize user to use bot
- Usage: `/auth` (reply to user) or `/auth @username`
- Allows non-admins to use bot commands
- Admin-only command

**◾ /unauth**
- Remove user authorization
- Usage: `/unauth` (reply to user) or `/unauth @username`
- Revokes authorization from user
- Admin-only command

**◾ /authlist**
- List authorized users
- Usage: `/authlist`
</blockquote>
"""

    tools_commands = """**🛠️ TOOLS COMMANDS**
<blockquote>
**◾ /del**
- Delete replied message
- Usage: Reply to a message and type `/del`
- Requires admin or delete permissions

**◾ /tagall**
- Tag all group members
- Usage: `/tagall [optional message]`
- Admin-only command

**◾ /cancel**
- Cancel ongoing tag process
- Usage: `/cancel`

**◾ /powers**
- Check admin permissions
- Usage: `/powers` (reply to user) or  `/powers`
</blockquote>
"""

    kang_commands = """**🎨 KANG COMMANDS**
<blockquote>
**◾ /kang**
- Clone sticker/video/photo
- Usage: Reply to image/video/sticker and type `/kang [emoji]`
- Adds sticker to your custom sticker pack

**◾ /qt**
- Create fake quote stickers
- Usage: Reply to a message and type `/qt [fake text]`
- Creates fake quote sticker of the user

**◾ /mmf**
- Write on images/stickers
- Usage: Reply to an image/sticker and type `/mmf [text]`
</blockquote>
"""

    status_commands = """**📊 STATUS COMMANDS**
<blockquote>
**◾ /ping**
- Check bot response time
- Usage: `/ping`
- Shows bot latency and uptime

**◾ /about**
- View user/chat information
- Usage: `/about` (shows your info)
- Reply to a user or `/about @username` (someone else's info)
- `/about` in a group shows group info

**◾ /stats**
- Bot statistics
- Usage: `/stats`

**◾ /ac**
- View active calls
- Usage: `/ac`
</blockquote>
"""

    # Create category buttons for main commands page
    category_buttons = [
        [
            InlineKeyboardButton("🎵 Pʟᴀʏʙᴀᴄᴋ", callback_data="commands_playback"),
            InlineKeyboardButton("🔐 Aᴜᴛʜ", callback_data="commands_auth")
        ],
        [
            InlineKeyboardButton("🛠️ Tᴏᴏʟꜱ", callback_data="commands_tools"),
            InlineKeyboardButton("🎨 Kᴀɴɢ", callback_data="commands_kang")
        ],
        [
            InlineKeyboardButton("📊 Sᴛᴀᴛᴜꜱ", callback_data="commands_status"),
            InlineKeyboardButton("🚫 Bʟᴏᴄᴋʟɪꜱᴛ", callback_data="commands_blocklist")
        ],
        [
            InlineKeyboardButton("🔑 Sᴜᴅᴏ", callback_data="commands_sudo"),
            InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="commands_broadcast")
        ],
        [InlineKeyboardButton("Hᴏᴍᴇ", callback_data="commands_back")]
    ]
    
    # Back button for category pages
    back_button = [
        [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="commands_all")],
    ]

    # Handle different callbacks based on data
    if data == "all":
        # Show all command categories
        await callback_query.message.edit_caption(
            caption="**📜 SELECT A COMMAND CATEGORY**",
            reply_markup=InlineKeyboardMarkup(category_buttons)
        )
    elif data == "playback":
        await callback_query.message.edit_caption(
            caption=playback_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "blocklist":
        await callback_query.message.edit_caption(
            caption=blocklist_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "sudo":
        await callback_query.message.edit_caption(
            caption=sudo_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "broadcast":
        await callback_query.message.edit_caption(
            caption=broadcast_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "auth":
        await callback_query.message.edit_caption(
            caption=auth_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "tools":
        await callback_query.message.edit_caption(
            caption=tools_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "kang":
        await callback_query.message.edit_caption(
            caption=kang_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "status":
        await callback_query.message.edit_caption(
            caption=status_commands,
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    elif data == "back":
        # System info collection
        uptime = await get_readable_time((time.time() - StartTime))
        start = datetime.datetime.now()
        try:
            cpu_cores = psutil.cpu_count(logical=False) or "N/A"
            ram = psutil.virtual_memory()
            ram_total = f"{ram.total / (1024**3):.2f} GB"
            disk = psutil.disk_usage('/')
            disk_total = f"{disk.total / (1024**3):.2f} GB"
        except Exception as e:
            cpu_cores = "N/A"
            ram_total = "N/A"
            disk_total = "N/A"
            
        # Home buttons
        buttons = [
            [InlineKeyboardButton("Aᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ", url=f"https://t.me/{client.me.username}?startgroup=true")],
            [InlineKeyboardButton("Hᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="commands_all")],
            [
                InlineKeyboardButton(
                    "Cʀᴇᴀᴛᴏʀ",
                    user_id=owner_id
                ) if ow_id else InlineKeyboardButton(
                    "Cʀᴇᴀᴛᴏʀ",
                    url=f"https://t.me/{app.me.username}"
                ),
                InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url=gvarstatus(owner_id, "support") or "https://t.me/nub_coder_updates")
            ],
        ]

        greet_message = gvarstatus(owner_id, "WELCOME") or f"""
🎵 **{client.me.mention()}** 🎵
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

🎧 **Yᴏᴜʀ ᴍᴜꜱɪᴄᴀʟ ᴊᴏᴜʀɴᴇʏ ʙᴇɢɪɴꜱ ʜᴇʀᴇ**

🔧 **SYSTEM STATUS**
• **Uᴘᴛɪᴍᴇ** » `{uptime}`
• **CPU ᴄᴏʀᴇꜱ** » `{cpu_cores}`
• **RAM** » `{ram_total}`
• **Dɪꜱᴋ** » `{disk_total}`

✨ **Pʀᴇᴍɪᴜᴍ Fᴇᴀᴛᴜʀᴇꜱ**
**• 8D ꜱᴜʀʀᴏᴜɴᴅ ꜱᴏᴜɴᴅ + ʜɪ-ꜰɪ**
**• 4K ᴜʟᴛʀᴀ HD ꜱᴛʀᴇᴀᴍɪɴɢ**
**• 0.1ꜱ ʀᴇꜱᴘᴏɴꜱᴇ ᴛɪᴍᴇ**
**• 20+ ꜱᴍᴀʀᴛ ᴄᴏɴᴛʀᴏʟꜱ**

⚙️ **Pᴇʀꜰᴏʀᴍᴀɴᴄᴇ**
**• 24/7 ɴᴏɴꜱᴛᴏᴘ ᴘʟᴀʏʙᴀᴄᴋ**
**• 99.9% ᴜᴘᴛɪᴍᴇ ɢᴜᴀʀᴀɴᴛᴇᴇ**"""
        d_ata = collection.find_one({"user_id": owner_id})
        premium_by = d_ata.get("premium_by", "PAID") if d_ata else "PAID"
        if premium_by in ("REFERRAL", "TRIAL"):
            greet_message += f"""\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ [⚡](http://t.me/{app.me.username}?start={owner_id})"""
            
        await callback_query.message.edit_caption(
            caption=await format_welcome_message(
                client, 
                greet_message, 
                callback_query.message.chat.id,
                callback_query.from_user.first_name if callback_query.message.chat.type == enums.ChatType.PRIVATE else callback_query.message.chat.title
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@Client.on_message(filters.command("blocklist"))
@retry()

async def blocklist_handler(client, message):
    admin_file = f"{ggg}/admin.txt"
    user_id = message.from_user.id
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
        is_admin or
        get_user_id_by_client(user_id, client) or
        (user_id in sudoers and premium_by == "PAID")
    )

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER/SUDOER'S COMMAND...**")

    # Check for admin or owner


    # Fetch blocklist from the database
    user_data = collection.find_one({"user_id": client.me.id})
    if not user_data:
        return await message.reply("No blocklist found.")

    blocked_users = user_data.get('busers', [])
    if not blocked_users:
        return await message.reply("No users are currently blocked.")

    blocklist_text = "Blocked Users:\n" + "\n".join([f"- `{user_id}`" for user_id in blocked_users])
    await message.reply_text(blocklist_text)


async def check_assistant(user_client, message):
   if not user_client.me.username in active:
      await message.reply(f"No userbot detected\nstopping the bot")
      await user_client.stop(block=False)




from pytgcalls import filters as call_filters

def currently_playing(user_client, message):
    song_queue = queues.get(f"dic_{user_client.me.id}")
    try:
        if len(song_queue[message.chat.id]) <=1:
           return False
        return True
    except KeyError:
        True


async def hd_stream_closed_kicked(client, update):
   logger.info(update)
   session_client = client._mtproto
   user_client = linkage.get(session_client.me.id)
   song_queue_key = f"dic_{user_client.me.id}"
   song_queue = queues.get(song_queue_key)
   try:
      await remove_active_chat(user_client, update.chat_id)
      song_queue[update.chat_id].clear()
   except Exception as e:
      logger.info(e)

async def end(client, update):
  session_client = client._mtproto
  user_client = linkage.get(session_client.me.id)

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
    return

  try:
    if update.chat_id in song_queue and song_queue[update.chat_id]:
      next_song = song_queue[update.chat_id].pop(0)
      await join_call(next_song['message'], next_song['title'], 
next_song['session'], next_song['yt_link'], next_song['chat'], next_song['duration'], next_song['mode'])
    else:
      logger.info(f"Song queue for chat {update.chat_id} is empty.")
      await client.leave_call(update.chat_id)
      await remove_active_chat(user_client, update.chat_id)
  except Exception as e:
    logger.info(f"Error in end function: {e}")

async def dend(user_client, update, channel_id= None):
  song_queue_key = f"dic_{user_client.me.id}"
  song_queue = queues.get(song_queue_key)
  if song_queue is None:
    logger.info(f"Song queue not found for user: {user_client.me.id}")
    await client.leave_call(channel_id or update.chat.id)
    await remove_active_chat(user_client, channel_id or  update.chat.id)
    playing[channel_id or update.chat.id].clear()
    return
  session_client_id = connector.get(user_client.me.username)
  session_client = clients.get(f"{session_client_id}_session")
  client = songs_client.get(session_client.me.id)
  try:
    if (channel_id or update.chat.id) in song_queue and song_queue[(channel_id or update.chat.id)]:
      next_song = song_queue[(channel_id or update.chat.id)].pop(0)
      playing[(channel_id or update.chat.id)] = next_song
      await join_call(next_song['message'], next_song['title'],next_song['session'], next_song['yt_link'],
 next_song['chat'], next_song['by'], next_song['duration'], next_song['mode'], next_song['thumb'])
    else:
      logger.info(f"Song queue for chat {(channel_id or update.chat.id)} is empty.")
      await client.leave_call(channel_id or update.chat.id)
      await remove_active_chat(user_client, channel_id or update.chat.id)
      playing[(channel_id or update.chat.id)].clear()
  except Exception as e:
    logger.info(f"Error in end function: {e}")

    
from PIL import Image
import imageio
import cv2
from pyrogram.raw.types import DocumentAttributeVideo, DocumentAttributeAudio


def generate_thumbnail(video_path, thumb_path):
    try:
        reader = imageio.get_reader(video_path)
        frame = reader.get_data(0)
        image = Image.fromarray(frame)
        image.thumbnail((320, 320))
        image.save(thumb_path, "JPEG")
        return thumb_path
    except Exception as e:
        # Fallback to black thumbnail
        Image.new('RGB', (320, 320), (0, 0, 0)).save(thumb_path, "JPEG")
        return thumb_path
# Play handler function




# Modified media download with progress
async def download_media_with_progress(client, msg, media_msg, type_of):
    start_time = time.time()
    filename = getattr(media_msg, 'file_name', 'file')
    session_name = f'user_{client.me.id}'
    user_dir = f"{ggg}/{session_name}/{msg.chat.id}"
    os.makedirs(user_dir, exist_ok=True)
    try:
        file_path = await client.download_media(media_msg,file_name=f"{user_dir}/",
            progress=progress_bar,
            progress_args=(client, msg, type_of, filename, start_time))
        return file_path
    except Exception as e:
        print(f"Download error: {e}")
        return None


# Modified progress bar with error handling
async def progress_bar(current, total, client, msg, type_of, filename, start_time):
    if total == 0:
        return
    
    try:
            progress_percent = current * 100 / total
            progress_message = f"{type_of} {filename}: {progress_percent:.2f}%\n"
            
            # Progress bar calculation
            progress_bar_length = 20
            num_ticks = int(progress_percent / (100 / progress_bar_length))
            progress_bar_text = '█' * num_ticks + '░' * (progress_bar_length - num_ticks)
            
            # Speed calculation
            elapsed_time = time.time() - start_time
            speed = current / (elapsed_time * 1024 * 1024) if elapsed_time > 0 else 0
            
            # Time remaining calculation
            time_left = (total - current) / (speed * 1024 * 1024) if speed > 0 else 0
            
            # Format message
            progress_message += (
                f"Speed: {speed:.2f} MB/s\n"
                f"Time left: {time_left:.2f}s\n"
                f"Size: {current/1024/1024:.2f}MB / {total/1024/1024:.2f}MB\n"
                f"[{progress_bar_text}]"
            )
            
            # Edit message with exponential backoff
            try:
              if random.choices([True, False], weights=[1, 20])[0]:
                await msg.edit(progress_message)
            except Exception as e:
                print(f"Progress update error: {e}")

    except Exception as e:
        print(f"Progress bar error: {e}")


import os
import cv2
from mutagen import File
from mutagen import MutagenError

def with_opencv(filename):
    # List of common audio file extensions
    audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.mp4', '.wma']
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Handle audio files with mutagen
    if file_ext in audio_extensions:
        try:
            audio = File(filename)
            if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                duration = audio.info.length
                print(int(duration))
                return int(duration)
            else:
                print(0)
                return 0
        except MutagenError:
            print(0)
            return 0
    # Handle video files with OpenCV
    else:
        video = cv2.VideoCapture(filename)
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps else 0
        video.release()
        print(int(duration))
        return int(duration)
# Example usage
# duration = get_media_duration('path/to/your/media/file.ogg')
# print(duration)
@Client.on_message(filters.command(["play", "vplay", "playforce", "vplayforce", "cplay", "cvplay", "cplayforce", "cvplayforce"]))
@retry()

@premium_only()
async def play_handler_func(user_client, message):
    session_name = f'user_{user_client.me.id}'
    user_dir = f"{ggg}/{session_name}"
    os.makedirs(user_dir, exist_ok=True)
    by = message.from_user
    try:
        await message.delete()
    except:
        pass
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {}) if user_data else []
    if message.from_user.id in busers:
        return

    command = message.command[0].lower()
    mode = "video" if command.startswith("v") or command.startswith("cv") else "audio"
    force_play = command.endswith("force")
    channel_mode = command.startswith("c")
    
    # Check if the command is sent in a group
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("The play commands can only be used in group chats.")
        return

    # Get the bot username and retrieve the session client ID from connector  
    youtube_link = None  
    input_text = message.text.split(" ", 1)  
    d_ata = collection.find_one({"user_id": get_owner_id_by_client(user_client)})  
    premium_by = d_ata.get("premium_by", "PAID")  
    song_queue = queues.get(f"dic_{user_client.me.id}")  
    act_calls = len(active.get(user_client.me.username, []))  
    
    # Determine if we need channel mode
    chat = message.chat
    target_chat_id = message.chat.id
    # For channel commands, check for linked channel
    if channel_mode:
        linked_chat = (await user_client.get_chat(message.chat.id)).linked_chat
        if not linked_chat:
            await message.reply("This group doesn't have a linked channel.")
            return
        target_chat_id = linked_chat.id
    
    # Check queue for the target chat
    current_queue = len(song_queue.get(target_chat_id, [])) if song_queue else 0  

    if premium_by in ("REFERRAL", "TRIAL") and (act_calls >= 5 or current_queue >= 5):  
        return await message.reply(  
            f"The bot is in trial mode, so it has the following limitations:\n"  
            f"- Active calls: {act_calls} (Limit: 5)\n"  
            f"- Song queue: {current_queue} (Limit: 5)"  
        )  
        
    massage = await message.reply(f"{upper_mono('Searching for your query, please wait')}")  
    
    # Set target chat as active based on channel mode or not
    is_active = await is_active_chat(user_client, target_chat_id)
    await add_active_chat(user_client, target_chat_id)  

    youtube_link = None  
    media_info = {}  

    # Check if replied to media message  
    if message.reply_to_message and message.reply_to_message.media:  
        media_msg = message.reply_to_message  
        media_type = None  
        duration = 0  
        thumbnail = None  

        # Video handling  
        if media_msg.video:  
            media = media_msg.video  
            media_type = "video"  
            title = media.file_name or "Telegram Video"  
            duration = media.duration  
            if media.thumbs:  
                thumbnail = await user_client.download_media(media.thumbs[0].file_id)  

        # Audio handling  
        elif media_msg.audio:  
            media = media_msg.audio  
            media_type = "audio"  
            title = media.title or "Telegram Audio"  
            duration = media.duration  
            if media.thumbs:  
                thumbnail = await user_client.download_media(media.thumbs[0].file_id)  

        # Voice message handling  
        elif media_msg.voice:  
            media = media_msg.voice  
            media_type = "voice"  
            title = "Voice Message"  
            duration = media.duration  

        # Video note handling  
        elif media_msg.video_note:  
            media = media_msg.video_note  
            media_type = "video_note"  
            title = "Video Note"  
            duration = media.duration  
            if media.thumbs:  
                thumbnail = await user_client.download_media(media.thumbs[0].file_id)  
        elif media_msg.document:  
            doc = media_msg.document  
            for attr in doc.attributes:  
                if isinstance(attr, DocumentAttributeVideo):  
                    media_type = "video"  
                    title = doc.file_name or "Telegram Video"  
                    duration = attr.duration  
                elif isinstance(attr, DocumentAttributeAudio):  
                    media_type = "audio"  
                    title = doc.file_name or "Telegram Audio"  
                    duration = attr.duration  

            if media_type and doc.thumbs:  
                thumbnail = await user_client.download_media(f"{user_dir}/{doc}".thumbs[0].file_id)  
        else:  
            await massage.edit(f"{upper_mono('❌ Unsupported media type')}")  
            return await remove_active_chat(user_client, target_chat_id)  
        if not media_type:  
            await massage.edit(f"{upper_mono('❌ Unsupported media type')}")  
            return await remove_active_chat(user_client, target_chat_id)  
        # For media messages  
        youtube_link = await download_media_with_progress(  
            user_client,  
            massage,  
            message.reply_to_message,  
            "Media"
        )

        # Generate thumbnail if missing  
        if not thumbnail and media_type in ["video", "video_note"]:  
            try:  
                thumbnail = generate_thumbnail(youtube_link, f'{user_dir}/thumb.png')  
            except Exception as e:  
                print(e)  
                thumbnail = None  
        # Format duration  
        if not duration or duration <=0:  
            duration = with_opencv(youtube_link)  
        duration = format_duration(int(duration))  
        media_info = {  
            'title': title,  
            'duration': duration,  
            'thumbnail': thumbnail,  
            'file_id': media.file_id,  
            'media_type': media_type,  
            'url': youtube_link  
        }  
    elif len(input_text) == 2:  
        search_query = input_text[1]  

        title, duration, youtube_link, thumbnail, channel_name, views, video_id = handle_youtube(search_query,user_dir)
        print(title)
        if not youtube_link:  
            try:  
                await massage.edit(f"{upper_mono('No matching query found, please retry!')}")  
                return await remove_active_chat(user_client, target_chat_id)  
            except:  
                return await remove_active_chat(user_client, target_chat_id)  
    else:  
        try:  
            await massage.edit(f"{upper_mono('No query provided, please provide one')}\n`/play query`")  
            return await remove_active_chat(user_client, target_chat_id)  
        except:  
            return  
    # Get thumb based on media type  
    if media_info:  
        thumb = await get_thumb(  
            media_info['title'],  
            media_info['duration'],  
            media_info['thumbnail'],  
            None,  # channel_name  
            None,  # views  
            None   # video_id  
        )  
        # Add your media playback logic here using media_info  
    else:  
        # Existing YouTube handling  
        thumb = await get_thumb(title, str(duration), thumbnail, channel_name, str(views), video_id)  

    bot_username = user_client.me.username  
    session_client_id = connector.get(bot_username)  
    if session_client_id is None:  
        await massage.edit("No session client connected. Please authorize first with /host")  
        return await remove_active_chat(user_client, target_chat_id)  
    owner_id = get_owner_id_by_client(user_client)  

    # Retrieve the session client from the clients dictionary  
    session_client = clients.get(f"{session_client_id}_session")  
    if not session_client:  
        await massage.edit("Session client not found. Please re-authorize with /host.")  
        return await remove_active_chat(user_client, target_chat_id)  

    # Join the group (same for both regular and channel mode)
    if message.chat.username:
        # Public group
        try:  
            try:  
                joined_chat = await session_client.get_chat(message.chat.username)  
            except:  
                joined_chat = await session_client.join_chat(message.chat.username)  
        except (InviteHashExpired, ChannelPrivate):  
            await massage.edit(f"Assistant is banned in this chat.\n\nPlease unban {session_client.me.username or session_client.me.id}")  
            return await remove_active_chat(user_client, target_chat_id)  
        except Exception as e:  
            await massage.edit(f"Failed to join the group. Error: {e}")  
            return await remove_active_chat(user_client, target_chat_id)  
    else:  
        # Private group
        bot_member = await user_client.get_chat_member(message.chat.id, user_client.me.id)  

        if bot_member.status == ChatMemberStatus.ADMINISTRATOR and bot_member.privileges.can_invite_users:  
            try:  
                invite_link = await user_client.export_chat_invite_link(message.chat.id)  
                try:  
                    joined_chat = await session_client.get_chat(message.chat.id)  
                except:  
                    joined_chat = await session_client.join_chat(invite_link)  
            except (InviteHashExpired, ChannelPrivate):  
                await massage.edit(f"Assistant is banned in this chat.\n\nPlease unban {session_client.me.mention()}\nuser id: {session_client.me.id}")  
                return await remove_active_chat(user_client, target_chat_id)  
            except Exception as e:  
                await massage.edit(f"Failed to join the group. Error: {e}")  
                return await remove_active_chat(user_client, target_chat_id)  
        else:  
            await massage.edit("I need 'Invite Users via Link' permission to join this private group. Please grant me this permission.")  
            return await remove_active_chat(user_client, target_chat_id)
    
    
    # Set the target chat based on whether it's channel mode or not
    target_chat = None
    if channel_mode:
        # For channel mode, use the linked chat
        target_chat = (await session_client.get_chat(message.chat.id)).linked_chat
        if not target_chat:
            await massage.edit("Failed to access the linked channel. Please make sure the group has a linked channel.")
            return await remove_active_chat(user_client, target_chat_id)
    else:
        # For regular mode, use the joined chat
        target_chat = joined_chat

    await put_queue(
        massage,
        title,
        user_client,
        youtube_link,
        target_chat,
        by,
        duration,
        mode,
        thumb, 
        force_play
    )
    if is_active and not force_play:
                song_queue = queues.get(f"dic_{user_client.me.id}")
                position = len(song_queue.get(message.chat.id)) if song_queue.get(target_chat.id) else 1
                keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="▷", callback_data=f"{'c' if channel_mode else ''}resume"),
                InlineKeyboardButton(text="II", callback_data=f"{'c' if channel_mode else ''}pause"),
                InlineKeyboardButton(text="‣‣I" if position <1 else f"‣‣I({position})", callback_data=f"{'c' if channel_mode else ''}skip"),
                InlineKeyboardButton(text="▢", callback_data=f"{'c' if channel_mode else ''}end"),
            ],
        [                                                                                          InlineKeyboardButton(
               text=f"{smallcap('Add to group')}" , url=f"https://t.me/{user_client.me.username}?startgroup=true"
            ),
            InlineKeyboardButton(
                text="✖ Close", 
                callback_data="close"
            )
        ],
        ])
                await user_client.send_message(message.chat.id, queue_styles[int(gvarstatus(owner_id, "format") or 11)].format(lightyagami(mode), f"[{lightyagami(title)}](https://t.me/{user_client.me.username}?start=vidid_{extract_video_id(youtube_link)})" if not os.path.exists(youtube_link) else  lightyagami(title), lightyagami(duration), position), reply_markup=keyboard,disable_web_page_preview=True)

    else:
      await dend(user_client, massage, target_chat.id if channel_mode else None)
    await message.delete()



from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


import re
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from yt_dlp import YoutubeDL

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API key for YouTube Data API
API_KEY = 'AIzaSyAnsUvlIJ0f44ILpQ4CS7aYbzkV4DfLZrE'  # Replace if needed

def format_duration(duration):
    """Format duration to HH:MM:SS, MM:SS, or SS format.
    
    Handles both integer seconds and ISO 8601 duration format.
    """
    # Check if duration is ISO 8601 format (from YouTube API)
    if isinstance(duration, str) and duration.startswith('PT'):
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
    else:
        # Handle integer seconds (from yt-dlp)
        try:
            duration = int(duration)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
        except (ValueError, TypeError):
            return "00:00"

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    elif minutes > 0:
        return f"{minutes:02d}:{seconds:02d}"
    else:
        return f"{seconds:02d}"

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def handle_youtube_api(argument):
    """Get YouTube video information using the YouTube Data API"""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # Determine if input is URL or search query
        video_id = extract_video_id(argument)

        if not video_id:
            # Perform search if it's not a URL
            search_response = youtube.search().list(
                q=argument,
                part='id',
                maxResults=1,
                type='video'
            ).execute()

            if not search_response.get('items'):
                return None

            video_id = search_response['items'][0]['id']['videoId']

        # Get video details
        video_response = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()

        if not video_response.get('items'):
            return None

        item = video_response['items'][0]
        snippet = item['snippet']
        stats = item['statistics']
        details = item['contentDetails']

        # Get best available thumbnail
        thumbnails = snippet.get('thumbnails', {})
        thumbnail = thumbnails.get('maxres', thumbnails.get('high',
            thumbnails.get('medium', thumbnails.get('default', {}))))['url']

        return (
            snippet.get('title', 'Title not found'),
            format_duration(details.get('duration', 'PT0S')),
            f'https://youtu.be/{video_id}',
            thumbnail,
            snippet.get('channelTitle', 'Channel not found'),
            stats.get('viewCount', 'N/A'),
            video_id
        )

    except HttpError as e:
        logger.warning(f"API Error: {e.resp.status} {e._get_reason()}")
        return None
    except Exception as e:
        logger.warning(f"Google API error: {str(e)}")
        return None



def truncate_description(description, max_length=50):
    """
    Process description by:
    1. Extracting first two lines
    2. Truncating to max_length characters
    
    Args:
        description (str): Original description
        max_length (int): Maximum length of description
    
    Returns:
        str: Processed description
    """
    if not description or description == 'N/A':
        return ''
    
    # Split description into lines
    lines = description.split('\n')
    
    # Take first two lines
    selected_lines = lines[:2]
    
    # Join the selected lines
    processed_description = ' '.join(selected_lines)
    
    # Truncate and add ellipsis if longer than max_length
    return (processed_description[:max_length] + '...') if len(processed_description) > max_length else processed_description


import yt_dlp
import os

import yt_dlp
import os

def download_instagram_reel(url, output_path):
    """
    Download an Instagram Reel using yt-dlp with browser cookies.

    Args:
        url (str): URL of the Instagram Reel.
        output_path (str, optional): Directory to save the downloaded Reel.
                                     Defaults to the current directory.
    """
    # Set default output path to current directory if not specified
    if output_path is None:
        output_path = os.getcwd()

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        'proxy':'socks5://localhost:9050',
        'format': 'mp4',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'nooverwrites': True,
        'no_color': True,
        'ignoreerrors': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info to determine filename before downloading
            info_dict = ydl.extract_info(url, download=False)
            file_path = ydl.prepare_filename(info_dict)

            # Download the Reel
            ydl.download([url])

        return file_path

    except Exception as e:
        return (f"Error downloading Reel: {e}")


def get_instagram_reel_details(reel_url, directory):
    """
    Extract details from an Instagram Reel using yt_dlp with Chrome browser cookies.
    
    Args:
        reel_url (str): URL of the Instagram Reel
    
    Returns:
        list: Formatted Reel details
    """
    # yt-dlp configuration with simplified cookie extraction
    ydl_opts = {
        'no_warnings': False,
        'quiet': False,
        'extract_flat': False,
        'no_color': True,
        'proxy':'socks5://localhost:9050'
    }

    try:
        # Create yt-dlp extractor
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info_dict = ydl.extract_info(reel_url, download=False)
            
            # Format details as specified
            reel_details = (
                truncate_description(info_dict.get('title')) or truncate_description(info_dict.get('description', '')),  # Description (truncated)
                format_duration(info_dict.get('duration')),  # Duration
                format_duration(info_dict.get('url')),  # Duration
                info_dict.get('thumbnail', ''),  # Thumbnail URL
                info_dict.get('channel', ''),  # Channel
                None,  # Placeholder for additional info
                None  # Placeholder for additional info
            )
            
            return reel_details

    except Exception as e:
        print(f"Error extracting Reel details: {e}")
        return None


def handle_youtube_ytdlp(argument):
    """Get YouTube video information using yt-dlp"""
    try:
        is_url = re.match(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+", argument)

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'noplaylist': True,
            'skip_download': True,
            'cookiesfrombrowser': ('chrome',),
        }
        

        with YoutubeDL(ydl_opts) as ydl:
            if is_url:
                info = ydl.extract_info(argument, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{argument}", download=False)['entries'][0]

            # Get highest resolution thumbnail
            thumbnail = info.get('thumbnails', [{}])[-1].get('url', 'Thumbnail not found') if info.get('thumbnails') else 'Thumbnail not found'
            
            video_id = info.get('id', 'ID not found')
            youtube_link = f'https://youtu.be/{video_id}'

            return (
                info.get('title', 'Title not found'),
                format_duration(info.get('duration', 0)),
                youtube_link,
                thumbnail,
                info.get('uploader', 'Channel not found'),
                info.get('view_count', 'N/A'),
                video_id
            )
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        return None


import re

from urllib.parse import urlparse


def is_url_and_not_youtube_regex(url_string):
       regex = r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
       pattern = re.compile(regex)

       try:
           if pattern.search(url_string): #Verify URL
               result = urlparse(url_string)  # Parse for domain
               is_youtube = (
            "youtube.com" in result.netloc or
            "youtu.be" in result.netloc
        )  #
               return not is_youtube #Return value
           else:
               return False
       except:
           return False
def handle_youtube(argument, directory):
    """
    Main function to get YouTube video information.
    Falls back to yt-dlp if the YouTube API fails.
    
    Returns:
        tuple: (title, duration, youtube_link, thumbnail, channel_name, views, video_id)
    """
    # First try using the YouTube Data API
    result = handle_youtube_api(argument) if not is_url_and_not_youtube_regex(argument) else get_instagram_reel_details(argument,directory)
    
    # If API fails (e.g., quota exceeded), fall back to yt-dlp
    if not result:
        logger.info("YouTube API failed or quota exceeded, falling back to yt-dlp...")
        result = handle_youtube_ytdlp(argument)
    
    # If both methods fail, return error values
    if not result:
        logger.error("Both YouTube API and yt-dlp failed")
        return ("Error", "00:00", None, None, None, None, None)
    
    return result



async def put_queue(
    message,
    title,
    user_client,
    yt_link,
    chat,
    by,
    duration,
audio_flags,
thumb,
forceplay = False):
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0
    put = {
        "message": message,
        "title": title,
        "duration": duration,
        "mode": audio_flags,
        "yt_link": yt_link,
        "chat": chat,
        "by": by,
        "session":user_client,
        "thumb":thumb
    }
    if forceplay:
        song_queue = queues.get(f"dic_{user_client.me.id}")
        check = song_queue.get(chat.id)
        if check:
            song_queue[chat.id].insert(0, put)
        else:
            song_queue[chat.id] = []
            song_queue[chat.id].append(put)
    else:
        song_queue = queues.get(f"dic_{user_client.me.id}")
        check = song_queue.get(chat.id)
        
        if not check:
           song_queue[chat.id] = []
        song_queue[chat.id].append(put)

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
StartTime = time.time()
async def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += time_list.pop() + ", "

    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time








async def get_chat_type(client, chat_id):
  try:
    chat = await client.get_chat(chat_id)
    return chat.type
  except FloodWait as e:
        logger.info(f"Rate limited! Sleeping for {e.value} seconds.")
        await asyncio.sleep(e.value)
  except Exception as e:
    logger.info(f"Error getting chat type for {chat_id}: {e}")
    return None



async def status(client, message):
    """Handles the /status command with song statistics"""
    Man = await message.reply_text("Collecting stats...")
    start = datetime.datetime.now()
    u = g = sg = c = a_chat = play_count = 0
    user_data = collection.find_one({"user_id": client.me.id})

    if user_data:
        # Clean old song entries and get count
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=24)
        collection.update_one(
            {"user_id": client.me.id},
            {"$pull": {"dates": {"$lt": time_threshold}}}
        )
        updated_data = collection.find_one({"user_id": client.me.id})
        play_count = len(updated_data.get('dates', [])) if updated_data else 0

        users = user_data.get('users', [])
        total_users = len(users)
        
        # Process chats in batches for better performance
        for i, chat_id in enumerate(users):
            try:
                chat_type = await get_chat_type(client, chat_id)
                
                if chat_type == enums.ChatType.PRIVATE:
                    u += 1
                elif chat_type == enums.ChatType.GROUP:
                    g += 1
                elif chat_type == enums.ChatType.SUPERGROUP:
                    sg += 1
                    try:
                        user_status = await client.get_chat_member(chat_id, client.me.id)
                        if user_status.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR):
                            a_chat += 1
                    except Exception as e:
                        logger.info(f"Admin check error: {e}")
                elif chat_type == enums.ChatType.CHANNEL:
                    c += 1

                # Update progress every 10 chats
                if i % 10 == 0 or i == total_users - 1:
                    progress_msg = f"""
<b>🔍 Collecting Stats ({min(i+1, total_users)}/{total_users})</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
✦ <b>Private:</b> <code>{u}</code>
✦ <b>Groups:</b> <code>{g}</code>
✦ <b>Super Groups:</b> <code>{sg}</code>
✦ <b>Channels:</b> <code>{c}</code>
✦ <b>Admin Positions:</b> <code>{a_chat}</code>
✦ <b>Songs Played (24h):</b> <code>{play_count}</code>
"""
                    await Man.edit_text(progress_msg)

            except Exception as e:
                logger.info(f"Error processing chat {chat_id}: {e}")

        end = datetime.datetime.now()
        ms = (end - start).seconds

        final_stats = f"""
<b>📊 Comprehensive Bot Statistics</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
⏱ <b>Processed in:</b> <code>{ms}s</code>

✦ <b>Private Chats:</b> <code>{u}</code>
✦ <b>Groups:</b> <code>{g}</code>
✦ <b>Super Groups:</b> <code>{sg}</code>
✦ <b>Channels:</b> <code>{c}</code>
✦ <b>Admin Privileges:</b> <code>{a_chat}</code>
✦ <b>Songs Played (24h):</b> <code>{play_count}</code>

<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>🎶 @{client.me.username} Performance Summary</b>
"""
        await Man.edit_text(final_stats)
        
    else:
        await Man.edit_text("❌ No operational data found for this bot")


@Client.on_callback_query(filters.regex("^(end|cend)$"))
@retry()

@admin_only()
async def button_end_handler(user_client: Client, callback_query: CallbackQuery):
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})

    if callback_query.from_user.id in busers:
        await callback_query.answer(f"{upper_mono('You do not have permission to end the session!')}", show_alert=True)
        return

    try:
        bot_username = user_client.me.username
        session_client_id = connector.get(bot_username)
        session_client = clients.get(f"{session_client_id}_session")
        call_py = songs_client.get(session_client.me.id)
        song_queue = queues.get(f"dic_{user_client.me.id}")

        # Determine the chat_id based on whether "cend" is used
        chat_id = (
            (await session_client.get_chat(callback_query.message.chat.id)).linked_chat.id
            if callback_query.data == "cend"
            else callback_query.message.chat.id
        )

        is_active = await is_active_chat(user_client, chat_id)
        if is_active:
            # Clear the song queue and end the session
            await remove_active_chat(user_client, chat_id)
            song_queue[chat_id].clear()
            await call_py.leave_call(chat_id)
            await callback_query.message.reply(
                f"✅ 𝗤𝗨𝗘𝗨𝗘 𝗖𝗟𝗘𝗔𝗥𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗦𝘁𝗿𝗲𝗮𝗺𝗶𝗻𝗴 𝘀𝘁𝗼𝗽𝗽𝗲𝗱\n┗ 👤 {callback_query.from_user.mention()}"
            )
            await callback_query.message.delete()
            playing[chat_id].clear()
        else:
            await remove_active_chat(user_client, chat_id)
            await call_py.leave_call(chat_id)
            await callback_query.message.reply(
                f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!"
            )
            playing[chat_id].clear()
    except NotInCallError:
        await callback_query.answer(
            f"✅ 𝗤𝗨𝗘𝗨𝗘 𝗖𝗟𝗘𝗔𝗥𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗦𝘁𝗿𝗲𝗮𝗺𝗶𝗻𝗴 𝘀𝘁𝗼𝗽𝗽𝗲𝗱\n┗ 👤 {callback_query.from_user.mention()}",
            show_alert=True,
        )
        playing[chat_id].clear()


from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, ChatMemberUpdated


@Client.on_message(filters.video_chat_ended)

async def on_video_chat_end(client: Client, message: Message):
    """
    Handler for when a video chat/voice chat ends
    """
    try:
        await remove_active_chat(client, message.chat.id)
        if message.chat.id in playing:
            playing[message.chat.id].clear()
    except Exception as e:
        logger.info(f"Error in video chat end handler: {e}")

@Client.on_chat_member_updated()

async def on_member_kick(client: Client, chat_member_updated: ChatMemberUpdated):
    """
    Handler for when a user is kicked from the group
    """
    try:
        if (chat_member_updated.old_chat_member and 
            chat_member_updated.old_chat_member.status != ChatMemberStatus.BANNED and
            chat_member_updated.new_chat_member.status == ChatMemberStatus.BANNED):
            
            bot_username = client.me.username
            session_client_id = connector.get(bot_username)
            
            if chat_member_updated.new_chat_member.user.id == session_client_id:
                await remove_active_chat(client, chat_member_updated.chat.id)
                if chat_member_updated.chat.id in playing:
                    playing[chat_member_updated.chat.id].clear()

    except Exception as e:
        logger.info(f"Error in member kick handler: {e}")

@Client.on_message(filters.command("end"))
@retry()

@admin_only()
async def end_handler_func(user_client, message):
  try:
         await message.delete()
  except:
         pass
  user_data = collection.find_one({"user_id": user_client.me.id})
  busers = user_data.get('busers', {})
  if message.from_user.id in busers:
       return
  try:
   bot_username = user_client.me.username
   session_client_id = connector.get(bot_username)
   session_client = clients.get(f"{session_client_id}_session")
   call_py = songs_client.get(session_client.me.id)
   song_queue = queues.get(f"dic_{user_client.me.id}")
   is_active = await is_active_chat(user_client, message.chat.id)
   if is_active:
       await remove_active_chat(user_client, message.chat.id)
       song_queue[message.chat.id].clear()
       await user_client.send_message(message.chat.id, 
f"✅ 𝗤𝗨𝗘𝗨𝗘 𝗖𝗟𝗘𝗔𝗥𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗦𝘁𝗿𝗲𝗮𝗺𝗶𝗻𝗴 𝘀𝘁𝗼𝗽𝗽𝗲𝗱\n┗ 👤 {message.from_user.mention()}"            )
       await call_py.leave_call(message.chat.id)
       playing[message.chat.id].clear()
   else:
     await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!"
)
     await remove_active_chat(user_client, message.chat.id)
     await call_py.leave_call(message.chat.id)
     playing[message.chat.id].clear()
  except NotInCallError:
     await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!"
)
     playing[message.chat.id].clear()



from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

@Client.on_callback_query(filters.regex("^(skip|cskip)$"))
@retry()

@admin_only()
async def button_end_handler(user_client: Client, callback_query: CallbackQuery):
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})

    if callback_query.from_user.id in busers:
        await callback_query.answer(f"{upper_mono('You do not have permission to end the session!')}", show_alert=True)
        return

    try:
        bot_username = user_client.me.username
        session_client_id = connector.get(bot_username)
        session_client = clients.get(f"{session_client_id}_session")
        call_py = songs_client.get(session_client.me.id)
        song_queue = queues.get(f"dic_{user_client.me.id}")

        chat_id = (
            (await session_client.get_chat(callback_query.message.chat.id)).linked_chat.id
            if callback_query.data == "cskip"
            else callback_query.message.chat.id
        )

        if chat_id in song_queue:
         if len(song_queue[chat_id]) >0:
            next = song_queue[chat_id].pop(0)
            await callback_query.message.reply(f"⏭️ 𝗦𝗞𝗜𝗣𝗣𝗜𝗡𝗚!\n┏━━━━━━━━━━━━━━\n┣ 𝗡𝗲𝘅𝘁 𝘁𝗿𝗮𝗰𝗸 𝗹𝗼𝗮𝗱𝗶𝗻𝗴...\n┗ 👤 {callback_query.from_user.mention()}")
            try:
                await call_py.pause(chat_id)
            except:
                pass
            await join_call(next['message'],
 next['title'], next['session'], next['yt_link'], next['chat'], next['by'], next['duration'], next['mode'], next['thumb']
)
         else:
            await call_py.leave_call(chat_id)
            await remove_active_chat(user_client, chat_id)
            await callback_query.message.reply(f"🚫 𝗦𝗞𝗜𝗣𝗣𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗤𝘂𝗲𝘂𝗲 𝗶𝘀 𝗻𝗼𝘄 𝗲𝗺𝗽𝘁𝘆!\n┗ 👤 {callback_query.from_user.mention()}")
            playing[chat_id].clear()
            await callback_query.message.delete()
        else:
            await remove_active_chat(user_client, chat_id)
            await call_py.leave_call(chat_id)
            await callback_query.message.reply(
                f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!"
            )
            playing[chat_id].clear()
    except NotInCallError:
        await callback_query.answer(
            f"✅ 𝗤𝗨𝗘𝗨𝗘 𝗖𝗟𝗘𝗔𝗥𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗦𝘁𝗿𝗲𝗮𝗺𝗶𝗻𝗴 𝘀𝘁𝗼𝗽𝗽𝗲𝗱\n┗ 👤 {callback_query.from_user.mention()}",
            show_alert=True,
        )
        playing[chat_id].clear()

@Client.on_message(filters.command("loop"))
@retry()

@admin_only()
async def loop_handler_func(user_client, message):
    try:
        await message.delete()
    except:
        pass
    
    # Check if user is banned
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})
    if message.from_user.id in busers:
        return

    try:
        # Get loop count from command
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await user_client.send_message(
                message.chat.id,
                "❌ Please specify the number of loops.\nUsage: /loop <number>"
            )
            return
        
        try:
            loop_count = int(command_parts[1])
            if loop_count <= 0 or loop_count > 20:
                await user_client.send_message(
                    message.chat.id,
                    "❌ Loop count must be from 0-20!"
                )
                return
        except ValueError:
            await user_client.send_message(
                message.chat.id,
                "❌ Please provide a valid number for loops!"
            )
            return

        # Check if there's a song playing
        if message.chat.id in playing and playing[message.chat.id]:
            current_song = playing[message.chat.id]
            song_queue = queues.get(f"dic_{user_client.me.id}")
            
            # Initialize queue for this chat if it doesn't exist
            if message.chat.id not in song_queue:
                song_queue[message.chat.id] = []
            
            # Add the current song to queue multiple times
            for _ in range(loop_count):
                song_queue[message.chat.id].insert(0, current_song)
            
            await user_client.send_message(
                message.chat.id,
                f"{upper_mono(f'Current song will be repeated {loop_count} times!')}\n\nʙʏ: {message.from_user.mention()}"
            )
        else:
            await user_client.send_message(
                message.chat.id,
                f"{upper_mono('Assistant is not streaming anything!')}"
            )
            
    except Exception as e:
        await user_client.send_message(
            message.chat.id,
            f"❌ An error occurred: {str(e)}"
        )

@Client.on_message(filters.command("skip"))
@retry()

@admin_only()
async def skip_handler_func(user_client, message):
  try:
         await message.delete()
  except:
         pass
  user_data = collection.find_one({"user_id": user_client.me.id})
  busers = user_data.get('busers', {})
  if message.from_user.id in busers:
       return
  try:
   bot_username = user_client.me.username
   session_client_id = connector.get(bot_username)
   session_client = clients.get(f"{session_client_id}_session")
   call_py = songs_client.get(session_client.me.id)
   song_queue = queues.get(f"dic_{user_client.me.id}")
   if message.chat.id in song_queue:
    if len(song_queue[message.chat.id]) >0:
       next = song_queue[message.chat.id].pop(0)
       await user_client.send_message(message.chat.id, f"⏭️ 𝗦𝗞𝗜𝗣𝗣𝗜𝗡𝗚!\n┏━━━━━━━━━━━━━━\n┣ 𝗡𝗲𝘅𝘁 𝘁𝗿𝗮𝗰𝗸 𝗹𝗼𝗮𝗱𝗶𝗻𝗴...\n┗ 👤 {message.from_user.mention()}")
       playing[message.chat.id] = next
       try:
          await call_py.pause(message.chat.id)
       except:
          pass
       await join_call(next['message'], next['title'], next['session'], next['yt_link'], next['chat'], next['by'], next['duration'], next['mode'], next['thumb']
)
    else:
       await call_py.leave_call(message.chat.id)
       await remove_active_chat(user_client, message.chat.id)
       await user_client.send_message(message.chat.id, f"🚫 𝗦𝗞𝗜𝗣𝗣𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗤𝘂𝗲𝘂𝗲 𝗶𝘀 𝗻𝗼𝘄 𝗲𝗺𝗽𝘁𝘆!\n┗ 👤 {message.from_user.mention()}")
       playing[message.chat.id].clear()
   else:
       await call_py.leave_call(message.chat.id)
       await remove_active_chat(user_client, message.chat.id)
       await user_client.send_message(message.chat.id, 
              f"🚫 𝗦𝗞𝗜𝗣𝗣𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗤𝘂𝗲𝘂𝗲 𝗶𝘀 𝗻𝗼𝘄 𝗲𝗺𝗽𝘁𝘆!\n┗ 👤 {message.from_user.mention()}")
       playing[message.chat.id].clear()
  except NotInCallError:
     await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!"
)
     playing[message.chat.id].clear()



@Client.on_callback_query(filters.regex("^(resume|cresume)$"))
@retry()

@admin_only()
async def button_resume_handler(user_client: Client, callback_query: CallbackQuery):
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})

    if callback_query.from_user.id in busers:
        await callback_query.answer("You don't have permission to resume!", show_alert=True)
        return

    try:
        bot_username = user_client.me.username
        session_client_id = connector.get(bot_username)
        session_client = clients.get(f"{session_client_id}_session")
        call_py = songs_client.get(session_client.me.id)

        chat_id = (
            (await session_client.get_chat(callback_query.message.chat.id)).linked_chat.id
            if callback_query.data == "cresume"
            else callback_query.message.chat.id
        )

        if await is_active_chat(user_client, chat_id):
            await call_py.resume(chat_id)
            await callback_query.message.reply(
                f"{upper_mono('Song resumed. Use the Pause button to pause again.')}\n\nʙʏ: {callback_query.from_user.mention()}"
            )
        else:
            await callback_query.answer(f"{upper_mono('Assistant is not streaming anything!')}")
    except NotInCallError:
        await callback_query.answer(f"{upper_mono('Assistant is not streaming anything!')}", show_alert=True)


@Client.on_callback_query(filters.regex("^(pause|cpause)$"))
@retry()

@admin_only()
async def button_pause_handler(user_client: Client, callback_query: CallbackQuery):
    user_data = collection.find_one({"user_id": user_client.me.id})
    busers = user_data.get('busers', {})

    if callback_query.from_user.id in busers:
        await callback_query.answer("You don't have permission to pause!", show_alert=True)
        return

    try:
        bot_username = user_client.me.username
        session_client_id = connector.get(bot_username)
        session_client = clients.get(f"{session_client_id}_session")
        call_py = songs_client.get(session_client.me.id)

        chat_id = (
            (await session_client.get_chat(callback_query.message.chat.id)).linked_chat.id
            if callback_query.data == "cpause"
            else callback_query.message.chat.id
        )

        if await is_active_chat(user_client, chat_id):
            await call_py.pause(chat_id)
            await callback_query.message.reply(
                f"{upper_mono('Song paused. Use the Resume button to continue.')}\n\nʙʏ: {callback_query.from_user.mention()}"
            )
        else:
            await callback_query.answer(f"{upper_mono('Assistant is not streaming anything!')}")
    except NotInCallError:
        await callback_query.answer(f"{upper_mono('Assistant is not streaming anything!')}", show_alert=True)

@Client.on_message(filters.command("resume"))
@retry()

@admin_only()
async def resume_handler_func(user_client, message):
  user_data = collection.find_one({"user_id": user_client.me.id})
  busers = user_data.get('busers', {})
  if message.from_user.id in busers:
       return
  try:
   bot_username = user_client.me.username
   session_client_id = connector.get(bot_username)
   session_client = clients.get(f"{session_client_id}_session")
   call_py = songs_client.get(session_client.me.id)
   if  await is_active_chat(user_client, message.chat.id):
       await call_py.resume(message.chat.id)
       await user_client.send_message(message.chat.id, f"▶️ 𝗥𝗘𝗦𝗨𝗠𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗨𝘀𝗲 /𝗽𝗮𝘂𝘀𝗲 𝘁𝗼 𝘀𝘁𝗼𝗽\n┗ 👤 {message.from_user.mention()}")
   else: await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!")
  except NotInCallError:
     await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!")


@Client.on_message(filters.command("pause"))
@retry()

@admin_only()
async def pause_handler_func(user_client, message):
  user_data = collection.find_one({"user_id": user_client.me.id})
  busers = user_data.get('busers', {})
  if message.from_user.id in busers:
       return
  try:
   bot_username = user_client.me.username
   session_client_id = connector.get(bot_username)
   session_client = clients.get(f"{session_client_id}_session")
   call_py = songs_client.get(session_client.me.id)
   if  await is_active_chat(user_client, message.chat.id):
       await call_py.pause(message.chat.id)
       await user_client.send_message(message.chat.id, f"⏸️ 𝗣𝗔𝗨𝗦𝗘𝗗!\n┏━━━━━━━━━━━━━━\n┣ 𝗨𝘀𝗲 /𝗿𝗲𝘀𝘂𝗺𝗲 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲\n┗ 👤 {message.from_user.mention()}"
)
   else:
       await user_client.send_message(message.chat.id,  f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!")
  except NotInCallError:
     await user_client.send_message(message.chat.id, f"🚫 𝗡𝗢 𝗦𝗧𝗥𝗘𝗔𝗠!\n┏━━━━━━━━━━━━━━\n┣ 𝗔𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝘁 𝗶𝗱𝗹𝗲\n┗ 🎧 𝗡𝗼𝘁𝗵𝗶𝗻𝗴 𝗽𝗹𝗮𝘆𝗶𝗻𝗴!")

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_callback_query(filters.regex("broadcast"))
@retry()

async def broadcast_callback_handler(client, callback_query: CallbackQuery):
    owner_id = get_owner_id_by_client(client)
    # Fetch user data for the callback query
    user_data = user_sessions.find_one({"user_id": owner_id})
    if not user_data:
        return await callback_query.answer("User data not found.", show_alert=True)

    group = user_data.get('group')
    private = user_data.get('private')
    ugroup = user_data.get('ugroup')
    uprivate = user_data.get('uprivate')
    bot = user_data.get('bot')
    userbot = user_data.get('userbot')
    pin = user_data.get('pin')
    await callback_query.message.delete()
    # Fetch bot data
    bot_data = collection.find_one({"user_id": client.me.id})
    message_to_broadcast, forwarding = broadcast_message.get(client.me.id)
    if bot_data and bot:
        X = await callback_query.message.reply("Starting broadcast from bot")
        users = bot_data.get('users', [])
        progress_msg = ""
        u, g, sg, a_chat = 0, 0, 0, 0

        # Use asyncio.gather for efficient parallel processing
        chat_types = await asyncio.gather(
            *[get_chat_type(client, chat_id) for chat_id in users]
        )
        
        # Prepare message for broadcast
        if not message_to_broadcast:
            return await callback_query.answer("No message ready for broadcast.", show_alert=True)

        for i, chat_type in enumerate(chat_types):
            if not chat_type:
                continue  # Skip if chat type could not be fetched

            # Handle the chat based on its type and flags
            try:
                if chat_type == enums.ChatType.PRIVATE and private:
                    await message_to_broadcast.copy(users[i])  if not forwarding else await message_to_broadcast.forward(users[i])
                    u+=1

                elif chat_type in (enums.ChatType.SUPERGROUP, enums.ChatType.GROUP) and group:
                    # Handle supergroup-specific actions
                    sent_message = await message_to_broadcast.copy(users[i]) if not forwarding else await message_to_broadcast.forward(users[i])
                    if chat_type == enums.ChatType.SUPERGROUP:
                        sg+=1
                    else:
                        g+=1
                    if pin:
                      try:
                        user_s = await client.get_chat_member(users[i], client.me.id)
                        if user_s.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR):
                            await sent_message.pin()
                            a_chat += 1
                      except FloodWait as e:
                              await asyncio.sleep(e.value)
                      except Exception as e:
                        logger.info(f"Error getting chat member status for {users[i]}: {e}")
                else:
                       continue

                # Update progress for each broadcast action (optional)
                progress_msg = f"Broadcasting to {u} private, {g} groups, {sg} supergroups, and {a_chat} pinned messages"
                await X.edit(progress_msg)
            except Exception as e:
                logger.info(f"Error in broadcasting to {users[i]}: {e}")
        await X.edit(f"Broadcasted to {u} private, {g} groups, {sg} supergroups, and {a_chat} pinned messages from bot")
    bot_username = client.me.username
    session_client_id = connector.get(bot_username)
    session_client = clients.get(f"{session_client_id}_session")

    if userbot and session_client:
        XX = await callback_query.message.reply("Starting broadcast from assistant")
        uu, ug, usg, ua_chat = 0, 0, 0, 0
        try:
            # Ensure communication with the bot
            try:
                await session_client.get_chat(client.me.id)
            except PeerIdInvalid:
                await session_client.send_message(bot_username, "/start")
            except UserBlocked:
                await session_client.unblock_user(bot_username)
            await asyncio.sleep(1)

            # Copy the message to session_client and fetch history
            copied_message = await message_to_broadcast.copy(session_client.me.id) if not forwarding else await message_to_broadcast.forward(session_client.me.id)
            await asyncio.sleep(2)

            msg = await compare_message(copied_message, client, session_client)
            if not msg:
             raise Exception("broadcast msg not found")
            # Broadcast to all dialogs
            async for dialog in session_client.get_dialogs():
                chat_id = dialog.chat.id
                chat_type = dialog.chat.type
                if str(chat_id) == str(-1001806816712):
                      continue
                try:
                    if chat_type == enums.ChatType.PRIVATE and uprivate:
                        await msg.copy(chat_id)
                        uu += 1

                    elif chat_type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP) and ugroup:
                        sent_message = await msg.copy(chat_id)  if not forwarding else await message_to_broadcast.forward(users[i])
                        if chat_type == enums.ChatType.SUPERGROUP:
                            usg += 1
                        else:
                            ug += 1

                    else:
                       continue
                    # Update progress
                    progress_text = (
                        f"Broadcasting via assistant...\n\n"
                        f"Private Chats: {uu}\n"
                        f"Groups: {ug}\n"
                        f"Supergroups: {usg}\n"
                    )
                    await XX.edit(progress_text)
                except FloodWait as e:
                               await asyncio.sleep(e.value)
                except Exception as e:
                    logger.info(f"Error broadcasting to {chat_id}: {e}")

        except Exception as e:
            logger.info(f"Error with session_client broadcast: {e}")
            await XX.reply(f"An error occurred during userbot broadcasting.{e}")

    # Finalize broadcast summary
        await XX.edit(
        f"Broadcast completed!\n\n"
        f"Private Chats: {uu}\n"
        f"Groups: {ug}\n"
        f"Supergroups: {usg}\n"
    )



async def get_status(client):
  bot_username = client.me.username
  session_client_id = connector.get(bot_username)

  session_client = clients.get(f"{session_client_id}_session")
  start = datetime.datetime.now()
  u = g = sg = a_chat =  0 # Initialize counters
  user_data = collection.find_one({"user_id": client.me.id})
  mess=""

  if user_data:
    users = user_data.get('users', [])
    progress_msg = ""


    # Use asyncio.gather for efficient parallel processing
    chat_types = await asyncio.gather(
      *[get_chat_type(client, chat_id) for chat_id in users]
    )
    for i, chat_type in enumerate(chat_types):
      if chat_type is None:
        continue # Skip if chat type could not be fetched

      if chat_type == enums.ChatType.PRIVATE:
        u += 1
      elif chat_type ==  enums.ChatType.GROUP:
        g += 1
      elif chat_type == enums.ChatType.SUPERGROUP:
        sg += 1
        try:
          user_s = await client.get_chat_member(users[i], int(client.me.id))
          if user_s.status in (
            enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.ADMINISTRATOR,
          ):
            a_chat += 1
        except Exception as e:
          logger.info(f"Error getting chat member status for {users[i]}: {e}")
    mess += (
        f"""<b>BOT STATS:</b>
<blockquote><b>`Private chats = {u}</b>`
<b>`Groups = {g}`
<b>`Super Groups = {sg}`<b>
<b>`Admin in Chats = {a_chat}`</b></blockquote>""")

      #Update the progress message every 10 iterations.
    uu = ug = usg  = ua_chat =0
    async for dialog in session_client.get_dialogs():
      try:
        if dialog.chat.type == enums.ChatType.PRIVATE:
            uu += 1
        elif dialog.chat.type == enums.ChatType.GROUP:
            ug += 1
        elif dialog.chat.type == enums.ChatType.SUPERGROUP:
            usg += 1
            user_s = await dialog.chat.get_member(int(session_client.me.id))
            if user_s.status in (
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.ADMINISTRATOR,
            ):
                ua_chat += 1
      except:
        pass
        # Count blocked users from the blocklist
    # Final message with stats

    mess += (
        f"""\n\n<b>ASSISTANT STATS:</b>
<blockquote><b>`Private Messages = {uu}`
<b>`Groups = {ug}`
<b>`Super Groups = {usg}`<b>
<b>`Admin in Chats = {ua_chat}`</b></blockquote>"""
    )
    mess += (f"\n\n<blockquote><b>CHOOSE THE OPTIONS BELOW⬇️⬇️ FOR BRODCASTING</b></blockquote>")
    broadcasts[client.me.id] = mess
    return mess
  else:
    return

async def compare_message(mess, client, session_client):
    async for msg in session_client.get_chat_history(chat_id=client.me.id, limit=2):
        # Compare text messages
        if mess.text and msg.text == mess.text:
            return msg
        
        # Compare media messages
        elif mess.media and msg.media:
            try:
                # Get the media type (photo, video, etc.)
                mess_media_type = mess.media.value
                msg_media_type = msg.media.value
                
                # Check if both messages have the same media type
                if mess_media_type == msg_media_type:
                    # Get file unique IDs for comparison
                    mess_file_id = getattr(mess, mess_media_type).file_unique_id
                    msg_file_id = getattr(msg, msg_media_type).file_unique_id
                    
                    # Compare file IDs
                    if mess_file_id and msg_file_id and mess_file_id == msg_file_id:
                        return msg
            except AttributeError:
                # Skip if media attributes are not accessible
                continue
    
    # Return None if no matching message is found
    return None

@Client.on_callback_query(filters.regex(r"toggle_(.*)"))
@retry()

async def toggle_setting(client, callback_query):
    sender_id = get_owner_id_by_client(client)

    user_data = user_sessions.find_one({"user_id": sender_id})
    if not user_data:
        return await callback_query.answer("User data not found. Please log in first.", show_alert=True)
    setting_to_toggle = callback_query.data.split("_", 1)[1]
    current_value = user_data.get(setting_to_toggle)
    new_value = not current_value
    user_sessions.update_one(
        {"user_id": sender_id},
        {"$set": {setting_to_toggle: new_value}}
    )
    await broadcast_command_handler(client, callback_query)


@Client.on_message(filters.command("stats"))
@retry()

async def status_command_handler(client, message):
    user_id = message.from_user.id
    admin_file = f"{ggg}/admin.txt"

    # Get user data and permissions
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
        is_admin or
        get_user_id_by_client(user_id, client) or
        (user_id in sudoers and premium_by == "PAID")
    )

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS OWNER/SUDOER'S COMMAND...**")

    await status(client, message)



@Client.on_message(filters.command(["broadcast", "fbroadcast"]) & filters.private)
@retry()

async def broadcast_command_handler(client, message):
    user_id = message.from_user.id
    admin_file = f"{ggg}/admin.txt"
    users_data = user_sessions.find_one({"user_id": get_owner_id_by_client(client)})
    sudoers = users_data.get("SUDOERS", [])
    premium_by = collection.find_one({"user_id": get_owner_id_by_client(client)}, {"premium_by": 1}).get("premium_by", "TRIAL")

    is_admin = False
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            is_admin = user_id in admin_ids

    # Check permissions
    is_authorized = (
    is_admin or (
        (get_user_id_by_client(user_id, client) or user_id in sudoers) and premium_by == "PAID"
    )
)

    if not is_authorized:
        return await message.reply("**MF\n\nTHIS IS PAID OWNER/SUDOER'S COMMAND...**")

    sender_id = get_owner_id_by_client(client)
    user_data = user_sessions.find_one({"user_id": sender_id})
    if not user_data:
        return await message.reply("User data not found. Please log in first.")
    if not isinstance(message, CallbackQuery):
      if not message.reply_to_message:
        return await message.reply("please reply to any message to brodcaste")
      broadcast_message[client.me.id] = [message.reply_to_message]
      broadcast_message[client.me.id].append(True if message.command[0].lower().startswith("f") else None)
    group = user_data.get('group')
    private = user_data.get('private')
    ugroup = user_data.get('ugroup')
    uprivate = user_data.get('uprivate')
    bot = user_data.get('bot')
    userbot = user_data.get('userbot')
    pin = user_data.get('pin')
    for_bot =[
            InlineKeyboardButton(f"Gʀᴏᴜᴘ {'✅' if group else '❌'}", callback_data="toggle_group"),
            InlineKeyboardButton(f"Pʀɪᴠᴀᴛᴇ {'✅' if private else '❌'}", callback_data="toggle_private"),
            InlineKeyboardButton(f"📌Pɪɴ {'✅' if pin else '❌'}", callback_data="toggle_pin"),]

    for_userbot = [
            InlineKeyboardButton(f"Gʀᴏᴜᴘ {'✅' if ugroup else '❌'}", callback_data="toggle_ugroup"),
            InlineKeyboardButton(f"Pʀɪᴠᴀᴛᴇ {'✅' if uprivate else '❌'}", callback_data="toggle_uprivate"),]
    buttons = [
            [InlineKeyboardButton(f"Fʀᴏᴍ ʙᴏᴛ {'⬇️' if bot else '❌'}", callback_data="toggle_bot"),], for_bot if bot else [],
        [
            InlineKeyboardButton(f"Fʀᴏᴍ ᴜꜱᴇʀʙᴏᴛ {'⬇️' if userbot else '❌'}", callback_data="toggle_userbot"),], for_userbot if userbot else [],
    ]


    buttons.append([InlineKeyboardButton("BROADCAST🚀🚀", callback_data="broadcast")])
    if isinstance(message, CallbackQuery):  # If it's a button click (CallbackQuery)
        if not client.me.id in broadcasts:
           await get_status(client)
        await message.edit_message_text(
            broadcasts[client.me.id],
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:  # If it's a normal command message
        mess = await message.reply("Getting all chats, please wait...")
        await get_status(client)
        if broadcasts[client.me.id]:
           await mess.edit(
            broadcasts[client.me.id],
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        else:
           await message.reply("No data found")



@Client.on_message(filters.command("powers") & filters.group)
@retry()

@admin_only()
async def handle_power_command(client, message):
    try:
        # Get bot's permissions in the group
        bot_member = await client.get_chat_member(
            chat_id=message.chat.id,
            user_id=client.me.id if not message.reply_to_message else message.reply_to_message.from_user.id
        )
        
        # Get chat info
        chat = await client.get_chat(message.chat.id)
        
        # Create permission status message
        power_message = (
            f"🤖 **{'Bot' if not message.reply_to_message else message.reply_to_message.from_user.mention()} Permissions in {chat.title}**\n\n"
            "📋 **Basic Powers:**\n"
        )
        
        # Basic permissions
        permissions = {
            "can_delete_messages": "Delete Messages",
            "can_restrict_members": "Restrict Members",
            "can_promote_members": "Promote Members",
            "can_change_info": "Change Group Info",
            "can_invite_users": "Invite Users",
            "can_pin_messages": "Pin Messages",
            "can_manage_video_chats": "Manage Video Chats",
            "can_manage_chat": "Manage Chat",
            "can_manage_topics": "Manage Topics"
        }
        
        # Add permission statuses
        for perm, display_name in permissions.items():
            status = getattr(bot_member.privileges, perm, False)
            emoji = "✅" if status else "❌"
            power_message += f"{emoji} {display_name}\n"
            
        # Add administrative status
        power_message += "\n📊 **Status:**\n"
        if bot_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
            power_message += "✨ Bot is an **Administrator**"
        elif bot_member.status == enums.ChatMemberStatus.MEMBER:
            power_message += "👤 Bot is a **Regular Member**"
        else:
            power_message += "❓ Bot Status: " + str(bot_member.status).title()
            
        # Add anonymous admin status if applicable
        if hasattr(bot_member.privileges, "is_anonymous"):
            anon_status = "✅" if bot_member.privileges.is_anonymous else "❌"
            power_message += f"\n{anon_status} Anonymous Admin"
            
        # Add custom title if exists
        if hasattr(bot_member, "custom_title") and bot_member.custom_title:
            power_message += f"\n👑 Custom Title: **{bot_member.custom_title}**"
            
        # Create inline buttons for refresh and support
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_power_{message.chat.id}"),
            ]
        ])
        
        await message.reply(
            power_message,
            #reply_markup=buttons
        )
        
    except Exception as e:
        logger.error(f"Power check error: {e}")
        await message.reply("❌ Failed to check bot permissions!")

# Callback handler for refresh button
#@Client.on_callback_query(filters.regex("^refresh_power_"))
#
#@admin_only()
async def refresh_power(client, callback_query):
    try:
        # Extract chat_id from callback data
        chat_id = int(callback_query.data.split("_")[2])
        
        # Check if the user who clicked is the one who requested
        if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
            await callback_query.answer("⚠️ Only the command invoker can refresh!", show_alert=True)
            return
            
        # Get updated bot permissions
        bot_member = await client.get_chat_member(
            chat_id=chat_id,
            user_id=client.me.id
        )
        
        # Get chat info
        chat = await client.get_chat(chat_id)
        
        # Create updated permission status message
        power_message = (
            f"🤖 **Bot Permissions in {chat.title}**\n\n"
            "📋 **Basic Powers:**\n"
        )
        
        # Basic permissions
        permissions = {
            "can_delete_messages": "Delete Messages",
            "can_restrict_members": "Restrict Members",
            "can_promote_members": "Promote Members",
            "can_change_info": "Change Group Info",
            "can_invite_users": "Invite Users",
            "can_pin_messages": "Pin Messages",
            "can_manage_video_chats": "Manage Video Chats",
            "can_manage_chat": "Manage Chat",
            "can_manage_topics": "Manage Topics"
        }
        
        # Add permission statuses
        for perm, display_name in permissions.items():
            status = getattr(bot_member.privileges, perm, False)
            emoji = "✅" if status else "❌"
            power_message += f"{emoji} {display_name}\n"
            
        # Add administrative status
        power_message += "\n📊 **Status:**\n"
        if bot_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
            power_message += "✨ Bot is an **Administrator**"
        elif bot_member.status == enums.ChatMemberStatus.MEMBER:
            power_message += "👤 Bot is a **Regular Member**"
        else:
            power_message += "❓ Bot Status: " + str(bot_member.status).title()
            
        # Add anonymous admin status if applicable
        if hasattr(bot_member.privileges, "is_anonymous"):
            anon_status = "✅" if bot_member.privileges.is_anonymous else "❌"
            power_message += f"\n{anon_status} Anonymous Admin"
            
        # Add custom title if exists
        if hasattr(bot_member, "custom_title") and bot_member.custom_title:
            power_message += f"\n👑 Custom Title: **{bot_member.custom_title}**"
        
        # Update the message with the same buttons
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_power_{chat_id}"),
            ]
        ])
        
        await callback_query.message.edit_text(
            power_message,
            reply_markup=buttons
        )
        
        await callback_query.answer("✅ Permissions refreshed!")
        
    except Exception as e:
        logger.error(f"Power refresh error: {e}")
        await callback_query.answer("❌ Failed to refresh permissions!", show_alert=True)




@Client.on_message(filters.command("qt"))
@retry()

async def duck_command_handler(client, message):
    if message.reply_to_message:
      try:
        sender = message.from_user.id
        session_name = f'user_{sender}'
        user_dir = f"{ggg}/{session_name}"
        os.makedirs(user_dir, exist_ok=True)
        # Extract information from the replied message
        replied_message = message.reply_to_message
        text = message.text.replace("/qt ",'')  # Split the message into words
        user = replied_message.from_user
        username = " ".join([user.first_name, user.last_name] if user.last_name else [user.first_name])
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
         with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if user.id in admin_ids:
                return await message.reply("You are fucking requesting me to create fake quote of my lord and my creator.\nSo Iwon't...**Fuck off!!**")
        is_admin = False
        admin_file = f"{ggg}/admin.txt"
        if os.path.exists(admin_file):
          with open(admin_file, "r") as file:
             admin_ids = [int(line.strip()) for line in file.readlines()]
             is_admin = sender in admin_ids
        owner_id = get_owner_id_by_client(client)
        if not is_admin and int(owner_id) == int(user.id):
                return await message.reply("You are fucking requesting me to create fake quote of my lord and my creator.\nSo Iwon't...**Fuck off!!**")
        try:
          await message.delete()
        except:
          pass
        session_name = f'user_{client.me.id}'
        user_dir = f"{ggg}/{session_name}"
        os.makedirs(user_dir, exist_ok=True)
        # Check if the user has a profile photo
        photo = user.photo.big_file_id if user.photo else None
        json ={
  "type": "quote",
  "format": "webp",
  "backgroundColor": "#1b1429",
  "width": 512,
  "height": 768,
  "scale": 2,
  "messages": [
    {
      "entities": [],
      "chatId": message.chat.id,
      "avatar": True,
      "from": {
        "id": user.id,
        "name": username,
        "photo":photo
      },
      "text": text,
      "replyMessage": {}
    }
  ]
}

        # Send a POST request to the Quotly API to generate the sticker

        response = requests.post('https://bot.lyo.su/quote/generate', json=json).json()
        buffer = base64.b64decode(response['result']['image'].encode('utf-8'))
        open(f'{user_dir}/Quotly.webp', 'wb').write(buffer)
            # Send the sticker

        await client.send_sticker(chat_id=message.chat.id , sticker=f'{user_dir}/Quotly.webp',reply_to_message_id=replied_message.id)
        await client.send_sticker(chat_id=app.me.id , sticker=f'{user_dir}/Quotly.webp')
      except Exception as e:
         logger.info(e)

@Client.on_message(filters.command("ping"))
@retry()

async def pingme(client, message):
    # Calculate uptime
    from random import choice
    uptime = await get_readable_time((time.time() - StartTime))
    start = datetime.datetime.now()
    owner_id = get_owner_id_by_client(client)
    owner = await client.get_users(owner_id)
    ow_id = owner.id if owner.username else None
    # Fun emoji animations for loading
    loading_emojis = ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
    ping_frames = [
        "█▒▒▒▒▒▒▒▒▒▒ 10%",
        "███▒▒▒▒▒▒▒ 30%",
        "█████▒▒▒▒▒ 50%",
        "███████▒▒▒ 70%",
        "█████████▒ 90%",
        "██████████ 100%"
    ]

    # Animated loading sequence
    msg = await message.reply_text("🏓 **Pinging...**")

    for frame in ping_frames:
        await msg.edit(f"```\n{frame}\n```{choice(loading_emojis)}")
        await asyncio.sleep(0.3)  # Smooth animation delay

    end = datetime.datetime.now()
    ping_duration = (end - start).microseconds / 1000

    # Status indicators based on ping speed
    if ping_duration < 100:
        status = "EXCELLENT 🟢"
    elif ping_duration < 200:
        status = "GOOD 🟡"
    else:
        status = "MODERATE 🔴"

    # Fancy formatted response
    response = f"""
╭──────────────────
│   PONG! 🏓
├──────────────────
│ ⌚ Speed: {ping_duration:.2f}ms
│ 📊 Status: {status}
│ ⏱️ Uptime: {uptime}
│ 👑 Owner: {owner.mention() if ow_id else f'[MUSIC BOT HOSTER ⚡](http://t.me/nub_hoster_bot?start={owner_id})'}
╰──────────────────
"""

    # Add random motivational messages
    quotes = [
        "Blazing fast! ⚡",
        "Speed demon! 🔥",
        "Lightning quick! ⚡",
        "Sonic boom! 💨"
    ]

    await msg.edit(
        response + f"\n<b>{choice(quotes)}</b>"
    )

from pyrogram import Client, enums, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os

@Client.on_message(filters.command("about"))
@retry()

async def info_command(client: Client, message: Message):
    chat = message.chat
    replied = message.reply_to_message
    
    # Setup user directory
    session_name = f'user_{client.me.id}'
    user_dir = f"{ggg}/{session_name}"
    os.makedirs(user_dir, exist_ok=True)
    photo_path = f"{user_dir}/logo.jpg"
    
    def create_copy_markup(text: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("Copy Info", copy_text=text)
        ]])

    # Handle second argument if provided
    target_user = None
    if len(message.command) > 1:
        user_input = message.command[1]
        try:
            # Try to get user by ID first
            if user_input.isdigit():
                target_user = await client.get_users(int(user_input))
            else:
                # If not ID, try username (with or without @ symbol)
                username = user_input.strip('@')
                target_user = await client.get_users(username)
        except Exception:
            await message.reply("❌ User not found. Please provide a valid username or ID.")
            return

    if target_user:
        # Handle user specified by argument
        user = target_user
        response = (
            "👤 **User Info**\n"
            f"🆔 **ID**: `{user.id}`\n"
            f"📛 **Name**: {user.first_name}"
        )
        if user.last_name:
            response += f" {user.last_name}\n"
        else:
            response += "\n"
        
        if user.username:
            response += f"🌐 **Username**: @{user.username}\n"
        
        # Add restriction, scam, and fake flags
        if user.is_restricted:
            response += "⚠️ **Account Restricted**: Yes\n"
            if user.restriction_reason:
                response += f"📝 **Restriction Reason**: {user.restriction_reason}\n"
        if user.is_scam:
            response += "🚫 **Scam Account**: Yes\n"
        if user.is_fake:
            response += "🎭 **Impersonator**: Yes\n"
        
        # Add status and join date for group queries
        if chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            try:
                member = await client.get_chat_member(chat.id, user.id)
                status_map = {
                    enums.ChatMemberStatus.OWNER: "👑 Owner",
                    enums.ChatMemberStatus.ADMINISTRATOR: "🔧 Admin",
                    enums.ChatMemberStatus.MEMBER: "👤 Member"
                }
                response += f"🎚 **Status**: {status_map.get(member.status, 'Unknown')}\n"
                
                if member.joined_date:
                    join_date = member.joined_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                    response += f"📅 **Joined**: {join_date}\n"
                else:
                    response += "📅 **Joined**: Unknown\n"
            except Exception:
                response += "🎚 **Status**: ❌ Not in group\n"
        
        # Handle profile photo
        if user.photo:
            try:
                await client.download_media(user.photo.big_file_id, photo_path)
                await message.reply_photo(
                    photo_path,
                    caption=response,
                    reply_markup=create_copy_markup(response)
                )
            except Exception:
                await message.reply(
                    response,
                    reply_markup=create_copy_markup(response)
                )
        else:
            await message.reply(
                response,
                reply_markup=create_copy_markup(response)
            )
        return

    # Rest of the original code for replied messages and chat info remains the same
    if replied:
        if replied.sender_chat:
            sender_chat = replied.sender_chat
            if sender_chat.id == chat.id:
                response = (
                    "👤 **Anonymous Group Admin**\n"
                    f"🏷 **Title**: {sender_chat.title}\n"
                    f"🆔 **Chat ID**: `{sender_chat.id}`"
                )
            else:
                response = (
                    "📢 **Channel Info**\n"
                    f"🏷 **Title**: {sender_chat.title}\n"
                    f"🆔 **ID**: `{sender_chat.id}`\n"
                )
                if sender_chat.username:
                    response += f"🌐 **Username**: @{sender_chat.username}\n"
                if sender_chat.description:
                    response += f"📄 **Description**: {sender_chat.description[:300]}..."
                
            await message.reply(
                response,
                reply_markup=create_copy_markup(response)
            )
            
        else:
            user = await client.get_users(replied.from_user.id)
            
            response = (
                "👤 **User Info**\n"
                f"🆔 **ID**: `{user.id}`\n"
                f"📛 **Name**: {user.first_name}"
            )
            if user.last_name:
                response += f" {user.last_name}\n"
            else:
                response += "\n"
            
            if user.username:
                response += f"🌐 **Username**: @{user.username}\n"
            
            if user.is_restricted:
                response += "⚠️ **Account Restricted**: Yes\n"
                if user.restriction_reason:
                    response += f"📝 **Restriction Reason**: {user.restriction_reason}\n"
            if user.is_scam:
                response += "🚫 **Scam Account**: Yes\n"
            if user.is_fake:
                response += "🎭 **Impersonator**: Yes\n"
            
            if chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                try:
                    member = await client.get_chat_member(chat.id, user.id)
                    status_map = {
                        enums.ChatMemberStatus.OWNER: "👑 Owner",
                        enums.ChatMemberStatus.ADMINISTRATOR: "🔧 Admin",
                        enums.ChatMemberStatus.MEMBER: "👤 Member"
                    }
                    response += f"🎚 **Status**: {status_map.get(member.status, 'Unknown')}\n"
                    
                    if member.joined_date:
                        join_date = member.joined_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                        response += f"📅 **Joined**: {join_date}\n"
                    else:
                        response += "📅 **Joined**: Unknown\n"
                except Exception:
                    response += "🎚 **Status**: ❌ Not in group\n"
            
            if user.photo:
                try:
                    await client.download_media(user.photo.big_file_id, photo_path)
                    await message.reply_photo(
                        photo_path,
                        caption=response,
                        reply_markup=create_copy_markup(response)
                    )
                except Exception:
                    await message.reply(
                        response,
                        reply_markup=create_copy_markup(response)
                    )
            else:
                await message.reply(
                    response,
                    reply_markup=create_copy_markup(response)
                )
    
    else:
        if chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            full_chat = await client.get_chat(chat.id)
            
            admin_count = 0
            async for member in client.get_chat_members(
                chat.id,
                filter=enums.ChatMembersFilter.ADMINISTRATORS
            ):
                admin_count += 1
            
            response = (
                "👥 **Group Info**\n"
                f"🏷 **Title**: {full_chat.title}\n"
                f"🆔 **ID**: `{full_chat.id}`\n"
            )
            
            if full_chat.username:
                response += f"🌐 **Username**: @{full_chat.username}\n"
            response += (
                f"👥 **Members**: {full_chat.members_count}\n"
                f"🔧 **Admins**: {admin_count}\n"
            )
            
            await message.reply(
                response,
                reply_markup=create_copy_markup(response)
            )
            
        else:
            user = await client.get_users(chat.id)
            
            response = (
                "👤 **User Info**\n"
                f"🆔 **ID**: `{user.id}`\n"
                f"📛 **Name**: {user.first_name}"
            )
            if user.last_name:
                response += f" {user.last_name}\n"
            else:
                response += "\n"
            
            if user.username:
                response += f"🌐 **Username**: @{user.username}\n"
            
            if user.is_restricted:
                response += "⚠️ **Account Restricted**: Yes\n"
                if user.restriction_reason:
                    response += f"📝 **Restriction Reason**: {user.restriction_reason}\n"
            
            if user.is_scam:
                response += "🚫 **Scam Account**: Yes\n"
            
            if user.is_fake:
                response += "🎭 **Impersonator**: Yes\n"
            
            if user.photo:
                try:
                    await client.download_media(user.photo.big_file_id, photo_path)
                    await message.reply_photo(
                        photo_path,
                        caption=response,
                        reply_markup=create_copy_markup(response)
                    )
                except Exception:
                    await message.reply(
                        response,
                        reply_markup=create_copy_markup(response)
                    )
            else:
                await message.reply(
                    response,
                    reply_markup=create_copy_markup(response)
                )


@Client.on_callback_query(filters.regex("^close$"))
@retry()

async def close_message(client, query):
    try:
        # Delete the original message
        await query.message.delete()
        # Send confirmation with mention
        await client.send_message(
            query.message.chat.id,
            f"🗑 Message closed by {query.from_user.mention}"
        )
    except Exception as e:
        print(f"Error closing message: {e}")




@Client.on_message(filters.command("kang"))
@retry()

async def kang(user_client, message):
    bot_username = user_client.me.username
    session_client_id = connector.get(bot_username)
    if session_client_id is None:
        await massage.edit("No session client connected. Please authorize first with /host")
        return await remove_active_chat(user_client, message.chat.id)
    owner_id = get_owner_id_by_client(user_client)
    client = clients.get(f"{session_client_id}_session")
    if not client:
       await massage.edit("Session client not found. Please re-authorize with /host.")
    user = message.from_user
    if not user:
       return await message.reply_text("Use this command as user")
    replied = message.reply_to_message
    Man = await message.reply_text("`It's also possible that the sticker is colong ahh...`")
    media_ = None
    emoji_ = None
    is_anim = False
    is_video = False
    resize = False
    ff_vid = False
    if replied and replied.media:
        if replied.photo:
            resize = True
        elif replied.document and "image" in replied.document.mime_type:
            resize = True
            replied.document.file_name
        elif replied.document and "tgsticker" in replied.document.mime_type:
            is_anim = True
            replied.document.file_name
        elif replied.document and "video" in replied.document.mime_type:
            resize = True
            is_video = True
            ff_vid = True
        elif replied.animation:
            resize = True
            is_video = True
            ff_vid = True
        elif replied.video:
            resize = True
            is_video = True
            ff_vid = True
        elif replied.sticker:
            if not replied.sticker.file_name:
                await Man.edit("**Sticker has no Name!**")
                return
            emoji_ = replied.sticker.emoji
            is_anim = replied.sticker.is_animated
            is_video = replied.sticker.is_video
            if not (
                replied.sticker.file_name.endswith(".tgs")
                or replied.sticker.file_name.endswith(".webm")
            ):
                resize = True
                ff_vid = True
        else:
            await Man.edit("**Unsupported File**")
            return
        media_ = await user_client.download_media(replied, file_name=f"{ggg}/user_{user_client.me.id}/")
    else:
        await Man.edit("**Please Reply to Photo/GIF/Sticker Media!**")
        return
    if media_:
        args = get_arg(message)
        pack = 1
        if len(args) == 2:
            emoji_, pack = args
        elif len(args) == 1:
            if args[0].isnumeric():
                pack = int(args[0])
            else:
                emoji_ = args[0]

        if emoji_ and emoji_ not in (
            getattr(emoji, _) for _ in dir(emoji) if not _.startswith("_")
        ):
            emoji_ = None
        if not emoji_:
            emoji_ = "✨"

        u_name = user.username
        u_name = "@" + u_name if u_name else user.first_name or user.id
        packname = f"Sticker_u{user.id}_v{pack}"
        custom_packnick = f"{u_name} Sticker Pack"
        packnick = f"{custom_packnick} Vol.{pack}"
        cmd = "/newpack"
        if resize:
            media_ = await resize_media(media_, is_video, ff_vid)
        if is_anim:
            packname += "_animated"
            packnick += " (Animated)"
            cmd = "/newanimated"
        if is_video:
            packname += "_video"
            packnick += " (Video)"
            cmd = "/newvideo"
        exist = False
        while True:
            try:
                exist = await client.invoke(
                    GetStickerSet(
                        stickerset=InputStickerSetShortName(short_name=packname), hash=0
                    )
                )
            except StickersetInvalid:
                exist = False
                break
            limit = 50 if (is_video or is_anim) else 120
            if exist.set.count >= limit:
                pack += 1
                packname = f"a{user.id}_by_userge_{pack}"
                packnick = f"{custom_packnick} Vol.{pack}"
                if is_anim:
                    packname += f"_anim{pack}"
                    packnick += f" (Animated){pack}"
                if is_video:
                    packname += f"_video{pack}"
                    packnick += f" (Video){pack}"
                await Man.edit(
                    f"`Create a New Sticker Pack {pack} Because the Sticker Pack is Full`"
                )
                continue
            break
        if exist is not False:
            try:
                await client.send_message("stickers", "/addsticker")
            except YouBlockedUser:
                await client.unblock_user("stickers")
                await client.send_message("stickers", "/addsticker")
            except Exception as e:
                return await Man.edit(f"**ERROR:** `{e}`")
            await asyncio.sleep(2)
            await client.send_message("stickers", packname)
            await asyncio.sleep(2)
            limit = "50" if is_anim else "120"
            while limit in await get_response(message, client):
                pack += 1
                packname = f"a{user.id}_by_{user.username}_{pack}"
                packnick = f"{custom_packnick} vol.{pack}"
                if is_anim:
                    packname += "_anim"
                    packnick += " (Animated)"
                if is_video:
                    packname += "_video"
                    packnick += " (Video)"
                    await Man.edit(
                    "`Creating a New Sticker Pack"
                    + str(pack)
                    + "Because the Sticker Pack is Full"
                )
                await client.send_message("stickers", packname)
                await asyncio.sleep(2)
                if await get_response(message, client) == "Invalid pack selected.":
                    await client.send_message("stickers", cmd)
                    await asyncio.sleep(2)
                    await client.send_message("stickers", packnick)
                    await asyncio.sleep(2)
                    await client.send_document("stickers", media_)
                    await asyncio.sleep(2)
                    await client.send_message("Stickers", emoji_)
                    await asyncio.sleep(2)
                    await client.send_message("Stickers", "/publish")
                    await asyncio.sleep(2)
                    if is_anim:
                        await client.send_message(
                            "Stickers", f"<{packnick}>", parse_mode=ParseMode.MARKDOWN
                        )
                        await asyncio.sleep(2)
                    await client.send_message("Stickers", "/skip")
                    await asyncio.sleep(2)
                    await client.send_message("Stickers", packname)
                    await asyncio.sleep(2)
                    await Man.edit(
                        f"**Sticker Added Successfully!**\n 🔥 **[CLICK HERE](https://t.me/addstickers/{packname})** 🔥\n**To Use Stickers**"
                    )
            await client.send_document("stickers", media_)
            await asyncio.sleep(2)
            if (
                await get_response(message, client)
                == "Sorry, the file type is invalid."
            ):
                await Man.edit(
                    "**Failed to Add Sticker, Use @Stickers Bot to Add Your Sticker.**"
                )
                return
            await client.send_message("Stickers", emoji_)
            await asyncio.sleep(2)
            await client.send_message("Stickers", "/done")
        else:
            await Man.edit("`Creating a New Sticker Pack`")
            try:
                await client.send_message("Stickers", cmd)
            except YouBlockedUser:
                await client.unblock_user("stickers")
                await client.send_message("stickers", "/addsticker")
            await asyncio.sleep(2)
            await client.send_message("Stickers", packnick)
            await asyncio.sleep(2)
            await client.send_document("stickers", media_)
            await asyncio.sleep(2)
            if (
                await get_response(message, client)
                == "Sorry, the file type is invalid."
            ):
                await Man.edit(
                    "**Failed to Add Sticker, Use @Stickers Bot to Add Your Sticker.**"
                )
                return
            await client.send_message("Stickers", emoji_)
            await asyncio.sleep(2)
            await client.send_message("Stickers", "/publish")
            await asyncio.sleep(2)
            if is_anim:
                await client.send_message("Stickers", f"<{packnick}>")
                await asyncio.sleep(2)
            await client.send_message("Stickers", "/skip")
            await asyncio.sleep(2)
            await client.send_message("Stickers", packname)
            await asyncio.sleep(2)
        await Man.edit(
            f"**Sticker Added Successfully!**\n 🔥 **[CLICK HERE](https://t.me/addstickers/{packname})** 🔥\n**To Use Stickers**"
        )
        if os.path.exists(str(media_)):
            os.remove(media_)






async def get_response(message, client):
    return [x async for x in client.get_chat_history("Stickers", limit=1)][0].text


@Client.on_message(filters.command("mmf"))

async def memify(client, message):
    if not message.reply_to_message_id:
        await message.reply_text("**Reply to any photo or sticker!**")
        return
    reply_message = message.reply_to_message
    if not reply_message.media:
        await message.reply_text( "**Reply to any photo or sticker!**")
        return
    file = await client.download_media(reply_message)
    Man = await message.reply_text( "`Processing . . .`")
    text = get_arg(message)
    if len(text) < 1:
        return await Man.edit(f"Please use `/mmf <text>`")
    meme = await add_text_img(file, text)
    await asyncio.gather(
        Man.delete(),
        client.send_sticker(
            message.chat.id,                                                                                          sticker=meme,
            reply_to_message_id=reply_message.id,                                                                 ),
    )
    os.remove(meme)
    await message.delete()


import subprocess
import os
from pyrogram import Client, filters

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

async def send_long_message(client, chat_id, text, reply_to_message_id=None):
    """Send message, splitting it if it exceeds 3900 characters"""
    if len(text) <= 3900:
        return await client.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )
    
    # Split the message into chunks of 3900 characters max
    chunks = []
    for i in range(0, len(text), 3900):
        chunks.append(text[i:i+3900])
    
    # Send each chunk as a separate message
    first_message = None
    for i, chunk in enumerate(chunks):
        if i == 0:
            # Send first chunk with reply to original message
            first_message = await client.send_message(
                chat_id=chat_id,
                text=chunk,
                reply_to_message_id=reply_to_message_id
            )
        else:
            # Send subsequent chunks as regular messages
            await client.send_message(
                chat_id=chat_id,
                text=chunk
            )
    
    return first_message

@Client.on_message(filters.command("pull") & filters.text)
@retry()
async def pull_handler(client, message):
    user_id = message.from_user.id
    
    # Check if the user is an admin by comparing their user ID with the ones in admin.txt
    admin_file = f"{ggg}/admin.txt"  # Assuming ggg is defined elsewhere in your code
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if user_id not in admin_ids:
                return  # Silently ignore if user is not an admin
    
    # Send a message to indicate the pull is starting
    progress_message = await message.reply("🔄 Executing git commands...")
    
    # Execute the git commands
    result = await execute_git_commands()
    
    # Format the result with code block
    formatted_result = f"```\n{result}\n```"
    
    # Delete the progress message
    await progress_message.delete()
    
    # Send the result, handling long messages
    await send_long_message(client, message.chat.id, formatted_result, message.id)
