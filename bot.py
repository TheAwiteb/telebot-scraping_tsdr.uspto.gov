import os
import requests
from lxml import html
from bs4 import BeautifulSoup as bs4
import threading
import telebot
from telebot import types
from time import sleep
from random import choice
from string import hexdigits
import json


url = "https://tsdr.uspto.gov/#caseNumber={}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"
source_url = "https://tsdr.uspto.gov/statusview/sn{}"
img_url = "https://tsdr.uspto.gov/img/{}/large?"

source_headrs = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, br',
    'Accept-Language':'en-US,en;q=0.5',
    'Connection':'keep-alive',
    'Cookie':'HttpOnly; _ga=GA1.2.1665582176.1619137947; _gid=GA1.2.896113611.1619137947; _ga=GA1.3.1665582176.1619137947; _gid=GA1.3.896113611.1619137947',
    'Host':'tsdr.uspto.gov',
    'TE':'Trailers',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
}

img_headrs = {
'Host':'tsdr.uspto.gov',
'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv',
'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Accept-Language':'en-US,en;q=0.5',
'Accept-Encoding':'gzip, deflate, br',
'Connection':'keep-alive',
'Cookie':'HttpOnly; HttpOnly; _ga=GA1.2.1665582176.1619137947; _gid=GA1.2.896113611.1619137947; _ga=GA1.3.1665582176.1619137947; _gid=GA1.3.896113611.1619137947',
'Upgrade-Insecure-Requests':'1',
'Cache-Control':'max-age=0',
}

def get_page_source(caseNumber:int):
    r = requests.get(source_url.format(caseNumber), headers=source_headrs)
    if r.status_code == 200:
        pass
    else:
        return None
    return r.text

def get_img(caseNumber:int):
    r = requests.get(img_url.format(caseNumber), headers=img_headrs)
    return r.content

def get_data(caseNumber:int):
    source = get_page_source(caseNumber)
    if source:
        soup = bs4(source, 'lxml')
        tree = html.fromstring(source)
        data = f"https://tsdr.uspto.gov/#caseNumber={caseNumber}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch\n\n"
        dct = {
            'Mark': tree.xpath("/html/body/li/div[1]/div/div[2]/div/div[2]/text()"),
            'US Registration Number':tree.xpath("/html/body/li/div[1]/div/div[3]/div[2]/div[2]/text()"),
            'Mark Information/Mark Literal Elements':tree.xpath("/html/body/li/div[2]/div[2]/div/div/div/div[1]/div[2]/text()"),
            'Current Owner(s) Information/Owner Name':tree.xpath("/html/body/li/div[2]/div[6]/div/div/div[1]/div/div[2]/text()"),
            'Current Owner(s) Information/Owner Address':tree.xpath("/html/body/li/div[2]/div[6]/div/div/div[2]/div/div[2]/div[1]/text()")+\
                tree.xpath("/html/body/li/div[2]/div[6]/div/div/div[2]/div/div[2]/div[2]/text()"),
        }
        
        mark = soup.find('div', class_="value markText")
        try:
            registration_number = soup.find('div', class_="double table").find_all('div', class_="row")[1].find('div', class_='value')
        except Exception:
            registration_number = None
        mark_ekements = soup.find('div', class_="expand_wrapper default_hide").find('div', class_='row').find('div', class_='value')
        try:
            name = soup.find_all('div', class_="expand_wrapper default_hide")[3].find('div', class_="single table").find('div', class_="value")
        except Exception:
            name = None
        try:
            address = soup.find_all('div', class_="expand_wrapper default_hide")[3].find_all('div', class_="single table")[1].find('div', class_="value")
        except Exception:
            address = None
            
        bs4_dct = {
            'Mark': mark.text.strip() if mark != None else None,
            'US Registration Number': registration_number.text.strip() if registration_number != None else None,
            'Mark Information/Mark Literal Elements': mark_ekements.text.strip() if mark_ekements != None else None,
            'Current Owner(s) Information/Owner Name': name.text.strip() if name != None else None,
            'Current Owner(s) Information/Owner Address': address.text.strip() if address != None else None,
        }
        for key, val in dct.items():
            data+=f"{key}: {val[0].strip() if val != [] else bs4_dct.get(key,None)}\n\n"
        return data
    else:
        return None

def valid_serial(serial):
    return True if requests.get(img_url.format(serial)).status_code==200 else False

def make_action(chat_id, action, timeout):
    bot.send_chat_action(chat_id=chat_id, action=action, timeout=timeout)

def edit_json(new_json):
    with open("./db.json", 'w') as f:
        json.dump(new_json, f)

def make_json(token, dev_id):
    new_json = {"token":f"{token}","dev_id":dev_id,"users":[dev_id,],"urls":[]}
    with open("./db.json", 'w+') as f:
        json.dump(new_json, f)

def get_json_file():
    with open('./db.json', 'r') as f:
        return json.load(f)

def get_column(column):
    return get_json_file()[column]

def check(column, word):
    return word in list(get_column(column))

def add_to_json(column, val):
    data = get_json_file()
    if type(data[column]) == list:
        data[column].append(val)
    else:
        data[column] = val
    edit_json(data)

