import re
import logging
from telethon import TelegramClient, events, functions
from datetime import timedelta, datetime, time, date, UTC
import asyncio, signal, sys
import consts as c
from consts import client
from shared import *


async def macro_buy(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            await conv.send_message(c.cmds['ps'])
            resp = await safe_get_resp(conv, c.target_id) # TODO discover how it works and include click in it
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
        await timeout_msg(e, c.timeout)
    except IndexError:
        await index_msg(e, q)


async def macro_upgrade(e, r, q): # PARTIAL
    logging.info(f'{r} | {q}')
    lost = []
    upgraded = []
    source = []
    history = ''
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['up'])
                resp = await safe_get_resp(conv, c.target_id)
                await safe_click(resp.buttons, c.rars[r])
                await asyncio.sleep(c.flood_prev)
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                resp = await safe_get_resp(conv, c.target_id)
                key = re.search(r'телефон\s.{1}\s(.+)\.', resp.text).group(1)
                source.append(c.phonesDB[str(r)].get(key, 0)) # TOFIX
                await resp.click(0, 0)
                await asyncio.sleep(c.flood_prev)
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
    await e.reply(f'<pre>Statistics\n\n'\
        f'>rates\n{len(upgraded)} / {len(source)} => {rate}\n\n'\
        f'>profit\n{sum(source):,} - {sum(lost):,} => {sum(upgraded):,} ({profit:,})\n\n'\
        f'>summary\n{rate*100}% | x{mprof}\n+{max(profit, 0):,} | {sum(upgraded):,} | -{sum(lost):,}</pre> <blockquote expandable>Details: {history}</blockquote>', parse_mode='html')


async def macro_sell(e, r, q):
    logging.info(f'{r} | {q}')
    try:
        async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
            for i in range(q):
                await conv.send_message(c.cmds['sa' if q == 2**16 else 'mp'])
                resp = await safe_get_resp(conv, c.target_id)
                await safe_click(resp.buttons, c.rars[r]) # TODO check if works
                if q == 2*16: resp = await safe_get_resp(conv, c.target_id)
                else: resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                if q < 0: return
                resp = await conv.get_edit(resp.id-1)
                await resp.click(0, 0)
                resp = await safe_get_resp(conv, c.target_id)
                await resp.click(0, 0)
    except TimeoutError:
        await timeout_msg(e, c.timeout)
    except IndexError:
        await index_msg(e, c.rars[r])
    
async def farm_calculate(e): # PARTIAL
    if e.is_reply:
        total = 0
        reply = await e.get_reply_message()
        cells = re.findall(r'сутки: (.*) ТОчек', reply.text)
        for c in cells: total += int(re.sub(',', '', c))
        await e.edit(f'{total:,}')


async def trade_add(e, r, q):
    logging.info(f'{r} | {q}')
    if e.is_reply:
        reply = await e.get_reply_message()
        try:
            async with client.conversation(e.chat_id, timeout=c.timeout) as conv:
                for i in range(q):
                    await safe_click(reply.buttons, 'Добавить телефон')
                    resp = await conv.get_edit(reply.id-1)
                    await safe_click(resp.buttons, c.rars[r])
                    resp = await conv.get_edit(resp.id-2)
                    await asyncio.sleep(c.flood_prev)
                    await resp.click(0, 0)
                    resp = await conv.get_edit(resp.id-2)
                    await asyncio.sleep(c.flood_prev)
                    logging.info('%i complete', i)
        except TimeoutError:
            await timeout_msg(e, c.timeout)
        except IndexError:
            await index_msg(e, c.rars[r])


async def print_who(e, n):
    msg = ''
    for r in c.phonesDB:
        for p in c.phonesDB[r]:
            if n.lower() in p.lower():
                msg += f'<b>Model</b>: {p}\n<b>Rarity</b>: {c.rars[int(r)]}\n<b>Price</b>: {c.phonesDB[r][p]}\n<b>Selling price</b>: {c.phonesDB[r][p]*0.75}\n\n'
    if len(msg) > 0:
        await e.reply(f'<blockquote>'+msg+'</blockquote>', parse_mode='html')
    else: 
        await e.reply('Not found')


async def dup_schedule(e, q):
    initial_offset = timedelta(seconds=0)
    msgs = await client(functions.messages.GetScheduledHistoryRequest(peer=e.chat_id, hash=0))
    for m in msgs.messages:
        if m.message == c.cmds['tc']:
            initial_offset = m.date-datetime.now(UTC)
            break
    for i in range(q, start=1):
        await schedule_msg(e, c.cmds['tc'], initial_offset + timedelta(seconds=i*c.tcreload), 1000)
    await e.edit(f'`.dtc -q{q}`\ndone')


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['macro_handler']))
async def macro_handler(e): # PARTIAL
    macro = re.search(r'^\.([a-z]+)', e.text)
    text = re.search(r'^\.[a-z]+.*-t(.*);\s?', e.text)
    flags = dict(re.findall(r'-([a-z]{1})(-?\d+)', e.text)) # TODO: single group

    r = int(flags.get('r', 0))
    q = int(flags.get('q', 0))
    t = None
    if text: t = text.group(1)
    m = int(flags.get('m', 0))
    x = int(flags.get('x', 2**32))

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
    elif macro.group(1) == 'tdi':
        if q < 0: q = 2**16
        await trade_add(e, r, q)
    elif macro.group(1) == 'who':
        await print_who(e, t)
    elif macro.group(1) == 'gps':
        from get_phones import get_phones
        await get_phones(client, logging)
    elif macro.group(1) == 'dtc':
        await dup_schedule(e, q)
    elif macro.group(1) == 'dam':
        await unschedule_dups(e.chat_id, t, datetime.now(UTC), 0) # TOFIX: delete last one
        await e.edit(f'`.dam -t{t};`\ndone')
