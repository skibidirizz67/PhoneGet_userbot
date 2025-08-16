from macros import *
from shared import *

import logging
import consts as c
from consts import client


reset_time = time(0, 10, 0, 0) # TODO


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=c.patterns['spam_handler']))
async def spam_handler(e): # PARTIAL
    logging.info('deleting')
    await e.delete()


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
        await schedule_msg(e, c.cmds['er'], offset, 600)
    else:
        try:
            await safe_click(e.buttons, 'Забрать✅')
            logging.info('collected')
        except IndexError:
            await index_msg(e, 'Забрать✅')
        await e.reply(c.cmds['er'])
        logging.info(f'sent {c.cmds['er']}')


@client.on(events.NewMessage(from_users=c.target, chats=c.chats, pattern=r'(?s)(?=.*Ваша майнинг ферма.*)'))
async def farm_handler(e): # TODO? possibly merge with other reset events
    logging.info('called')
    income = re.search(r'фермой: (\d+),?(\d+)?', e.text)
    if int(income.group(1) + (income.group(2) or '')) > 0:
        logging.info(f'getting income {income.group(1) + income.group(2)}')
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


@client.on(events.NewMessage(outgoing=True, pattern=c.patterns['cmd_handler'])) # TODO
async def cmd_handler(e): # PARTIAL
    text = e.pattern_match.group(1)
    for key in c.cmds:
        if text == key:
            await e.delete()
            await e.reply(c.cmds[key])
            return