"""

                                                                                                 
                                                                                                 
TTTTTTTTTTTTTTTTTTTTTTTWWWWWWWW                           WWWWWWWWIIIIIIIIIIXXXXXXX       XXXXXXX
T:::::::::::::::::::::TW::::::W                           W::::::WI::::::::IX:::::X       X:::::X
T:::::::::::::::::::::TW::::::W                           W::::::WI::::::::IX:::::X       X:::::X
T:::::TT:::::::TT:::::TW::::::W                           W::::::WII::::::IIX::::::X     X::::::X
TTTTTT  T:::::T  TTTTTT W:::::W           WWWWW           W:::::W   I::::I  XXX:::::X   X:::::XXX
        T:::::T          W:::::W         W:::::W         W:::::W    I::::I     X:::::X X:::::X   
        T:::::T           W:::::W       W:::::::W       W:::::W     I::::I      X:::::X:::::X    
        T:::::T            W:::::W     W:::::::::W     W:::::W      I::::I       X:::::::::X     
        T:::::T             W:::::W   W:::::W:::::W   W:::::W       I::::I       X:::::::::X     
        T:::::T              W:::::W W:::::W W:::::W W:::::W        I::::I      X:::::X:::::X    
        T:::::T               W:::::W:::::W   W:::::W:::::W         I::::I     X:::::X X:::::X   
        T:::::T                W:::::::::W     W:::::::::W          I::::I  XXX:::::X   X:::::XXX
      TT:::::::TT               W:::::::W       W:::::::W         II::::::IIX::::::X     X::::::X
      T:::::::::T                W:::::W         W:::::W          I::::::::IX:::::X       X:::::X
      T:::::::::T                 W:::W           W:::W           I::::::::IX:::::X       X:::::X
      TTTTTTTTTTT                  WWW             WWW            IIIIIIIIIIXXXXXXX       XXXXXXX
                                                                                                 

Twixx Telegram Botu
Bu bot Twixx tarafından yapılmıştır. Hiç bir ücret karşılığı satılamaz.
Tamamen Ücretsizdir.

Created by Twixx
Discord: Kynarix
CheatGlobal: https://cheatglobal.com/members/twixx.64436/
"""

from telethon import TelegramClient, events
import asyncio
import os
import schedule
import time
from datetime import datetime, timedelta
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from collections import deque
from functools import lru_cache
from rich.layout import Layout
from rich.columns import Columns
from rich.traceback import install
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import aiohttp
import uuid
import sqlite3
import aiosqlite
import traceback
import logging

install()

console = Console(record=True)
os.system("title Twix Telegram Bot v1.0") 
console.print("[cyan]Twix Telegram Bot v1.0[/]")

# Telegram API bilgileri
API_ID = '' #api id
API_HASH = '' #api hash
PHONE_NUMBER = '' #telefon numaranızı buraya yazın (+905554443322 gibi)
DOWNLOAD_PATH = './downloads'
MAX_STORAGE_GB = 900
MIN_FREE_SPACE_GB = 1 
MAX_CONCURRENT_DOWNLOADS = 5 
CHUNK_SIZE = 1024 * 1024 
BOT_CREATOR = "Twix"

FILTER_DATE = datetime(2025, 1, 28)  # buraya tarih girin (hangi tarihten sonraki mesajları tarayacak)
CHANNEL_IDS = [
    -1002410689650,
    -1002192829947,
    -1001696596066,
    -1002105943934,
    -1002149777415,
    -1002107853176,
    -1002399362820,
    -1001988659913
]

download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
class LimitedQueue(asyncio.Queue):
    def __init__(self, maxsize=1000):
        super().__init__(maxsize=maxsize)

download_queue = LimitedQueue(maxsize=1000)
processed_messages = deque(maxlen=1000)

client = TelegramClient('TwixLogv1', API_ID, API_HASH)

bot_stats = {
    "taranan_mesaj": 0,
    "indirilen_dosya": 0,
    "atlanan_dosya": 0,
    "toplam_boyut": 0,
    "kanal_istatistikleri": {},
    "aktif_kanal": None,
    "bulunan_txt": 0,
    "son_indirilen": "",
    "depolama_limiti": MAX_STORAGE_GB,
    "kalan_depolama": MAX_STORAGE_GB,
    "indirme_hizi": "0 KB/s",
    "tahmini_sure": "∞",
    "filtrelenen_mesaj": 0,
    "son_tarih": None
}

