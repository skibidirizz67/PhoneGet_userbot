import re
import os, sys
import logging
from datetime import timedelta, datetime, UTC
from telethon import TelegramClient, events, functions
from consts import client
import consts as c

def txt_to_sec(text):
    time = re.findall(c.patterns['txt_to_sec'], text)
    if len(time) < 1: return False
    return timedelta(hours=int(time[0]), minutes=int(time[1]), seconds=int(time[2]))


async def safe_click(matrix, text):
    for row in matrix:
        for btn in row:
            if text.lower() in btn.text.lower():
                await btn.click()
                return
    raise IndexError


def find_phone(n, p):
    for r in c.phonesDB:
        for k in c.phonesDB[r]:
            if (n.lower() in k.lower()) and ((p == c.phonesDB[r][k]) if p > 0 else True): # notice diff in name comparison
                return True
    return False


async def safe_click_scroll(conv, matrix, text, price):
    try:
        if find_phone(text, price):
            await safe_click(matrix, text)
        else: raise IndexError
    except IndexError:
        await safe_click(matrix, '➡️')
        resp = await conv.get_edit()
        await safe_click_scroll(conv, resp.buttons, text, price)


async def safe_get_resp(conv, target_id):
    resp = None
    while (resp := await conv.get_response()).sender_id != target_id: pass
    return resp

async def timeout_msg(e, timeout):
    logging.error(f'timeout {timeout}s')
    await e.reply(f'timeout, bot didn\'t respond in {timeout}s')

async def index_msg(e, btn_text):
    logging.error(f'button "{btn_text}" not found')
    await e.reply(f'button "{btn_text}" not found')


async def unschedule_dups(chat, text, date, minimal):
    exact = False
    msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=chat, hash=0))
    for m in msgs.messages:
        if m.message == text:
            diff = abs((date - m.date).total_seconds())
            if diff < 1:
                if exact:
                    await client(functions.messages.DeleteScheduledMessagesRequest(peer=c.target_id, id=[m.id]))
                else:
                    exact = True
            elif diff < minimal:
                await client(functions.messages.DeleteScheduledMessagesRequest(peer=c.target_id, id=[m.id]))
    return exact


async def schedule_msg(e, text, offset, minimal):
    schedule = datetime.now(UTC) + offset + timedelta(seconds=1)
    if not (await unschedule_dups(e.chat_id, text, schedule, minimal)):
        await e.reply(text, schedule=schedule)
        logging.info(f'scheduled "{text}" to {schedule}')


def terminate(signum, frame):
    logging.info('STOP')
    logging.info('STOP complete, terminating')
    sys.exit(0)