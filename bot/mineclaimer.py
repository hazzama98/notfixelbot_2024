import time
import random
import asyncio
from bot.utils import night_sleep, Colors

async def mine_claimer(NotPxClient, session_name):
    await asyncio.sleep(5)  # Mulai dengan jeda...
    print("[+] {}Proses klaim otomatis dimulai{}.".format(Colors.CYAN, Colors.END))
    while True:
        await night_sleep()  # Periksa dan tidur jika waktu antara 12-1 pagi waktu Iran
        acc_data = NotPxClient.accountStatus()
        
        if acc_data is None:
            print("[!] {}{}{}: {}Gagal mengambil status akun. Mencoba kembali...{}".format(Colors.CYAN, session_name, Colors.END, Colors.RED, Colors.END))
            await asyncio.sleep(5)
            continue
        
        if 'fromStart' in acc_data and 'speedPerSecond' in acc_data:
            fromStart = acc_data['fromStart']
            speedPerSecond = acc_data['speedPerSecond']
            maxMiningTime = acc_data['maxMiningTime'] / 60
            random_recharge_speed = random.randint(30,90)

            if fromStart * speedPerSecond > 0.3:
                claimed_count = round(NotPxClient.claim_mining(), 2)
                print("[+] {}{}{}: {} Token NotPexel {}berhasil ditambang{}.".format(
                    Colors.CYAN, session_name, Colors.END,
                    claimed_count, Colors.GREEN, Colors.END
                ))
        else:
            print("[!] {}{}{}: {}Format data akun tidak sesuai. Mencoba kembali...{}".format(Colors.CYAN, session_name, Colors.END, Colors.RED, Colors.END))
        
        print("[!] {}{}{}: Istirahat selama {} menit...".format(Colors.CYAN, session_name, Colors.END,round((maxMiningTime+random_recharge_speed)/60),2))
        await asyncio.sleep(maxMiningTime+random_recharge_speed)