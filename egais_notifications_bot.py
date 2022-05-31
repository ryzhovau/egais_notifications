import pickle
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from natasha import (
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    AddrExtractor,

    Doc)

# pip install aiogram natasha

# Задайте токен бота и чат, в который бот будет добавлен. Остальные чаты он игнорит
API_TOKEN = 'xxxxx:yyyyyyyyyyyyyyyyyyyyyy'
our_chat = -zzzzzzzzzzzz

# Первоначальный список администраторов
admins = [xxxxxxx]

# Дальше простым смертным править нечего
commands_list = ['/add', '/del', '/start', '/list']

def get_settings():
    with open('keywords.pickle', 'rb') as f:
        return pickle.loads(f.read())

def set_settings(data):
    with open('keywords.pickle', 'wb') as f:
        f.write(pickle.dumps(data))
try:
    settings = get_settings()
except:
    settings = {'users': list(admins), 'admins': list(admins)}
    for i in admins:
        settings[i] = {'words': list(), 'users': list()}

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
addr_extractor = AddrExtractor(morph_vocab)

def process_message(text):
    try:
        doc = Doc(text)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        doc.parse_syntax(syntax_parser)
        doc.tag_ner(ner_tagger)
        cities = []
        for span in doc.spans:
            span.normalize(morph_vocab)
            if span.type == 'LOC':
                cities.append(span.normal.strip().lower())
        return cities
    except Exception as err:
        print(err)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(content_types = [ContentType.PHOTO, ContentType.DOCUMENT, ContentType.TEXT])
async def main(message: types.Message):

    text = message.text or message.caption
    if not text:
        return
    print('Message from', message.chat.id, ':', text, 'user:', message.from_user.id)

    from_id = message.from_user.id
    if (message.chat.id != our_chat and message.chat.id < 0) or (message.chat.id > 0 and message.from_user.id not in settings['users']):
        await message.answer("Для работы бота необходимо получить разрешение.")
        return

    com = text.strip()

    if from_id in settings['admins'] and com.split()[0] in ['/add_users', '/del_users', '/add_admins', '/del_admins', '/list_admins', '/list_users']:
        if com.split()[0] == '/list_admins':
            await message.answer(f"""Список администраторов: {', '.join([f"{i}" for i in settings['admins']])}.""")
        elif com.split()[0] == '/list_users':
            await message.answer(f"""Список пользователей: {', '.join([f"{i}" for i in settings['users']])}.""")
        else:
            users = list(map(int, com[com.find(' ')+1:].strip().lower().split()))
        if com.split()[0] == '/add_users':
            settings['users'] = list(set(settings['users'] + users))
            await message.answer(f"""Добавил в список пользователей: {', '.join([f"{i}" for i in users])}.""")
        elif com.split()[0] == '/del_users':
            settings['users'] = list(set(settings['users']) - set(users))
            await message.answer(f"""Убрал из списка пользователей: {', '.join([f"{i}" for i in users])}.""")
        elif com.split()[0] == '/add_admins':
            settings['admins'] = list(set(settings['admins'] + users))
            await message.answer(f"""Добавил в список администраторов: {', '.join([f"{i}" for i in users])}.""")
        elif com.split()[0] == '/del_admins':
            settings['admins'] = list(set(settings['admins']) - set(users))
            await message.answer(f"""Убрал из списка администраторов: {', '.join([f"{i}" for i in users])}.""")

        for i in settings['users']:
            if i not in settings:
                settings[i] = {'words': list(), 'users': list()}
        to_del = []
        for i in set(settings.keys()) - set(['users', 'admins']):
            if i not in settings['users']:
                to_del.append(i)
        for i in to_del:
            del settings[i]

        set_settings(settings)
        return

    if message.chat.id == our_chat:
        net_words = set(process_message(text))
        all_words = text.lower().strip()
        our_users = settings['users']
        for user in our_users:

            uwords = set(settings[user]['words'])
            send = False
            for i in uwords:
                if i in all_words or i in net_words:
                    send = True
            if from_id in [i['id'] for i in settings[user]['users']]:
                send = True
            if send:
                await message.forward(user)
        return

    if message.is_forward() and message.forward_from:
        name = ((message.forward_from['first_name'] if message.forward_from['first_name'] else "") + ' ' + (message.forward_from['last_name'] if message.forward_from['last_name'] else "")).strip()
        fid = message.forward_from['id']
        if fid in [i['id'] for i in settings[from_id]['users']]:
            for i in range(len(settings[from_id]['users'])):
                if settings[from_id]['users'][i]['id'] == fid:
                    del settings[from_id]['users'][i]
                    break
            await message.answer("Убрал пользователя из списка отслеживаемых.")
        else:
            settings[from_id]['users'].append({'name': name, 'id': fid})
            await message.answer("Добавил пользователя в список отслеживаемых.")
    elif not com or com.split()[0] not in commands_list:
        await message.answer("Для получения инструкции используйте команду /start.")
    elif com == '/start':
        await message.answer("Бот отслеживает сообщения по ключевым словам и выбранным пользователям в чате ЕГАИС инфо.\n\nДля добавления слов воспользуйтесь командой:\n/add ключевые_слова_через_пробел\nДля удаления слов используйте:\n/del ключевые_слова_через_пробел\nЧтобы увидеть перечень отслеживаемых слов и пользователей, воспользуйтесь командой /list.\n\nПерешлите сюда любое сообщение выбранного пользователя, чтобы добавить или убрать его из числа отслеживаемых.")
    elif com.split()[0] == '/del':
        if com == '/del': await message.answer("Введите слова, которые нужно удалить!")
        else:
            words = com[com.find(' ')+1:].strip().lower().split()
            settings[from_id]['words'] = list(set(settings[from_id]['words']) - set(words))
            await message.answer(f"""Удалил из списка слов: {', '.join([f"'{i}'" for i in words])}.""")
    elif com.split()[0] == '/add':
        if com == '/add': await message.answer("Введите слова, которые нужно добавить!")
        else:
            words = com[com.find(' ')+1:].strip().lower().split()
            settings[from_id]['words'] = list(set(settings[from_id]['words'] + words))
            await message.answer(f"""Добавил в список слов: {', '.join([f"'{i}'" for i in words])}.""")
    elif com.split()[0] == '/list':
        await message.answer(f"""Ваш список слов: {', '.join([f"{i}" for i in settings[from_id]['words']])}.
Ваш список пользователей: {', '.join([f"{j['name']} (ID: {j['id']})" for j in settings[from_id]['users']])}.""")
    else:
        await message.answer("Cтранная команда. Посмотрите справку в /start.")

    set_settings(settings)

executor.start_polling(dp, skip_updates=False)
