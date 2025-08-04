from telethon import TelegramClient, events
import logging, re
from threading import Timer
from datetime import timedelta, datetime, time, date
import asyncio, signal, sys
import consts as c


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO) # TODO

card_timer = Timer(0, None) # TODO
daily_timer = Timer(0, None)
farm_timer = Timer(0, None)

reset_time = time(0, 10, 0, 0) # TODO

client = TelegramClient('anon', c.api_id, c.api_hash)


def txt_to_sec(text): # PARTIAL
    time = re.findall(c.patterns['txt_to_sec'], text)
    return timedelta(hours=int(time[0]), minutes=int(time[1]), seconds=int(time[2])).total_seconds()


async def send_msg(target, text): # PARTIAL
    await client.send_message(target, text)
    logging.info('sent "%s"', text)
def schedule_msg(loop, target, text):
    asyncio.run_coroutine_threadsafe(send_msg(target, text), loop)


async def macro_buy(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=10) as conv:
            await conv.send_message(c.cmds['ps'])
            while (resp := await conv.get_response()).sender_id != c.target_id: pass # TODO
            await resp.click(int(r/2), r%2)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(1, 0)
            resp = await conv.get_edit(resp.id-1)
            btns = resp.buttons
            if q < 0: await resp.click(len(btns)-2, len(btns[len(btns)-2])-1)
            elif btns[int(q/5)][q%5].text == f'{q+1}': await resp.click(int(q/5), q%5)
            else: raise IndexError
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
    except TimeoutError:
        logging.info('timeout 10 s')
        await e.reply('timeout, bot didn\'t respond in 10 seconds')
    except IndexError:
        logging.error([f'button text didn\'t match {q}'])
        await e.reply(f'quantity "{q}" not found')


async def macro_upgrade(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    lost = upgraded = 0
    ismatch = False
    try:
        async with client.conversation(e.chat_id, timeout=10) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['up'])
                while (resp := await conv.get_response()).sender_id != c.target_id: pass
                for bs in resp.buttons: # TODO
                    for b in bs:
                        if c.rars[r] in b.text.lower():
                            await b.click()
                            ismatch = True
                if not ismatch: raise IndexError
                ismatch = False
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                while (resp := await conv.get_response()).sender_id != c.target_id: pass
                await resp.click(0, 0)
                resp = await conv.get_edit(resp.id-1)
                if 'Неудача!' in resp.text: lost += 1
                elif 'Успех!' in resp.text: upgraded += 1
                logging.info('%i complete', i)
    except TimeoutError:
        logging.error('timeout 10 s')
        await e.reply('timeout, bot didn\'t respond in 10 seconds')
    except (IndexError, TypeError):
        logging.error([f'button text didn\'t match {c.rars[r]}'])
        await e.reply(f'rarity "{c.rars[r]}" not found')
    await e.reply(f'```Statistics\n\n{upgraded} / {lost+upgraded} => {upgraded/(lost+upgraded)}```') # \n\n{upgraded_sum} - {source_sum} => {upgraded_sum-source_sum} [x{upgraded_sum/source_sum}]


async def macro_sell(e, r, q):
    logging.info(f'{r} | {q}')
    ismatch = False
    try:
        async with client.conversation(e.chat_id, timeout=10) as conv:
            for i in range(q):
                if q < 0: await conv.send_message(c.cmds['sa'])
                else: await conv.send_message(c.cmds['mp'])
                while (resp := await conv.get_response()).sender_id != c.target_id: pass
                for bs in resp.buttons:
                    for b in bs:
                        if c.rars[r] in b.text.lower():
                            await b.click()
                            ismatch = True
                if not ismatch: raise IndexError
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
                while (resp := await conv.get_response()).sender_id != c.target_id: pass
                await resp.click(0, 0)
    except TimeoutError:
        logging.error('timeout 10 s')
        await e.reply('timeout, bot didn\'t respond in 10 seconds')
    except IndexError:
        logging.error([f'button text didn\'t match {q}'])
        await e.reply(f'qunatity "{q}" not found') # ???


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['cmd_handler'])) # TODO
async def cmd_handler(e): # PARTIAL
    text = e.pattern_match.group(1)
    for key in c.cmds:
        if text == key:
            await e.delete()
            await e.reply(c.cmds[key])
            return


