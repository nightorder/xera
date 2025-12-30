import os
import sys
import toml
import asyncio
import logging
from colorama import Fore, Style, init
from telethon import TelegramClient
from utils.logger import logger
from core.health_manager import health_manager
import core.tgraid as tgraid
import core.additional as additional
import core.leave as leave
import core.report as report
import core.addsticker as addsticker
import core.polls_views as polls_views

init(autoreset=True)
sys.stdout.reconfigure(encoding='utf-8')
logging.getLogger('telethon').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

# LOAD CONFIG
try:
    with open("config.toml") as file: config = toml.load(file)
    api_id = config["authorization"]["api_id"]
    api_hash = config["authorization"]["api_hash"]
except:
    logger.error("Config not error.")
    sys.exit(1)

CLIENTS = {}
SESSION_FILES = []

async def prepare_session_list():
    global SESSION_FILES
    SESSION_FILES = [f for f in os.listdir("accs") if f.endswith(".session")]
    logger.info(f"Loaded {len(SESSION_FILES)} session files.", "INIT")

async def get_active_clients():
    if CLIENTS: return CLIENTS
    if not SESSION_FILES:
        logger.error("No sessions found!", "INIT")
        return {}

    logger.pending(f"Connecting to {len(SESSION_FILES)} nodes...", "INIT")
    sem = asyncio.Semaphore(50)
    
    async def _connect(s_file):
        async with sem:
            try:
                client = TelegramClient(os.path.join("accs", s_file), api_id, api_hash)
                await client.connect()
                if await client.is_user_authorized(): CLIENTS[s_file] = client
                else: await client.disconnect()
            except: pass

    await asyncio.gather(*[asyncio.create_task(_connect(f)) for f in SESSION_FILES])
    
    if not CLIENTS: logger.error("0 sessions connected!", "INIT")
    else: logger.success(f"{len(CLIENTS)} Nodes Active.", "INIT")
    return CLIENTS

