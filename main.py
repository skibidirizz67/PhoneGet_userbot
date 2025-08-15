from telethon import TelegramClient, events, functions
import logging, re
from datetime import timedelta, datetime, time, date, UTC
import asyncio, signal, sys

import handlers

import consts as c
from consts import client


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO) # TODO

#client = TelegramClient('anon', c.api_id, c.api_hash)

loop = None


async def init():
    global loop
    loop = asyncio.get_event_loop()
    stc = ser = stf = True
    msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=c.target_id, hash=0))
    for m in msgs.messages:
        if m.message == c.cmds['tc']: stc = False
        elif m.message == c.cmds['er']: ser = False
        elif m.message == c.cmds['tf']: stf = False
    if stc: await client.send_message(c.target_id, c.cmds['tc'])
    if ser: await client.send_message(c.target_id, c.cmds['er'])
    if stf: await client.send_message(c.target_id, c.cmds['tf'])


def terminate(signum, frame):
    logging.info('STOP')
    logging.info('STOP complete, terminating')
    sys.exit(0)


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