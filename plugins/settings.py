# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from telethon import events, Button
import re
import os
import asyncio
import string
import random
from shared_client import client as gf
from config import OWNER_ID
from utils.func import get_user_data_key, save_user_data, users_collection, save_user_session, remove_user_session
from utils.encrypt import ecs

VIDEO_EXTENSIONS = {
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mpeg', 'mpg', '3gp', 'm4v', 'ogv'
}
SET_PIC = 'settings.jpg'
MESS = 'Customize settings for your files...'

active_conversations = {}

async def _cleanup_cached_uclient(user_id):
    try:
        from plugins.batch import UC
        if user_id in UC:
            try:
                await UC[user_id].stop()
            except Exception:
                pass
            UC.pop(user_id, None)
    except Exception:
        pass
    try:
        if os.path.exists(f"{user_id}_client.session"):
            os.remove(f"{user_id}_client.session")
    except Exception:
        pass

@gf.on(events.NewMessage(incoming=True, pattern=r'^/settings(?:\s|$|@)'))
async def settings_command(event):
    user_id = event.sender_id
    await send_settings_message(event.chat_id, user_id)

async def send_settings_message(chat_id, user_id):
    buttons = [
        [
            Button.inline('📝 Set Chat ID', b'setchat'),
            Button.inline('🏷️ Set Rename Tag', b'setrename')
        ],
        [
            Button.inline('📋 Set Caption', b'setcaption'),
            Button.inline('🔄 Replace Words', b'setreplacement')
        ],
        [
            Button.inline('🗑️ Remove Words', b'delete'),
            Button.inline('🔄 Reset Settings', b'reset')
        ],
        [
            Button.inline('🔑 Session Login', b'addsession'),
            Button.inline('🚪 Logout', b'logout')
        ],
        [
            Button.inline('🖼️ Set Thumbnail', b'setthumb'),
            Button.inline('❌ Remove Thumbnail', b'remthumb')
        ],
        [
            Button.url('🆘 Report Errors', 'https://t.me/team_spy_pro')
        ]
    ]
    await gf.send_message(chat_id, MESS, buttons=buttons)

@gf.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    
    callback_actions = {
        b'setchat': {
            'type': 'setchat',
            'message': """Send me the ID of that chat(with -100 prefix): 
__👉 **Note:** if you are using custom bot then your bot should be admin that chat if not then this bot should be admin.__
👉 __If you want to upload in topic group and in specific topic then pass chat id as **-100CHANNELID/TOPIC_ID** for example: **-1004783898/12**__"""
        },
        b'setrename': {
            'type': 'setrename',
            'message': 'Send me the rename tag:'
        },
        b'setcaption': {
            'type': 'setcaption',
            'message': 'Send me the caption:'
        },
        b'setreplacement': {
            'type': 'setreplacement',
            'message': "Send me the replacement words in the format: 'WORD(s)' 'REPLACEWORD'"
        },
        b'addsession': {
            'type': 'addsession',
            'message': 'Send Pyrogram V2 session string:'
        },
        b'delete': {
            'type': 'deleteword',
            'message': 'Send words separated by space to delete them from caption/filename...'
        },
        b'setthumb': {
            'type': 'setthumb',
            'message': 'Please send the photo you want to set as the thumbnail.'
        }
    }
    
    if event.data in callback_actions:
        await event.answer()
        action = callback_actions[event.data]
        await start_conversation(event, user_id, action['type'], action['message'])
    elif event.data == b'logout':
        await event.answer()
        result = await users_collection.update_one(
            {'user_id': int(user_id)},
            {'$unset': {'session_string': ''}}
        )
        await _cleanup_cached_uclient(user_id)
        if result.modified_count > 0:
            await event.respond('Logged out and deleted session successfully.')
        else:
            await event.respond('You are not logged in.')
    elif event.data == b'reset':
        await event.answer()
        try:
            await users_collection.update_one(
                {'user_id': int(user_id)},
                {'$unset': {
                    'delete_words': '',
                    'replacement_words': '',
                    'rename_tag': '',
                    'caption': '',
                    'chat_id': ''
                }}
            )
            thumbnail_path = f'{user_id}.jpg'
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            await event.respond('✅ All settings reset successfully. To logout, click /logout')
        except Exception as e:
            await event.respond(f'Error resetting settings: {e}')
    elif event.data == b'remthumb':
        await event.answer()
        try:
            os.remove(f'{user_id}.jpg')
            await event.respond('Thumbnail removed successfully!')
        except FileNotFoundError:
            await event.respond('No thumbnail found to remove.')

async def start_conversation(event, user_id, conv_type, prompt_message):
    if user_id in active_conversations:
        await event.respond('Previous conversation cancelled. Starting new one.')
    
    msg = await event.respond(f'{prompt_message}\n\n(Send /cancel to cancel this operation)')
    active_conversations[user_id] = {'type': conv_type, 'message_id': msg.id}

@gf.on(events.NewMessage(incoming=True, pattern=r'^/cancel(?:\s|$|@)'))
async def cancel_conversation(event):
    user_id = event.sender_id
    if user_id in active_conversations:
        await event.respond('Cancelled enjoy baby...')
        del active_conversations[user_id]

