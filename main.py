
import asyncio
import os
from config import STRING_SESSION
# Third-party libraries
from pytgcalls import filters as call_filters
from pytgcalls import PyTgCalls
from pytgcalls.types import ChatUpdate
from pyrogram import Client
from pyrogram.errors.exceptions import SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, \
    AuthKeyUnregistered, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired, UserDeactivated

# Local modules
from tools import *
from config import API_ID, API_HASH, ggg, BOT_TOKEN,logger


user_sessions = {}

# Cache directory setup
cache_dir = f"{ggg}/cache"
os.makedirs(cache_dir, exist_ok=True)

# Chat management functions


user_id = "your_user_id" # replace this with the user id
if user_id not in user_sessions:
        user_sessions[user_id] = {"string_session": STRING_SESSION}


user_data = user_sessions.get(user_id, {})
user_session_string = user_data.get("string_session", "")
user_bot_token = user_data.get("bot_token", BOT_TOKEN)

try:
    # Create and start the user client using the bot token
    user_client = Client(f"bot_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,workers=5,
        bot_token=BOT_TOKEN,
        plugins=dict(root="plugins",include=["bots"]),
        in_memory=True, sleep_threshold=32,
    )
    await user_client.start()
    client_name = f"{user_client.me.first_name} {user_client.me.last_name or ''}".strip()
    logger.info(f"Bot authorized successfully! 🎉 Authorized as: {client_name}")

    owners[user_client.me.id] = user_id
    
except (SessionRevoked, UserDeactivatedBan, AuthKeyInvalid, AuthKeyUnregistered,
        SessionRevoked, AuthTokenExpired, AuthKeyDuplicated, AccessTokenExpired,
        UserDeactivated) as e:
    logger.error(f"Failed to authorize bot: {e}")
    if user_id in user_sessions:
      del user_sessions[user_id]
      
except AttributeError:
    logger.info("The object is None; it doesn't have an 'id' attribute.")
    
except Exception as e:
    logger.error(f"Error starting user client: {e}")
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
                await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")


reload_all_plugins()
session_client= None
try:
    # Create and start the session client
    session_client = Client(f"user_{user_id}",
        api_id=API_ID,


        api_hash=API_HASH,
        session_string=STRING_SESSION,
        in_memory=True, no_updates=True, sleep_threshold=32
        )
    auth = await session_client.connect()
    if not auth:
       
        await app.send_message(user_id, f"Client is not authorized for {user_id}. Please authorize first.")


        await session_client.disconnect()
        

        return

    await session_client.disconnect()
    call_py = PyTgCalls(session_client)
    call_py.add_handler(end, call_filters.stream_end())
    call_py.add_handler(hd_stream_closed_kicked, call_filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT) | call_filters.chat_update(ChatUpdate.Status.KICKED))
    await call_py.start()
    await asyncio.sleep(2)

    client_name = f'{session_client.me.first_name if session_client.me else ""} {session_client.me.last_name or "" if session_client.me else ""}'.strip()
   
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
        UserDeactivated) :
    logger.error(f"Failed to authorize session: {e}")
    if user_id in user_sessions:
      del user_sessions[user_id]

except AttributeError:
    logger.info("The object is None; it doesn't have an 'id' attribute.")
    
except Exception as e:
    logger.error(f"Error starting session client: {e}")
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
                await app.send_message(admin_id, f"Error starting client for user {user_id}: {e}")

# Global variable management functions
def set_gvar(user_id,user_data, key, value):
    set_user_data(user_id,user_data, key, value)

def get_user_data(user_id,user_data, key):
    return user_data.get(key)

def set_user_data(user_id,user_data, key, value):
    
    user_data[key] = value

def gvarstatus(user_id, key):
    return get_user_data(user_id, key)
def unset_user_data(user_id, key):
    
    if user_id in user_sessions and key in user_sessions[user_id]:
            del user_sessions[user_id][key]

# File and Mime type management functions
def rename_file(old_name, new_name):
    
    """
        Renames a file and logs the operation. Handles common errors such as
        FileNotFound and FileExistsError.
    """
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
