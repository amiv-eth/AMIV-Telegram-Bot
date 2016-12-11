#!/usr/bin/env python3

# python imports
import urllib
from requests import get
from datetime import datetime
from dateutil import tz
import time

# AMIV Bot imports
from AMIV_Bot_Token import TOKEN_AMIV_BOT

# constants
LOOPTIMEOUT = 5 # in seconds
URL_BOT = "https://api.telegram.org/bot{}/".format(TOKEN_AMIV_BOT)
URL_AMIV_EVENTS = "http://192.168.1.100/events?sort=-_time_start"


#
# Functions to Telegram API
#

def get_updates(offset=None):
    url = URL_BOT + "getUpdates?timeout=10"
    if offset:
        url += "&offset={}".format(offset)
    return get(url).json()


def get_last_update_id(updates):
    update_ids=[]
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL_BOT + "sendMessage?parse_mode=markdown&text={}&chat_id={}".format(text, chat_id)
    get(url)


#
# Event Formatter
#

def send_events_en(chat_id):
    # get all future events from AMIV API
    curutc = datetime.utcnow()
    searchstring = "where={\"time_advertising_start\":{\"$lte\":\"%s\"}, \"time_start\":{\"$gte\":\"%s\"}}" % (curutc.strftime("%Y-%m-%dT%H:%M:%SZ"), curutc.strftime("%Y-%m-%dT%H:%M:%SZ"))
    resp = get(URL_AMIV_EVENTS + "&" + searchstring).json()
    if not ("_items" in resp):
        print("Did not get _items in response. Abort.")
        return
    fevents = resp["_items"]

    # send no event message if no events here
    if not fevents:
        send_message("Could not find any future AMIV events. Check back soon :)", chat_id)
        return

    for fe in fevents:
        te = ""
        if "title_en" in fe:
            te += "*%s*\n" % fe["title_en"]
        else:
            send_message("We unfortunately dont have an english Title, so well just send you the german one", chat_id )
            te += "*%s*\n" % fe["title_ge"]
        if "time_start" in fe:
            dt = datetime.strptime(fe["time_start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz.tzutc())
            zuricht = dt.astimezone(tz.tzlocal())
            te += "_start: am %s um %s Uhr_\n" % (zuricht.strftime("%d.%m.%Y"), zuricht.strftime("%H:%M"))
        if "location" in fe:
            te += "_place: %s_\n" % fe["location"]
        if "price" in fe:
            te += "_price: %.2f CHF_\n" % (float(fe["price"])/100)
        if "description_en" in fe:
            te += fe["description_en"]
            te += "\n"
        else:
            send_message("We unfortunately dont have an english description, so well just send you the german one", chat_id)
            te += fe["description_de"]
            te += "\n"

        send_message(te, chat_id)


def send_events_de(chat_id):
    # get all future events from AMIV API
    curutc = datetime.utcnow()
    searchstring = "where={\"time_advertising_start\":{\"$lte\":\"%s\"}, \"time_start\":{\"$gte\":\"%s\"}}" % (curutc.strftime("%Y-%m-%dT%H:%M:%SZ"), curutc.strftime("%Y-%m-%dT%H:%M:%SZ"))
    resp = get(URL_AMIV_EVENTS + "&" + searchstring).json()
    if not ("_items" in resp):
        print("Did not get _items in response. Abort.")
        return
    fevents = resp["_items"]

    # send no event message if no events here
    if not fevents:
        send_message("Es gibt momentan keine zukünftigen Events. Frag uns doch später nochmal an :)", chat_id)
        return

    for fe in fevents:
        te = ""
        if "title_de" in fe:
            te += "*%s*\n" % fe["title_de"]
        else:
            send_message("Wir haben leider keinen deutschen Titel gefunden, wir werden dir den englischen schicken", chat_id)
            te += "*%s*\n" % fe["title_en"]
        if "time_start" in fe:
            dt = datetime.strptime(fe["time_start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz.tzutc())
            zuricht = dt.astimezone(tz.tzlocal())
            te += "_Start: am %s um %s Uhr_\n" % (zuricht.strftime("%d.%m.%Y"), zuricht.strftime("%H:%M"))
        if "location" in fe:
            te += "_Ort: %s_\n" % fe["location"]
        if "price" in fe:
            te += "_Preis: %.2f CHF_\n" % (float(fe["price"])/100)
        if "description_de" in fe:
            te += fe["description_de"]
            te += "\n"
        else:
            send_message("Wir haben leider keine deutsche Beschreibung gefunden, wir werden dir die englische schicken", chat_id)
            te += fe["description_en"]
            te += "\n"

        send_message(te, chat_id)

def help(chat_id):
    HELP_TEXT = """This is the first AMIV-Event-Bot. \nFor now, he can send you all the upcoming events in either english or german. \n
Therefore just write /event or /events and you'll get asked in what language you want the Events in. \n \n \n
or you could even write \'/events de\',   \'/events d\',\'/events en\', \'/events e\'...   """

    send_message(HELP_TEXT, chat_id)

def main():
    last_update_id = None
    firstTime = True

    while True:
        # pause the loop
        time.sleep(LOOPTIMEOUT)

        # read all new messages from Telegram bot
        updates=get_updates(last_update_id)
        if ("result" in updates) and (len(updates["result"]) > 0):
            last_update_id = get_last_update_id(updates)+1
        else:
            continue
        print(updates)

        # discard the first batch of valid updates to not spam users from old messages
        if firstTime:
            firstTime = False
            continue

        # for every new /event chat message, call send events
        for r in updates["result"]:
            print(r)
            msg = r["message"]["text"].lower()
            chat = r["message"]["chat"]["id"]
            if (msg == "/events") or (msg == "/event"):
                send_message("Do you wanna have /english or /german Events?", chat)
            elif msg in ["/english", "/events en", "/events e", "/event en", "/event e"]:
                send_events_en(chat)
            elif msg in ["/german", "/events de", "/events d", "/event de", "/event d"]:
                send_events_de(chat)
            elif (msg == "/help"):
                help(chat)
            else:
                send_message("Could not understand. Please write /events or /event.", chat)


if __name__ == '__main__':
    main()
