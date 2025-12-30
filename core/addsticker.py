"""
Add/Remove Stickers - Pure Asyncio
"""
import asyncio
from telethon import functions, types
from telethon.tl.functions.messages import GetAllStickersRequest
from utils.logger import logger

async def add_stickers(clients, pack_shortname):
    logger.info(f"Adding sticker pack {pack_shortname}...", "STICKER")
    
    async def _add(client, s_name):
        try:
            # Resolving stickerset by shortname
            stickerset = types.InputStickerSetShortName(short_name=pack_shortname)
            await client(functions.messages.InstallStickerSetRequest(
                stickerset=stickerset,
                archived=False
            ))
            logger.success("Added pack", s_name)
        except Exception as e:
            logger.error(f"Add failed: {e}", s_name)

    tasks = [asyncio.create_task(_add(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)

async def remove_stickers(clients):
    logger.info("Removing all sticker packs...", "STICKER")
    
    async def _remove(client, s_name):
        try:
            sets = await client(GetAllStickersRequest(0))
            for s in sets.sets:
                await client(functions.messages.UninstallStickerSetRequest(
                    stickerset=types.InputStickerSetID(id=s.id, access_hash=s.access_hash)
                ))
            logger.success("Cleaned stickers", s_name)
        except Exception as e:
            logger.error(f"Remove failed: {e}", s_name)

    tasks = [asyncio.create_task(_remove(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)
