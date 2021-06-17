#!/usr/bin/env python3

from datetime import datetime

import toml
from telethon import TelegramClient, events
from telethon.tl.types import User

RESET = '\x1b[0m'
BOLD = '\x1b[1m'
DIM = '\x1b[2m'
RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'
MAGENTA = '\x1b[35m'
CYAN = '\x1b[36m'
WHITE = '\x1b[37m'
GRAY = '\x1b[90m'

config = toml.load('config.toml')

client = TelegramClient('telegram-logger', config['api_id'], config['api_hash'])
client.start()

enabled_chats = config.get('enabled_chats', [])
disabled_chats = config.get('disabled_chats', [])


def get_display_name(entity):
    if isinstance(entity, User):
        display_name = entity.first_name
        if entity.last_name:
            display_name += f' {entity.last_name}'
    else:
        display_name = entity.title

    return display_name


@client.on(events.NewMessage)
async def on_new_message(event):
    msg = event.message

    date = msg.date.strftime('%Y-%m-%d %H:%M:%S')

    chat = await client.get_entity(msg.peer_id)
    if enabled_chats and chat.id not in enabled_chats:
        return
    if disabled_chats and chat.id in disabled_chats:
        return
    chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'

    msg_display = f'({msg.id})'

    if msg.from_id:
        try:
            user = await client.get_entity(msg.from_id)
        except ValueError:
            await client.get_participants(chat.id)

            try:
                user = await client.get_entity(msg.from_id)
            except ValueError:
                await client.get_participants(chat.id, aggressive=True)
                user = await client.get_entity(msg.from_id)
        user_display = f'<{user.username or get_display_name(user)} ({user.id})>'
    else:
        user_display = None

    text = msg.message

    out = f'{GRAY}{date} {BOLD}{BLUE}MSG {GRAY}{chat_display} {RESET}{GRAY}{msg_display}'
    if user_display:
        out += f' {RESET}{BOLD}{user_display}'
    out += f' {RESET}{text}'
    print(out)


@client.on(events.MessageEdited)
async def on_message_edited(event):
    msg = event.message

    date = msg.date.strftime('%Y-%m-%d %H:%M:%S')

    chat = await client.get_entity(msg.peer_id)
    if enabled_chats and chat.id not in enabled_chats:
        return
    if disabled_chats and chat.id in disabled_chats:
        return
    chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'

    msg_display = f'({msg.id})'

    if msg.from_id:
        try:
            user = await client.get_entity(msg.from_id)
        except ValueError:
            await client.get_participants(chat.id)

            try:
                user = await client.get_entity(msg.from_id)
            except ValueError:
                await client.get_participants(chat.id, aggressive=True)
                user = await client.get_entity(msg.from_id)
        user_display = f'<{user.username or get_display_name(user)} ({user.id})>'
    else:
        user_display = None

    text = msg.message

    out = f'{GRAY}{date} {BOLD}{YELLOW}EDIT {GRAY}{chat_display} {RESET}{GRAY}{msg_display}'
    if user_display:
        out += f' {RESET}{BOLD}{user_display}'
    out += f' {RESET}{text}'
    print(out)


@client.on(events.MessageDeleted)
async def on_message_deleted(event):
    msg = event.original_update

    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if getattr(msg, 'channel_id', None):
        chat = await client.get_entity(msg.channel_id)
        if enabled_chats and chat.id not in enabled_chats:
            return
        if disabled_chats and chat.id in disabled_chats:
            return
        chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'
    else:
        chat_display = None

    msg_display = f'({", ".join(str(x) for x in event.deleted_ids)})'

    out = f'{GRAY}{date} {BOLD}{RED}DEL'
    if chat_display:
        out += f' {GRAY}{chat_display}'
    out += f' {RESET}{GRAY}{msg_display}'
    print(out)


print('Listening for messages')
client.run_until_disconnected()
