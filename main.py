from telethon import TelegramClient, events
import logging, re
from threading import Timer
from datetime import timedelta
import asyncio, signal, sys
import consts as c


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO)

card_timer = Timer(0, None)
daily_timer = Timer(0, None)
# TODO? custom macros(remembers user's actions and replicates)(possibly json) and custom timers

client = TelegramClient('anon', c.api_id, c.api_hash)


def txt_to_sec(text):
    time = re.findall(c.patterns['txt_to_sec'], text)
    return timedelta(hours=int(time[0]), minutes=int(time[1]), seconds=int(time[2])).total_seconds()


async def send_msg(target, text):
    await client.send_message(target, text)
    logging.info('[send_msg] sent "%s"', text)


async def macro_buy(event, r, q):
    logging.info('[macro_buy] %i | %i', r, q)
    try:
        async with client.conversation(event.chat_id, timeout=10) as conv:
            resp = None
            await conv.send_message(c.cmds['ps'])
            while True:
                resp = await conv.get_response()
                if resp.sender_id == c.target_id: break
            await resp.click(int(r/2), r%2)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
            resp = await conv.get_edit(resp.id)
            await resp.click(1, 0)
            resp = await conv.get_edit(response.id)
            if resp.buttons[int(q/5)][q%5].text == f'{q+1}':
                await resp.click(int(q/5), q%5)
            else:
                logging.info(f'[macro_buy] button text didn\'t match {q}, cancelled')
                await event.reply(f'button text didn\'t match {q}')
                return
            resp = await conv.get_edit(resp.id)
            await resp.click(0, 0)
    except TimeoutError:
        logging.info('[macro_buy] timeout')
        await event.reply('timeout, bot didn\'t respond in 10 seconds')


async def macro_upgrade(event, r, q):
    logging.info('[macro_upgrade] %i | %i', r, q)
    lost = 0
    upgraded = 0
    try:
        async with client.conversation(event.chat_id, timeout=10) as conv:
            resp = None
            ismatch = False
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
                    logging.info(f'[macro_upgrade] button text didn\'t match {c.rars[r]}, cancelled')
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
                logging.info('[macro_upgrade] %i complete', i)
    except TimeoutError:
        logging.error('[macro_buy] timeout, bot didn\'t respond in 10 seconds')
        await event.reply('timeout')
    except IndexError:
        logging.error([f'[macro_buy] no button {r}'])
    await event.reply(f'```Statistics\n\nTotal: {q}\nUpgraded: {upgraded}\nLost: {lost}\nRate: {(upgraded)/q}```')


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
    flags = dict(re.findall(r'-([a-z]{1})(\d+)', event.text))

    r = int(flags.get('r', 0))
    q = int(flags.get('q', 0))

    if macro.group() == '.buy':
        await macro_buy(event, r, q-1)
    elif macro.group() == '.upg':
        await macro_upgrade(event, r, q)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['spam_handler']))
async def spam_handler(event):
    logging.info('[spam_handler] triggered, deleting')
    await event.delete()


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['card_handler']))
async def card_handler(event):
    logging.info('[card_handler] triggered, sending cmd')
    await event.reply(c.cmds['tc'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['cardt_handler']))
async def cardt_handler(event):
    logging.info('[cardt_handler] triggered, scheduling cmd')
    global card_timer
    card_timer.cancel()

    time = txt_to_sec(event.text)
    loop = asyncio.get_event_loop()

    card_timer = Timer(time, lambda: Timer(time, lambda: asyncio.run_coroutine_threadsafe(send_msg(c.target, c.cmds['tc']), loop)))
    card_timer.start()
    logging.info('[cardt_handler] waiting for %i seconds', time)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['daily_handler']))
async def daily_handler(event):
    logging.info('[daily_handler] triggered, clicking btn')
    await event.message.click(0, 0)
    logging.info('[daily_handler] clicked, sending cmd')
    await event.reply(c.cmds['ен'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['dailyt_handler']))
async def dailyt_handler(event):
    logging.info('[dailyt_handler] triggered, scheduling cmd')
    global daily_timer
    daily_timer.cancel()

    time = txt_to_sec(event.text)
    loop = asyncio.get_event_loop()

    daily_timer = Timer(time, lambda: asyncio.run_coroutine_threadsafe(send_msg(c.target, c.cmds['er']), loop))
    daily_timer.start()
    logging.info('[dailyt_handler] waiting for %i seconds', time)


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
async def farm_handler(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        total = 0
        for c in cells:
            total += int(re.sub(',', '', c))
        await event.edit(f'Total daily income: {total}')


async def init():
    logging.info('[init] setting timers')
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