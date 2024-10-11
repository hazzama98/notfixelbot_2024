import random
from bot.utils import night_sleep, Colors, load_data_from_json, select_random_pixel
import asyncio
import config
import os

async def painters(NotPxClient, session_name):
    print("[+] {}Proses pengecatan otomatis dimulai{}.".format(Colors.CYAN, Colors.END))
    while True:
        try:
            await night_sleep()  # Assuming night_sleep is a blocking function; handle this accordingly
            user_status = NotPxClient.accountStatus()
            if not user_status:
                await asyncio.sleep(5)  # Use await for asyncio.sleep
                continue

            charges = user_status['charges']
            balance = user_status['userBalance']
            levels_recharge = user_status['boosts']['reChargeSpeed'] + 1
            
            if charges > 0:
                if config.X3_PIXEl:
                    data = load_data_from_json(os.path.dirname(os.path.abspath(__file__))+'/data/data.json')
                    for _ in range(charges):
                        color,pixelid = select_random_pixel(data)
                        # pixelid = (y* 1000) + x+1
                        
                        # print(pixelid)
                        pixelstatus = NotPxClient.pixelStatus(pixelid)
                        pixelcolor = pixelstatus['pixel']['color']
                        # print(pixelstatus)
                        if pixelcolor != color:
                            balance = NotPxClient.paintPixel(pixelid, color)
                            print("[+] {}{}{}: 1 {}Piksel berhasil dicat{}. Saldo Terbaru: {}{}{}".format(
                                Colors.CYAN, session_name, Colors.END,
                                Colors.GREEN, Colors.END,
                                Colors.GREEN, balance, Colors.END
                            ))
                        else:
                            print("[+] {}{}{}: 0 {}Piksel tidak berhasil dicat{}. Mencoba piksel baru! Saldo pengguna: {}{}{}".format(
                                Colors.CYAN, session_name, Colors.END,
                                Colors.RED, Colors.END,
                                Colors.GREEN, balance, Colors.END
                            ))
                        t = random.randint(1, 10)
                        print("[!] {}{} anti-deteksi{}: Istirahat selama {} detik...".format(Colors.CYAN, session_name, Colors.END, t))
                        await asyncio.sleep(t)  # Awaiting asyncio.sleep
                else:
                    for _ in range(charges):
                        balance = NotPxClient.autoPaintPixel()
                        print("[+] {}{}{}: 1 {}Piksel berhasil dicat{}. Saldo Terbaru: {}{}{}".format(
                            Colors.CYAN, session_name, Colors.END,
                            Colors.GREEN, Colors.END,
                            Colors.GREEN, balance, Colors.END
                        ))
                        t = random.randint(1, 10)
                        print("[!] {}{} anti-deteksi{}: Istirahat selama {} detik...".format(Colors.CYAN, session_name, Colors.END, t))
                        await asyncio.sleep(t)  # Awaiting asyncio.sleep
            else:
                recharge_speed = user_status['reChargeSpeed'] / 1000
                random_recharge_speed = random.randint(10, 60)
                print("[!] {}{}{}: {}Tidak ada muatan tersedia{}. Istirahat selama {} menit...".format(
                    Colors.CYAN, session_name, Colors.END,
                    Colors.YELLOW, Colors.END,
                    round(((recharge_speed + random_recharge_speed) / 60), 2)
                ))
                await asyncio.sleep(recharge_speed + random_recharge_speed)  # Awaiting asyncio.sleep
        except Exception as e:
            print(e)
            print(f"[!] {Colors.RED}Kesalahan{Colors.END} {session_name}. Mencoba kembali dalam 5 detik...")
            await asyncio.sleep(5)  # Awaiting asyncio.sleep
