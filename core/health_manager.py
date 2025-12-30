"""
XERA Health Manager
Manages account health, sleeping (FloodWait), and auto-recovery.
"""
import asyncio
import time
from telethon import TelegramClient
from utils.logger import logger

class HealthManager:
    def __init__(self):
        # {session_name: wake_up_timestamp}
        self.sleeping = {}
        # {session_name: True} - Active
        # {session_name: False} - Dead/Invalid
        self.status = {} 

    def is_active(self, session_name):
        # If sleeping
        if session_name in self.sleeping:
            if time.time() < self.sleeping[session_name]:
                return False
            else:
                # Woke up
                del self.sleeping[session_name]
                logger.success("Account woke up!", session_name)
                return True
        return True

    def report_error(self, session_name, error_msg):
        # FloodWait handling
        if "wait of" in str(error_msg).lower() or "flood" in str(error_msg).lower():
            import re
            # Extract seconds
            secs = 300 # Default
            found = re.findall(r'(\d+) seconds', str(error_msg))
            if found:
                secs = int(found[0])
            
            self.sleeping[session_name] = time.time() + secs
            logger.pending(f"Sleeping for {secs}s (FloodWait)", session_name)
        else:
            # Fatal errors? Or temporary? 
            # "RPCError", "AuthKeyError" -> Fatal
            # "PeerFlood" -> Sleep
            # Fatal errors logic
            err_str = str(error_msg)
            # "You can't write in this chat" / "CHAT_WRITE_FORBIDDEN"
            # "invalid Peer" / "PEER_ID_INVALID"
            # "AuthKey" / "UserDeactivated"
            
            fatal_keywords = ["AuthKey", "UserDeactivated", "can't write", "write in this chat", "invalid Peer", "CHAT_WRITE_FORBIDDEN"]
            
            if any(k in err_str for k in fatal_keywords):
                logger.error(f"Account STOPPED (Fatal/Restricted): {error_msg}", session_name)
                # Mark as dead for this runtime
                self.sleeping[session_name] = time.time() + 999999
            else:
                # Temporary error, sleep short
                self.sleeping[session_name] = time.time() + 60
                logger.pending(f"Temporary Error, sleeping 60s: {error_msg}", session_name)

    async def monitor_loop(self):
        """Runs in background to log wake-ups or maintenance."""
        while True:
            await asyncio.sleep(180) # 3 Minutes
            now = time.time()
            woke = 0
            for s, wake_time in list(self.sleeping.items()):
                if now >= wake_time:
                    del self.sleeping[s]
                    woke += 1
            
            if woke > 0:
                logger.success(f"BACKGROUND: {woke} accounts woke up and rejoined pool.", "HEALTH")

health_manager = HealthManager()