def delte_json(column, word):
    data = get_json_file()
    try:
        word = int(word)
    except Exception:
        pass
    try:
        idx = data[column].index(word)
        data[column].pop(idx)
    except Exception:
        pass
    edit_json(data)


if os.path.lexists(path="./db.json"):
    token = get_column("token")
    dev_id = get_column("dev_id")
else:
    token = input("you can get token from https://t.me/BotFather\nEnter bot token: ")
    dev_id = int(input("you can get id from https://t.me/userinfobot\nEnter dev id: "))
    make_json(token, dev_id)

bot = telebot.TeleBot(token)
bot_name = bot.get_me().first_name + ' ' +f"{bot.get_me().last_name if (bot.get_me().last_name != None) else ''}"
bot_username = bot.get_me().username
bot_url = "https://t.me/"+bot_username

def send_data(message,text=None, inline_mode=False):
    if inline_mode:
        pass
    else:
        chat_id = message.chat.id
        msg_id = message.id
        text = str(message.text).replace('/search', '').strip()
        threading.Thread(target=make_action,args=(chat_id, 'typing', 2)).start()
    if text.isnumeric():
        if valid_serial(text):
            data = get_data(text)
            img = get_img(text)
            if inline_mode:
                return data, img
            else:
                bot.send_photo(chat_id=chat_id, reply_to_message_id=msg_id,
                                photo=img, caption=data, reply_markup=
                                    types.InlineKeyboardMarkup().add(
                                        types.InlineKeyboardButton(text=bot_name, url=bot_url)
                                    ))
        else:
            if inline_mode:
                return "ال Serial Number غير صحيح", None
            else:
                bot.reply_to(message, f"{url.format(text)}\n\nال Serial Number غير صحيح",)
    else:
        if inline_mode:
            return "يمكنك البحث عبر ال *Serial Number* فقط ", None
        else:
            bot.reply_to(message, "يمكنك البحث عبر ال *Serial Number* فقط ", 
                        parse_mode="Markdown")

def make_url():
    return ''.join(choice(hexdigits) for i in range(22))

def back_button(markup):
    markup.add(types.InlineKeyboardButton(text="رجوع🔙", callback_data="_ back"))
    return markup

def edit_panel(chat_id, msg_id, func_markup):
    panel_name = func_markup.__name__ if str(func_markup.__class__) == "<class 'function'>" else func_markup
    switcher = {
        "home_panel":"اهلا بك في لوحة التحكم\nيمكنك من هنا حذف الاعضاء ومسح رابط الدعوة وانشاء رابط دعوة",
        "member_panel":"يمكنك من هنا حذف الاعضاء الذين يسخدمون البوت",
        "url_panel":"يمكنك من هنا انشاء رابط دعوة للبوت\nويمكنك حذف الروابط من هنا",
        }
    text = switcher.get(panel_name)
    bot.edit_message_text(text=text, chat_id=chat_id, message_id=msg_id,
                                    reply_markup=globals()[panel_name]()) #globals Return a dictionary representing the current global symbol table.


# panels
def home_panel():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text="انشاء رابط دعوة", callback_data="home make_url"),types.InlineKeyboardButton(
                text="حذف الاعضاء", callback_data="home delete_members")
    )
    return markup

def member_panel():
    members = get_column(column='users')
    members.pop(0)
    if len(members) > 0:
        markup = types.InlineKeyboardMarkup()
        for member in members:
            try:
                name = bot.get_chat(member).first_name
                markup.add(types.InlineKeyboardButton(
                    text=name, callback_data=f"members show {member}"),types.InlineKeyboardButton(
                        text='🗑️', callback_data=f"members delete {member}")
                        )
            except:
                delte_json('users', member)
        return back_button(markup)
    else:
        return None

def url_panel():
    urls = get_column('urls')
    markup = types.InlineKeyboardMarkup()
    for url in urls:
        markup.add(types.InlineKeyboardButton(
                text=url, callback_data=f"url show {url}"),types.InlineKeyboardButton(
                    text='🗑️', callback_data=f"url delete {url}")
                    )
    markup.add(types.InlineKeyboardButton(
                text="اضف رابط", callback_data=f"url add"))
    return back_button(markup)

@bot.message_handler(func=lambda msg: True, commands= ["start", 'help', 'search'])
def command_handler(message):
    chat_id = message.chat.id
    msg_id = message.id
    user_id = message.from_user.id
    text = str(message.text)
    privete_chat = True if bot.get_chat(chat_id).type == 'private' else False
    if text.startswith('/start'):
        if privete_chat:
            if user_id == int(dev_id):
                bot.reply_to(message, "اهلا بك في لوحة التحكم\nيمكنك من هنا حذف الاعضاء ومسح رابط الدعوة وانشاء رابط دعوة",
                                reply_markup=home_panel())
            else:
                if check('users', user_id):
                    bot.reply_to(message, f"اهلا بك في {bot_name}\nهنا يمكنك استخراج معلومات من موقع tsdr.uspto.gov\nلمعرفة طريقة الاستخدام ارسل /help")
                else:
                    if len(text.split()) == 2 and check('urls', text.replace('/start', '').strip()):
                        add_to_json('users', user_id)
                        command_handler(message)
                    else:
                        bot.reply_to(message, f'عذرا لايمكنك تشغيل البوت\nيمكنك طلب رابط دعوة من @{bot.get_chat(dev_id).username}')
        else:
            pass
    elif text.startswith('/help'):
        if check('users', user_id):
            bot.reply_to(message, "لاستخراج المعلومات ارسل السيريال نمبر\nاو\n/search <serial number>")
        else:
            pass
    elif text.startswith('/search'):
        if len(text.split()) == 2:
            send_data(message)
        else:
            bot.reply_to(message, 'يوجد خطاء بالسينتاكس')

