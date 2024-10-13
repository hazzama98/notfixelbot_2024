import requests
import json
import time
import random
from setproctitle import setproctitle
from convert import get
from colorama import Fore, Style, init
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib.parse
import asyncio
from get_query import get_web_app_data, load_api_credentials, get_available_sessions
import os
from colorama import Fore, Back, Style, init
import time


url = "https://notpx.app/api/v1"

WAIT = 180 * 3
DELAY = 1

WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

init(autoreset=True)

setproctitle("notpixel")

image = get("")

c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

def log_message(message, color=Style.RESET_ALL):
    current_time = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {color}{message}{Style.RESET_ALL}")

def get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = get_session_with_retries()

def get_color(pixel, header):
    try:
        response = session.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except KeyError:
        return "#000000"
    except requests.exceptions.Timeout:
        log_message("Request timed out", Fore.RED)
        return "#000000"
    except requests.exceptions.ConnectionError as e:
        log_message(f"Connection error: {e}", Fore.RED)
        return "#000000"
    except requests.exceptions.RequestException as e:
        log_message(f"Request failed: {e}", Fore.RED)
        return "#000000"

def claim(header):
    log_message("Initiating resource acquisition", Fore.CYAN)
    try:
        session.get(f"{url}/mining/claim", headers=header, timeout=10)
    except requests.exceptions.RequestException as e:
        log_message(f"Resource acquisition unsuccessful: {e}", Fore.RED)

def get_pixel(x, y):
    return y * 1000 + x + 1

def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

start_x = 920
start_y = 386

def paint(canvas_pos, color, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }

    try:
        response = session.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = get_pos(canvas_pos, 1000)

        if response.status_code == 400:
            log_message("Energy resources depleted", Fore.RED)
            return False
        if response.status_code == 401:
            return -1

        log_message(f"Pixel modification successful: {x},{y}", Fore.GREEN)
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"Pixel modification unsuccessful: {e}", Fore.RED)
        return False

def extract_username_from_initdata(init_data):
    decoded_data = urllib.parse.unquote(init_data)
    
    username_start = decoded_data.find('"username":"') + len('"username":"')
    username_end = decoded_data.find('"', username_start)
    
    if username_start != -1 and username_end != -1:
        return decoded_data[username_start:username_end]
    
    return "Unknown"

def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [f"initData {line.strip()}" for line in file if line.strip()]
    return accounts

