import os
import aiogram
import asyncio
from aiogram.types import Message
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ParseMode, ChatActions
import aioschedule
import openai
from datetime import datetime,timedelta,timezone
import json
from pydub import  AudioSegment
from datetime import datetime
from aiogram import executor
import requests
import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(message)s',
    filename='admin.log'
)

global api_params, available_plans_message

# process_flag = Flase

user_data = {}
payments_data ={}

pro_users_data = {'pro_user_data':{}}
pro_users_data['pro_user_data']['premium_users'] = []
pro_users_data['pro_user_data']['admins_list'] = [5363402037,1157489909,1964422280]
pro_users_data['pro_user_data']['banned_user'] = []
temp_user_id = ""

api_params = {
    "api_params":{
    "chat_history": 10,
    "system_prompt": "",
    "user_prompt": "",
    "default_params": {"message": [
        {"role": "system", "content": ""},
        {"role": "user", "content": ""}
    ],
        "temperature": 0.5,
        "max_tokens": 1024,
        "top_p": 1,
    },
    "openai_apikey" : [],
    "welcome_message":"Hello Welcome to the bot",
    "image_message":"Hi honey, let's make your dreams come true, I want you to describe me how you would like me to be. Choose real girl or anime first, then what kind of body type you want me to have, including hair, face, tits, ass.... Then tell me what kind of clothes you want me to wear and where you want me to be (beach, pool, couch...) Let your imagination fly my dear!",
    "sch_message":"This is scheduled message",
    "free_token_expiration":"I have to admit, I'm having a blast chatting with you! And if you want to continue our conversation and receive a custom avatar photo, subscribing to our full version is the way to go. Don't keep me waiting!Honey"
    }
}


