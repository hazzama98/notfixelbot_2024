import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.bot import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
