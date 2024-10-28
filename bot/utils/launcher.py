import asyncio
import argparse
import sys
import os
import time
from random import randint
from typing import Any
from better_proxy import Proxy
from colorama import Fore, Style, init
import base64
import json
import requests
import aiohttp

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions, get_tg_client
from bot.utils.accounts import Accounts
from bot.utils.firstrun import load_session_names

init(autoreset=True)

art_work = Fore.BLUE + """
╔═══════════════════════════════════════════╗
║              Bot Automation               ║
║         Developed by @ItbaArts_Dev        ║
╚═══════════════════════════════════════════╝                                
""" + Style.RESET_ALL

async def loading_animation(message, duration):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        try:
            sys.stdout.write(f"\r{frames[i % len(frames)]} {message}")
            sys.stdout.flush()
        except UnicodeEncodeError:
            sys.stdout.write(f"\r* {message}")
            sys.stdout.flush()
        i += 1
        await asyncio.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

async def key_bot():
    url = base64.b64decode("aHR0cDovL2l0YmFhcnRzLmNvbS9hcGkuanNvbg==").decode('utf-8')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                try:
                    data = await response.json()
                    header = data['header']
                    print(header)
                except json.JSONDecodeError:
                    text = await response.text()
                    print(text)
    except Exception as e:
        print_(f"Failed to load header")
        
            
def log_message(message, color=Style.RESET_ALL, status="", end='\n'):
    status_symbol = "[⚔]" if status == "success" else "[-]" if status == "fail" else "[*]"
    sys.stdout.write(f"{color}{status_symbol} {message}{Style.RESET_ALL}{end}")
    sys.stdout.flush()

async def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


start_text = f"""
{Fore.CYAN}╔════════════════════════════════════════════╗
║           Choose Action:                   ║
║                                            ║
║   {Fore.GREEN}[1]{Fore.CYAN} Run Bot                              ║
║   {Fore.GREEN}[2]{Fore.CYAN} Create New Session                   ║
║                                            ║
╚════════════════════════════════════════════╝{Style.RESET_ALL}
"""


def get_proxy(raw_proxy: str) -> Proxy:
    return Proxy.from_str(proxy=raw_proxy).as_url if raw_proxy else None


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    action = parser.parse_args().action

    if not action:
        await clear_terminal()
        await key_bot()

        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                log_message("Action must be number", color=Fore.YELLOW, status="fail")
            elif action not in ["1", "2"]:
                log_message("Action must be 1 or 2", color=Fore.YELLOW, status="fail")
            else:
                action = int(action)
                break

    used_session_names = load_session_names()

    if action == 2:
        await register_sessions()
    elif action == 1:
        accounts = await Accounts().get_accounts()
        await run_tasks(accounts=accounts, used_session_names=used_session_names)


async def run_tasks(accounts: [Any, Any, list], used_session_names: [str]):
    # Tambahkan animasi loading
    await loading_animation("Preparing tasks...", 3)

    tasks = []
    for account in accounts:
        session_name, user_agent, raw_proxy = account.values()
        first_run = session_name not in used_session_names
        tg_client = await get_tg_client(session_name=session_name, proxy=raw_proxy)
        proxy = get_proxy(raw_proxy=raw_proxy)
        tasks.append(asyncio.create_task(run_tapper(tg_client=tg_client, user_agent=user_agent, proxy=proxy, first_run=first_run)))
        await asyncio.sleep(randint(5, 20))

    await asyncio.gather(*tasks)
