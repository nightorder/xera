"""
XERA Account Checker - Stable
Ensures file handles are released before moving.
"""
import os
import shutil
import asyncio
from telethon import TelegramClient
from utils.logger import logger
import toml

try:
    with open("config.toml") as file:
        config = toml.load(file)
    api_id = config["authorization"]["api_id"]
    api_hash = config["authorization"]["api_hash"]
except:
    api_id = None
    api_hash = None

async def check_session(session_file):
    path = os.path.join("accs", session_file)
    session_name = session_file
    client = None
    is_valid = False
    
    try:
        client = TelegramClient(path, api_id, api_hash)
        await client.connect()
        
        if await client.is_user_authorized():
            is_valid = True
        else:
            logger.error("Session Invalid", session_name)
            is_valid = False
            
    except Exception as e:
        logger.error(f"Check Error: {e}", session_name)
        is_valid = False
    finally:
        if client:
            await client.disconnect()
            # Explicitly wait a moment for file handle release on Windows
            await asyncio.sleep(0.1)

    return is_valid

async def run_checker():
    logger.info("XERA CHECKER: Validating sessions...", "CHECK")
    
    session_files = [f for f in os.listdir("accs") if f.endswith(".session")]
    if not session_files:
        logger.warning("No sessions found!", "CHECK")
        return

    invalid_files = []
    
    # Check sessions concurrently
    sem = asyncio.Semaphore(20)

    async def _safe_check(s_file):
        async with sem:
            if not await check_session(s_file):
                return s_file
            return None

    tasks = [asyncio.create_task(_safe_check(f)) for f in session_files]
    results = await asyncio.gather(*tasks)
    
    # Collect invalid files after checking ensures no active clients hold the file
    for res in results:
        if res:
            invalid_files.append(res)
            
    # Now move invalid files
    for s_file in invalid_files:
        try:
            src = os.path.join("accs", s_file)
            dst = os.path.join("accs", "invalid", s_file)
            
            # Retry mechanism for moving
            for _ in range(3):
                try:
                    shutil.move(src, dst)
                    break
                except PermissionError:
                    await asyncio.sleep(0.5)
            else:
                logger.error(f"Could not move {s_file} (Locked)", "CHECK")
                
        except Exception as e:
            logger.error(f"Move failed: {e}", s_file)

    valid_count = len(session_files) - len(invalid_files)
    logger.info(f"Checked {len(session_files)} accounts.", "CHECK")
    
    if len(invalid_files) > 0:
        logger.success(f"{valid_count} Valid | {len(invalid_files)} Invalid (Moved to accs/invalid)", "CHECK")
    else:
        logger.success(f"All {valid_count} accounts are VALID.", "CHECK")
