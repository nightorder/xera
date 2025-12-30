"""
See/View Functions - Refactored for stability.
Safe threading with explicit event loops/async.
"""
import asyncio
import toml
from threading import Thread, Semaphore
from telethon import TelegramClient, functions
from utils.logger import logger

with open("config.toml") as file:
    config = toml.load(file)

api_id = config["authorization"]["api_id"]
api_hash = config["authorization"]["api_hash"]

thread_semaphore = Semaphore(20)

class Channel(Thread):
    def __init__(self, acc, channel, ids, private):
        Thread.__init__(self)
        self.acc = acc
        self.channel = channel
        self.tg_ids = ids
        self.private = private
        self.daemon = True

    def run(self):
        thread_semaphore.acquire()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def worker():
            try:
                target_channel = self.channel
                if self.private:
                    try:
                        target_channel = -1000000000000 - int(self.channel)
                    except:
                        pass

                async with TelegramClient("accs/" + self.acc, api_id, api_hash, loop=loop) as client:
                    await client(functions.messages.GetMessagesViewsRequest(
                        peer=target_channel,
                        id=self.tg_ids,
                        increment=True
                    ))
                    logger.success(f"Viewed {len(self.tg_ids)} messages", self.acc)
            except Exception as e:
                logger.error(f"View failed: {e}", self.acc)
        
        try:
            loop.run_until_complete(worker())
        finally:
            try:
                loop.close()
            except:
                pass
            thread_semaphore.release()
