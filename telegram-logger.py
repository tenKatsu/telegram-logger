#!/usr/bin/env python3

import toml
from telethon import TelegramClient, events

config = toml.load('config.toml')

client = TelegramClient('telegram-logger', config['api_id'], config['api_hash'])
client.start()

enabled_chats = config.get('enabled_chats', [])
disabled_chats = config.get('disabled_chats', [])


@client.on(events.NewMessage)
async def on_new_message(event):
    msg = event.message

    date = msg.date.strftime('%Y-%m-%d %H:%M:%S')

    chat = await client.get_entity(msg.peer_id)
    if enabled_chats and chat.id not in enabled_chats:
        return
    if disabled_chats and chat.id in disabled_chats:
        return
    chat_display = f'[{chat.username or chat.title} ({chat.id})]'

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
        user_display = f'<{user.username} ({user.id})>'
    else:
        user_display = None

    text = msg.message

    out = f'{date} {chat_display} MSG {msg_display}'
    if user_display:
        out += f' {user_display}'
    out += f' {text}'
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
    chat_display = f'[{chat.username or chat.title} ({chat.id})]'

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
        user_display = f'<{user.username} ({user.id})>'
    else:
        user_display = None

    text = msg.message

    out = f'{date} {chat_display} EDIT {msg_display}'
    if user_display:
        out += f' {user_display}'
    out += f' {text}'
    print(out)

client.run_until_disconnected()
