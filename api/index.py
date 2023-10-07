import os
from dotenv import load_dotenv
import datetime

import logging

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Update, Bot
from telegram.ext import CommandHandler, Updater,  Dispatcher
from deta import Deta

load_dotenv()

# TOKEN = os.environ.get("TELE_TOKEN")
TOKEN = os.getenv("TELE_TOKEN")

# using deta w/c means nosql
DETA_KEY = os.getenv("DETA_KEY")


logging.basicConfig(format="%(asctime)s - %(name)s - %(message)s", level=logging.INFO)

app = FastAPI()

deta = Deta(DETA_KEY)

user_db = deta.Base("User_DB") # detail user info()
logg_db = deta.Base("Log_DB") # exrecise logg
waiting_db = deta.Base("Waiting_DB") # waiting for approval list


def load_admin():
    """to load admins with their ids"""
    admin_db = deta.Base("Admin_DB")
    admins = admin_db.fetch().items
    admins_db_ids = [admin["admin_id"] for admin in admins]
    return admins_db_ids

admins_id_list = load_admin()

def load_waiting():
    waiting_list = waiting_db.fetch({"approved":False}).items
    waiting_db_ids = [waiting["user_id"] for waiting in waiting_list]
    return waiting_db_ids

waiting_id_list = load_waiting()

def load_user():
    users = user_db.fetch().items
    users_db_ids =[user["user_id"] for user in users]
    return users_db_ids

user_id_list = load_user()

todayNow = datetime.datetime.now()

START_MSG = """
Hi 👋 <a href="tg://user?id={user_id}">{name}</a>

Welcome to the <b>Dere Gym</b>

Use the <a href="http://t.me/deregymbot/gymup">WepApp</a> for full exprience

"""

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[dict]
    edited_message: Optional[dict]
    channel_post: Optional[dict]
    edited_channel_post: Optional[dict]
    inline_query: Optional[dict]
    chosen_inline_result: Optional[dict]
    callback_query: Optional[dict]
    shipping_query: Optional[dict]
    pre_checkout_querry: Optional[dict]
    poll: Optional[dict]
    poll_answer: Optional[dict]


def start(update):
    """
    When start button touched
    """
    user = update.effective_user or update.effectuve_chat
    first_name = getattr(user, "first_name", '')
    update.message.reply_html(text=START_MSG.format(name=first_name, user_id=user.id))


def see_waiting_list(update):
    """
    to list out waiting users lists
    """
    effective_user = update.effective_user
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    waiting_list = waiting_db.fetch({"approved":False}).items
    if waiting_list == []:
        update.message.reply_text("no one is in waiting list")
        return
    for waiting in waiting_list:
        update.message.reply_text(f"""user name: {waiting['user_name']}
                                  user id: {waiting['user_id']}
                                  first name: {waiting['first_name']}
                                  requested at: {waiting['requested_at']}""")
        # update.message.reply_text("user_name: "+waiting["user_name"]+"\nuser_id: "+waiting["user_id"]+"\nfirst_name: "+waiting["first_name"]+"\nrequested at: "+waiting["requested_at"])


def list_users(update):
    """
    to list all users with their basic info
    """
    effective_user = update.effective_user
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    all_users = user_db.fetch().items
    for user in all_users:
        update.message.reply_text(f"""user name: {user['user_name']}
                                  user id: {user['user_id']}
                                  first name: {user['first_name']}
                                  entry date: {user['entry_date']}""")
        # update.message.reply_text("user_name: "+user["user_name"]+"\nuser_id: "+user["user_id"]+"\nfirst_name: "+user["first_name"]+"\nentry_date: " +user["entry_date"])


def show_exe_log(update, context):
    """
    to show exercise log for single person
    """
    effective_user = update.effective_user
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    # this will load all the data 
    user_id = str(context.args[0:]).split(",")[0].replace("[",'').replace("'", '').replace("]", '')
    # the entire log for one perons
    logs = logg_db.fetch({"user_id":user_id}).items
    for log in logs:
        print("log: ", log)
        update.message.reply_text(f"""User id: {log['user_id']}
                                  Body Area: {log['body_area']}
                                  Date worked: {log['date_worked']}
                                  Equipment used: {log['equipment_used']}
                                  Exercise name: {log['exercise_name']}
                                  Duration: {log['exercise_duration']}
                                  Additional info: {log['additional_info']}
        """)
        # update.message.reply_text("User id: "+log["user_id"]+"\nBody Area: "+log['body_area']+"\nDate worked: "+log['date_worked']+"\nEquipment used: "+log['equipment_used']+"\nExercise name: "+log['exercise_name']+"\nDuration: "+log['exercise_duration']+"\nAdditional info: "+log['additional_info'])


