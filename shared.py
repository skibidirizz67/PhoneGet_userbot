import re
import logging
from datetime import timedelta
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
    