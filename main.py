from telethon import TelegramClient, events
import logging
from threading import Timer
import re
from datetime import timedelta
import asyncio
import signal, sys

logging.basicConfig(filename='phoneget_userbot.log', filemode='a', format='[%(asctime)s] [%(levelname)s]: %(message)s', level=logging.INFO)

f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

target = '@phonegetcardsbot'

card_timer = Timer(0, None)
daily_timer = Timer(0, None)

client = TelegramClient('anon', api_id, api_hash)

me = None

cmds = {'тк':'ТКарточка', 'та':'ТАкк', 'мо':'Мои телефоны', 'мт':'Магазин телефонов', 'му':'Магазин улучшений', 'ап':'Апгрейд',
'ен':'Ежедневная награда', 'са':'/sellall', 'тл':'Таблица лидеров', 'п':'/pay', 'ев':'/event', 'тр':'/trade',
'км':'тк - ТКарточка\nта - ТАкк\nмо - Мои телефоны\nмт - Магазин телефонов\nму - Магазин улучшений\nап - Апргрейд\nен - Ежедневаня награда\nса - /sellall\nтл - Таблица лидеров\nп - /pay\nев - /event\nтр - /trade\nкм - Этот текст'}


async def init():
    global me
    me = await client.get_me()
    me = me.username

    logging.info("[init] setting timers")
    await client.send_message(target, cmds['тк'])
    await client.send_message(target, cmds['ен'])


def terminate(signum, frame):
    card_timer.cancel()
    daily_timer.cancel()
    logging.info("STOP complete, terminating")
    sys.exit(0)


signal.signal(signal.SIGTERM, terminate)

logging.info("\n\nSTARTING")
client.start()
logging.info("START complete")

logging.info("INIT")
client.loop.run_until_complete(init())


@client.on(events.NewMessage(outgoing=True, pattern=r'\!'))
async def cmd_handler(event):
    text = event.text[1:]
    for key in cmds:
        if text == key:
            await event.delete()
            await event.reply(cmds[key])


def txt_to_sec(text):
    pattern = re.findall(r'(\d+)\s*(ч|м|с)', text, re.IGNORECASE)

    h = m = s = 0
    for v, u in pattern:
        v = int(v)
        u = u.lower()
        if u in 'ч':
            h += v
        elif u in 'м':
            m += v
        elif u in 'с':
            s += v
    
    return timedelta(hours=h, minutes=m, seconds=s).total_seconds()


@client.on(events.NewMessage(from_users=target, pattern=rf'(?s)(?=.*@{me})(?=.*Вам выпал телефон!)'))
async def card_handler(event):
    logging.info('[card_handler] triggered, sending cmd')
    await event.reply(cmds['тк'])


@client.on(events.NewMessage(from_users=target, pattern=r'(?is).*розыгрыш.*|.*подписка на каналы.*'))
async def spam_handler(event):
    logging.info('[spam_handler] triggered, deleting')
    await event.delete()


async def send_msg(target, text):
    await client.send_message(target, text)
    logging.info('[send_msg] sent "%s"', text)
def schedule_msg(loop, target, text):
    asyncio.run_coroutine_threadsafe(send_msg(target, text), loop)


@client.on(events.NewMessage(from_users=target, pattern=rf'(?s)(?=.*@{me})(?=.*Вы сможете выбить карту еще раз через)'))
async def cardt_handler(event):
    logging.info('[cardt_handler] triggered, scheduling cmd')
    global card_timer
    card_timer.cancel()

    time = txt_to_sec(event.text[event.text.rfind('з')+2:])
    loop = asyncio.get_event_loop()

    card_timer = Timer(time, lambda: schedule_msg(loop, target, cmds['тк']))
    card_timer.start()
    logging.info('[cardt_handler] waiting for %i seconds', time)


@client.on(events.NewMessage(from_users=target, pattern=r'(?s).*Ежедневные награды:.*'))
async def daily_handler(event):
    logging.info('[daily_handler] triggered, clicking btn')
    await event.message.click(0, 0)
    logging.info('[daily_handler] clicked, sending cmd')
    await event.reply(cmds['ен'])


@client.on(events.NewMessage(from_users=target, pattern=r'(?s).*Новая награда будет доступна завтра.*'))
async def dailyt_handler(event):
    logging.info('[dailyt_handler] triggered, scheduling cmd')
    global daily_timer
    daily_timer.cancel()

    time = txt_to_sec(event.text[event.text.rfind('з')+3:])
    loop = asyncio.get_event_loop()

    daily_timer = Timer(time, lambda: schedule_msg(loop, target, cmds['ен']))
    daily_timer.start()
    logging.info('[dailyt_handler] waiting for %i seconds', time)


logging.info("RUN")
client.run_until_disconnected()