def fetch_mining_data(header):
    try:
        response = session.get(f"https://notpx.app/api/v1/mining/status", headers=header, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_balance = data.get('userBalance', 'Unknown')
            if user_balance != 'Unknown':
                user_balance = int(float(user_balance))
            log_message(f"Current balance: {user_balance}", Fore.MAGENTA)
            return user_balance
        else:
            log_message(f"Mining data retrieval unsuccessful: {response.status_code}", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Error encountered during mining data retrieval: {e}", Fore.RED)
        return None

async def random_delay(min_seconds=0.5, max_seconds=2):
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)

def get_surrounding_colors(x, y, headers):
    surrounding_positions = [
        (x-1, y),  # left
        (x+1, y),  # right
        (x, y-1),  # up
        (x, y+1)   # down
    ]
    colors = []
    for pos_x, pos_y in surrounding_positions:
        color = get_color(get_canvas_pos(pos_x, pos_y), headers)
        if color != -1:
            colors.append(color)
    return colors

async def human_like_painting(x, y, target_color, headers):
    await random_delay(0.1, 0.3)
    log_message(f"Cursor movement to {x},{y}", Fore.CYAN)
    
    await random_delay(0.1, 0.2)
    log_message("Pixel selection initiated", Fore.CYAN)
    
    surrounding_colors = get_surrounding_colors(x, y, headers)
    if surrounding_colors:
        most_common_color = max(set(surrounding_colors), key=surrounding_colors.count)
        if most_common_color != target_color:
            log_message(f"Surrounding colors differ. Cancelling coloring at {x},{y}", Fore.YELLOW)
            return False
    
    await random_delay(0.2, 0.5)
    log_message(f"Color {target_color} selected", Fore.CYAN)
    
    await random_delay(0.1, 0.3)
    log_message("Selection confirmed", Fore.CYAN)
    
    result = paint(get_canvas_pos(x, y), target_color, headers)
    
    return result

async def update_query_id(session_name):
    log_message("Query ID update in progress...", Fore.YELLOW)
    api_id, api_hash = load_api_credentials()
    if not api_id or not api_hash:
        log_message("API credentials not found. Please verify your env.txt file.", Fore.RED)
        return None

    webappdata = await get_web_app_data(session_name)
    if webappdata:
        with open('bot/data/notpixel/query.txt', 'w') as f:
            f.write(webappdata)
        log_message(f"Query ID for session {session_name} successfully updated", Fore.GREEN)
        return webappdata
    else:
        log_message("WebAppData retrieval unsuccessful", Fore.RED)
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(username, balance, pixels_painted, earned_balance):
    clear_screen()
    print(f"{Fore.CYAN}╔═══════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}                   NOT PIXEL                   {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚═══════════════════════════════════════════════╝")
    print(f"{Fore.CYAN}═════════════════════════════════════════════════")
    print(f"{Fore.YELLOW}Username: {Fore.WHITE}{username:<15} {Fore.YELLOW}Balance: {Fore.WHITE}{int(balance) if balance is not None else 'Unknown':<10}")
    print(f"{Fore.CYAN}═════════════════════════════════════════════════")
    print(f"{Fore.YELLOW}Pixels painted: {Fore.WHITE}{pixels_painted:<6} {Fore.YELLOW}Earned balance: {Fore.WHITE}{int(earned_balance) if earned_balance is not None else 'Unknown':<10}")
    print(f"{Fore.CYAN}═════════════════════════════════════════════════")
    print(f"{Fore.YELLOW}Progress")
    print(f"{Fore.CYAN}═════════════════════════════════════════════════")
    # Add empty lines for progress updates
    for _ in range(3):
        print()

def update_progress(message):
    # Move cursor up 6 lines (5 empty lines + 1 for the bottom border)
    print(f"\033[6A\r{Fore.GREEN}{message:<53}")
    # Move cursor back down
    print("\033[5B", end="")

async def main(auth, account, session_name):
    headers = {'authorization': auth}
    username = extract_username_from_initdata(auth)
    balance = 0
    pixels_painted = 0
    earned_balance = 0
    initial_balance = 0
    consecutive_failures = 0

    try:
        initial_balance = fetch_mining_data(headers)
        if initial_balance is None:
            initial_balance = 0
        
        print_header(username, initial_balance, pixels_painted, earned_balance)

        claim(headers)

        size = len(image) * len(image[0])
        order = [i for i in range(size)]
        random.shuffle(order)

        max_pixels_per_session = random.randint(10, 20)

        for pos_image in order:
            x, y = get_pos(pos_image, len(image[0]))
            await random_delay()
            try:
                color = get_color(get_canvas_pos(x, y), headers)
                if color == -1:
                    update_progress("Query ID expired. Initiating update...")
                    new_auth = await update_query_id(session_name)
                    if new_auth:
                        headers['authorization'] = f"initData {new_auth}"
                        update_progress("Query ID successfully updated. Resuming process...")
                        new_balance = fetch_mining_data(headers)
                        if new_balance is not None:
                            balance = new_balance
                            earned_balance = balance - initial_balance
                        print_header(username, balance, pixels_painted, earned_balance)
                        continue
                    else:
                        update_progress("Query ID update unsuccessful. Terminating process for this account.")
                        break

                if image[y][x] == ' ' or color == c[image[y][x]]:
                    update_progress(f"Pixel at {start_x + x - 1},{start_y + y - 1} skipped")
                    continue

                result = await human_like_painting(x, y, c[image[y][x]], headers)
                if result == -1:
                    update_progress("Query ID expired. Initiating update...")
                    new_auth = await update_query_id(session_name)
                    if new_auth:
                        headers['authorization'] = f"initData {new_auth}"
                        update_progress("Query ID successfully updated. Resuming process...")
                        new_balance = fetch_mining_data(headers)
                        if new_balance is not None:
                            balance = new_balance
                            earned_balance = balance - initial_balance
                        print_header(username, balance, pixels_painted, earned_balance)
                        continue
                    else:
                        update_progress("Query ID update unsuccessful. Terminating process for this account.")
                        break
                elif result:
                    pixels_painted += 1
                    consecutive_failures = 0
                    new_balance = fetch_mining_data(headers)
                    if new_balance is not None:
                        balance = new_balance
                        earned_balance = balance - initial_balance
                    print_header(username, balance, pixels_painted, earned_balance)
                    update_progress(f"Painted: {start_x + x - 1},{start_y + y - 1}")
                    
                    if pixels_painted >= max_pixels_per_session:
                        update_progress(f"Reached limit of {max_pixels_per_session} pixels. Taking a short break.")
                        await random_delay(30, 60)
                        pixels_painted = 0
                        max_pixels_per_session = random.randint(10, 20)
                    continue
                else:
                    update_progress(f"Failed to color pixel at {start_x + x - 1},{start_y + y - 1}. Searching for another location.")
                    continue

            except IndexError:
                update_progress(f"IndexError encountered at pos_image: {pos_image}, y: {y}, x: {x}")

    except requests.exceptions.RequestException as e:
        update_progress(f"Network error in account {account}: {e}")

async def night_sleep():
    now = datetime.now()
    sleep_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    sleep_end = sleep_start + timedelta(hours=1, minutes=1)
    
    if sleep_start <= now < sleep_end:
        sleep_duration = sleep_end - now
        log_message(f"Entering nocturnal rest mode until {sleep_end.strftime('%H:%M:%S')}", Fore.YELLOW)
        await asyncio.sleep(sleep_duration.total_seconds())
        log_message("Nocturnal rest mode concluded. Resuming operations...", Fore.GREEN)
    elif now.hour == 23:
        sleep_duration = sleep_start - now + timedelta(hours=1, minutes=1)
        log_message(f"Preparing for nocturnal rest mode. Commencement at {sleep_start.strftime('%H:%M:%S')}", Fore.YELLOW)
        await asyncio.sleep(sleep_duration.total_seconds())
        log_message("Nocturnal rest mode concluded. Resuming operations...", Fore.GREEN)

async def countdown(seconds, message):
    end_time = datetime.now() + timedelta(seconds=seconds)
    while datetime.now() < end_time:
        remaining = end_time - datetime.now()
        minutes, secs = divmod(remaining.seconds, 60)
        countdown_msg = f"\r{message} {minutes:02d}:{secs:02d}"
        print(countdown_msg, end='', flush=True)
        await asyncio.sleep(1)
    print("\rCountdown completed.                 ")

async def process_accounts(accounts):
    while True:
        await night_sleep()
        
        first_account_start_time = datetime.now()

        sessions = get_available_sessions()
        random.shuffle(sessions)
        for account, session_name in zip(accounts, sessions):
            username = extract_username_from_initdata(account)
            log_message(f"--- INITIATING SESSION FOR ACCOUNT: {username} ---", Fore.BLUE)
            await main(account, account, session_name)
            
            wait_time = random.randint(60, 180)
            log_message(f"Session completed. Entering cooldown period for {wait_time} seconds.", Fore.YELLOW)
            await countdown(wait_time, "Cooldown period remaining:")

        time_elapsed = datetime.now() - first_account_start_time
        time_to_wait = timedelta(hours=1) - time_elapsed

        if time_to_wait.total_seconds() > 0:
            wait_time = int(time_to_wait.total_seconds())
            log_message(f"All accounts processed. Initiating extended rest period of {wait_time // 60} minutes.", Fore.YELLOW)
            actual_wait_time = random.uniform(wait_time * 0.9, wait_time * 1.1)
            await countdown(int(actual_wait_time), "Extended rest period remaining:")
        else:
            log_message(f"Extended rest period unnecessary. Total processing time exceeded 1 hour.", Fore.YELLOW)

if __name__ == "__main__":
    accounts = load_accounts_from_file('bot/data/notpixel/query.txt')

    asyncio.run(process_accounts(accounts))