import os
import asyncio
from telethon.sync import TelegramClient
from telethon import functions
from urllib.parse import unquote

# Ensure all necessary imports are present here

def load_api_credentials():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    env_path = os.path.join(root_dir, 'env.txt')
    
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
            if api_id and api_hash:
                return api_id, api_hash
    print("[!] API credentials not found or incomplete in env.txt")
    return None, None

def get_available_sessions():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sessions_dir = os.path.join(root_dir, 'sessions')
    if not os.path.exists(sessions_dir):
        return []
    return [f.split('.')[0] for f in os.listdir(sessions_dir) if f.endswith('.session')]

async def get_web_app_data(session_name):
    api_id, api_hash = load_api_credentials()
    if not api_id or not api_hash:
        print("[!] API credentials not found. Please check your env.txt file.")
        return None

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    session_path = os.path.join(root_dir, 'sessions', session_name)

    async with TelegramClient(session_path, api_id, api_hash) as client:
        try:
            notcoin = await client.get_entity("notpixel")
            msg = await client(functions.messages.RequestWebViewRequest(
                peer=notcoin,
                bot=notcoin,
                platform="android",
                url="https://notpx.app/"
            ))
            webappdata_global = msg.url.split('https://notpx.app/#tgWebAppData=')[1].replace("%3D","=").split('&tgWebAppVersion=')[0].replace("%26","&")
            user_data = webappdata_global.split("&user=")[1].split("&auth")[0]
            webappdata_global = webappdata_global.replace(user_data, unquote(user_data))
            return webappdata_global
        except Exception as e:
            print(f"[!] Error: {str(e)}")
            return None

async def create_query_id():
    api_id, api_hash = load_api_credentials()
    if not api_id or not api_hash:
        print("[!] API credentials not found. Please check your env.txt file in the root directory.")
        return

    sessions = get_available_sessions()
    if not sessions:
        print("[!] No available sessions. Please create a session first.")
        return

    print("Available sessions:")
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session}")

    while True:
        try:
            choice = int(input("Select a session number: "))
            if 1 <= choice <= len(sessions):
                session_name = sessions[choice - 1]
                break
            else:
                print("[!] Invalid choice. Please try again.")
        except ValueError:
            print("[!] Please enter a valid number.")

    webappdata = await get_web_app_data(session_name)
    if webappdata:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        query_file_path = os.path.join(current_dir, 'query.txt')
        
        with open(query_file_path, 'w') as f:
            f.write(webappdata)
        print(f"[+] Query ID for session {session_name} has been successfully saved to {query_file_path}")
    else:
        print("[!] Failed to retrieve WebAppData")

if __name__ == "__main__":
    asyncio.run(create_query_id())