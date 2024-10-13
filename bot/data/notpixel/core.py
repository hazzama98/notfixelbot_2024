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
from PIL import Image
import io
import numpy as np
import os
from colorama import Fore, Back, Style, init
import time
import aiohttp
import ssl


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

async def human_like_painting(x, y, color, headers):
    await random_delay(0.1, 0.3)
    log_message(f"Cursor movement to {x},{y}", Fore.CYAN)
    
    await random_delay(0.1, 0.2)
    log_message("Pixel selection initiated", Fore.CYAN)
    
    await random_delay(0.2, 0.5)
    log_message(f"Color {color} selected", Fore.CYAN)
    
    await random_delay(0.1, 0.3)
    log_message("Selection confirmed", Fore.CYAN)
    
    result = paint(get_canvas_pos(x, y), color, headers)
    
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
    print(f"{Fore.CYAN}╔════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}                   NOT PIXEL                    {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚════════════════════════════════════════════════╝")
    print(f"{Fore.CYAN}══════════════════════════════════════════════════")
    print(f"{Fore.YELLOW}Username: {Fore.WHITE}{username:<15} {Fore.YELLOW}Balance: {Fore.WHITE}{int(balance) if balance is not None else 'Unknown':<10}")
    print(f"{Fore.CYAN}══════════════════════════════════════════════════")
    print(f"{Fore.YELLOW}Pixels painted: {Fore.WHITE}{pixels_painted:<6} {Fore.YELLOW}Earned balance: {Fore.WHITE}{int(earned_balance) if earned_balance is not None else 'Unknown':<10}")
    print(f"{Fore.CYAN}════════════════ P R O G R E S S ═════════════════")
    # Add empty lines for progress updates
    for _ in range(4):
        print()

def update_progress(message):
    # Move cursor up 6 lines (5 empty lines + 1 for the bottom border)
    print(f"\033[6A\r{Fore.GREEN}{message:<53}")
    # Move cursor back down
    print("\033[5B", end="")

def get_surrounding_colors(x, y, headers):
    surrounding_colors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # kiri, kanan, atas, bawah
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
            color = get_color(get_canvas_pos(nx, ny), headers)
            if color != -1:
                surrounding_colors.append(color)
    return surrounding_colors

def get_most_common_color(colors):
    if not colors:
        return None
    return max(set(colors), key=colors.count)

def get_center_priority_order(size):
    center = size // 2
    return sorted(range(size), key=lambda x: abs(x - center))

# Buat konteks SSL yang mengabaikan verifikasi sertifikat
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Buat sesi aiohttp dengan konteks SSL kustom
async def get_aiohttp_session():
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))

async def get_image_colors():
    url = "https://image.notpx.app/api/v2/image"
    async with await get_aiohttp_session() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(io.BytesIO(image_data))
                    return np.array(image)
        except aiohttp.ClientError as e:
            log_message(f"Gagal mengambil gambar: {str(e)}", Fore.RED)
    return None

def get_dominant_color(image, x, y, radius=5):
    height, width = image.shape[:2]
    x1, y1 = max(0, x - radius), max(0, y - radius)
    x2, y2 = min(width, x + radius + 1), min(height, y + radius + 1)
    
    region = image[y1:y2, x1:x2].reshape(-1, 3)
    colors, counts = np.unique(region, axis=0, return_counts=True)
    dominant_color = tuple(map(int, colors[counts.argmax()]))  # Konversi ke int
    return dominant_color

async def find_pixel_to_color(image):
    height, width = image.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    for r in range(0, max(width, height), 5):
        for x in range(max(0, center_x - r), min(width, center_x + r + 1)):
            for y in range(max(0, center_y - r), min(height, center_y + r + 1)):
                pixel_color = tuple(map(int, image[y, x]))  # Konversi ke int
                dominant_color = get_dominant_color(image, x, y)
                
                if pixel_color != dominant_color:
                    return x, y, pixel_color
    
    return None

