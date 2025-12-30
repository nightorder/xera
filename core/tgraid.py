import random
import asyncio
import os
import toml
from telethon import functions
from utils.logger import logger
from core.health_manager import health_manager

RAID_DELAY = 0.05
if os.path.exists("config.toml"):
    try:
        data = toml.load("config.toml")
        RAID_DELAY = float(data.get("raid", {}).get("delay", 0.05))
    except: pass

async def spam_worker(client, session_name, target, spam_type, messages, msg_tp, files, speed_mode, reply_to_id=None):
    count = 0
    try:
        try: entity = await client.get_entity(target)
        except:
            try:
                from telethon.tl.functions.channels import JoinChannelRequest
                await client(JoinChannelRequest(target))
                await asyncio.sleep(1)
                entity = await client.get_entity(target)
                logger.success("Auto-joined target!", session_name)
            except:
                logger.error(f"Target not found: {target}", session_name)
                return

        while True:
            if not health_manager.is_active(session_name):
                await asyncio.sleep(5)
                continue

            try:
                msg = random.choice(messages) if msg_tp == 1 else (messages[0] if isinstance(messages, list) else messages)
                if reply_to_id:
                    try: await client.send_message(entity, msg, comment_to=int(reply_to_id))
                    except: await client.send_message(entity, msg, reply_to=int(reply_to_id))
                else: await client.send_message(entity, msg)

                count += 1
                logger.success(f"Sent #{count}", session_name)
                await asyncio.sleep(random.randint(5, 10) if speed_mode == 2 else RAID_DELAY)
                
            except Exception as e:
                health_manager.report_error(session_name, e)
                await asyncio.sleep(1)
    except: pass

async def start_raid(clients, target, spam_type, messages, msg_tp, files, speed_mode, reply_to_id=None):
    logger.info(f"XERA ATTACK: {target} | {len(clients)} Bots", "RAID")
    tasks = [asyncio.create_task(spam_worker(c, n, target, spam_type, messages, msg_tp, files, speed_mode, reply_to_id)) for n, c in clients.items()]
    try: await asyncio.gather(*tasks)
    except asyncio.CancelledError: logger.info("Raid Abandoned", "RAID")
