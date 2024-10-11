import os
import threading
import asyncio
import hashlib
import time
import uuid
import requests
import json
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import night_sleep, Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime, timedelta

BOT_TOKEN = "7722039584:AAG2BweKTZQJ60esvAMkRtcZ7_eTnzywj9E"
ADMIN_CHAT_ID = "5373988314"

bot = telebot.TeleBot(BOT_TOKEN)

# File to store active keys and their information
KEYS_FILE = "active_keys.json"

# Load existing keys from file
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save keys to file
def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

# Dictionary to store active keys and their information
active_keys = load_keys()

def generate_license_key():
    key = uuid.uuid4().hex
    expiration_date = (datetime.now() + timedelta(days=5)).isoformat()
    active_keys[key] = {"expiration": expiration_date, "user": None}
    save_keys(active_keys)
    return key

def check_license(key, username):
    if key in active_keys:
        expiration = datetime.fromisoformat(active_keys[key]["expiration"])
        if datetime.now() < expiration:
            if active_keys[key]["user"] is None:
                active_keys[key]["user"] = username
                save_keys(active_keys)
                bot.send_message(ADMIN_CHAT_ID, f"New user: {username} has activated key: {key}")
                return True
            elif active_keys[key]["user"] == username:
                return True
            else:
                return "License key is already in use by another user"
        else:
            del active_keys[key]
            save_keys(active_keys)
            return False
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Selamat datang di layanan kami yang istimewa! 🌟\n\nBerikut adalah perintah yang tersedia:\n\n/generate_key - Menghasilkan kunci lisensi baru (hanya untuk admin)\n/check_key [kunci] - Memeriksa validitas kunci lisensi Anda\n/active_users - Menampilkan daftar pengguna aktif (hanya untuk admin)\n\nSilakan gunakan perintah yang sesuai untuk memulai pengalaman Anda bersama kami!")

@bot.message_handler(commands=['generate_key'])
def generate_key(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "Anda tidak memiliki izin untuk menghasilkan kunci.")
        return
    
    key = generate_license_key()
    bot.reply_to(message, f"Kunci yang dihasilkan: {key}\nBerlaku selama 5 hari.")

@bot.message_handler(commands=['check_key'])
def check_key(message):
    key = message.text.split()[1] if len(message.text.split()) > 1 else None
    if key:
        result = check_license(key, message.from_user.username)
        if result == True:
            bot.reply_to(message, "Kunci Anda valid dan aktif.")
        elif result == "License key is already in use by another user":
            bot.reply_to(message, "Kunci lisensi sudah digunakan oleh pengguna lain.")
        else:
            bot.reply_to(message, "Kunci tidak valid atau sudah kadaluarsa.")
    else:
        bot.reply_to(message, "Silakan berikan kunci untuk diperiksa.")

@bot.message_handler(commands=['active_users'])
def active_users(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "Anda tidak memiliki izin untuk melihat pengguna aktif.")
        return
    
    user_count = sum(1 for info in active_keys.values() if info["user"] is not None)
    user_list = "\n".join([f"Kunci: {key}, Pengguna: {info['user']}" for key, info in active_keys.items() if info["user"] is not None])
    bot.reply_to(message, f"Total pengguna aktif: {user_count}\n\n{user_list}")

def multithread_starter(key, username):
    result = check_license(key, username)
    if result == True:
        print("License key verified. Starting the script...")
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        dirs = os.listdir("sessions/")
        sessions = list(filter(lambda x: x.endswith(".session"), dirs))
        sessions = list(map(lambda x: x.split(".session")[0], sessions))
        
        for session_name in sessions:
            try:
                cli = NotPx("sessions/" + session_name)

                def run_painters():
                    asyncio.run(painters(cli, session_name))

                def run_mine_claimer():
                    asyncio.run(mine_claimer(cli, session_name))

                threading.Thread(target=run_painters).start()
                threading.Thread(target=run_mine_claimer).start()
            except Exception as e:
                print("[!] {}Error on load session{} \"{}\", error: {}".format(Colors.RED, Colors.END, session_name, e))
    elif result == "License key is already in use by another user":
        print("[!] " + result)
    else:
        print("[!] Invalid or expired license key. Please contact the admin for a valid key.")

def add_api_credentials():
    api_id = input("Enter API ID: ")
    api_hash = input("Enter API Hash: ")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    with open(env_path, "w") as f:
        f.write(f"API_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")
    print("[+] API credentials saved successfully in env.txt file.")

def reset_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        os.remove(env_path)
        print("[+] API credentials reset successfully.")
    else:
        print("[!] No env.txt file found. Nothing to reset.")

def reset_session():
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    sessions = [f for f in os.listdir("sessions/") if f.endswith(".session")]
    if not sessions:
        print("[!] No sessions found.")
        return
    print("Available sessions:")
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session[:-8]}")
    choice = input("Enter the number of the session to reset: ")
    try:
        session_to_reset = sessions[int(choice) - 1]
        os.remove(os.path.join("sessions", session_to_reset))
        print(f"[+] Session {session_to_reset[:-8]} reset successfully.")
    except (ValueError, IndexError):
        print("[!] Invalid choice. Please try again.")

def load_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            api_id = None
            api_hash = None
            for line in lines:
                if line.startswith('API_ID='):
                    api_id = line.split('=')[1].strip()
                elif line.startswith('API_HASH='):
                    api_hash = line.split('=')[1].strip()
            return api_id, api_hash
    return None, None

def process():
    print(f"""{Colors.CYAN}
╔═══════════════════════════════╗
║        Bot Not Pixel v2.0     ║
║   Dibuat oleh: itbaarts_dev   ║
╚═══════════════════════════════╝{Colors.END}""")
    print("Starting Telegram bot...")
    bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
    bot_thread.start()
    
    while True:
        key = input("Enter your license key to use the script: ")
        username = input("Enter your username: ")
        result = check_license(key, username)
        if result == True:
            print("License key verified. You can now use the script.")
            break
        elif result == "License key is already in use by another user":
            print("[!] " + result)
        else:
            print("[!] Invalid or expired license key. Please contact the admin for a valid key.")
    
    while True:
        print("\nMain Menu:")
        print("1. Add Account Session")
        print("2. Start Bot Mining")
        print("3. Configure API Credentials")
        print("4. Reset API Credentials")
        print("5. Reset Session")
        print("6. Exit Application")
        
        option = input("Please select an option: ")
        
        if option == "1":
            name = input("\nEnter Session name: ")
            if not os.path.exists("sessions"):
                os.mkdir("sessions")
            if not any(name in i for i in os.listdir("sessions/")):
                api_id, api_hash = load_api_credentials()
                if api_id and api_hash:
                    client = TelegramClient("sessions/" + name, api_id, api_hash).start()
                    client.disconnect()
                    print("[+] Session {} {}saved success{}.".format(name, Colors.GREEN, Colors.END))
                else:
                    print("[!] API credentials not found. Please add them first.")
            else:
                print("[x] Session {} {}already exist{}.".format(name, Colors.RED, Colors.END))
        elif option == "2":
            multithread_starter(key, username)
        elif option == "3":
            add_api_credentials()
        elif option == "4":
            reset_api_credentials()
        elif option == "5":
            reset_session()
        elif option == "6":
            print("Exiting...")
            bot.stop_polling()
            bot_thread.join()
            break
        else:
            print("[!] Invalid option. Please try again.")

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    process()