async def fetch_energy_status(headers):
    try:
        async with await get_aiohttp_session() as session:
            async with session.get(f"{url}/mining/status", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('energy', 0)
    except Exception as e:
        log_message(f"Gagal mengambil status energi: {str(e)}", Fore.RED)
    return 0

async def process_account(account, session_name):
    headers = {'authorization': account}
    username = extract_username_from_initdata(account)
    balance = 0
    pixels_painted = 0
    earned_balance = 0
    initial_balance = 0
    consecutive_failures = 0
    energy = 100  # Inisialisasi energi

    try:
        initial_balance = await fetch_mining_data(headers)
        if initial_balance is None:
            initial_balance = 0
        
        print_header(username, initial_balance, pixels_painted, earned_balance)

        await claim(headers)

        while True:
            try:
                # Periksa status energi
                energy = await fetch_energy_status(headers)
                if energy <= 0:
                    log_message("Energi habis. Menunggu pengisian energi...", Fore.YELLOW)
                    await asyncio.sleep(60)  # Tunggu 1 menit sebelum memeriksa lagi
                    continue

                image_colors = await get_image_colors()
                if image_colors is None:
                    log_message("Gagal mendapatkan gambar. Mencoba lagi...", Fore.RED)
                    await asyncio.sleep(5)
                    continue

                pixel_info = await find_pixel_to_color(image_colors)
                if pixel_info is None:
                    log_message("Tidak ada pixel yang perlu diwarnai. Menunggu...", Fore.YELLOW)
                    await asyncio.sleep(5)
                    continue

                x, y, color = pixel_info
                color_hex = '#{:02x}{:02x}{:02x}'.format(*color)  # Konversi ke format hex
                
                # Konversi koordinat gambar ke koordinat canvas
                canvas_x = start_x + x - 1
                canvas_y = start_y + y - 1
                
                # Periksa warna saat ini di canvas
                current_color = get_color(get_canvas_pos(canvas_x, canvas_y), headers)
                if current_color == -1:
                    # Handle kasus ketika query ID kedaluwarsa
                    update_progress("Query ID expired. Initiating update...")
                    new_auth = await update_query_id(session_name)
                    if new_auth:
                        headers['authorization'] = f"initData {new_auth}"
                        update_progress("Query ID successfully updated. Resuming process...")
                        continue
                    else:
                        update_progress("Query ID update unsuccessful. Terminating process for this account.")
                        break

                # Jika warna saat ini berbeda dari warna yang kita inginkan, lakukan pewarnaan
                if current_color != color_hex:
                    result = await human_like_painting(canvas_x, canvas_y, color_hex, headers)
                    if result:
                        pixels_painted += 1
                        consecutive_failures = 0
                        energy -= 1  # Kurangi energi setelah berhasil mewarnai
                        new_balance = await fetch_mining_data(headers)
                        if new_balance is not None:
                            balance = new_balance
                            earned_balance = balance - initial_balance
                        print_header(username, balance, pixels_painted, earned_balance)
                        update_progress(f"Painted: {canvas_x},{canvas_y}. Energy left: {energy}")
                    elif result == -1:  # Asumsi -1 menandakan energi habis
                        log_message("Energy resources depleted. Waiting for recharge...", Fore.YELLOW)
                        await asyncio.sleep(60)  # Tunggu 1 menit sebelum mencoba lagi
                    else:
                        consecutive_failures += 1
                        update_progress(f"Failed to paint. Consecutive failures: {consecutive_failures}")
                        if consecutive_failures >= 3:
                            wait_time = random.randint(10, 30)
                            update_progress(f"3 consecutive failures. Waiting for {wait_time} minutes.")
                            await asyncio.sleep(wait_time * 60)
                            consecutive_failures = 0

                # Tambahkan jeda untuk menghindari permintaan yang terlalu cepat
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                log_message(f"Kesalahan jaringan: {str(e)}", Fore.RED)
                await asyncio.sleep(5)
            except Exception as e:
                log_message(f"Kesalahan tidak terduga: {str(e)}", Fore.RED)
                await asyncio.sleep(5)

    except Exception as e:
        update_progress(f"Error in account {account}: {str(e)}")

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
            await process_account(account, session_name)
            
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
