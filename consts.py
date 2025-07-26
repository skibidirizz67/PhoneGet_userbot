

f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

log_path = 'phoneget_userbot.log'

target = '@phonegetcardsbot'

cmds = {'тк':'ТКарточка', 'та':'ТАкк', 'мо':'Мои телефоны', 'мт':'Магазин телефонов', 'му':'Магазин улучшений', 'ап':'Апгрейд',
'ен':'Ежедневная награда', 'са':'/sellall', 'тл':'Таблица лидеров', 'п':'/pay', 'ев':'/event', 'тр':'/trade',
'км':'тк - ТКарточка\nта - ТАкк\nмо - Мои телефоны\nмт - Магазин телефонов\nму - Магазин улучшений\nап - Апргрейд\nен - Ежедневаня награда\nса - /sellall\nтл - Таблица лидеров\nп - /pay\nев - /event\nтр - /trade\nкм - Этот текст'}

me = None
async def getme():
    global me
    me = 'dikiy_opezdal' # TODO: client.get_me()

patterns = {
    'card_handler':rf'(?s)(?=.*@{me})(?=.*Вам выпал телефон!)',
    'spam_handler':r'(?is).*розыгрыш.*|.*подписка на каналы.*',
    'cardt_handler':rf'(?s)(?=.*@{me})(?=.*Вы сможете выбить карту еще раз через)',
    'daily_handler':rf'(?s)(?=.*@{me})(?=.*Ежедневные награды:)',
    'dailyt_handler':rf'(?s)(?=.*@{me})(?=.*Новая награда будет доступна завтра)',
}