SCAN_INTERVAL = 6 * 60 * 60
DB_PATH = 'downloads.db'

class DownloadTracker:
    def __init__(self):
        self.active_downloads = {}
    
    def add_download(self, filename, total_size):
        self.active_downloads[filename] = {
            'progress': 0,
            'speed': '0 B/s',
            'size': total_size,
            'start_time': time.time()
        }
        logging.info(f"İndirme başlatıldı: {filename}")
    
    def update_download(self, filename, progress, speed):
        if filename in self.active_downloads:
            self.active_downloads[filename].update({
                'progress': progress,
                'speed': speed
            })
    
    def remove_download(self, filename):
        if filename in self.active_downloads:
            del self.active_downloads[filename]
            logging.info(f"İndirme tamamlandı: {filename}")

download_tracker = DownloadTracker()

logging.basicConfig(
    filename='log.txt',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def init_db():
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logging.info("Eski veritabanı silindi - Twix Bot")
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE downloaded_files (
                    message_id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    download_date TIMESTAMP NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT DEFAULT 'completed',
                    created_by TEXT DEFAULT 'Twix'
                )
            ''')
            await db.commit()
            logging.info("Veritabanı başarıyla oluşturuldu")
            console.print("[green]Veritabanı yeniden oluşturuldu ✓")
    except Exception as e:
        error_msg = f"Veritabanı başlatma hatası: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        console.print(f"[bold red]{error_msg}")
        raise e

async def is_file_downloaded(message_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT filename FROM downloaded_files WHERE message_id = ?', (message_id,))
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        console.print(f"[bold red]Veritabanı kontrol hatası: {str(e)}")
        return False

async def mark_as_downloaded(message_id, filename, channel_id, file_size, file_path):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO downloaded_files 
                (message_id, filename, channel_id, download_date, file_size, file_path, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, filename, channel_id, datetime.now().isoformat(), file_size, file_path, 'completed', BOT_CREATOR))
            await db.commit()
            success_msg = f"✓ Dosya veritabanına kaydedildi: {filename}"
            logging.info(success_msg)
            console.print(f"[green]{success_msg}")
            return True
    except Exception as e:
        error_msg = f"Veritabanı kayıt hatası: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        console.print(f"[bold red]{error_msg}")
        return False

class BotInterface:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=15)
        )
        self.start_time = datetime.now()
        self.live = Live(self.layout, refresh_per_second=4, screen=True, transient=True)
        self.last_message = ""
        self.last_update = time.time()
        self.last_size = 0

    def generate_layout(self):
        header = Table.grid()
        header.add_column(style="bold cyan", justify="center")
        header.add_row(
            Panel(
                f"[bold cyan]Telegram Log Bot by Twix[/] - Çalışma Süresi: {str(datetime.now() - self.start_time).split('.')[0]}\n"
                f"[green]Aktif Kanal:[/] {bot_stats['aktif_kanal']} | "
                f"[yellow]Tarih Filtresi:[/] {FILTER_DATE.strftime('%d.%m.%Y')}\n"
                f"[magenta]Son İşlem:[/] {self.last_message}\n"
            )
        )
        
        stats_table = Table(show_header=True, header_style="bold magenta", title="Genel İstatistikler")
        stats_table.add_column("İstatistik", style="cyan", width=30)
        stats_table.add_column("Değer", justify="right", style="green", width=20)
        stats_table.add_column("Detay", style="yellow", width=30)
        
        total_size_mb = bot_stats["toplam_boyut"] / (1024*1024)
        total_size_gb = total_size_mb / 1024
        
        stats_table.add_row(
            "Taranan/Filtrelenen Mesaj",
            f"{bot_stats['taranan_mesaj']}",
            f"Filtrelenen: {bot_stats['filtrelenen_mesaj']}"
        )
        stats_table.add_row(
            "Bulunan/İndirilen .txt",
            f"{bot_stats['bulunan_txt']}/{bot_stats['indirilen_dosya']}",
            f"Atlanan: {bot_stats['atlanan_dosya']}"
        )
        stats_table.add_row(
            "Toplam İndirilen Boyut",
            f"{total_size_mb:.2f} MB",
            f"{total_size_gb:.2f} GB"
        )
        stats_table.add_row(
            "Depolama Durumu",
            f"{bot_stats['kalan_depolama']:.2f} GB Boş",
            f"Toplam: {bot_stats['toplam_boyut'] / (1024*1024*1024):.2f} / {MAX_STORAGE_GB} GB"
        )
        stats_table.add_row(
            "İndirme Hızı",
            f"{bot_stats['indirme_hizi']}",
            f"Tahmini Süre: {bot_stats['tahmini_sure']}"
        )
        stats_table.add_row(
            "Son İndirilen Dosya",
            f"{bot_stats['son_indirilen'][:30]}...",
            f"Son Tarih: {bot_stats['son_tarih']}"
        )
        stats_table.add_row(
            "İndirme Kuyruğu",
            f"{download_queue.qsize()}/1000",
            f"Bekleyen: {download_queue.qsize()}"
        )
        
        kanal_table = Table(
            show_header=True,
            header_style="bold blue",
            title="Kanal İstatistikleri",
            title_style="bold blue"
        )
        kanal_table.add_column("Kanal ID", style="cyan")
        kanal_table.add_column("Taranan", justify="right", style="green")
        kanal_table.add_column("İndirilen", justify="right", style="green")
        kanal_table.add_column("Atlanan", justify="right", style="yellow")
        kanal_table.add_column("Boyut", justify="right", style="magenta")
        
        for kanal_id, stats in bot_stats["kanal_istatistikleri"].items():
            kanal_table.add_row(
                str(kanal_id),
                str(stats.get("taranan", 0)),
                str(stats.get("indirilen", 0)),
                str(stats.get("atlanan", 0)),
                f"{stats.get('boyut', 0) / (1024*1024):.2f} MB"
            )

        downloads_table = Table(
            show_header=True,
            header_style="bold blue",
            title="Aktif İndirmeler",
            title_style="bold cyan"
        )
        downloads_table.add_column("Dosya Adı", style="cyan", width=40)
        downloads_table.add_column("İlerleme", justify="right", style="green", width=10)
        downloads_table.add_column("Hız", justify="right", style="yellow", width=15)
        downloads_table.add_column("Boyut", justify="right", style="magenta", width=15)
        
        for filename, info in download_tracker.active_downloads.items():
            progress_str = f"{info['progress']}%"
            size_str = _format_size(info['size'])
            downloads_table.add_row(
                filename[:37] + "..." if len(filename) > 40 else filename,
                progress_str,
                info['speed'],
                size_str
            )
        
        self.layout["header"].update(header)
        self.layout["body"].update(
            Panel(
                Columns([
                    stats_table,
                    downloads_table if download_tracker.active_downloads else ""
                ])
            )
        )
        self.layout["footer"].update(Panel(kanal_table))

    def update_progress(self, current_size):
        current_time = time.time()
        time_diff = current_time - self.last_update
        size_diff = current_size - self.last_size
        
        if time_diff > 0:
            speed = size_diff / time_diff
            if speed > 0:
                bot_stats["indirme_hizi"] = _format_speed(speed)
                remaining_size = (bot_stats["bulunan_txt"] - bot_stats["indirilen_dosya"]) * (current_size / (bot_stats["indirilen_dosya"] + 1))
                bot_stats["tahmini_sure"] = _format_time(remaining_size / speed)
            
        self.last_update = current_time
        self.last_size = current_size

    def update_message(self, message):
        self.last_message = message
        self.refresh()

    async def start(self):
        self.live.start()
        
    def stop(self):
        self.live.stop()

    def refresh(self):
        self.generate_layout()

interface = BotInterface()

@lru_cache(maxsize=1000)
async def is_file_exists(file_path):
    return os.path.exists(file_path)

async def process_download_queue():
    while True:
        try:
            message, filename = await download_queue.get()
            async with download_semaphore:
                await download_with_progress(message, filename)
            download_queue.task_done()

            queue_size = download_queue.qsize()
            if queue_size > 0:
                interface.update_message(f"Kuyrukta bekleyen dosya: {queue_size}")
                
        except Exception as e:
            interface.update_message(f"Kuyruk işleme hatası: {str(e)}")

def normalize_channel_id(channel_id: int) -> int:
    return abs(channel_id)

async def init_channel_stats():
    try:
        for channel_id in CHANNEL_IDS:
            positive_id = normalize_channel_id(channel_id)
            if positive_id not in bot_stats["kanal_istatistikleri"]:
                bot_stats["kanal_istatistikleri"][positive_id] = {
                    "taranan": 0,
                    "indirilen": 0,
                    "atlanan": 0,
                    "boyut": 0
                }
        logging.info("Kanal istatistikleri başlatıldı")
    except Exception as e:
        logging.error(f"Kanal istatistikleri başlatma hatası: {str(e)}")
        raise e

async def download_with_progress(message, filename):
    file_path = None
    current_progress = 0
    start_time = time.time()
    
    try:
        if await is_file_downloaded(message.id):
            interface.update_message(f"Dosya zaten indirilmiş: {filename}")
            return

        file_path = os.path.join(DOWNLOAD_PATH, filename)
        
        download_tracker.add_download(filename, message.file.size)
        
        async def progress_callback(current, total):
            nonlocal current_progress
            progress = int(current * 100 / total)
            if progress > current_progress:
                current_progress = progress
                elapsed_time = time.time() - start_time
                speed = current / elapsed_time if elapsed_time > 0 else 0
                speed_str = _format_speed(speed)

                download_tracker.update_download(filename, progress, speed_str)
                interface.update_message(f"İndiriliyor: {filename} - %{progress} - {speed_str}")
                interface.refresh()

        await client.download_media(
            message,
            file_path,
            progress_callback=progress_callback
        )
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            channel_id = normalize_channel_id(message.peer_id.channel_id)
            db_success = await mark_as_downloaded(
                message_id=message.id,
                filename=filename,
                channel_id=channel_id,
                file_size=file_size,
                file_path=file_path
            )
            
            if not db_success:
                error_msg = f"Veritabanına kayıt başarısız: {filename}"
                logging.error(error_msg)
                console.print(f"[bold red]{error_msg}")
                os.remove(file_path)
                return

            bot_stats["indirilen_dosya"] += 1
            bot_stats["toplam_boyut"] += file_size
            bot_stats["son_indirilen"] = filename
            bot_stats["son_tarih"] = message.date.strftime("%d.%m.%Y %H:%M")
            
            if channel_id in bot_stats["kanal_istatistikleri"]:
                bot_stats["kanal_istatistikleri"][channel_id]["boyut"] += file_size
                bot_stats["kanal_istatistikleri"][channel_id]["indirilen"] += 1
            
            success_msg = f"Dosya başarıyla indirildi ve kaydedildi: {filename}"
            logging.info(success_msg)
            interface.update_message(success_msg)
            interface.refresh()

    except Exception as e:
        error_msg = f"İndirme hatası: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        console.print(f"[bold red]{error_msg}")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as del_error:
                logging.error(f"Dosya silme hatası: {str(del_error)}")
    finally:
        download_tracker.remove_download(filename)
        interface.refresh()

async def scan_channel_history(channel_id):

    try:
        positive_id = abs(channel_id)
        interface.update_message(f"Kanal taranıyor: {channel_id}")
        
        async for message in client.iter_messages(channel_id):
            msg_date = message.date.replace(tzinfo=None)
            if msg_date < FILTER_DATE:
                continue
            
            bot_stats["filtrelenen_mesaj"] += 1
            
            if message.id in processed_messages:
                continue
            
            bot_stats["taranan_mesaj"] += 1
            bot_stats["kanal_istatistikleri"][positive_id]["taranan"] += 1
            processed_messages.append(message.id)
            
            if message.media and hasattr(message.media, 'document'):
                file_name = message.file.name
                if not file_name or not file_name.lower().endswith('.txt'):
                    bot_stats["atlanan_dosya"] += 1
                    bot_stats["kanal_istatistikleri"][positive_id]["atlanan"] += 1
                    continue
                
                bot_stats["bulunan_txt"] += 1
                await download_queue.put((message, file_name))
                bot_stats["kanal_istatistikleri"][positive_id]["indirilen"] += 1
            
            interface.refresh()
                    
    except Exception as e:
        error_msg = f"Kanal tarama hatası: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        interface.update_message(f"Kanal tarama hatası: {str(e)}")

async def periodic_scan():
    while True:
        try:
            for channel_id in CHANNEL_IDS:
                bot_stats["aktif_kanal"] = channel_id
                await scan_channel_history(channel_id)
            
            interface.update_message("Tarama tamamlandı. 6 saat bekleniyor...")
            await asyncio.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            interface.update_message(f"Periyodik tarama hatası: {str(e)}")
            await asyncio.sleep(60)

def _format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def _format_speed(speed):
    return _format_size(speed) + "/s"

def _format_time(seconds):
    if seconds == float('inf') or seconds < 0:
        return "∞"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}s {minutes}d"

async def main():
    try:
        console.clear()
        os.system("title Twix Telegram Bot v1.0 - Başlatılıyor...")
        console.print("[bold cyan]Twix Telegram Bot Başlatılıyor...[/]")
        
        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)
            console.print("[green]İndirme klasörü oluşturuldu - Twix ✓[/]")
        await init_db()
        console.print("[green]Veritabanı başlatıldı ✓")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('SELECT 1')
            console.print("[green]Veritabanı bağlantısı başarılı ✓")
        await init_channel_stats()
        console.print("[green]Kanal istatistikleri başlatıldı ✓")
        
        if not await login():
            console.print("[bold red]Giriş başarısız oldu. Program sonlandırılıyor... ✗")
            return
        await check_storage_limit()
        
        await interface.start()
        os.system("title Twix Telegram Bot v1.0 - Çalışıyor") 

        download_workers = [
            asyncio.create_task(process_download_queue())
            for _ in range(MAX_CONCURRENT_DOWNLOADS)
        ]
        
        scan_task = asyncio.create_task(periodic_scan())
        
        await asyncio.gather(
            client.run_until_disconnected(),
            scan_task
        )
    except Exception as e:
        os.system("title Twix Telegram Bot v1.0 - HATA!")
        error_msg = traceback.format_exc()
        console.print(f"[bold red]Program başlatma hatası:[/]\n{error_msg}")
        return

async def check_storage():
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(DOWNLOAD_PATH):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024 * 1024)

async def get_folder_size():
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(DOWNLOAD_PATH):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024 * 1024)

async def check_storage_limit():
    current_size = await get_folder_size()
    bot_stats["toplam_boyut"] = current_size * (1024 * 1024 * 1024)
    bot_stats["kalan_depolama"] = MAX_STORAGE_GB - current_size
    return current_size >= (MAX_STORAGE_GB - MIN_FREE_SPACE_GB)

async def clean_old_files():
    try:
        if not await check_storage_limit():
            return

        files = []
        for dirpath, dirnames, filenames in os.walk(DOWNLOAD_PATH):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                files.append((fp, os.path.getctime(fp)))

        files.sort(key=lambda x: x[1])

        while await check_storage_limit() and files:
            old_file = files.pop(0)[0]
            try:
                file_size = os.path.getsize(old_file)
                os.remove(old_file)
                bot_stats["toplam_boyut"] -= file_size
                interface.update_message(f"Depolama limiti aşıldı. Eski dosya silindi: {os.path.basename(old_file)}")
            except Exception as e:
                interface.update_message(f"Dosya silme hatası: {str(e)}")
                
    except Exception as e:
        interface.update_message(f"Temizleme hatası: {str(e)}")

async def show_stats():
    interface.refresh()

async def login():
    if not client.is_connected():
        await client.connect()
    
    if not await client.is_user_authorized():
        console.print(f"[yellow]Telegram hesabına giriş yapılıyor: {PHONE_NUMBER}")
        try:
            await client.send_code_request(PHONE_NUMBER)
            verification_code = console.input("[bold cyan]Telefonunuza gelen doğrulama kodunu girin: ")
            
            try:
                await client.sign_in(PHONE_NUMBER, verification_code)
            except Exception as e:
                if 'password' in str(e).lower():
                    password = console.input("[bold cyan]İki faktörlü doğrulama şifrenizi girin: ")
                    await client.sign_in(password=password)
                else:
                    raise e
            
            console.print("[bold green]Giriş başarılı! ✓")
        except Exception as e:
            console.print(f"[bold red]Giriş hatası: {str(e)} ✗")
            return False
    
    return True

if __name__ == '__main__':
    try:
        os.system("title Twix Telegram Bot v1.0 - Başlatılıyor...")
        console.print("[bold cyan]Twix Telegram Bot v1.0 Başlatılıyor...[/]")
        asyncio.run(main())
    except KeyboardInterrupt:
        os.system("title Twix Telegram Bot v1.0 - Kapatılıyor...")
        console.print("\n[yellow]Twix Bot kapatılıyor...")
        client.disconnect()
        console.print("[bold green]Twix Bot güvenli bir şekilde kapatıldı. ✓") 