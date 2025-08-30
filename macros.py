import re
import os, sys
import logging
from telethon import TelegramClient, events, functions, tl
from datetime import timedelta, datetime, time, date, UTC
import asyncio, signal, sys
import consts as c
from consts import client
from shared import *


async def macro_buy(e, r, q, n, p):
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            await conv.send_message(c.cmds['ps'])
            resp = await safe_get_resp(conv, c.target_id) # TODO discover how it works and include click in it?
            await safe_click(resp.buttons, c.rars[r])
            resp = await conv.get_edit(resp.id-1)
            await safe_click_scroll(conv, resp.buttons, n, p)
            resp = await conv.get_edit(resp.id-1)
            await resp.click(1, 0)
            resp = await conv.get_edit(resp.id-1)
            btns = resp.buttons
            if q < 0: await resp.click(len(btns)-2, len(btns[len(btns)-2])-1)
            else: await safe_click(btns, f'{q}') # TODO check if works
            resp = await conv.get_edit(resp.id-1)
            await resp.click(0, 0)
    except TimeoutError:
        await timeout_msg(e, c.timeout)
    except IndexError:
        await index_msg(e, q)


async def macro_upgrade(e, r, q, n, p):
    logging.info(f'{r} | {q}')
    lost = []
    upgraded = []
    source = []
    history = ''
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['up'])
                resp_wait = datetime.now()
                resp = await safe_get_resp(conv, c.target_id)
                resp_wait = datetime.now() - resp_wait
                await safe_click(resp.buttons, c.rars[r])
                await asyncio.sleep(max(c.flood_prev-resp_wait.total_seconds(), 0))
                resp = await conv.get_edit(resp.id-1)
                await safe_click_scroll(conv, resp.buttons, n, p)
                resp = await safe_get_resp(conv, c.target_id)
                key = re.search(r'телефон\s.{1}\s(.+)\.', resp.text).group(1)
                source.append(c.phonesDB[str(r)].get(key, 0)) # TOFIX
                resp_wait = datetime.now()
                await resp.click(0, 0)
                resp_wait = datetime.now() - resp_wait
                await asyncio.sleep(max(c.flood_prev-resp_wait.total_seconds(), 0))
                resp = await conv.get_edit(resp.id-1)
                value = int(re.sub(',', '', re.search(r': (.*) ТОчек', resp.text).group(1)))
                if 'Неудача!' in resp.text:
                    lost.append(value)
                    history += f'\n❌ {key} ({source[len(source)-1]:,}) =[x0.0]=> LOST (0)'
                elif 'Успех!' in resp.text:
                    upgraded.append(value)
                    history += f'\n✅ {key} ({source[len(source)-1]:,}) =[x{round(upgraded[len(upgraded)-1]/source[len(source)-1], 2)}]=> {re.search(r'телефон:\s.{1}\s(.+)\n', resp.text).group(1)} ({upgraded[len(upgraded)-1]:,})'
                logging.info('%i complete', i)
    except TimeoutError:
        await timeout_msg(e, c.timeout)
    except KeyError:
        logging.error('keyerror')
    except IndexError:
        if q != 2**16 or len(source) == 0: await index_msg(e, c.rars[r])
    if len(source) == 0: return
    rate = round(len(upgraded)/len(source), 2)
    profit = sum(upgraded)-sum(source)
    mprof = round(sum(upgraded)/sum(source), 2)

    await e.reply(f'<pre>{tabulate([[]], ['upgraded', 'total', 'ratio', 'lost'], tablefmt="rounded_outline")}</pre>')

    await e.reply(f'<pre>Statistics\n\n'\
        f'>rates\n{len(upgraded)} / {len(source)} => {rate}\n\n'\
        f'>profit\n{sum(source):,} - {sum(lost):,} => {sum(upgraded):,} ({profit:,})\n\n'\
        f'>summary\n{rate*100}% | x{mprof}\n+{max(profit, 0):,} | {sum(upgraded):,} | -{sum(lost):,}</pre> <blockquote expandable>Details: {history}</blockquote>', parse_mode='html')


async def macro_sell(e, r, q, n, p):
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['sa' if q == 2**16 else 'mp'])
                resp = await safe_get_resp(conv, c.target_id)
                await safe_click(resp.buttons, c.rars[r]) # TODO check if works
                if q == 2*16:
                    resp = await safe_get_resp(conv, c.target_id)
                    resp.click(0, 0)
                    return
                resp = await conv.get_edit(resp.id-1)
                await safe_click_scroll(conv, resp.buttons, n, p)
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                resp = await safe_get_resp(conv, c.target_id)
                await resp.click(0, 0)
    except TimeoutError:
        await timeout_msg(e, c.timeout)
    except IndexError:
        await index_msg(e, c.rars[r])
    

async def farm_calculate(e):
    if e.is_reply:
        total = 0
        reply = await e.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        for c in cells: total += int(re.sub(',', '', c))
        await e.edit(f'{total:,}')


async def trade_add(e, r, q, n, p):
    logging.info(f'{r} | {q}')
    if e.is_reply:
        reply = await e.get_reply_message()
        try:
            async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
                for i in range(q):
                    await safe_click(reply.buttons, 'Добавить телефон')
                    resp = await conv.get_edit(reply.id-1)
                    await safe_click(resp.buttons, c.rars[r])
                    resp_wait = datetime.now()
                    resp = await conv.get_edit(resp.id-2)
                    resp_wait = datetime.now() - resp_wait
                    await asyncio.sleep(max(c.flood_prev-resp_wait.total_seconds(), 0))
                    await safe_click_scroll(conv, resp.buttons, n, p)
                    resp_wait = datetime.now()
                    resp = await conv.get_edit(resp.id-2)
                    resp_wait = datetime.now() - resp_wait
                    await asyncio.sleep(max(c.flood_prev-resp_wait.total_seconds(), 0))
                    logging.info('%i complete', i)
        except TimeoutError:
            if i < 6:
                await timeout_msg(e, c.timeout)
        except IndexError:
            await index_msg(e, c.rars[r])


