from telethon import TelegramClient, events
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s]: %(message)s', level=logging.INFO)

f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

me = 5359995738
targets = [7808172033]

cmds = {'тк':'ТКарточка', 'та':'ТАкк', 'мо':'Мои телефоны', 'мт':'Магазин телефонов', 'му':'Мои улучшения', 'ап':'Апгрейд', 'ен':'Ежедневная награда', 'са':'/sellall'}

client = TelegramClient('anon', api_id, api_hash)

@client.on(events.NewMessage(from_users=targets))
async def nm_handler(event):
    print(0)

@client.on(events.NewMessage(outgoing=True, pattern=r'\!'))
async def cmd_handler(event):
    text = event.text[1:]
    for key in cmds:
        if text == key:
            await event.reply(cmds[key])
            await event.delete()

client.start()
client.run_until_disconnected()