def show_personal(update, context):
    """
    to show personal info detail about single person
    """
    effective_user = update.effective_user
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    user_id = str(context.args[0:]).split(",")[0].replace("[",'').replace("'", '').replace("]", '')
    user = user_db.fetch({"user_id":user_id}).items[0]
    update.message.reply_text(f"""
        User Name: " {user['user_name']}
        User Id: {user['user_id']}
        First Name: {user['first_name']}
        Entry Date: {user['entry_date']}
        Weight: {str(user['weight'])}
        Height: {str(user['height'])}
        Main goal: {user['main_goal']}
        DoB: {user['dob']}
        Fat percent: {str(user['fat_percent'])}
        Waist Circumference: {str(user['waist_circumference'])}
        Hip Circumference: {str(user['hip_circumference'])}
        Calf Circumference: {str(user['calf_circumference'])}
        Chest Width: {str(user['chest_width'])}
        Shoulder Width: {str(user['shoulder_width'])}
        Bicep Circumference: {str(user['bicep_circumference'])}
    """
    )
    # update.message.reply_text("User Name: "+user['user_name']+"\nUser Id: "+user['user_id']+"\nFirst Name: "+user['first_name']+"\nEntry Date: " +
    #                           user['entry_date']+"\nWeight: "+str(user['weight'])+"\nHeight: "+str(user['height'])+"\nMain goal: "+user['main_goal']+"\nDoB: "
    #                           +user['dob']+"\nFat percent: "+str(user['fat_percent'])+"\nWaist Circumference: "+str(user['waist_circumference'])+"\nHip Circumference: "
    #                           +str(user['hip_circumference'])+"\nCalf Circumference: "+str(user['calf_circumference'])+"\nChest Width: "+str(user['chest_width'])+
    #                           "\nShoulder Width: "+str(user['shoulder_width'])+"\nBicep Circumference: "+str(user['bicep_circumference']))

def show_change():
    """
    to see changes info about one person
    """

def aprove_user(update, context):
    """to give aproval to users"""
    effective_user = update.effective_user
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    user_id = str(context.args[0:]).split(",")[0].replace("[",'').replace("'", '').replace("]", '')
    print("user id: ", user_id)
    # if user_id is not in waiting db or if user_id is already in user_db i have to check 
    # if user_id in 
    if str(user_id) not in waiting_id_list or str(user_id) in user_id_list:
        update.message.reply_text(text="""
                user id not found in waiting list or it is already in user db
        """)
        return 
    waiting_user = waiting_db.fetch({"approved":False, "user_id": user_id}).items

    user_name = waiting_user["user_name"]
    first_name = waiting_user["first_name"]
    last_name = waiting_user["last_name"]

    user_info_dict = {}

    user_info_dict["full_name"] = ""
    user_info_dict["dob"] = ""
    user_info_dict["gender"]= ""
    user_info_dict["height"]= 0.0
    user_info_dict["weight"]= 0.0
    user_info_dict["main_goal"]=""
    user_info_dict["entry_date"]=""
    user_info_dict["created_at"]=datetime.date.today().strftime("%d/%m/%Y")
    user_info_dict["updated_at"]=datetime.date.today().strftime("%d/%m/%Y")
    user_info_dict["first_name"]=first_name
    user_info_dict["last_name"]=last_name
    user_info_dict["user_name"]=user_name
    user_info_dict["key"] =user_id
    user_info_dict["user_id"]=user_id

    user_info_dict["fat_percent"] = ""
    user_info_dict["waist_circumference"] = ""
    user_info_dict["hip_circumference"] = ""
    user_info_dict["calf_circumference"] = ""
    user_info_dict["chest_width"] = ""
    user_info_dict["shoulder_width"] = ""
    user_info_dict["bicep_circumference"] = ""

    user_db.put(user_info_dict)

    waiting_info_dict = {"approved":True}
    
    waiting_db.update(waiting_info_dict, user_id)

    update.message.reply_text(text=f"""
        user id {user_id} of user name {user_name} is added to user db successfully.
    """)


def register_fun_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('aprove_user', aprove_user))
    dispatcher.add_handler(CommandHandler('see_waiting_list', see_waiting_list))
    dispatcher.add_handler(CommandHandler('list_users', list_users))
    dispatcher.add_handler(CommandHandler('show_exe_log', show_exe_log))
    dispatcher.add_handler(CommandHandler('show_personal', show_personal))

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    register_fun_handlers(dispatcher)
    updater.start_polling()
    updater.idle()

@app.post("/webhook")
def webhook(Webhook_data: TelegramWebhook):
    bot = Bot(token=TOKEN)
    update = Update.de_json(Webhook_data.__dict__, bot)
    dispatcher = Dispatcher(bot, None, workers=4, use_context=True)
    register_fun_handlers(dispatcher)
    dispatcher.process_update(update)
    return {"status":"okay"}    

@app.get("/")
def index():
    return {"status":"okay"}