async def print_who(e, n, p, q):
    def loop():
        nonlocal msg
        for r in c.phonesDB:
            i = 0
            for k in c.phonesDB[r]:
                if (n.lower() in k.lower()) and ((p == c.phonesDB[r][k]) if p > 0 else True):
                    i += 1
                    if i > q: return
                    msg += f'<b>Model</b>: {k}\n<b>Rarity</b>: {c.rars[int(r)]}\n<b>Price</b>: {c.phonesDB[r][k]}\n<b>Selling price</b>: {c.phonesDB[r][k]*0.75}\n\n'
    q = q if q > 0 else 2**32
    msg = ''
    loop()
    if len(msg) > 0:
        await e.reply(f'<blockquote>'+msg+'</blockquote>', parse_mode='html')
    else: 
        await e.reply('Not found')


async def dup_schedule(e, q):
    initial_offset = timedelta(seconds=0)
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            await conv.send_message(c.cmds['tc'])
            resp = await safe_get_resp(conv, c.target_id)
            msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=e.chat_id, hash=0))
            for m in msgs.messages:
                if m.message == c.cmds['tc']:
                    initial_offset = m.date-datetime.now(UTC)
                    break
    except TimeoutError:
        initial_offset = c.tcreload
    for i in range(q):
        await schedule_msg(e, c.cmds['tc'], initial_offset + timedelta(seconds=i*(c.tcreload+60)), c.tcreload)
    await e.edit(f'`{e.text}`\n\ndone')


def uprofit_calculate(e, n):
    for r in c.phonesDB:
        for k in c.phonesDB[r]:
            if n.lower() in k.lower():
                pass # take price and compare to avg price of next rarity + display general profit from stat


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['macro_handler']))
async def macro_handler(e):
    macro = re.search(r'^\.([a-z]+)', e.text)
    flags = re.findall(r'-([a-z]{1})(?:([0-9\,]+)|(?:\"(.+)\"\,?)+)', e.text)
    for i, t in enumerate(flags): flags[i] = tuple(x for x in t if x != '')
    flags = dict(flags)

    r = list(map(int, flags.get('r', '0').split(','))) # rarity/reboot/repeat
    q = list(map(int, flags.get('q', '0').split(','))) # quantity/quit
    p = list(map(int, flags.get('p', '0').split(','))) # price
    s = list(map(int, flags.get('s', '0').split(','))) # seconds/sleep
    n = flags.get('n', '').replace('"', '').split(',') # name

    def si(a, i): return a[min(i, len(a)-1)]

    match macro.group(1):
        case 'buy':
            longest = max(len(r), len(q), len(n), len(p))
            for i in range(longest):
                await macro_buy(e, si(r, i), si(q, i), si(n, i), si(p, i))
        case 'upg':
            longest = max(len(r), len(q), len(n), len(p))
            for i in range(longest):
                await macro_upgrade(e, si(r, i), si(q, i), si(n, i), si(p, i))
        case 'sell':
            longest = max(len(r), len(q), len(n), len(p))
            for i in range(longest):
                await macro_sell(e, si(r, i), si(q, i), si(n, i), si(p, i))
        case 'cti':
            await farm_calculate(e)
        case 'tdi':
            longest = max(len(r), len(q), len(n), len(p))
            for i in range(longest):
                await trade_add(e, si(r, i), si(q, i), si(n, i), si(p, i))
        case 'who':
            longest = max(len(n), len(p), len(q))
            for i in range(longest):
                await print_who(e, si(n, i), si(p, i), si(q, i))
        case 'gps':
            from get_phones import get_phones
            await get_phones(client, logging)
        case 'dtc':
            for i in range(len(q)):
                await dup_schedule(e, q[i])
        case 'dam':
            for i in range(len(n)):
                await unschedule_dups(e.chat_id, n[i], datetime.now(UTC), 100000000)
            await e.edit(f'`{e.text}`\n\ndone')
        case 'ctl':
            if r[0] == 1:
                python = sys.executable
                os.execv(python, [python] + sys.argv)
            elif q[0] == 1:
                async with client.conversation(e.chat_id) as conv:
                    await conv.send_message('Terminating in 10s, `.tac` to cancel...')
                    await asyncio.sleep(10)
                    await conv.send_message('Terminating...')
                    terminate(0, 0)
            elif s[0] == 1:
                pass # bot_sleep()
        case 'tac':
            async with client.conversation(e.chat_id, exclusive=False) as conv:
                await conv.cancel_all()
                await e.edit(f'`{e.text}`\n\ndone')
        case 'scm':
            longest = max(len(n), len(s))
            for i in range(longest):
                await schedule_msg(e, si(n, i), timedelta(seconds=si(s, i)), si(s, i))
                if si(r, i) == 1:
                    await schedule_msg(e, e.text, timedelta(seconds=si(s, i)), si(s, i))
        case 'pup':
            for i in range(n):
                await uprofit_calculate(e, n[i])
        case 'idk':
            files = [
                os.path.join("/home/user0/videos/camera", f)
                for f in os.listdir("/home/user0/videos/camera")
            ]
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            await e.edit(f'loading {files[q[0]]}...')
            await e.reply(file=files[q[0]])