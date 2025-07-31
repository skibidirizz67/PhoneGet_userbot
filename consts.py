# TODO? move all customizable text to json
f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

log_path = 'phoneget_userbot.log'
log_format = '[%(asctime)s] [%(levelname)s]: %(message)s'

target = '@phonegetcardsbot'
target_id = 7808172033
chats = '@phonegetcardsbot'

tradelist = ['dikiy_opezdal', 'ladzepo_yikid']

patterns = {
    'txt_to_sec'     : r'(\d+)\s*(?:ч|м|с)',
    'cmd_handler'    : r'\!',
    'macro_handler'  : r'\.',
    'spam_handler'   : r'(?is).*розыгрыш.*|.*подписка на каналы.*',
    'card_handler'   : r'(?s)(?=.*Вам выпал телефон!)',
    'cardt_handler'  : r'(?s)(?=.*Вы сможете выбить карту еще раз через)',
    'daily_handler'  : r'(?s)(?=.*Ежедневные награды:)',
    'dailyt_handler' : r'(?s)(?=.*Новая награда будет доступна завтра)',
    'trade_handler'  : r'(?s)(?=.*Вам пришло предложение обмена)',
    'etrade_handler' : r'(?s)(?=.*ПОДТВЕРДИТЕ ОБМЕН)'
}
for u in tradelist: patterns['trade_handler'] = patterns['trade_handler']+rf'(?=.*{u})'

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