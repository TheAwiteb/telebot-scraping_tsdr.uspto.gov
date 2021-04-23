import os
import requests
from lxml import html
from bs4 import BeautifulSoup as bs4
from time import sleep
import threading
import telebot
from telebot import types


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
    if r.status_code == 200:
        pass
    else:
        return None
    return r.content

def get_data(caseNumber:int):
    source = get_page_source(caseNumber)
    soup = bs4(source, 'lxml')
    if source:
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


def make_action(chat_id, action, timeout):
    bot.send_chat_action(chat_id=chat_id, action=action, timeout=timeout)



if os.path.lexists(path="./token.txt"):
    with open("./token.txt", 'r') as f:
        TOKEN = f.read()
else:
    TOKEN =  input("Enter bot token: ")
    with open("./token.txt", 'w+') as f:
        f.write(TOKEN)

bot = telebot.TeleBot(TOKEN)
bot_name = bot.get_me().first_name + ' ' +f"{bot.get_me().last_name if (bot.get_me().last_name != None) else ''}"
bot_username = bot.get_me().username
bot_url = "https://t.me/"+bot_username


@bot.message_handler(func=lambda msg: True, content_types= ["text"])
def message_handler(message):
    chat_id = message.chat.id
    msg_id = message.id
    text = str(message.text)
    threading.Thread(target=make_action,args=(chat_id, 'typing', 2)).start()
    if text.isnumeric():
        data = get_data(text)
        img = get_img(text)
        if data and img:
            bot.send_photo(chat_id=chat_id, reply_to_message_id=msg_id,
                            photo=img, caption=data, reply_markup=
                                types.InlineKeyboardMarkup().add(
                                    types.InlineKeyboardButton(text=bot_name, url=bot_url)
                                ))
        else:
            bot.reply_to(message, f"{url.format(text)}\n\nال Serial Number غير صحيح",)
    else:
        bot.reply_to(message, "يمكنك البحث عبر ال *Serial Number* فقط ", 
                        parse_mode="Markdown")
# Run bot
while True:
    print(f"Start {bot_name}")
    try:
        bot.polling(none_stop=True, interval=0, timeout=0)
    except Exception as e:
        print(e)
        sleep(10)