from telethon import TelegramClient, events, functions
import logging, re
from datetime import timedelta, datetime, time, date, UTC
import asyncio, signal, sys
from tabulate import tabulate
import os

import handlers

import consts as c
from consts import client
from consts import settings
from shared import terminate


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO) # TODO

loop = None


async def init():
    global loop
    loop = asyncio.get_event_loop()
    stc = ser = stf = True
    msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=settings.target_id, hash=0))
    for m in msgs.messages:
        if m.message == settings.cmds['tc']: stc = False
        elif m.message == settings.cmds['er']: ser = False
        elif m.message == settings.cmds['tf']: stf = False
    if stc: await client.send_message(settings.target_id, settings.cmds['tc'])
    if ser: await client.send_message(settings.target_id, settings.cmds['er'])
    if stf: await client.send_message(settings.target_id, settings.cmds['tf'])


logging.info('\n\nSTARTING')
client.start()
logging.info('START complete')

logging.info('INIT')
signal.signal(signal.SIGTERM, terminate)
client.loop.run_until_complete(init())
logging.info('INIT complete')

logging.info('RUNNING')
client.run_until_disconnected()

terminate(0, 0)