@gf.on(events.NewMessage(incoming=True))
async def handle_conversation_input(event):
    user_id = event.sender_id
    text = event.message.text or ''
    if user_id not in active_conversations or text.startswith('/'):
        return
        
    conv_type = active_conversations[user_id]['type']
    
    handlers = {
        'setchat': handle_setchat,
        'setrename': handle_setrename,
        'setcaption': handle_setcaption,
        'setreplacement': handle_setreplacement,
        'addsession': handle_addsession,
        'deleteword': handle_deleteword,
        'setthumb': handle_setthumb
    }
    
    if conv_type in handlers:
        await handlers[conv_type](event, user_id)
    
    if user_id in active_conversations:
        del active_conversations[user_id]

async def handle_setchat(event, user_id):
    try:
        chat_id = (event.text or '').strip()
        if not chat_id:
            await event.respond('❌ Please provide a valid chat ID.')
            return
        await save_user_data(user_id, 'chat_id', chat_id)
        await event.respond('✅ Chat ID set successfully!')
    except Exception as e:
        await event.respond(f'❌ Error setting chat ID: {e}')

async def handle_setrename(event, user_id):
    rename_tag = (event.text or '').strip()
    if not rename_tag:
        await event.respond('❌ Please provide a valid rename tag.')
        return
    await save_user_data(user_id, 'rename_tag', rename_tag)
    await event.respond(f'✅ Rename tag set to: {rename_tag}')

async def handle_setcaption(event, user_id):
    caption = event.text
    if not caption:
        await event.respond('❌ Please provide a valid caption.')
        return
    await save_user_data(user_id, 'caption', caption)
    await event.respond('✅ Caption set successfully!')

async def handle_setreplacement(event, user_id):
    match = re.match(r"'(.+?)'\s+'(.+?)'", (event.text or '').strip())
    if not match:
        await event.respond("❌ Invalid format. Usage: 'WORD(s)' 'REPLACEWORD'")
    else:
        word, replace_word = match.groups()
        delete_words = await get_user_data_key(user_id, 'delete_words', [])
        if word in delete_words:
            await event.respond(f"❌ The word '{word}' is in the delete list and cannot be replaced.")
        else:
            replacements = await get_user_data_key(user_id, 'replacement_words', {})
            replacements[word] = replace_word
            await save_user_data(user_id, 'replacement_words', replacements)
            await event.respond(f"✅ Replacement saved: '{word}' will be replaced with '{replace_word}'")

async def handle_addsession(event, user_id):
    session_string = (event.text or '').strip()
    if not session_string:
        await event.respond('❌ Please send a valid session string.')
        return
    encrypted_session = ecs(session_string)
    await save_user_session(user_id, encrypted_session)
    await _cleanup_cached_uclient(user_id)
    await event.respond('✅ Session string added successfully!')

async def handle_deleteword(event, user_id):
    words_to_delete = (event.message.text or '').split()
    if not words_to_delete:
        await event.respond('❌ Please provide words to delete.')
        return
    delete_words = await get_user_data_key(user_id, 'delete_words', [])
    delete_words = list(set(delete_words + words_to_delete))
    await save_user_data(user_id, 'delete_words', delete_words)
    await event.respond(f"✅ Words added to delete list: {', '.join(words_to_delete)}")

async def handle_setthumb(event, user_id):
    if event.photo:
        temp_path = await event.download_media()
        try:
            thumb_path = f'{user_id}.jpg'
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            os.rename(temp_path, thumb_path)
            await event.respond('✅ Thumbnail saved successfully!')
        except Exception as e:
            await event.respond(f'❌ Error saving thumbnail: {e}')
    else:
        await event.respond('❌ Please send a photo. Operation cancelled.')

def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def rename_file(file, sender, edit):
    try:
        delete_words = await get_user_data_key(sender, 'delete_words', [])
        custom_rename_tag = await get_user_data_key(sender, 'rename_tag', '')
        replacements = await get_user_data_key(sender, 'replacement_words', {})
        
        dir_name, base_name = os.path.split(str(file))
        last_dot_index = base_name.rfind('.')
        if last_dot_index > 0:
            ggn_ext = base_name[last_dot_index + 1:]
            if ggn_ext.isalnum() and len(ggn_ext) <= 9:
                original_file_name = base_name[:last_dot_index]
                if ggn_ext.lower() in VIDEO_EXTENSIONS:
                    file_extension = 'mp4'
                else:
                    file_extension = ggn_ext
            else:
                original_file_name = base_name[:last_dot_index]
                file_extension = 'mp4'
        else:
            original_file_name = base_name
            file_extension = 'mp4'
        
        for word in delete_words:
            original_file_name = original_file_name.replace(word, '')
        
        for word, replace_word in replacements.items():
            original_file_name = original_file_name.replace(word, replace_word)
        
        original_file_name = re.sub(r'[<>:"/\\|?*]', '_', original_file_name).strip() or "file"
        clean_tag = re.sub(r'[<>:"/\\|?*]', '_', custom_rename_tag).strip() if custom_rename_tag else ""
        
        if clean_tag:
            new_base_name = f'{original_file_name} {clean_tag}.{file_extension}'
        else:
            new_base_name = f'{original_file_name}.{file_extension}'
        
        new_file_name = os.path.join(dir_name, new_base_name) if dir_name else new_base_name
        
        if new_file_name != str(file):
            if os.path.exists(new_file_name):
                os.remove(new_file_name)
            os.rename(file, new_file_name)
        return new_file_name
    except Exception as e:
        print(f"Rename error: {e}")
        return file
