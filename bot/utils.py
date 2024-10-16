import datetime
import random
import pytz
import asyncio
import json
import sys
import time

class Colors:
    # Source: https://gist.github.com/rene-d/9e584a7dd2935d0f461904b9f2950007
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"
    # cancel SGR codes if we don't write to a terminal
    if not __import__("sys").stdout.isatty():
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        # set Windows console in VT mode
        if __import__("platform").system() == "Windows":
            kernel32 = __import__("ctypes").windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            del kernel32

async def night_sleep():
    makassar_tz = pytz.timezone('Asia/Makassar')  # Menggunakan zona waktu Asia/Makassar
    now = datetime.datetime.now(makassar_tz)
    
    if 0 <= now.hour < 2:  
        sleep_duration = random.randint(7, 10)
        print(f"[!] Saat ini pukul {now.strftime('%H:%M')} di Asia/Makassar. Tidur selama {sleep_duration} jam...")
        await asyncio.sleep(sleep_duration * 3600)  # Menggunakan asyncio.sleep untuk tidur non-blocking
    else:
        print(f"[!] Saat ini pukul {now.strftime('%H:%M')} di Asia/Makassar. Melanjutkan skrip...")
def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
def calc_id(x: int, y: int, x1: int, y1: int):
    px_id = random.randint(min(y, y1), max(y1, y)) * 1000
    px_id += random.randint(min(x, x1), max(x1, x)) + 1
    # print(px_id)
    return px_id
def select_random_pixel(data):
    paint = random.choice(data['data'])
    color = paint['color']
    random_cor = random.choice(paint['cordinates'])
    # print(f"{color}: {random_cor}")
    px_id = calc_id(random_cor['start'][0], random_cor['start'][1], random_cor['end'][0], random_cor['end'][1])

    # Return the selected pixel and its color
    return color, px_id

async def loading_animation(message, duration):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        try:
            sys.stdout.write(f"\r{frames[i % len(frames)]} {message}")
            sys.stdout.flush()
        except UnicodeEncodeError:
            # Fallback ke karakter ASCII jika terjadi error
            sys.stdout.write(f"\r* {message}")
            sys.stdout.flush()
        i += 1
        await asyncio.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

async def progress_bar(current, total, message):
    percent = int(current * 100 / total)
    bar = '█' * percent + '-' * (100 - percent)
    sys.stdout.write(f"\r{message}: |{bar}| {percent}%")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")

def log_message(message, color=Colors.END, status="", end='\n'):
    status_symbol = "[+]" if status == "success" else "[-]" if status == "fail" else "[*]"
    sys.stdout.write(f"{color}{status_symbol} {message}{Colors.END}{end}")
    sys.stdout.flush()
