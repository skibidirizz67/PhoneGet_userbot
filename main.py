from telethon import TelegramClient, events
import logging, re
from threading import Timer
from datetime import timedelta, datetime, time, date
import asyncio, signal, sys
import consts as c
import json


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO)

card_timer = Timer(0, None)
daily_timer = Timer(0, None)
farm_timer = Timer(0, None)
buy_timer = Timer(0, None)
# TODO? custom macros(remembers user's actions and replicates)(possibly json) and custom timers

reset_time = time(0, 30, 0, 0)

client = TelegramClient('anon', c.api_id, c.api_hash)


def txt_to_sec(text):
    time = re.findall(c.patterns['txt_to_sec'], text)
    return timedelta(hours=int(time[0]), minutes=int(time[1]), seconds=int(time[2])).total_seconds()


async def send_msg(target, text):
    await client.send_message(target, text)
    logging.info('sent "%s"', text)
def schedule_msg(loop, target, text):
    asyncio.run_coroutine_threadsafe(send_msg(target, text), loop)


async def macro_buy(event, r, q):
    logging.info('%i | %i', r, q)
    resp = None
    try:
        async with client.conversation(event.chat_id, timeout=10) as conv:
            await conv.send_message(c.cmds['ps'])
            while True:
                resp = await conv.get_response()
                if resp.sender_id == c.target_id: break
            await resp.click(int(r/2), r%2)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(1, 0)
            resp = await conv.get_edit(resp.id-1)
            if q < 0:
                await resp.click(len(resp.buttons)-2, len(resp.buttons[len(resp.buttons)-2])-1)
            else:
                if resp.buttons[int(q/5)][q%5].text == f'{q+1}':
                    await resp.click(int(q/5), q%5)
                else:
                    logging.info(f'button text didn\'t match {q}, cancelled')
                    await event.reply(f'button text didn\'t match {q}')
                    return
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
    except TimeoutError:
        logging.info('timeout')
        await event.reply('timeout, bot didn\'t respond in 10 seconds')
    except IndexError:
        logging.error([f'no button {q}'])
        await event.reply(f'button text didn\'t match {q}')


async def macro_upgrade(event, r, q): # TOFIX: ismatch doesn't work properly
    logging.info('%i | %i', r, q)
    lost = 0
    upgraded = 0
    resp = None
    ismatch = False
    try:
        async with client.conversation(event.chat_id, timeout=10) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['up'])
                while True:
                    resp = await conv.get_response()
                    if resp.sender_id == c.target_id: break
                for bs in resp.buttons:
                    for b in bs:
                        if c.rars[r] in b.text.lower():
                            await b.click()
                            ismatch = True
                if not ismatch:
                    logging.info(f'button text didn\'t match {c.rars[r]}, cancelled')
                    await event.reply(f'button text didn\'t match {c.rars[r]}')
                    return
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                while True:
                    resp = await conv.get_response()
                    if resp.sender_id == c.target_id: break
                await resp.click(0, 0)
                resp = await conv.get_edit(resp.id-1)
                if 'Неудача!' in resp.text: lost += 1
                elif 'Успех!' in resp.text: upgraded += 1
                logging.info('%i complete', i)
    except TimeoutError:
        logging.error('timeout')
        await event.reply('timeout, bot didn\'t respond in 10 seconds')
    except (IndexError, TypeError):
        logging.error([f'no button {r}'])
    await event.reply(f'```statistics\n==========\n{upgraded} / {lost+upgraded} => {upgraded/(lost+upgraded)}```') # \n\n{upgraded_sum} - {source_sum} => {upgraded_sum-source_sum} [x{upgraded_sum/source_sum}]


