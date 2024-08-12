import requests
import random
import os
import sys
import logging
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from requests.exceptions import Timeout

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your bot's token
BOT_TOKEN = '7323066808:AAHWjz2Yjz2WR5n9xDU9k9sbnKAXh8qG89o'

# List of required channel links
REQUIRED_CHANNELS = [
    {'name': 'GODT00L', 'link': 'https://t.me/GODT00L'},
    {'name': 'CAREMETA', 'link': 'https://t.me/caremeta'},
    {'name': 'LUCITHECURSE', 'link': 'https://t.me/LUCITHECURSE'}
]

user_verified = {}

# List of user agents to rotate
# List of user agents to rotate
USER_AGENTS = [
    "Instagram 10.26.0 Android",
    "Instagram 20.12.0 iPhone",
    "Instagram 30.15.0 Windows",
    "Instagram 40.10.0 macOS",
    "Instagram 50.18.0 Android",
    "Instagram 60.21.0 iPhone",
    "Instagram 70.25.0 Windows",
    "Instagram 80.30.0 macOS",
    # new agents
    "Instagram 90.35.0 Android",    # New User Agent
    "Instagram 100.40.0 iPhone",    # New User Agent
    "Instagram 110.45.0 Windows",   # New User Agent
    "Instagram 120.50.0 macOS",     # New User Agent
    "Instagram 130.55.0 Android",   # New User Agent
    "Instagram 140.60.0 iPhone",    # New User Agent
    "Instagram 150.65.0 Windows",   # New User Agent
    "Instagram 160.70.0 macOS",     # New User Agent
    "Instagram 170.75.0 Android"    # New User Agent
    # Add more user agents as needed
]

# State for conversation handler
AWAITING_USERNAME = 1

# File paths
BANNED_USERS_FILE = "banned_users.txt"
AUTHORIZED_USERS_FILE = "admin.txt"

# Sets to store banned and authorized user IDs
banned_users = set()
authorized_users = set()

# Admin password
ADMIN_PASSWORD = 'lucifucks'

# Admin session flag
admin_logged_in = False

# File path to store user IDs
USER_IDS_FILE = "user_ids.txt"

def store_user_id(user_id: int):
    if not os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'a') as file:
            file.write(f"{user_id}\n")
    else:
        with open(USER_IDS_FILE, 'r') as file:
            existing_ids = file.read().splitlines()
        
        if str(user_id) not in existing_ids:
            with open(USER_IDS_FILE, 'a') as file:
                file.write(f"{user_id}\n")


# Function to send password reset code
def send_password_reset(username):
    url = "https://b.i.instagram.com/api/v1/accounts/send_password_reset/"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-CSRFToken": "YXvnZ43BVgH4y_ddhNTbFI",
        "Cookie": "csrftoken=YXvnZ43BVgH4y_ddhNTbFI",
    }
    data = {
        "username": username,
        "device_id": "android-cool-device"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Timeout:
        return {"status": "fail", "message": "Request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "fail", "message": 
             "Invalid Request.\n:XClient Error.\nPlease Try Again Later.\n\n[≭] Sᴜᴘᴘᴏʀᴛ & Uᴘᴅᴀᴛᴇs ~ @LuciTheCurse\n[≭]Wʜᴀᴛ Iꜱ Cʟɪᴇɴᴛ Eʀʀᴏʀ?\n::https://t.me/LuciTheCurse/16\n"}
    except ValueError:
        return {"status": "fail", "message": "Invalid response from Instagram. Please try again later."}

# Function to extract partial email from response
def extract_partial_email(response):
    if response.get('obfuscated_email'):
        return response['obfuscated_email']
    else:
        return "Could not find obfuscated email."

# Function to save banned users to file
def save_banned_users():
    with open(BANNED_USERS_FILE, 'w') as file:
        file.write("\n".join(str(uid) for uid in banned_users))

# Function to load banned users from file
def load_banned_users():
    global banned_users
    try:
        with open(BANNED_USERS_FILE, 'r') as file:
            banned_users = set(int(line.strip()) for line in file.readlines())
    except FileNotFoundError:
        open(BANNED_USERS_FILE, 'a').close()

# Function to save authorized users to file
def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, 'w') as file:
        file.write("\n".join(str(uid) for uid in authorized_users))

