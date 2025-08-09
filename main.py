from telethon import TelegramClient, events, functions
import logging, re
from datetime import timedelta, datetime, time, date, UTC
import asyncio, signal, sys
import consts as c


logging.basicConfig(filename=c.log_path, filemode='a', format=c.log_format, level=logging.INFO) # TODO

reset_time = time(0, 10, 0, 0) # TODO

client = TelegramClient('anon', c.api_id, c.api_hash)

loop = None


def txt_to_sec(text):
    time = re.findall(c.patterns['txt_to_sec'], text)
    if len(time) < 1: return False
    return timedelta(hours=int(time[0]), minutes=int(time[1]), seconds=int(time[2]))


async def safe_click(matrix, text):
    for row in matrix:
        for btn in row:
            if text in btn.text.lower():
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


async def macro_buy(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            await conv.send_message(c.cmds['ps'])
            safe_get_resp(conv, c.target_id) # TODO discover how it works and include click in it
            await safe_click(resp.buttons, c.rars[r])
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(1, 0)
            resp = await conv.get_edit(resp.id-1)
            btns = resp.buttons
            if q < 0: await resp.click(len(btns)-2, len(btns[len(btns)-2])-1)
            else: await safe_click(btns, f'{q+1}') # TODO check if works
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
    except TimeoutError:
        timeout_msg(e, c.timeout)
    except IndexError:
        index_msg(e, q)


async def macro_upgrade(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    lost = upgraded = 0
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['up'])
                safe_get_resp(conv, c.target_id)
                await safe_click(resp.buttons, c.rars[r])
                await asyncio.sleep(c.flood_prev)
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                safe_get_resp(conv, c.target_id)
                await resp.click(0, 0)
                await asyncio.sleep(c.flood_prev)
                resp = await conv.get_edit(resp.id-1)
                if 'Неудача!' in resp.text: lost += 1
                elif 'Успех!' in resp.text: upgraded += 1
                logging.info('%i complete', i)
    except TimeoutError:
        timeout_msg(e, c.timeout)
    except IndexError:
        if q != 2**16 or lost+upgraded == 0: index_msg(e, c.rars[r])
    if lost+upgraded == 0: return
    await e.reply(f'```Statistics\n\n{upgraded} / {lost+upgraded} => {upgraded/(lost+upgraded)}```') # \n\n{upgraded_sum} - {source_sum} => {upgraded_sum-source_sum} [x{upgraded_sum/source_sum}]


async def macro_sell(e, r, q):
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['sa' if q == 2**16 else 'mp'])
                safe_get_resp(conv, c.target_id)
                await safe_click(resp.buttons, c.rars[r]) # TODO check if works
                if q == 2*16: safe_get_resp(conv, c.target_id)
                else: resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                if q < 0: return
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                safe_get_resp(conv, c.target_id)
                await resp.click(0, 0)
    except TimeoutError:
        timeout_msg(e, c.timeout)
    except IndexError:
        index_msg(e, c.rars[r])


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['cmd_handler'])) # TODO
async def cmd_handler(e): # PARTIAL
    text = e.pattern_match.group(1)
    for key in c.cmds:
        if text == key:
            await e.delete()
            await e.reply(c.cmds[key])
            return


async def farm_calculate(e): # PARTIAL
    if e.is_reply:
        total = 0
        reply = await e.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        for c in cells: total += int(re.sub(',', '', c))
        await e.edit(f'{total:,}')


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['macro_handler']))
async def macro_handler(e): # PARTIAL
    macro = re.search(r'^\.([a-z]+)', e.text)
    flags = dict(re.findall(r'-([a-z]{1})(-?\d+)', e.text)) # TODO: single group

    r = int(flags.get('r', 0))
    q = int(flags.get('q', 0))

    if macro.group(1) == 'buy':
        await macro_buy(e, r, q-1)
    elif macro.group(1) == 'upg':
        if q < 0: q = 2**16
        await macro_upgrade(e, r, q)
    elif macro.group(1) == 'sell':
        if q < 0: q = 2**16
        await macro_sell(e, r, q)
    elif macro.group(1) == 'cti':
        await farm_calculate(e)


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['spam_handler']))
async def spam_handler(e): # PARTIAL
    logging.info('deleting')
    await e.delete()


async def unschedule_dups(chat, text, date, minimal):
    exact = False
    msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=chat, hash=0))
    for m in msgs.messages:
        if m.message == text:
            diff = (m.date-date).total_seconds()
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
    exact = await unschedule_dups(e.chat_id, text, schedule, minimal)
    if not exact:
        await e.reply(text, schedule=schedule)
        logging.info(f'scheduled to {schedule}')


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['card_handler']))
async def card_handler(e): # PARTIAL
    logging.info('called')
    text = e.pattern_match
    offset = txt_to_sec(text.group(1))
    if offset:
        await schedule_msg(e, c.cmds['tc'], offset, 600)
    elif re.search(rf'({c.rarsregex})', text.group(2).lower()):
        await e.reply(c.cmds['tc'])
        logging.info(f'sent {c.cmds['tc']}')


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['daily_handler']))
async def daily_handler(e): # PARTIAL
    logging.info('called')
    text = e.pattern_match
    offset = txt_to_sec(text.group(1))
    if offset:
        await schedule_msg(e, c.cmds[tc], offset, 600)
    else:
        try:
            await safe_click(e.buttons, 'Забрать✅')
            logging.info('collected')
        except IndexError:
            await index_msg(e, 'Забрать✅')
        await e.reply(c.cmds['er'])
        logging.info(f'sent {c.cmds['tc']}')


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=r'(?s)(?=.*Ваша майнинг ферма.*)'))
async def farm_handler(e): # TODO? possibly merge with other reset events
    logging.info('called')
    income = re.search(r'фермой: (\d+),?(\d+)?', e.text)
    if int(income.group(1) + (income.group(2) or '')) > 0:
        logging.info('getting income')
        await safe_click(e.buttons, 'снять деньги с фермы')
    offset = datetime.combine(date.min, reset_time) - datetime.combine(date.min, datetime.now().time())
    if offset < timedelta(0): offset = timedelta(hours=24) + offset
    await schedule_msg(e, c.cmds['tf'], offset, 600)

    
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
        for u in c.whitelist:
            if u in msg.text:
                await e.click(0, 0)


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