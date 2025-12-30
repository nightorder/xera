"""
Leave Functions - Pure Asyncio
"""
import asyncio
from telethon import functions, types
from utils.logger import logger

async def leave_channel(clients, channel_link):
    logger.info(f"Leaving {channel_link}...", "LEAVE")
    
    # We need to resolve entity first? Or just try to leave if joined?
    # Usually better to resolve per client or once.
    # If it's a public username, resolving once is enough.
    # If private link, need join hash? Wait, this is LEAVE.
    # Providing ID or Username.
    
    async def _leave(client, s_name):
        try:
            # Simple approach: try to get entity and leave
            if channel_link.startswith("-100") or channel_link.isdigit():
                 entity = int(channel_link)
            else:
                 entity = channel_link
            
            await client(functions.channels.LeaveChannelRequest(entity))
            logger.success("Left channel", s_name)
        except Exception as e:
            # logger.error(f"Leave failed: {e}", s_name)
            pass

    tasks = [asyncio.create_task(_leave(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)

async def leave_all(clients):
    logger.info("Leaving ALL chats/channels...", "LEAVE")
    
    async def _leave_all(client, s_name):
        try:
            dialogs = await client.get_dialogs()
            count = 0
            for d in dialogs:
                try:
                    if isinstance(d.entity, (types.Channel, types.Chat)):
                        await client(functions.channels.LeaveChannelRequest(d.id))
                        count += 1
                except:
                    pass
            logger.success(f"Left {count} chats", s_name)
        except Exception as e:
            logger.error(f"Error: {e}", s_name)

    tasks = [asyncio.create_task(_leave_all(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)