async def macro_sell(event, r, q): # TODO: check if works
    logging.info('%i | %i', r, q)
    resp = None
    ismatch = False
    try:
        async with client.conversation(event.chat_id, timeout=10) as conv:
            for i in range(1 if q<0 else q):
                if q < 0: await conv.send_message(c.cmds['sa'])
                else: await conv.send_message(c.cmds['mp'])
                while True:
                    resp = await conv.get_response()
                    if resp.sender_id == c.target_id: break
                for bs in resp.buttons:
                    for b in bs:
                        if c.rars[r] in b.text.lower():
                            await b.click()
                            ismatch = True
                if not ismatch:
                    logging.info(f'button text didn\'t match {c.rars[r]}, cancelled')
                    await event.reply(f'button text didn\'t match {c.rars[r]}')
                    return
                if q < 0:
                    while True:
                        resp = await conv.get_response()
                        if resp.sender_id == c.target_id: break
                    await resp.click(0, 0)
                    return
                else: resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                while True:
                    resp = await conv.get_response()
                    if resp.sender_id == c.target_id: break
                await resp.click(0, 0)
    except TimeoutError:
        logging.info('timeout')
        await event.reply('timeout, bot didn\'t respond in 10 seconds')
    except IndexError:
        logging.error([f'no button {q}'])
        await event.reply(f'button text didn\'t match {q}')


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['cmd_handler']))
async def cmd_handler(event):
    text = event.text[1:]
    for key in c.cmds:
        if text == key:
            await event.delete()
            await event.reply(c.cmds[key])
            return None


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['macro_handler']))
async def macro_handler(event):
    macro = re.search(r'^\.([a-z]+)', event.text) # TOFIX: dot capturing
    flags = dict(re.findall(r'-([a-z]{1})(-?\d+)', event.text)) # TODO: single group

    r = int(flags.get('r', 0))
    q = int(flags.get('q', 0))
    logging.info(q)

    if macro.group() == '.buy':
        await macro_buy(event, r, q-1)
    elif macro.group() == '.upg':
        if q < 0: q = 2**16
        await macro_upgrade(event, r, q)
    elif macro.group() == '.sell':
        await macro_sell(event, r, q)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['spam_handler']))
async def spam_handler(event):
    logging.info('triggered, deleting')
    await event.delete()


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['card_handler']))
async def card_handler(event):
    if c.rars[0] in event.text.lower(): # TODO: finish smart card management
        await macro_upgrade(event, 0, 1)
    logging.info('triggered, sending cmd')
    await event.reply(c.cmds['tc'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['cardt_handler']))
async def cardt_handler(event):
    logging.info('triggered, scheduling cmd')
    global card_timer
    card_timer.cancel()

    wait = txt_to_sec(event.text)
    loop = asyncio.get_event_loop()

    card_timer = Timer(wait, lambda: schedule_msg(loop, c.target, c.cmds['tc']))
    card_timer.start()
    logging.info('waiting for %i seconds(%i m)', wait, int(wait/60))


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['daily_handler']))
async def daily_handler(event):
    logging.info('triggered, clicking btn')
    await event.message.click(0, 0)
    logging.info('clicked, sending cmd')
    await event.reply(c.cmds['ен'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['dailyt_handler']))
async def dailyt_handler(event):
    logging.info('triggered, scheduling cmd')
    global daily_timer
    daily_timer.cancel()

    wait = txt_to_sec(event.text)
    loop = asyncio.get_event_loop()

    daily_timer = Timer(wait, lambda: schedule_msg(loop, c.target, c.cmds['er']))
    daily_timer.start()
    logging.info('waiting for %i seconds(%i m)', wait, int(wait/60))


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=r'(?s)(?=.*Ваша майнинг ферма.*)'))
async def farm_handler(event): # TODO? possibly merge with other reset events
    logging.info('triggered')
    income = re.search(r'фермой: (\d+),?(\d+)?', event.text)
    if int(income.group(1) + (income.group(2) or '')) > 0:
        logging.info('getting income')
        await event.click(len(event.buttons)-1, len(event.buttons[len(event.buttons)-1])-1)
    wait = datetime.combine(date.min, reset_time) - datetime.combine(date.min, datetime.now().time())
    if wait < timedelta(0):
        wait = timedelta(hours=24) + wait
    loop = asyncio.get_event_loop()
    farm_timer = Timer(wait.total_seconds(), lambda: schedule_msg(loop, c.target, c.cmds['tf']))
    farm_timer.start()
    logging.info(f'waiting for {wait}')


