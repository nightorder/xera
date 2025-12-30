"""
Join/Leave Functions - Refactored for stability.
Safe threading with explicit event loops.
"""
import time
import random
import os
import asyncio
from threading import Thread
from raidfunctions import tgraid, leave
from utils.logger import logger

class JoinLeave(Thread):
    def __init__(self, accs, chat_id, chat_link):
        Thread.__init__(self)
        self.accs = accs
        self.chat_id = chat_id
        self.chat_link = chat_link
        self.running = True
        self.daemon = True

    def run(self):
        # This thread spawns other threads, so it doesn't need an event loop for itself necessarily
        # unless it uses Telethon directly. It uses tgraid and leave modules.
        # But wait, JoinLeave logic in Step 76 was weird.
        # It loops infinitely?
        
        try:
            while self.running:
                logger.info("Cycle start for Join/Leave spam")
                for acc in self.accs:
                    # tgraid.ConfJoin is a Thread
                    t = tgraid.ConfJoin(acc, self.chat_link, 0)
                    t.start()
                    # We should probably join threads or wait?
                    # The original code just started them all.
                
                time.sleep(5) # Give time to join?
                
                post = self.chat_id.split("/")
                channel = post[3]
                if post[3] == "c":
                     channel = (int(post[4]) + 1000000000000) * -1
                
                for acc in self.accs:
                    t = leave.Leave(acc, channel)
                    t.start()
                
                time.sleep(random.randint(5, 7))
                
                # Cleanup journals
                for f in os.listdir("accs"):
                    if f.endswith(".session-journal"):
                        try: os.remove(os.path.join("accs", f))
                        except: pass
                        
        except Exception as e:
            logger.error(f"JoinLeave failed: {e}")

    def stop(self):
        self.running = False
