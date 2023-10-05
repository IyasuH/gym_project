import os
from dotenv import load_dotenv
import time
import datetime

import logging

from typing import Optional
from fastapi import FastAPI
import telegram
from pydantic import BaseModel
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Updater, Filters, Dispatcher, CallbackContext
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
    admins_db_ids = []
    for admin in admins:
        admins_db_ids.append(admin["admin_id"])
    return admins_db_ids

admins_id_list = load_admin()

def load_waiting():
    waiting_list = waiting_db.fetch({"approved":False}).items
    waiting_db_ids = []
    for waiting in waiting_list:
        waiting_db_ids.append(waiting["user_id"])
    return waiting_db_ids

waiting_id_list = load_waiting()

def load_user():
    users = user_db.fetch().items
    users_db_ids =[]
    for user in users:
        users_db_ids.append(user["user_id"])
    return users_db_ids

user_id_list = load_user()

todayNow = datetime.datetime.now()

gym_users = []

START_MSG = """ Hello 
    Welcome to the <b>GYM </b>
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

def start(update, context):
    """When start button touched
    
    Keyword arguments:
    update --
    context -- 
    Return: 
    """
    user = update.effective_user or update.effectuve_chat

    update.message.reply_html(text=START_MSG)

def record_user_data(update, context):
    """
    here the key for the row will be the telegram_id
    to record personal data for saved users(users that are already in the database)
    so basically the process is updating not inserting into database
    """
    # so first let check wheter user is the database or ont
    effective_user = update.effective_user
    if effective_user.id not in gym_users:
        """
        user is not actually gym user
        """
        update.message.reply_html(text="I don't think you are a user")
        return
    gym_user = effective_user
    info_raw = str(context.args[0:])
    # first to check the output let's print it
    print(info_raw)
    info_ = info_raw.split(",")

    info_full_name =  info_[0].replace("[", '').replace("'", '')
    info_age = info_[1].replace("'", '')
    info_gender = info_[2].replace("'", '')
    info_height = info_[3].replace("'", '')
    info_weight = info_[4].replace("'", '')
    info_specific_goal = info_[5].replace("'",'')
    info_entry_date = info_[6].replace("]",'').replace("'",'')
    
    # assuming this data is already saved in the table
    gymUserName = getattr(gym_user, "user_name", '')
    gymFirstName = getattr(gym_user, "first_name", '')
    gymLastName = getattr(gym_user, "last_name", '')
    gymKey = getattr(gym_user, "key", '') # since 
    updatedAt = todayNow

    user_info_dict = {}
    user_info_dict["full_name"] = info_full_name
    user_info_dict["age"] = info_age
    user_info_dict["gender"] = info_gender
    user_info_dict["height"] = info_height
    user_info_dict["weight"] = info_weight
    user_info_dict["goal"] = info_specific_goal
    user_info_dict["entry_date"] = info_entry_date
    user_info_dict["updated_at"] = updatedAt
    user_info_dict["first_name"] = gymFirstName
    user_info_dict["last_name"] = gymLastName
    user_info_dict["username"] = gymUserName
    user_info_dict["telegram_id"] = gymKey # since i use telegram user_id is used as key for the row

    user_db.put(user_info_dict)
    update.message.reply_html("<b>User Info</b> is updated scuessfully")

def record_log(update, context):
    """
    to record exercise log for user
    """    
    effective_user = update.effective_user
    if effective_user.id not in gym_users:
        """
        user is not actually gym user
        """
        update.message.reply_html(text="I don't think you are a user")
        return
    gym_user = effective_user
    log_data = str(context.args[0:])

    logg_ = log_data.split(",")
    body_area = logg_[0].replace("[", '').replace(",",'')
    exercise_name = logg_[1].replace(",",'')
    equipment_used = logg_[2].replace(",",'') # 4kg dumbbell
    reps_number = logg_[3].replace(",", '') # 8 reps, or 2 minute
    tot_cycle = logg_[4].replace(",",'') # 3 times
    date_worked = logg_[5].replace(",",'') #

    user_id = logg_[6].replace(",",'') # here user_id should be

    logg_info_dict = {}
    logg_info_dict["body_area"] = body_area
    logg_info_dict["exercise_name"] = exercise_name
    logg_info_dict["equipment_used"] = equipment_used
    logg_info_dict["reps_number"] = reps_number
    logg_info_dict["tot_cycle"] = tot_cycle
    logg_info_dict["date_worked"] = date_worked

    logg_db.put(logg_info_dict)
    update.message.reply_html("<b>Logg is added</b>")


def see_waiting_list(update, context):
    """list out waiting list  """
    effective_user = update.effective_user
    print("The effective user id is: ", effective_user.id)
    print("The admins id list is: ", admins_id_list)
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    waiting_list = waiting_db.fetch({"approved":False}).items
    if waiting_list == []:
        update.message.reply_text("no one is in waiting list")
        return
    for waiting in waiting_list:
        update.message.reply_text("user_name: "+waiting["user_name"]+"\nuser_id: "+waiting["user_id"]+"\nfirst_name: "+waiting["first_name"]+"\nrequested at: "+waiting["requested_at"])


def is_approved():
    """to check single user id is approved or not"""

def aprove_user(update, context):
    """to give aproval to users"""
    effective_user = update.effective_user
    print("The effective user id is: ", effective_user.id)
    print("The admins id list is: ", admins_id_list)
    if str(effective_user.id) not in admins_id_list:
        update.message.reply_text(text="I don't get it")
        return
    user_id = str(context.args[0:]).split(",")[0].replace("[",'').replace("'", '')
    print("user id: ", user_id)
    # if user_id is not in waiting db or if user_id is already in user_db i have to check 
    # if user_id in 
    if str(user_id) not in waiting_id_list or str(user_id) in user_id_list:
        update.message.reply_text(text="user id not found in waiting list or it is already in user db")
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

    update.message.reply_text(text="user id {} of user name {} is added to user db successfully.".format(user_id, user_name))


def register_fun_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('aprove_user', aprove_user))
    dispatcher.add_handler(CommandHandler('see_waiting_list', see_waiting_list))

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