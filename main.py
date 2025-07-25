from telethon import TelegramClient, events
import logging, re
from threading import Timer
from datetime import timedelta
import asyncio, signal, sys
import consts as c


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO)

card_timer = Timer(0, None)
daily_timer = Timer(0, None)

client = TelegramClient('anon', c.api_id, c.api_hash)


logging.info('\n\nSTARTING')
client.start()
client.loop.run_until_complete(c.getme(client))
logging.info('START complete')


def txt_to_sec(text):
    pattern = re.findall(r'(\d+)\s*(ч|м|с)', text, re.IGNORECASE)
    h = m = s = 0
    for v, u in pattern:
        v = int(v)
        u = u.lower()
        if u in 'ч': h += v
        elif u in 'м': m += v
        elif u in 'с': s += v
    return timedelta(hours=h, minutes=m, seconds=s).total_seconds()


async def send_msg(target, text):
    await client.send_message(target, text)
    logging.info('[send_msg] sent "%s"', text)
def schedule_msg(loop, target, text):
    asyncio.run_coroutine_threadsafe(send_msg(target, text), loop) # TODO: remake, idk feels wrong


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['cmd_handler']))
async def cmd_handler(event):
    text = event.text[1:]
    for key in c.cmds:
        if text == key:
            await event.delete()
            await event.reply(c.cmds[key])
            return None


@client.on(events.NewMessage(from_users=c.target, pattern=c.patterns['spam_handler']))
async def spam_handler(event):
    logging.info('[spam_handler] triggered, deleting')
    await event.delete()


@client.on(events.NewMessage(from_users=c.target, pattern=c.patterns['card_handler']))
async def card_handler(event):
    logging.info('[card_handler] triggered, sending cmd')
    await event.reply(c.cmds['tc'])


@client.on(events.NewMessage(from_users=c.target, pattern=c.patterns['cardt_handler']))
async def cardt_handler(event):
    logging.info('[cardt_handler] triggered, scheduling cmd')
    global card_timer
    card_timer.cancel()

    time = txt_to_sec(event.text[event.text.rfind('з')+2:])
    loop = asyncio.get_event_loop()

    card_timer = Timer(time, lambda: schedule_msg(loop, c.target, c.cmds['тк']))
    card_timer.start()
    logging.info('[cardt_handler] waiting for %i seconds', time)


@client.on(events.NewMessage(from_users=c.target, pattern=c.patterns['daily_handler']))
async def daily_handler(event):
    logging.info('[daily_handler] triggered, clicking btn')
    await event.message.click(0, 0)
    logging.info('[daily_handler] clicked, sending cmd')
    await event.reply(c.cmds['ен'])


@client.on(events.NewMessage(from_users=c.target, pattern=c.patterns['dailyt_handler']))
async def dailyt_handler(event):
    logging.info('[dailyt_handler] triggered, scheduling cmd')
    global daily_timer
    daily_timer.cancel()

    time = txt_to_sec(event.text[event.text.rfind('з')+3:])
    loop = asyncio.get_event_loop()

    daily_timer = Timer(time, lambda: schedule_msg(loop, c.target, c.cmds['ен']))
    daily_timer.start()
    logging.info('[dailyt_handler] waiting for %i seconds', time)


async def init():
    logging.info('[init] setting timers')
    await client.send_message(c.target, c.cmds['тк'])
    await client.send_message(c.target, c.cmds['ен'])


def terminate(signum, frame):
    logging.info('STOP')
    card_timer.cancel()
    daily_timer.cancel()
    logging.info('STOP complete, terminating')
    sys.exit(0)


logging.info('INIT')
signal.signal(signal.SIGTERM, terminate)
client.loop.run_until_complete(init())
logging.info('INIT complete')

logging.info('RUNNING')
client.run_until_disconnected()

terminate(0, 0)