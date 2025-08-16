import json, os
from telethon import TelegramClient

# TODO? move all customizable text to json
f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

log_path = 'phoneget_userbot.log'
log_format = '[%(asctime)s] [%(levelname)s] [%(funcName)s]: %(message)s'

target = '@phonegetcardsbot'
target_id = 7808172033
chats = '@phonegetcardsbot'

timeout = 10
flood_prev = 0.75

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phonesDB.json'), 'r') as f:
    phonesDB = json.load(f)

client = TelegramClient('anon', api_id, api_hash)

def arr2regex(arr):
    result = ''
    for i in arr:
        result += i + '|'
    return result[:-1]

with open('settings.json', 'r') as f:
    settings = json.load(f)
    whitelist = settings['WL']
    tcreload = settings['TCR']

wtregex = arr2regex(whitelist)

rars = {
    0: 'ширп',
    1: 'необ',
    2: 'редк',
    3: 'мист',
    4: 'хром',
    5: 'арк',
    6: 'арт',
    7: 'фант'
}
rarsregex = arr2regex(rars.values())

patterns = {
    'txt_to_sec'     : r'(\d+)\s*(?:ч|м|с)',
    'cmd_handler'    : r'^!(.+)',
    'macro_handler'  : r'^\.(.+)', # TODO
    'spam_handler'   : r'(?is).*розыгрыш.*|.*подписка на каналы.*',
    'card_handler'   : rf'(?is).*(выпал.*({rarsregex}).*|выбить.*).*',
    'daily_handler'  : r'(?s).*(награды:.*|завтра.*).*',
    'trade_handler'  : rf'(?s).*(от @({wtregex})|(@({wtregex}).*✅.*Вы|ПОДТВЕРДИТЕ)).*'
}

cmds = {
    **dict.fromkeys(['тк', 'tc'], 'ТКарточка'),
    **dict.fromkeys(['та', 'ta'], 'ТАкк'),
    **dict.fromkeys(['мо', 'mp'], 'Мои телефоны'),
    **dict.fromkeys(['мт', 'ps'], 'Магазин телефонов'),
    **dict.fromkeys(['му', 'us'], 'Магазин улучшений'),
    **dict.fromkeys(['ап', 'up'], 'Апгрейд'),
    **dict.fromkeys(['ен', 'er'], 'Ежедневная награда'),
    **dict.fromkeys(['са', 'sa'], '/sellall'),
    **dict.fromkeys(['тл', 'lt'], 'Таблица лидеров'),
    **dict.fromkeys(['п',  'p'],  '/pay'),
    **dict.fromkeys(['ев', 'ev'], '/event'),
    **dict.fromkeys(['тр', 'tr'], '/trade'),
    **dict.fromkeys(['ав', 'av'], '/avito'),
    **dict.fromkeys(['тф', 'tf'], '/tfarm'),
    **dict.fromkeys(['км', 'h'],
    '```тк|tc — ТКарточка\n'+
        'та|ta — ТАкк\n'+
        'мо|mp — Мои телефоны\n'+
        'мт|ps — Магазин телефонов\n'+
        'му|us — Магазин улучшений\n'+
        'ап|up — Апгрейд\n'+
        'ен|er — Ежедневная награда\n'+
        'са|sa — /sellall\n'+
        'тл|lt — Таблица лидеров\n'+
        'п |p  — /pay\n'+
        'ев|ev — /event\n'+
        'тр|tr — /trade\n'+
        'ав|av — /avito\n'+
        'тф|tf — /tfarm\n'+
        'км|h  — This text\n```')
}