async def farm_calculate(e, l): # PARTIAL
    if e.is_reply:
        reply = await e.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        total = 0
        for c in cells: total += int(re.sub(',', '', c))
        if l > 0: await e.edit(f'```{total}/d | {total/l*100}```')
        else: await e.edit(f'```{total}/d```')


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['macro_handler']))
async def macro_handler(e): # PARTIAL
    macro = re.search(r'^\.([a-z]+)', e.text)
    flags = dict(re.findall(r'-([a-z]{1})(-?\d+)', e.text)) # TODO: single group

    r = int(flags.get('r', 0))
    q = int(flags.get('q', 0))
    l = int(flags.get('l', 0))

    if macro.group(1) == 'buy':
        await macro_buy(e, r, q-1)
    elif macro.group(1) == 'upg':
        if q < 0: q = 2**16
        await macro_upgrade(e, r, q)
    elif macro.group(1) == 'sell':
        await macro_sell(e, r, q)
    elif macro.group(1) == 'cti':
        await farm_calculate(e, l)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['spam_handler']))
async def spam_handler(e): # PARTIAL
    logging.info('deleting')
    await e.delete()


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['card_handler']))
async def card_handler(e): # PARTIAL
    if c.rars[0] in e.text.lower():
        await macro_upgrade(e, 0, 1)
    logging.info('sending cmd')
    await e.reply(c.cmds['tc'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['cardt_handler']))
async def cardt_handler(e): # PARTIAL
    logging.info('scheduling cmd')
    global card_timer
    card_timer.cancel()

    wait = txt_to_sec(e.text)
    loop = asyncio.get_event_loop()

    card_timer = Timer(wait, lambda: schedule_msg(loop, c.target, c.cmds['tc']))
    card_timer.start()
    logging.info('waiting for %i seconds(%i m)', wait, int(wait/60))


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['daily_handler']))
async def daily_handler(e): # PARTIAL
    logging.info('triggered, clicking btn')
    await e.message.click(0, 0)
    logging.info('clicked, sending cmd')
    await e.reply(c.cmds['ен'])


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['dailyt_handler']))
async def dailyt_handler(e): # PARTIAL
    logging.info('triggered, scheduling cmd')
    global daily_timer
    daily_timer.cancel()

    wait = txt_to_sec(e.text)
    loop = asyncio.get_event_loop()

    daily_timer = Timer(wait, lambda: schedule_msg(loop, c.target, c.cmds['er']))
    daily_timer.start()
    logging.info('waiting for %i seconds(%i m)', wait, int(wait/60))


@client.on(events.NewMessage(outgoing=True, pattern=r'(?s)(?=.*Ваша майнинг ферма.*)'))
async def farm_handler(e): # TODO? possibly merge with other reset events
    logging.info('triggered')
    income = re.search(r'фермой: (\d+),?(\d+)?', e.text)
    if int(income.group(1) + (income.group(2) or '')) > 0:
        logging.info('getting income')
        await e.click(len(e.buttons)-1, len(e.buttons[len(e.buttons)-1])-1)
    wait = datetime.combine(date.min, reset_time) - datetime.combine(date.min, datetime.now().time())
    if wait < timedelta(0): wait = timedelta(hours=24) + wait
    loop = asyncio.get_event_loop()
    farm_timer = Timer(wait.total_seconds(), lambda: schedule_msg(loop, c.target, c.cmds['tf']))
    farm_timer.start()
    logging.info(f'waiting for {wait}')

    
@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['trade_handler'])) # TODO
@client.on(events.MessageEdited(from_users=c.target, chats=c.chats, pattern=c.patterns['trade_handler']))
async def trade_handler(e): # PARTIAL
    text = e.pattern_match.group(1)
    if 'от @' in text:
        logging.info('allowing')
        await e.click(0, 0)
    elif 'отдаёт' in text:
        logging.info('ready')
        await e.reply(text[:text.find(' ')])
        await e.click(2, 0)
    elif 'ПОДТВЕРДИТЕ' in text:
        logging.info('confirming')
        msg = await client.get_messages(e.chat_id, ids=e.id-1)
        if not msg: msg = await client.get_messages(e.chat_id, ids=e.id-2)
        logging.info(msg)
        for u in c.tradelist:
            if u in msg.text:
                await e.click(0, 0)


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