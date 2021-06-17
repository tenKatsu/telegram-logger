#!/usr/bin/env python3

import sqlite3
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

DB_PATH = 'data.sqlite3'


config = toml.load('config.toml')

client = TelegramClient('telegram-logger', config['api_id'], config['api_hash'])
client.start()


def get_display_name(entity):
    if isinstance(entity, User):
        display_name = entity.first_name
        if entity.last_name:
            display_name += f' {entity.last_name}'
    else:
        display_name = entity.title

    return display_name


def is_enabled(chat_id):
    enabled_chats = config.get('enabled_chats', [])
    disabled_chats = config.get('disabled_chats', [])

    return (not enabled_chats or chat_id in enabled_chats) and (chat_id not in disabled_chats)


def iso_date(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


async def get_user(user_id, chat_id=None):
    if not user_id:
        return None

    try:
        return await client.get_entity(user_id)
    except ValueError:
        if not chat_id:
            return None

        await client.get_participants(chat_id)

        try:
            return await client.get_entity(user_id)
        except ValueError:
            await client.get_participants(chat_id, aggressive=True)
            try:
                return await client.get_entity(user_id)
            except ValueError:
                return None


@client.on(events.NewMessage)
async def on_new_message(event):
    msg = event.message

    date = msg.date

    chat = await client.get_entity(msg.peer_id)
    if not is_enabled(chat.id):
        return

    user = await get_user(msg.from_id, chat.id)

    text = msg.message

    chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'
    msg_display = f'({msg.id})'
    if user:
        user_display = f'<{user.username or get_display_name(user)} ({user.id})>'

    out = f'{GRAY}{iso_date(date)} {BOLD}{BLUE}MSG {GRAY}{chat_display} {RESET}{GRAY}{msg_display}'
    if user:
        out += f' {RESET}{BOLD}{user_display}'
    out += f' {RESET}{text}{RESET}'
    print(out)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("""
            INSERT INTO events
                (type, date, chat_id, message_id, user_id, text)
            VALUES
                ('new_message', :date, :chat_id, :message_id, :user_id, :text)
        """, {
            'date': msg.date.timestamp(),
            'chat_id': chat.id,
            'message_id': msg.id,
            'user_id': user.id if user else None,
            'text': text,
        })


@client.on(events.MessageEdited)
async def on_message_edited(event):
    msg = event.message

    date = msg.date

    chat = await client.get_entity(msg.peer_id)
    if not is_enabled(chat.id):
        return

    user = await get_user(msg.from_id, chat.id)

    text = msg.message

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("""
        SELECT
            text
        FROM
            events
        WHERE
            chat_id = :chat_id
            AND message_id = :message_id
        ORDER BY
            rowid DESC
        LIMIT
            1
        """, {'chat_id': chat.id, 'message_id': msg.id})

        row = c.fetchone()

    if row:
        old_text = row[0]
    else:
        old_text = None

    if text == old_text:
        # Non-text change (e.g. inline keyboard)
        return

    chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'
    msg_display = f'({msg.id})'
    if user:
        user_display = f'<{user.username or get_display_name(user)} ({user.id})>'

    out = f'{GRAY}{iso_date(date)} {BOLD}{YELLOW}EDIT {GRAY}{chat_display} {RESET}{GRAY}{msg_display}'
    if user:
        out += f' {RESET}{BOLD}{user_display}'
    if old_text:
        out += f'\n{RESET}-{RED}{old_text} {RESET}\n+{BOLD}{GREEN}{text}{RESET}'
    else:
        out += f' {GREEN}{text}{RESET}'
    print(out)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("""
            INSERT INTO events
                (type, date, chat_id, message_id, user_id, text)
            VALUES
                ('message_edited', :date, :chat_id, :message_id, :user_id, :text)
        """, {
            'date': msg.date.timestamp(),
            'chat_id': chat.id,
            'message_id': msg.id,
            'user_id': user.id if user else None,
            'text': text,
        })


@client.on(events.MessageDeleted)
async def on_message_deleted(event):
    msg = event.original_update

    date = datetime.now()

    if getattr(msg, 'channel_id', None):
        chat = await client.get_entity(msg.channel_id)
        if not is_enabled(chat.id):
            return
    else:
        chat = None

    if chat:
        chat_display = f'[{chat.username or get_display_name(chat)} ({chat.id})]'

    for msg_id in event.deleted_ids:
        msg_display = f'({msg_id})'

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            c.execute("""
            SELECT
                chat_id, user_id, text
            FROM
                events
            WHERE
                chat_id LIKE :chat_id
                AND message_id = :message_id
            ORDER BY
                rowid DESC
            LIMIT
                1
            """, {
                'chat_id': chat.id if chat else '%',
                'message_id': msg_id,
            })

            row = c.fetchone()

        if row:
            chat_id, user_id, old_text = row
        else:
            chat_id, user_id, old_text = None, None, None

        if chat_id and not is_enabled(chat_id):
            return

        if user_id:
            user = await get_user(user_id, chat.id if chat else None)
        else:
            user = None
        if user:
            user_display = f'<{user.username or get_display_name(user)} ({user.id})>'

        out = f'{GRAY}{iso_date(date)} {BOLD}{RED}DEL'
        if chat:
            out += f' {GRAY}{chat_display}'
        out += f' {RESET}{GRAY}{msg_display}'
        if user:
            out += f' {RESET}{BOLD}{user_display}'
        if old_text:
            out += f' {BOLD}{RED}{old_text}'
        out += RESET
        print(out)

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO events
                    (type, date, chat_id, message_id)
                VALUES
                    ('message_deleted', :date, :chat_id, :message_id)
            """, {
                'date': date.timestamp(),
                'chat_id': chat.id if chat else None,
                'message_id': msg_id,
            })


with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        type TEXT NOT NULL,
        date REAL NOT NULL,
        chat_id INTEGER,
        message_id INTEGER NOT NULL,
        user_id INTEGER,
        text TEXT
    )
    """)

print('Listening for messages')
client.run_until_disconnected()
