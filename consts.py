f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

log_path = 'phoneget_userbot.log'
log_format = '[%(asctime)s] [%(levelname)s]: %(message)s'

target = '@phonegetcardsbot'
me = None

patterns = {}
async def getme(client):
    global me, patterns
    me = await client.get_me()
    me = me.username
    patterns = {
        'cmd_handler':r'\!',
        'spam_handler':r'(?is).*розыгрыш.*|.*подписка на каналы.*',
        'card_handler':rf'(?s)(?=.*@{me})(?=.*Вам выпал телефон!)',
        'cardt_handler':rf'(?s)(?=.*@{me})(?=.*Вы сможете выбить карту еще раз через)',
        'daily_handler':rf'(?s)(?=.*@{me})(?=.*Ежедневные награды:)',
        'dailyt_handler':rf'(?s)(?=.*@{me})(?=.*Новая награда будет доступна завтра)'
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
    **dict.fromkeys(['п', 'p'], '/pay'),
    **dict.fromkeys(['ев', 'ev'], '/event'),
    **dict.fromkeys(['тр', 'tr'], '/trade'),
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
        'п|p   — /pay\n'+
        'ев|ev — /event\n'+
        'тр|tr — /trade\n'+
        'км|h  — This text\n```')
}