async def main_menu():
    logger.banner()
    menu = ["1. Spam User", "2. Spam Group", "3. Spam Comments", "4. Join Chat", "5. Leave Channel", "6. Report Content", "7. Bio Manager", "8. Name Manager", "9. Avatar Manager", "10. View Posts", "11. Vote Poll", "12. Sticker Manager", "0. Exit"]
    for m in menu: print(m)
    print("")

    try:
        choice = await asyncio.to_thread(input, f"{Fore.CYAN}> {Fore.WHITE}")
        if choice == "0": return False
        if choice not in [str(i) for i in range(1, 13)]: return True

        clients = await get_active_clients()
        if not clients: 
            await asyncio.sleep(2)
            return True

        if choice == "1":
            target = await asyncio.to_thread(input, "Target (@username/link): ")
            target = target.split("t.me/")[-1].strip("/") if "t.me/" in target else target
            msg = await asyncio.to_thread(input, "Message: ")
            await tgraid.start_raid(clients, target, 1, [msg], 2, [], 1)
        
        elif choice == "2":
            target = await asyncio.to_thread(input, "Group Link: ")
            msg = await asyncio.to_thread(input, "Message: ")
            await tgraid.start_raid(clients, target, 1, [msg], 2, [], 1)

        elif choice == "3":
            link = await asyncio.to_thread(input, "Post Link: ")
            msg = await asyncio.to_thread(input, "Message: ")
            try:
                parts = link.split("/")
                msg_id = int(parts[-1])
                channel = int("-100" + parts[-2]) if "/c/" in link else parts[-2]
                await tgraid.start_raid(clients, channel, 1, [msg], 2, [], 1, reply_to_id=msg_id)
            except: logger.error("Invalid link")

        elif choice == "4":
            link = await asyncio.to_thread(input, "Link: ")
            from telethon.tl.functions.channels import JoinChannelRequest
            from telethon.tl.functions.messages import ImportChatInviteRequest
            logger.info("Joining...", "XERA")
            async def _j(c, s):
                try:
                    if "joinchat" in link or "+" in link:
                        await c(ImportChatInviteRequest(link.split("+")[-1] if "+" in link else link.split("joinchat/")[-1]))
                    else: await c(JoinChannelRequest(link))
                    logger.success("Joined", s)
                except Exception as e: health_manager.report_error(s, e)
            await asyncio.gather(*[asyncio.create_task(_j(c, n)) for n, c in clients.items()])

        elif choice == "5":
            link = await asyncio.to_thread(input, "Link: ")
            await leave.leave_channel(clients, link.split("t.me/")[-1].strip("/") if "t.me/" in link else link)

        elif choice == "6":
            link = await asyncio.to_thread(input, "Post Link: ")
            reason = int(await asyncio.to_thread(input, "Reason (0-6): "))
            comment = await asyncio.to_thread(input, "Comment: ")
            try:
                parts = link.split("/")
                pid, channel = int(parts[-1]), (int("-100" + parts[-2]) if "/c/" in link else parts[-2])
                await report.report_spam(clients, channel, [pid], reason, comment)
            except: logger.error("Invalid link")

        elif choice == "7":
            bio = await asyncio.to_thread(input, "Bio: ")
            await additional.update_bio(clients, bio)

        elif choice == "8":
            try:
                n, s = [], []
                for fn in ["names.txt", "name.txt"]:
                    if os.path.exists(fn): 
                        with open(fn, encoding='utf-8') as f: n = f.read().splitlines(); break
                for fs in ["surnames.txt", "surname.txt"]:
                    if os.path.exists(fs):
                        with open(fs, encoding='utf-8') as f: s = f.read().splitlines(); break
                if not n and not s: logger.error("Names file missing!")
                else: await additional.update_name(clients, n, s)
            except: logger.error("Read error")

        elif choice == "10":
            link = await asyncio.to_thread(input, "Post Link: ")
            try:
                parts = link.split("/")
                msg_id, channel = int(parts[-1]), (int("-100" + parts[-2]) if "/c/" in link else parts[-2])
                await polls_views.view_messages(clients, channel, [msg_id])
            except: logger.error("Invalid link")

        elif choice == "11":
            link = await asyncio.to_thread(input, "Poll Link: ")
            opt = await asyncio.to_thread(input, "Option Indices (0,1): ")
            try:
                parts = link.split("/")
                msg_id, channel = int(parts[-1]), (int("-100" + parts[-2]) if "/c/" in link else parts[-2])
                await polls_views.vote_poll(clients, channel, msg_id, opt.split(","))
            except: logger.error("Invalid link")

        elif choice == "12":
            print(f"\n{Fore.CYAN}1. Add Pack\n2. Delete All{Fore.WHITE}")
            sub = await asyncio.to_thread(input, "> ")
            if sub == "1":
                link = await asyncio.to_thread(input, "Link/Name: ")
                await addsticker.add_stickers(clients, link.split("addstickers/")[-1] if "addstickers/" in link else link)
            elif sub == "2": await addsticker.remove_stickers(clients)

        elif choice == "9": await additional.update_avatar(clients)

    except KeyboardInterrupt:
        logger.warning("\nCancelled. Returning to menu...", "SYSTEM")
        await asyncio.sleep(1)
    except Exception as e: logger.error(f"Error: {e}")
    return True

async def shutdown():
    logger.info("Shutting down...", "SYSTEM")
    if CLIENTS:
        for c in CLIENTS.values():
            try: await c.disconnect()
            except: pass
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks: t.cancel()
    if tasks: await asyncio.gather(*tasks, return_exceptions=True)

async def startup_sequence():
    for d in ["accs/invalid", "raidfiles", "avatars", "stickers", "logs"]: os.makedirs(d, exist_ok=True)
    await prepare_session_list()
    monitor = asyncio.create_task(health_manager.monitor_loop())
    try:
        while True:
            if not await main_menu(): break
    finally:
        monitor.cancel()
        await shutdown()

def exception_handler(loop, context):
    if "Event loop is closed" in str(context.get("exception", "")) or "Task was destroyed" in str(context.get("exception", "")): return
    logger.debug(f"Async Error: {context.get('exception', context['message'])}")

def main():
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(exception_handler)
        loop.run_until_complete(startup_sequence())
    except: pass
    finally:
        try:
            for t in asyncio.all_tasks(loop): t.cancel()
            loop.close()
        except: pass

if __name__ == "__main__": main()