@bot.message_handler(func=lambda msg: True, content_types= ["text"])
def message_handler(message):
    chat_id = message.chat.id
    privete_chat = True if bot.get_chat(chat_id).type == 'private' else False
    if privete_chat:
        send_data(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.id
    user_id = call.from_user.id
    callback = call.data.split()
    print(callback)
    interface = callback[0]
    button = callback[1]
    if button == "back":
        edit_panel(msg_id=msg_id, chat_id=chat_id, func_markup=home_panel)
    else:
        if interface == 'home':
            if button == "make_url":
                edit_panel(msg_id=msg_id, chat_id=chat_id, func_markup=url_panel)
            elif button == 'delete_members':
                markup = member_panel()
                if markup:
                    edit_panel(msg_id=msg_id, chat_id=chat_id, func_markup=member_panel)
                else:
                    bot.answer_callback_query(call.id, text="لايوجد اعضاء")
        elif interface == 'url':
            if button == 'add':
                urls = get_column('urls')
                url = make_url()
                while url == urls:
                    url = make_url()
                add_to_json('urls', url)
                edit_panel(chat_id=chat_id, msg_id=msg_id, func_markup=url_panel)
                bot.answer_callback_query(call.id, text="تم اضافة الرابط")
            elif button == 'delete':
                delte_json(column='urls', word=callback[2])
                edit_panel(chat_id=chat_id, msg_id=msg_id, func_markup=url_panel)
                bot.answer_callback_query(call.id, text="تم حذف الرابط")
            elif button == 'show':
                bot.send_message(chat_id=chat_id, text=f"https://t.me/{bot_username}?start="+callback[2])
                bot.answer_callback_query(call.id, text="تم ارسال الرابط")
        elif interface == "members":
            if button == 'show':
                bot.send_message(chat_id, f"[يمكنك الدخول على حسابه من هنا](tg://user?id={callback[2]})",
                                    parse_mode="Markdown", reply_to_message_id=msg_id)
                bot.answer_callback_query(call.id, text="تم ارسال حساب العضو")
            elif button == 'delete':
                delte_json(column='users', word=callback[2])
                users = get_column('users')
                len_users = len(users)
                if len_users != 1:
                    edit_panel(chat_id=chat_id, msg_id=msg_id, func_markup=member_panel)
                else:
                    bot.delete_message(chat_id, msg_id)
                bot.answer_callback_query(call.id, text="تم مسح العضو")


@bot.inline_handler(lambda query: True)
def query_video(inline_query):
    user_id = inline_query.from_user.id
    text = inline_query.query
    if check('users', user_id):
        data, img = send_data(text=text, message=None, inline_mode=True)
        if img:
            r = types.InlineQueryResultArticle('1', text, types.InputTextMessageContent(f"{url.format(text)}\n\nSerial Number: {text}\n{data}"),
                                                description="اضفط هنا لعرض  المعلومات",thumb_height=20, thumb_width=20,thumb_url=img_url.format(text))
            bot.answer_inline_query(inline_query.id, [r])
        else:
            if len(text) == 0:
                pass
            else:
                try:
                    r = types.InlineQueryResultArticle('1', "يوجد خطأ", types.InputTextMessageContent(f"{url.format(text) if text.isnumeric() else ''}\
                                                                        \n\nSerial Number: {text} \n Error:\n{data}",), description=data,thumb_height=20, thumb_width=20,
                                                            thumb_url="https://i.pinimg.com/originals/90/0b/c3/900bc32b424bc3b817ff1edd38476991.jpg")
                    bot.answer_inline_query(inline_query.id, [r])
                except Exception as e:
                    print(e)
    else:
        r = types.InlineQueryResultArticle('1', "ليس مصرح لك استعمال البوت", types.InputTextMessageContent("عذرا لايمكنك استعمال البوت\nيمكنك طلب الرابط من المالك"),
                                            description="يمكنك طلب رابط الدعوة من مالك البوت", thumb_height=20, thumb_width=20,
                                                thumb_url="https://i.pinimg.com/originals/90/0b/c3/900bc32b424bc3b817ff1edd38476991.jpg")
        bot.answer_inline_query(inline_query.id, [r])






# Run bot
while True:
    print(f"Start {bot_name}")
    try:
        bot.polling(none_stop=True, interval=0, timeout=0)
    except Exception as e:
        print(e)
        sleep(10)