# Function to load authorized users from file
def load_authorized_users():
    global authorized_users
    try:
        with open(AUTHORIZED_USERS_FILE, 'r') as file:
            authorized_users = set(int(line.strip()) for line in file.readlines())
    except FileNotFoundError:
        open(AUTHORIZED_USERS_FILE, 'a').close()

# Function to check if user is banned
def is_user_banned(chat_id):
    return chat_id in banned_users

# Function to check if user is authorized admin
def is_user_authorized(chat_id):
    return chat_id in authorized_users

# Function to cancel the conversation
def cancel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    store_user_id(user_id)  # Store user ID here
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    store_user_id(user_id)  # Store user ID here
    user = update.message.from_user  # Move the user assignment outside the if block

    if is_user_banned(user_id):
        update.message.reply_text("You are restricted from using this bot. Kindly contact the developer to gain access.")
        return

    # Recheck membership status every time the user starts the bot
    if user_verified.get(user_id, False) and check_membership(user_id, context):
        update.message.reply_text(f"Hi Sir/Mam! \nWelcome to the Helper Bot.\n"
                     "Type / to load commands, then select the desired command to get started. Thank you !! 💸🕊️\n"
                     "                              ~ @d3luci4x 🫶🏻❤️‍🔥\n",
                )
        return
    else:
        user_verified[user_id] = False

    # If not verified, prompt to join channels

    # If not verified, prompt to join channels
    keyboard = [
        [InlineKeyboardButton(f' {channel["name"]}', url=channel['link'])] for channel in REQUIRED_CHANNELS
    ] + [[InlineKeyboardButton('JOINED ✅', callback_data='start_joined')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please join the channels below and then press "joined":', reply_markup=reply_markup)

def check_membership(user_id: int, context: CallbackContext) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            channel_name = channel['name']
            logger.info(f"Attempting to check membership for user {user_id} in channel {channel_name}")
            member = context.bot.get_chat_member(chat_id=f'@{channel_name}', user_id=user_id)
            logger.info(f"Checking membership for {user_id} in {channel_name}: {member.status}")
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking membership for {channel['name']}: {e}")
            return False
    return True


# Reset command handler
# Reset command handler
def reset(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    store_user_id(user_id)  # Store user ID here
    chat_id = update.message.chat_id

    if is_user_banned(chat_id):
        update.message.reply_text("You are restricted from using this bot.")
        return ConversationHandler.END

    # Check if the user is a member of all required channels
    if check_membership(user_id, context):
        update.message.reply_text(
            "To send a password reset link, enter your Instagram username.\n"
            "Example: johndoe123"
        )
        return AWAITING_USERNAME
    else:
        # Prompt the user to join channels
        keyboard = [
            [InlineKeyboardButton(f' {channel["name"]}', url=channel['link'])] for channel in REQUIRED_CHANNELS
        ] + [[InlineKeyboardButton('JOINED ✅', callback_data='reset_joined')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Please join the channels below and then press "joined":',
            reply_markup=reply_markup
        )
        return ConversationHandler.END

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    if callback_data == 'start_joined':
        if check_membership(user_id, context):
            user_verified[user_id] = True
            query.answer("Thank you for joining the channels!")
            query.edit_message_text(
                text=f"Hi [{query.from_user.first_name}](tg://user?id={query.from_user.id})! \nWelcome to the Helper Bot.\n"
                     "Type / to load commands, then select the desired command to get started. Thank you !! 💸🕊️\n"
                     "                              ~ @d3luci4x 🫶🏻❤️‍🔥\n",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            query.answer("You have not joined all the required channels.", show_alert=True)
            query.edit_message_text(text="You have not joined all the required channels. Please join and try again.")

    elif callback_data == 'reset_joined':
        if check_membership(user_id, context):
            query.answer("Thank you for joining the channels!")
            query.edit_message_text(
                text=f"Hi [{query.from_user.first_name}](tg://user?id={query.from_user.id})! \n"
                     "To send a password reset link, enter your Instagram username.\n"
                     "Example: johndoe123\n\n"
                     "                              ~ @d3luci4x 🫶🏻❤️‍🔥\n",
                parse_mode=ParseMode.MARKDOWN
            )
            return AWAITING_USERNAME
        else:
            query.answer("You have not joined all the required channels.", show_alert=True)
            query.edit_message_text(text="You have not joined all the required channels. Please join and try again.")



# Message handler for Instagram username
def handle_username(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    if is_user_banned(chat_id):
        update.message.reply_text("You are restricted from using this bot.")
        return ConversationHandler.END

    username = update.message.text
    response = send_password_reset(username)

    if 'obfuscated_email' in response:
        update.message.reply_text(
            f"Password reset code sent to: {extract_partial_email(response)}.\n"
            "Please check your email and follow the instructions to reset your password.\n\n[≭] Sᴜᴘᴘᴏʀᴛ & Uᴘᴅᴀᴛᴇs ~ @LuciTheCurse."
        )
    else:
        error_message = response.get('message', 'Unknown error occurred')
        if "wait a few minutes" in error_message.lower():
            error_message = "Your account has been rate-limited by Instagram. Please wait a few minutes before sending the reset link to this account."
        update.message.reply_text(f"Error: {error_message}")
    return ConversationHandler.END

# Function to get list of banned users
# Function to get list of banned users
def get_banned(update: Update, context: CallbackContext):
    global admin_logged_in
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if banned_users:
        update.message.reply_text(f"List of banned users:\n" + "\n".join(str(uid) for uid in banned_users))
    else:
        update.message.reply_text("No users are currently banned.")

# Function to get list of authorized users
def get_authorized(update: Update, context: CallbackContext):
    global admin_logged_in
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if authorized_users:
        update.message.reply_text(f"List of authorized users:\n" + "\n".join(str(uid) for uid in authorized_users))
    else:
        update.message.reply_text("No users are currently authorized.")

# Admin login command handler
def admin_login(update: Update, context: CallbackContext):
    global admin_logged_in
    chat_id = update.message.chat_id
    if len(context.args) != 1:
        update.message.reply_text("Please provide the admin password.")
        return

    password_attempt = context.args[0]

    try:
        with open(AUTHORIZED_USERS_FILE, 'r') as file:
            authorized_users = set(int(line.strip()) for line in file.readlines())
    except FileNotFoundError:
        authorized_users = set()

    if password_attempt == ADMIN_PASSWORD and chat_id in authorized_users:
        admin_logged_in = True
        
        # Get admin's first name for personalized greeting
        admin_name = update.message.from_user.first_name
        
        # Generate profile link (you can adjust this based on your bot's profile settings)
        profile_link = f"https://t.me/{update.message.from_user.username}"
        
        # Reply with personalized greeting and available commands
        update.message.reply_text(
            f"Welcome, {admin_name}! \nYou are logged in as admin.\n"
            f"Your profile: {profile_link}\n\n"
            "Here are the available admin commands:\n"
            "/get_banned - Get list of banned users\n"
            "/get_authorized - Get list of authorized users\n"
            "/ban <chat_id> - Ban a user\n"
            "/unban <chat_id> - Unban a user\n"
            "/admin_logout - Logout from admin panel"
        )
    else:
        update.message.reply_text("Incorrect admin password or you are not authorized to access the admin panel.")

# Function to logout from admin panel
def admin_logout(update: Update, context: CallbackContext):
    global admin_logged_in
    chat_id = update.message.chat_id
    
    if chat_id in authorized_users:
        admin_logged_in = False
        update.message.reply_text("Admin logout successful.")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Function to ban a user
def ban_user(update: Update, context: CallbackContext):
    global admin_logged_in
    chat_id = update.message.chat_id
    
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("Please provide the chat ID of the user to ban.")
        return
    
    try:
        chat_id_to_ban = int(context.args[0])
        
        if chat_id_to_ban in authorized_users:
            update.message.reply_text("You cannot ban another admin.")
            return
        
        banned_users.add(chat_id_to_ban)
        save_banned_users()
        update.message.reply_text(f"User with Chat ID {chat_id_to_ban} has been banned.")
    except ValueError:
        update.message.reply_text("Invalid chat ID format. Please provide a valid integer chat ID.")

# Function to unban a user
def unban_user(update: Update, context: CallbackContext):
    global admin_logged_in
    chat_id = update.message.chat_id
    
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("Please provide the chat ID of the user to unban.")
        return
    
    try:
        chat_id_to_unban = int(context.args[0])
        
        if chat_id_to_unban in banned_users:
            banned_users.remove(chat_id_to_unban)
            save_banned_users()
            update.message.reply_text(f"User with Chat ID {chat_id_to_unban} has been unbanned.")
        else:
            update.message.reply_text("This user is not currently banned.")
    except ValueError:
        update.message.reply_text("Invalid chat ID format. Please provide a valid integer chat ID.")

# Function to add an authorized user
def add_authorized_user(update: Update, context: CallbackContext):
    global admin_logged_in
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("Please provide the chat ID of the user to authorize.")
        return
    
    try:
        new_authorized_id = int(context.args[0])
        if new_authorized_id not in authorized_users:
            authorized_users.add(new_authorized_id)
            save_authorized_users()
            update.message.reply_text(f"User with Chat ID {new_authorized_id} has been authorized.")
        else:
            update.message.reply_text("This user is already authorized.")
    except ValueError:
        update.message.reply_text("Invalid chat ID format. Please provide a valid integer chat ID.")

# Function to remove an authorized user
def remove_authorized_user(update: Update, context: CallbackContext):
    global admin_logged_in
    if not admin_logged_in:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("Please provide the chat ID of the user to deauthorize.")
        return
    
    try:
        authorized_id_to_remove = int(context.args[0])
        if authorized_id_to_remove in authorized_users:
            authorized_users.remove(authorized_id_to_remove)
            save_authorized_users()
            update.message.reply_text(f"User with Chat ID {authorized_id_to_remove} has been deauthorized.")
        else:
            update.message.reply_text("This user is not currently authorized.")
    except ValueError:
        update.message.reply_text("Invalid chat ID format. Please provide a valid integer chat ID.")

# Command handler for unknown commands
def unknown_command(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, I didn't understand that command.")

# Error handler
def error_handler(update: Update, context: CallbackContext):
    """Log the error."""
    error_msg = f"Update {update} caused error {context.error}"
    print(error_msg)
    # You can also log the errors to a file or other logging service

# Main function to handle Telegram bot commands
def main() -> None:
    # Load banned and authorized users from files
    load_banned_users()
    load_authorized_users()

    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('reset', reset)],
        states={
            AWAITING_USERNAME: [MessageHandler(Filters.text & ~Filters.command, handle_username)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],  # Define cancel command handler here
    )

    dispatcher.add_handler(conv_handler)

    # Add command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler('reset', reset))
    dispatcher.add_handler(CommandHandler('get_banned', get_banned))
    dispatcher.add_handler(CommandHandler('get_authorized', get_authorized))
    dispatcher.add_handler(CommandHandler('admin_login', admin_login, pass_args=True))
    dispatcher.add_handler(CommandHandler('admin_logout', admin_logout))
    dispatcher.add_handler(CommandHandler('ban', ban_user, pass_args=True))
    dispatcher.add_handler(CommandHandler('unban', unban_user, pass_args=True))
    dispatcher.add_handler(CommandHandler('add_authorized', add_authorized_user, pass_args=True))
    dispatcher.add_handler(CommandHandler('remove_authorized', remove_authorized_user, pass_args=True))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

    # Add error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()