async def buy_handler(event, r, q): # TOFIX: it doesn't work at all
    logging.info('triggered')
    wait = datetime.combine(date.min, reset_time) - datetime.combine(date.min, datetime.now().time())
    if wait < timedelta(0):
        wait = timedelta(hours=24) + wait
    loop = asyncio.get_event_loop()
    buy_timer = Timer(wait.total_seconds(), lambda: schedule_buy(loop, event, r, q))
    buy_timer.start()
    logging.info(f'waiting for {wait}')


@client.on(events.MessageEdited(from_users=c.target, chats=c.chats, pattern=r'(?s).*(@dikiy_opezdal|@ladzepo_yikid).*✅.*Вы'))
async def tradeb_handler(event):
    logging.info('matched, clicking')
    await event.click(2, 0)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['trade_handler']))
async def trade_handler(event):
    logging.info('matched, confirming')
    await event.reply(re.search(r'.*от @(.*)', event.text).group())
    await event.click(0, 0)
        

@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['etrade_handler']))
async def etrade_handler(event):
    msg = await client.get_messages(event.chat_id, ids=event.id-3)
    for u in c.tradelist:
        if u in msg.text:
            await event.click(0, 0)


@client.on(events.NewMessage(outgoing=True, pattern=r'^\.cti'))
async def farm_calculate(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        total = 0
        for c in cells:
            total += int(re.sub(',', '', c))
        await event.edit(f'Total daily income: {total}')


@client.on(events.NewMessage(outgoing=True, pattern=r'^createDB'))
async def create_phonesDB(event):
    logging.info('creating phones DB')
    resp = None
    pattern = r'(.*) \((\d+) ТОчек\)'
    phonesDB = {
        0: {},
        1: {},
        2: {},
        3: {},
        4: {},
        5: {},
        6: {
            'Xiaomi 15 Diamond Edition': 500000,
            'Xiaomi Mi Mix Alpha': 500000,
            'Samsung Galaxy S21 Olympic Edition': 500000,
            'Samsung K Zoom': 500000,
            'Xiaomi Poco X3': 500000,
            'Яндекс.Телефон': 500000,
            'OnePlus 5T Star Wars Limited Edition': 500000,
            'OnePlus Ace 5 Extreme Edition': 500000,
            'OPPO Find X Lamborghini': 500000,
            'Xiaomi Redmi Note 9A': 500000,
            'Samsung Galaxy Flip 6 Olympic Edition': 500000,
            'Телефон дизайнера: Nothing Phone 1': 500000,
            'Nokia 3310': 500000,
            'Apple Iphone 5s Gold Edition': 500000,
            'ZTE Nubia Music': 500000,
            'Light L16': 500000
        },
        7: {
            'Apple iPhone 9': 3000000,
            'Bubblephone Concept': 3000000,
            'Nokia Lumia McLaren': 3000000,
            'Google Project Ara': 3000000,
            'Nokia 888 Concept': 3000000
        }
    }
    async with client.conversation(event.chat_id) as conv:
        await conv.send_message(c.cmds['ps'])
        while True:
            resp = await conv.get_response()
            if resp.sender_id == c.target_id: break
        r = 0
        for bs in resp.buttons:
            for b in bs:
                await b.click()
                resp = await conv.get_edit(resp.id-1)
                while '➡️' in resp.buttons[len(resp.buttons)-2][2].text:
                    for ps in resp.buttons:
                        for p in ps:
                            if 'ТОчек' in p.text:
                                phone = re.search(pattern, p.text)
                                phonesDB[r][phone.group(1)] = int(phone.group(2))
                    await resp.buttons[len(resp.buttons)-2][2].click()
                    resp = await conv.get_edit(resp.id-1)
                    await asyncio.sleep(1)
                await resp.buttons[len(resp.buttons)-1][0].click()
                resp = await conv.get_edit(resp.id-1)
                r += 1
    with open('phonesDB.json', 'w') as f:
        json.dump(phonesDB, f, indent=4)


async def avito_sniff(event): # TODO: develop idea
    pass


async def init():
    logging.info('setting timers')
    #await client.send_message(c.target, c.cmds['тк'])
    #await client.send_message(c.target, c.cmds['ен'])


def terminate(signum, frame):
    logging.info('STOP')
    card_timer.cancel()
    daily_timer.cancel()
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