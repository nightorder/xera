"""
Polls Functions - Refactored for stability.
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
    def __init__(self, acc, channel, poll_id, variants, private):
        Thread.__init__(self)
        self.acc = acc
        self.channel = channel
        self.poll_id = poll_id
        self.variants = variants
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
                    except: pass

                async with TelegramClient("accs/" + self.acc, api_id, api_hash, loop=loop) as client:
                     # Using bytes for options as required by SendVoteRequest if manual construction
                     # But telethon might wrap it. Let's assume passed variants are strings or ints
                     options = [bytes([int(v)]) for v in self.variants] 
                     
                     await client(functions.messages.SendVoteRequest(
                        peer=target_channel,
                        msg_id=self.poll_id,
                        options=[bytes(v, 'utf-8') for v in self.variants] # Assuming text variants for now or similar
                     ))
                     logger.success("Voted in poll", self.acc)
            except Exception as e:
                logger.error(f"Vote failed: {e}", self.acc)
        
        try:
            loop.run_until_complete(worker())
        finally:
            try:
                loop.close()
            except:
                pass
            thread_semaphore.release()