cred = credentials.Certificate('firebase_auth.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


API_TOKEN = "5953972947:AAFQln7T6uGPh4OXcgObHZiTrCILRMp4TpA"


bot = aiogram.Bot(API_TOKEN)
dp = aiogram.Dispatcher(bot)


# Buttons
chat_history_button = InlineKeyboardButton(
    text="Chat History Limit", callback_data="chat_history_limit")
system_content_button = InlineKeyboardButton(
    text="System Prompt", callback_data="system_prompt")
user_content_button = InlineKeyboardButton(
    text="User Prompt", callback_data="user_prompt")
temperature_button = InlineKeyboardButton(
    text="Temperature", callback_data="temperature")
max_tokens_button = InlineKeyboardButton(
    text="Max Token", callback_data="max_token")
top_p_button = InlineKeyboardButton(text="TOP P", callback_data="top_p")
change_api_key_button = InlineKeyboardButton(text="Change OpenAI API",callback_data="openai_api")
back_from_setconfig_button = InlineKeyboardButton(
    text="⬅ Back", callback_data="back_from_setconfig")
set_config_keyboard = InlineKeyboardMarkup(row_width=2).add(system_content_button,
                                                            user_content_button, temperature_button, max_tokens_button, top_p_button,change_api_key_button, chat_history_button, back_from_setconfig_button)

cancel_button = InlineKeyboardButton(
    text="Cancel", callback_data="cancel_edit")
cancel_keyboard = InlineKeyboardMarkup().add(cancel_button)

welcome_message_button = InlineKeyboardButton(text="Welcome Message", callback_data="welcome_message")
image_message = InlineKeyboardButton(text="Image Message",callback_data="image_message")
schedule_message_button =  InlineKeyboardButton(text="Scheduled Message",callback_data="sch_msg")
free_token_expiry_button = InlineKeyboardButton(text="Free Trial Expiry Message",callback_data="free_trial_expiry")
back_from_message_button= InlineKeyboardButton(text="⬅ Back",callback_data="back_action")
messages_keyboard = InlineKeyboardMarkup(row_width=2).add(welcome_message_button,image_message,schedule_message_button,free_token_expiry_button,back_from_message_button)

cancel_edit_message_button = InlineKeyboardButton(text="Cancel",callback_data="cancel_action")
cancel_msg_keyboard = InlineKeyboardMarkup().add(cancel_edit_message_button)

cancel_image_prompt_button =  InlineKeyboardButton(text="Cancel",callback_data="cancel_image_prompt")
cancel_image_prompt_keyboard = InlineKeyboardMarkup().add(cancel_image_prompt_button)


# Start command
@dp.message_handler(commands=['start'])
async def start_message(message: Message):
    if message.chat.type == "private":
        if not str(message.chat.id) in pro_users_data["pro_user_data"]['banned_user']:
            if not str(message.chat.id) in user_data :
                user_data[str(message.chat.id)] = {}
                user_data[str(message.chat.id)]['user_type'] = 'free'
                user_data[str(message.chat.id)]['free_prompts'] = 10
                user_data[str(message.chat.id)]['state'] = 'chat_state'
                user_data[str(message.chat.id)
                        ]['username'] = f'@{message.from_user.username}'
                user_data[str(message.chat.id)
                        ]['name'] = message.from_user.first_name
                user_data[str(message.chat.id)]['dialog_history'] = []
                user_data[str(message.chat.id)]['image_prompts'] = 0
                user_data[str(message.chat.id)]['subscription_details']={"plan":"","expiration_time":""}
            await message.reply(text=api_params['api_params']["welcome_message"])
        else:
            await message.reply("You are banned from using this bot.Please contact the admin")


# Add Pro user
@dp.message_handler(commands=['addpro'])
async def addpro(message: Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            prouser_username = message.text
            split_values = prouser_username.split()
            split_values.pop(0)
            if len(split_values) > 0:
                for value in split_values:
                    if not value in pro_users_data['pro_user_data']['premium_users']:
                        pro_users_data['pro_user_data']['premium_users'].append(value)
                    for k, v in user_data.items():
                        if v['username'] == value:
                            user_data[k]['user_type'] = "premium"
                await message.reply("Users added successfully in pro users")
            else:
                await message.reply("Please enter the command in valid format '/addpro @username1 @username2'")
        else:
            await message.reply("You are not authorized to perform this action.")
    await hourly_backup()

# Remove Pro user
@dp.message_handler(commands=['removepro'])
async def removepro(message: Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            prouser_username = message.text
            split_values = prouser_username.split()
            split_values.pop(0)
            if len(split_values) > 0:
                for value in split_values:
                    if value in pro_users_data['pro_user_data']['premium_users']:
                        pro_users_data['pro_user_data']["premium_users"].remove(value)
                    for k, v in user_data.items():
                        if v['username'] == value:
                            user_data[k]['user_type'] = 'free'
                await message.reply("Users removed from premium subscription.")
            else:
                await message.reply("Please enter a command in a valid format /removepro @username1 @username1 @username2")
        else:
            await message.reply("You are not authorized to perform this action.")
    await hourly_backup()

# Image prompt command
@dp.message_handler(commands=['image'])
async def image_prompt(message:Message):
    if user_data[str(message.chat.id)]['user_type'] == "premium" or message.chat.id in pro_users_data['pro_user_data']['admins_list']:
        if user_data[str(message.chat.id)]['image_prompts'] >0:
            await message.reply(text=f"{api_params['api_params']['image_message']}",reply_markup=cancel_image_prompt_keyboard)
            user_data[str(message.chat.id)]['state'] ="waiting_for_image_prompt" 
        else:
            await message.reply("You have 0 image prompts remaining.Please topup using /subscribe.")
    else:
        await message.reply("OOPS! Subscribe to full version to access the /image prompt")

# Display all users
@dp.message_handler(commands=['showusers'])
async def show_users(message: Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            user_list = "List of bot users.\n"
            for key in user_data:
                user_list += f'{user_data[key]["name"]} || <i>{user_data[key]["username"]}</i> || <code>{key}</code>\n'
            await message.answer(text=user_list, parse_mode=ParseMode.HTML)
        else:
            await message.answer(text="You are not authorized to perform this action.")

# Ban user
@dp.message_handler(commands=['ban'])
async def ban_user(message:Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            if not message.get_args().strip() == "":
                try:
                    user_to_ban = str(message.get_args())
                    pro_users_data['pro_user_data']['banned_user'].append(user_to_ban)
                    if user_to_ban in user_data:
                        del user_data[user_to_ban]
                    await message.reply("User banned successfully")
                except Exception as e:
                    logging.error(f"Error in banning user : {e}")  
            else:
                await message.reply("Please enter a valid user id followed by the command <code>/ban</code>",parse_mode=ParseMode.HTML)
        else:
            await message.answer(text="You are not authorized to perform this action.")
    await hourly_backup()

# Unban user
@dp.message_handler(commands=['unban'])
async def unban_user(message:Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            if not message.get_args().strip() == "":
                try:
                    user_to_unban = str(message.get_args())
                    pro_users_data['pro_user_data']['banned_user'].remove(user_to_unban)
                except Exception as e:

                    logging.error(f"Error in unbanning user : {e}")

            
                await message.reply("User unbanned successfully.")
            else:
                await message.reply("Please enter a valid user id followed by the command <code>/ban</code>",parse_mode=ParseMode.HTML)
        else:
            await message.answer(text="You are not authorized to perform this action.")
    await hourly_backup()

# Display list of pro users
@dp.message_handler(commands=['showprousers'])
async def show_pro_users(message:Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            pro_user_list_message = f"List of pro users \n\n"
            for userid in user_data:
                if user_data[userid]['user_type'] == 'premium':
                    pro_user_list_message += f'Username : {user_data[userid]["username"]} || Name : {user_data[userid]["name"]} || UserID : <code>{userid}</code>\n'
            await message.answer(text=pro_user_list_message,parse_mode=ParseMode.HTML)
        else:
            await message.answer(text="You are not authorized to perform this action.")

# Reset chat history
@dp.message_handler(commands=['reset'])
async def reset_history(message: Message):
    if message.chat.type == "private":
        try:
            user_data[str(message.chat.id)]['dialog_history'] = []
            await message.reply("Chat History cleared successfully.")
        except Exception as e:

            logging.error(f"Error in resetting the chat history. User : {message.chat.id} || Username :{user_data[str(message.chat.id)]['username']}. Error : {e}")

# Send message to user
@dp.message_handler(commands=['sendmsg'])
async def sendmsg(message: Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            global temp_user_id
            temp_user_id = message.get_args()
            if str(temp_user_id) in user_data:
                user_data[str(message.chat.id)
                          ]['state'] = "sending_message_to_user"
                m_text = f"You are sending the message to - Name : {user_data[str(temp_user_id)]['name']} || Username : {user_data[(temp_user_id)]['username']}\nPlease send the the image or message which you want to send."
                cancel_sending_button = InlineKeyboardButton(
                    text="Cancel", callback_data="cancel_sending")
                cancel_sending_keyboard = InlineKeyboardMarkup().add(cancel_sending_button)
                await message.answer(text=m_text, reply_markup=cancel_sending_keyboard)
            else:
                await message.answer(text="Invalid user id. Please make sure user has started the bot")
                user_data[str(message.chat.id)]['state'] = "chat_state"
        else:
            await message.answer(text="You are not authorized to perform this action.")

# API Configuration Keyboard 
@dp.message_handler(commands=['setconfig'])
async def set_config(message: Message):
    if message.chat.type == "private":
        set_config_message = f"Please select the parameter which you want to change"
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            await message.reply(text=set_config_message, reply_markup=set_config_keyboard)
        else:
            await message.reply("You are not authorized to perform this action.")

# Backup command
@dp.message_handler(commands=['backup'])
async def take_backup(message:Message):
    if message.chat.type == "private":
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
           await write_to_db(user_data,'user_data') 
           await write_to_db(api_params,'api_params')
           await write_to_db(pro_users_data,'pro_users_data')
           await message.reply("Data backed up successfully")

           logging.info("Data Backed UP Successfully.")

# Message Configuration Keyboard
@dp.message_handler(commands = ['setmsgs'])
async def set_messages(message:Message):
    if message.chat.type =="private":
        set_message = f"Please select the message which you want to change"
        if message.chat.id in pro_users_data['pro_user_data']['admins_list']:
            await message.reply(text=set_message, reply_markup=messages_keyboard)
        else:
            await message.reply("You are not authorized to perform this action.")


@dp.message_handler(commands=['subscribe'])
async def show_available_plans(message:Message):
    user_id = message.chat.id
    if message.chat.type == "private":
        # Plan IDs
        daily_plan_sub_id = "uyevgd_hg34rff_hdhs45_gdg45"
        weekly_plan_sub_id = "dfghjk_56dcdgh_sfdghcj_sfdgh"
        monthly_plan_sub_id = "fdghf78_sfgdhj_67vsdb_tsyd"
        yearly_plan_sub_id = "gsgdv_56sfsg_gydu_64gry"
        topup_sub_id = "tsgdgsd_fdgsh34_rwtyer"

        # Plan URLS
        daily_payment_url = f"https://lanabot3-volvo3321rdp1.b4a.run/payment?chat_id={user_id}&subs_id={daily_plan_sub_id}"
        weekly_payment_url = f"https://lanabot3-volvo3321rdp1.b4a.run/payment?chat_id={user_id}&subs_id={weekly_plan_sub_id}"
        monthly_payment_url = f"https://lanabot3-volvo3321rdp1.b4a.run/payment?chat_id={user_id}&subs_id={monthly_plan_sub_id}"
        yearly_payment_url = f"https://lanabot3-volvo3321rdp1.b4a.run/payment?chat_id={user_id}&subs_id={yearly_plan_sub_id}"
        topup_payment_url = f"https://lanabot3-volvo3321rdp1.b4a.run/payment?chat_id={user_id}&subs_id={topup_sub_id}"

        # Plan Buttons
        daily_plan_button = InlineKeyboardButton(text="Day - $5.00", url=daily_payment_url)
        weekly_plan_button = InlineKeyboardButton(text="Week - $10.00", url=weekly_payment_url)
        monthly_plan_button =  InlineKeyboardButton(text="Month - $30.00",url=monthly_payment_url)
        yearly_plan_button =  InlineKeyboardButton(text="Year - $250.00",url=yearly_payment_url)
        topup_button =  InlineKeyboardButton(text="Top UP - $10.00",url=topup_payment_url)
        plan_keyboard = InlineKeyboardMarkup(row_width=1).add(daily_plan_button,weekly_plan_button,monthly_plan_button,yearly_plan_button,topup_button)
        
        plan_message = f"Select the plan from below list.\n"
        if user_data[str(message.chat.id)]['subscription_details']['plan'] =="" and user_data[str(message.chat.id)]['subscription_details']['expiration_time'] =="":
            plan_message += "You currently do not have any plan now"
        else:
            if not user_data[str(message.chat.id)]['subscription_details']['plan'] =="":
                plan_message += f"You currently have {user_data[str(message.chat.id)]['subscription_details']['plan']} plan and it is expiring on {(user_data[str(message.chat.id)]['subscription_details']['expiration_time']).date()} "
        await message.reply(text=plan_message,reply_markup=plan_keyboard)
         

@dp.message_handler(commands=['checkstatus'])
async def check_payment_status(message:Message):
    userID =  str(message.chat.id)
    if message.chat.type =="private":
        if userID in user_data:
            await read_db(payments_data,'payments_data')
            if userID in payments_data:
                if not payments_data[userID]['subscription_details']['expiration_time'] == user_data[userID]['subscription_details']['expiration_time']:
                    subscription_details = payments_data[userID]['subscription_details']
                    img_prompts = payments_data[userID]['image_prompts']
                    user_data[userID]['image_prompts'] = user_data[userID]['image_prompts']+img_prompts
                    user_data[userID]['subscription_details'] = subscription_details
                    payments_data[userID]['image_prompts'] =0
                    if not subscription_details['plan'] == "":
                        user_data[userID]['user_type'] ='premium'
                    await write_to_db(user_data,"user_data")
                    await write_to_db(payments_data,'payments_data')
                    await message.reply("Subscription Updated successfully.")
                if not payments_data[userID]['image_prompts'] ==0:
                    img_prompts = payments_data[userID]['image_prompts']
                    user_data[userID]['image_prompts'] = user_data[userID]['image_prompts']+img_prompts
                    payments_data[userID]['image_prompts'] =0
                    await write_to_db(user_data,"user_data")
                    await write_to_db(payments_data,'payments_data')



# Handling Callback Queries
@dp.callback_query_handler()
async def query_handler(call: CallbackQuery):
    global api_params
    user_id = str(call.message.chat.id)

    if call.data == "chat_history_limit":
        user_data[user_id]['state'] = "waiting_for_chat_history"
        res_message = f"Current Chat History : {api_params['api_params']['chat_history']}.\n\nEnter the number which you want to set for chat history. Which you want to set"
        await call.message.answer(text=res_message, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "system_prompt":
        user_data[user_id]['state'] = "waiting_for_system_prompt"
        res_message = f"Current System prompt : {api_params['api_params']['system_prompt']}.\n\nPlease send the new System Prompt. "
        await call.message.answer(text=res_message, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "user_prompt":
        user_data[user_id]['state'] = "waiting_for_user_prompt"
        res_message = f"Current User prompt : {api_params['api_params']['user_prompt']}.\n\nPlease send the new User Prompt."
        await call.message.answer(text=res_message, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "temperature":
        user_data[user_id]['state'] = "waiting_for_temperature"
        res_message = f"Current Temperature : {api_params['api_params']['default_params']['temperature']}.\n\nPlease send the Temperature. Default is <i>0.5</i>. It should be between 1 to 0.5"
        await call.message.answer(text=res_message, parse_mode=ParseMode.HTML, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "max_token":
        user_data[user_id]['state'] = "waiting_for_tokens"
        res_message = f"Current Max Token : {api_params['api_params']['default_params']['max_tokens']}.\n\nPlease send the Max Token you want to set. Default is <i>1024</i>."
        await call.message.answer(text=res_message, parse_mode=ParseMode.HTML, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "top_p":
        user_data[user_id]['state'] = "waiting_for_topp"
        res_message = f"Current Max Token : {api_params['api_params']['default_params']['top_p']}.\n\nPlease send the Top P. Default is <i>1</i>. It should be between 1 to 0.5"
        await call.message.answer(text=res_message, parse_mode=ParseMode.HTML, reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "openai_api":
        user_data[user_id]['state'] = "waiting_for_api_key"
        res_message = f"Current API key : <i>{api_params['api_params']['openai_apikey']}</i>\n\n Please send the new api key"
        await call.message.answer(text=res_message,parse_mode=ParseMode.HTML,reply_markup=cancel_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
      
    elif call.data == "welcome_message":
        user_data[user_id]['state'] = "waiting_for_welcome_message"
        res_message =  f"Current Welcome Message : <i>{api_params['api_params']['welcome_message']}.</i>\n\nPlease send the new Welcome message you want to set."
        await call.message.answer(text=res_message,parse_mode=ParseMode.HTML,reply_markup=cancel_msg_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    elif call.data == "image_message":
        user_data[user_id]['state'] = "waiting_for_image_message"
        res_message =  f"Current Image Message : <i>{api_params['api_params']['image_message']}.</i>\n\nPlease send the new Image message you want to set."
        await call.message.answer(text=res_message,parse_mode=ParseMode.HTML,reply_markup=cancel_msg_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "sch_msg":
        user_data[user_id]['state'] = "waiting_for_sch_message"
        res_message =  f"Current Scheduled Message : <i>{api_params['api_params']['sch_message']}.</i>\n\nPlease send the new Scheduled message you want to set."
        await call.message.answer(text=res_message,parse_mode=ParseMode.HTML,reply_markup=cancel_msg_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "free_trial_expiry":
        user_data[user_id]['state'] = "waiting_for_free_trial_message"
        res_message =  f"Current Free Trial Expiry Message : <i>{api_params['api_params']['free_token_expiration']}.</i>\n\nPlease send the new Free trial Expiry message you want to set."
        await call.message.answer(text=res_message,parse_mode=ParseMode.HTML,reply_markup=cancel_msg_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    elif call.data == "cancel_edit":
        user_data[user_id]["state"] = "chat_state"
        set_config_message = f"Please select the parameter which you want to change"
        await call.message.answer(text=set_config_message, reply_markup=set_config_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    elif call.data == "cancel_action":
        user_data[user_id]["state"] = "chat_state"
        set_message = f"Please select the message which you want to change"
        await call.message.answer(text=set_message,reply_markup=messages_keyboard)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "cancel_image_prompt":
        user_data[user_id]["state"] = "chat_state"
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "cancel_sending":
        user_data[user_id]["state"] = "chat_state"
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "back_from_setconfig":
        user_data[user_id]["state"] = "chat_state"
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "back_action":
        user_data[user_id]['state'] = "chat_state"
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


# Handling messages without command
@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.DOCUMENT,types.ContentType.AUDIO,types.ContentType.VOICE])
async def handle_normal_message(message: Message):
    if message.chat.type == "private":
        global api_params, available_plans_message
        user_id = str(message.chat.id)
        if user_id in user_data:
            content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.DOCUMENT]
            if message.content_type in content_types:
                if user_data[user_id]['state'] == "waiting_for_chat_history":
                    try:
                        chat_history = int(message.text)
                        api_params['api_params']['chat_history'] = chat_history
                        await message.reply("Chat History Limit saved successfully", reply_markup=set_config_keyboard)
                        user_data[user_id]["state"] = "chat_state"
                    except Exception as e:
                        await message .reply("Please enter a valid number for chat history")
                elif user_data[user_id]['state'] == "waiting_for_system_prompt":
                    sys_prompt = message.text
                    api_params['api_params']['system_prompt'] = sys_prompt
                    await message.reply("System Prompt saved successfully", reply_markup=set_config_keyboard)
                    user_data[user_id]["state"] = "chat_state"
                elif user_data[user_id]['state'] == "waiting_for_user_prompt":
                    u_prompt = message.text
                    api_params['api_params']['user_prompt'] = u_prompt
                    await message.reply("User Prompt saved successfully", reply_markup=set_config_keyboard)
                    user_data[user_id]["state"] = "chat_state"
                elif user_data[user_id]['state'] == "waiting_for_temperature":
                    try:
                        temperature = float(message.text)
                        if not (temperature > 2.0 or temperature < 0):
                            api_params['api_params']['default_params']['temperature'] = temperature
                            await message.reply("Temperature saved successfully", reply_markup=set_config_keyboard)
                            user_data[user_id]["state"] = "chat_state"
                        else:
                            await message.answer("Please enter the temperature between 0 to 1")
                    except Exception as e:
                        await message.answer("Please send a valid number for Temperature")

                elif user_data[user_id]['state'] == "waiting_for_tokens":
                    try:
                        max_tokens = int(message.text)
                        api_params['api_params']['default_params']['max_tokens'] = max_tokens
                        await message.reply("Max Tokens saved successfully", reply_markup=set_config_keyboard)
                        user_data[user_id]["state"] = "chat_state"
                    except Exception as e:
                        await message.answer("Please send a valid number for Max tokens")

                elif user_data[user_id]['state'] == "waiting_for_topp":
                    try:
                        topp = float(message.text)
                        if not (topp > 1.0 or topp < 0):
                            api_params['api_params']['default_params']['top_p'] = topp
                            await message.reply("Top_P saved successfully", reply_markup=set_config_keyboard)
                            user_data[user_id]["state"] = "chat_state"
                        else:
                            await message.answer("Please enter the Top P between 0 to 1")
                    except Exception as e:
                        await message.answer("Please send a valid number for Top P")
                elif user_data[user_id]['state'] == "waiting_for_api_key":
                    try:
                        api_key =  message.text
                        if not api_key =="":
                            api_params['api_params']["openai_apikey"] = api_key
                            await message.reply("API key saved successfully",reply_markup=set_config_keyboard)
                            user_data[user_id]['state'] = "chat_state"
                    except Exception as e:
                        await message.answer("Something went wrong.Please try again.")

                elif user_data[user_id]['state'] =="waiting_for_welcome_message":
                    try:
                        welcome_message =  message.text
                        if not welcome_message == "":
                            api_params['api_params']["welcome_message"] = welcome_message
                            await message.reply("Welcome message saved successfully.",reply_markup=messages_keyboard)
                            user_data[user_id]['state'] = "chat_state"
                    except Exception as e:
                        await message.answer("Something went wrong.Please try again.")

                elif user_data[user_id]['state'] =="waiting_for_image_message":
                    try:
                        image_message =  message.text
                        if not image_message == "":
                            api_params['api_params']["image_message"] = image_message
                            await message.reply("Image message saved successfully.",reply_markup=messages_keyboard)
                            user_data[user_id]['state'] = "chat_state"
                    except Exception as e:
                        await message.answer("Something went wrong.Please try again.")

                elif user_data[user_id]['state'] =="waiting_for_sch_message":
                    try:
                        sch_message =  message.text
                        if not sch_message == "":
                            api_params['api_params']["sch_message"] = sch_message
                            await message.reply("Scheduled message saved successfully.",reply_markup=messages_keyboard)
                            user_data[user_id]['state'] = "chat_state"
                    except Exception as e:
                        await message.answer("Something went wrong.Please try again.")

                elif user_data[user_id]['state'] =="waiting_for_image_prompt":
                    img_prompt =  message.text
                    if not img_prompt =="":
                        message_to_send = f"New Image prompt received from the user.\n\nUser ID : <code>{message.chat.id}</code>\nUsername : {message.from_user.username}\nName: {message.from_user.first_name} \nUser's Image prompt : <code>{img_prompt}</code>"
                        await bot.send_message(chat_id=-805894773,text=message_to_send,parse_mode=ParseMode.HTML)
                        user_data[user_id]["state"] = "chat_state"

                elif user_data[user_id]['state'] =="waiting_for_free_trial_message":
                    try:
                        free_trial_message =  message.text
                        if not free_trial_message == "":
                            api_params['api_params']['free_token_expiration'] = free_trial_message
                            await message.reply("Free trial expiration message saved successfully.",reply_markup=messages_keyboard)
                            user_data[user_id]['state'] = "chat_state"
                    except Exception as e:
                        await message.answer("Something went wrong.Please try again.")

                elif user_data[user_id]['state'] == "sending_message_to_user":
                    global temp_user_id
                    try:
                        if message:
                            await bot.copy_message(chat_id=temp_user_id, from_chat_id=message.chat.id, message_id=message.message_id)
                            if message.content_type == types.ContentType.PHOTO:
                                await bot.send_message(chat_id=temp_user_id,text="Are you happy with what you see honey?If not then send a new avatar prompt.")
                            await message.answer("Message sent successfully to user.If you want to send another message use <code>/sendmsg</code>", parse_mode=ParseMode.HTML)
                            user_data[str(temp_user_id)]['image_prompts'] = user_data[user_id]['image_prompts']-1
                            user_data[user_id]["state"] = "chat_state"
                            temp_user_id = ""
                    except Exception as e:
                        await message.reply("Something went wrong. Please try again using command <i>/sendmsg</i>", parse_mode=ParseMode.HTML)

                        logging.error(f"Error sending message to user: {e}")


                # Normal chat handled
                elif user_data[user_id]['state'] == "chat_state":
                    if not str(message.chat.id) in pro_users_data["pro_user_data"]['banned_user']:

                        if user_data[str(message.chat.id)]['user_type'] == "premium" or message.chat.id in pro_users_data['pro_user_data']["admins_list"]:
                            random_index = await get_random_index(api_params['api_params']['openai_apikey'])
                            random_api = api_params['api_params']['openai_apikey'][random_index]
                            openai.api_key = random_api
                            prompt_message = message.text

                            dialog_msgs = user_data[str(
                                message.chat.id)]['dialog_history']
                            f_messages = await generate_prompt(prompt_message, dialog_msgs)
                            temp = api_params['api_params']['default_params']['temperature']
                            max_token = api_params['api_params']['default_params']['max_tokens']
                            topp = api_params['api_params']['default_params']['top_p']
                            await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
                            try:
                                response = openai.ChatCompletion.create(
                                    model="gpt-3.5-turbo",
                                    messages=f_messages,
                                    temperature=temp,
                                    max_tokens=max_token,
                                    top_p=topp,
                                    frequency_penalty=0.0,
                                    presence_penalty=0.0
                                )
                                response_text = response['choices'][0]['message']['content']
                                temp_dict = {"user": prompt_message,
                                                "bot": response_text}
                                user_data[str(message.chat.id)
                                            ]['dialog_history'].append(temp_dict)

                                if len(user_data[str(message.chat.id)]['dialog_history']) > api_params['api_params']['chat_history']:
                                    (user_data[str(message.chat.id)]
                                        ['dialog_history']).pop(0)
                            except Exception as e:
                                response_text = "Something went wrong. Please try again."

                                logging.error(f"Error in OpenAI API: {e}")

                            await message.reply(text=response_text)
                        
                        elif user_data[str(message.chat.id)]['user_type'] == "free" and user_data[str(message.chat.id)]['free_prompts'] > 0:
                            random_index = await get_random_index(api_params['api_params']['openai_apikey'])
                            random_api = api_params['api_params']['openai_apikey'][random_index]
                            openai.api_key = random_api
                            prompt_message = message.text
                            dialog_msgs = user_data[str(
                                message.chat.id)]['dialog_history']
                            f_messages = await generate_prompt(prompt_message, dialog_msgs)

                            temp = api_params['api_params']['default_params']['temperature']
                            max_token = api_params['api_params']['default_params']['max_tokens']
                            topp = api_params['api_params']['default_params']['top_p']
                            await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
                            try:
                                response = openai.ChatCompletion.create(
                                    model="gpt-3.5-turbo",
                                    messages=f_messages,
                                    temperature=temp,
                                    max_tokens=max_token,
                                    top_p=topp,
                                    frequency_penalty=0.0,
                                    presence_penalty=0.0
                                )
                                response_text = response['choices'][0]['message']['content']
                                temp_dict = {"user": prompt_message,
                                                "bot": response_text}
                                user_data[str(message.chat.id)
                                            ]['dialog_history'].append(temp_dict)
                                if len(user_data[str(message.chat.id)]['dialog_history']) > api_params['api_params']['chat_history']:
                                    (user_data[str(message.chat.id)]
                                        ['dialog_history']).pop(0)

                                user_data[str(message.chat.id)]['free_prompts'] = user_data[str(
                                    message.chat.id)]['free_prompts'] - 1
                            except Exception as e:
                                response_text = "Something went wrong. Please try again."

                                logging.error(f"Error in OpenAI API: {e}")

                            await message.reply(text=response_text)
                        else:
                            no_free_credit_left_message = f"{api_params['api_params']['free_token_expiration']}"
                            await message.answer(text=no_free_credit_left_message)
            elif message.content_type == types.ContentType.VOICE:
                if user_data[str(message.chat.id)]['user_type'] == "premium" or message.chat.id in pro_users_data['pro_user_data']["admins_list"]:
                    # Dowmloading Audio file
                    audio= message.voice
                    timestamp= datetime.now().strftime('%H%M%S')
                    audio_file_name= f"{timestamp}_{str(message.chat.id)}.ogg"
                    audio_file_path= f'audios/{audio_file_name}'
                    await bot.download_file_by_id(audio.file_id,audio_file_path)

                    try:
                    # Converting OGG to MP3
                        ogg_file=AudioSegment.from_file(audio_file_path,format='ogg')
                        mp3_audio_file_name=f'{timestamp}_{str(message.chat.id)}.mp3'
                        mp3_file_path= f'audios/{mp3_audio_file_name}'
                        ogg_file.export(mp3_file_path,format='mp3')
                    except Exception as e:
                        logging.error(f"ogg to mp3 error : {e}")
                    try:
                        a_file = open(mp3_file_path,'rb') 
                        text =  await transcribe_audio(a_file)
                        a_file.close()
                    except Exception as e:
                        logging.error(f"OpenAI audio error : {e}")

                    prompt_message = text
                    dialog_msgs = user_data[str(
                        message.chat.id)]['dialog_history']
                    f_messages = await generate_prompt(prompt_message, dialog_msgs)
                    temp = api_params['api_params']['default_params']['temperature']
                    max_token = api_params['api_params']['default_params']['max_tokens']
                    topp = api_params['api_params']['default_params']['top_p']
                    await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=f_messages,
                            temperature=temp,
                            max_tokens=max_token,
                            top_p=topp,
                            frequency_penalty=0.0,
                            presence_penalty=0.0
                        )
                        response_text = response['choices'][0]['message']['content']
                        temp_dict = {"user": prompt_message,
                                        "bot": response_text}
                        user_data[str(message.chat.id)
                                    ]['dialog_history'].append(temp_dict)

                        if len(user_data[str(message.chat.id)]['dialog_history']) > api_params['api_params']['chat_history']:
                            (user_data[str(message.chat.id)]
                                ['dialog_history']).pop(0)
                    except Exception as e:
                        response_text = "Something went wrong. Please try again."

                        logging.error(f"Error in OpenAI API: {e}")

                    await message.reply(text=response_text)
                    if os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
                    if os.path.exists(mp3_file_path):
                        os.remove(mp3_file_path)
                else:
                    no_free_credit_left_message = f"{api_params['api_params']['free_token_expiration']}"
                    await message.answer(text=no_free_credit_left_message)

# Transcribe Audio

async def transcribe_audio(audio_data):
    random_index = await get_random_index(api_params['api_params']['openai_apikey'])
    random_api = api_params['api_params']['openai_apikey'][random_index]
    openai.api_key = random_api
    r =  await openai.Audio.atranscribe('whisper-1',audio_data)
    return r['text']

# Get Random Index
async def get_random_index(elem_list):
    random_indices = random.sample(range(len(elem_list)),len(elem_list))
    random_index =random_indices[0]
    return random_index

# Generating Prompt
async def generate_prompt(u_prompt, dialog_messages):
    system_content = api_params['api_params']['system_prompt']
    msgs = [{"role": "system", "content": f"{system_content}"}]
    if len(dialog_messages) > 0:
        for dialog_message in dialog_messages:
            msgs.append({"role": "user", "content": dialog_message['user']})
            msgs.append(
                {"role": "assistant", "content": dialog_message['bot']})

    msgs.append({"role": "user", "content": u_prompt})
    return msgs

# Hourly Backup
async def hourly_backup():
    try:
        await write_to_db(user_data,'user_data') 
        await write_to_db(api_params,'api_params')
        await write_to_db(pro_users_data,'pro_users_data')

        logging.info("Hourly backup successfully")
    except Exception as e:
        logging.error(f"Error in hourly backup : {e}")

# Scheduled Message sender
async def schedule_message():
    if not api_params['api_params']['sch_message'] =="":
        users = list(user_data.keys())
        for user in users:
            try:
                await bot.send_message(chat_id=user, text=api_params['api_params']['sch_message'])
            except Exception as e:
                logging.error(f"Sch Error : {e} ")
            
async def check_user_payments():
    await read_db(payments_data,'payments_data')
    for user in list(user_data.keys()):
        if user in payments_data:
            if not payments_data[user]['subscription_details']['expiration_time'] == user_data[user]['subscription_details']['expiration_time']:
                subscription_details =payments_data[user]['subscription_details']
                user_data[user]['subscription_details'] = subscription_details
                if not subscription_details['plan'] == "":
                    user_data[user]['user_type'] ='premium'

    for user in list(user_data.keys()):
        c_time= datetime.now()+timedelta(minutes=1)
        current_time = c_time.replace(tzinfo=timezone.utc)

        if user_data[user]['subscription_details']['expiration_time'] < current_time:
            user_data[user]['subscription_details']['plan'] = ""
            user_data[user]['subscription_details']['expiration_time'] = ""
            user_data[user]['user_type'] = 'free'
            payments_data[user]['subscription_details']['plan'] =""
            payments_data[user]['subscription_details']['expiration_time'] =""
        
    await write_to_db(payments_data,'payments_data')
    await write_to_db(user_data,'user_data')

# Check Recurring payments
async def payment_scheduler():
    aioschedule.every().day.at("11:00").do(check_user_payments)
    # while True:
    #     await aioschedule.run_pending()
    #     await asyncio.sleep(10)


# Daily Message Scheduler
async def scheduler():
    aioschedule.every().day.at("20:00").do(schedule_message)


# Hourly Backup
async def sch_backup():
    aioschedule.every().hour.do(hourly_backup)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(30)

# Webhook Hitter
async def webhook_hitter():
    webhook_url = "https://lanabot3-volvo3321rdp1.b4a.run/"
    while True:
        try:
            response = requests.get(webhook_url)
            if response.status_code ==200:
                print("Website is alive ")
            else:
                print("Website returned a non-200 status code:",response.status_code)
        except Exception as e:

            logging.error(f"Error in webhook: {e}")

        await asyncio.sleep(200)

# Read from Database
async def read_db(wDictonary,dict_name):
    data_ref = db.collection(dict_name)
    data_docs = data_ref.get()

    for doc in data_docs:
        wDictonary[doc.id] = doc.to_dict()

# Write to database
async def write_to_db(dictonary_name,dict_name):
    try:
        for key,value in dictonary_name.items():
            doc_ref = db.collection(dict_name).document(key)
            doc_ref.set(value)

    except Exception as e:
        logging.error(f"Error in writing data in DB: {e}")


async def main(_):
    await read_db(user_data,'user_data')
    await read_db(api_params,'api_params')
    await read_db(pro_users_data,'pro_users_data')
    print("Bot is up...")
    asyncio.create_task(scheduler())
    asyncio.create_task(webhook_hitter())
    asyncio.create_task(sch_backup())
    asyncio.create_task(payment_scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=main)
