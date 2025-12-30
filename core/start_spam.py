"""
Spam Configuration and Startup - Refactored for stability.

Handles spam configuration prompts and thread launching.
"""
import os
import toml
import time
from raidfunctions import tgraid
from utils.logger import logger

# Load configuration
with open("config.toml") as file:
    config = toml.load(file)

raid_message = config["raid"]["message"]


class Settings:
    """Spam settings and configuration handler."""
    
    def __init__(self, join_chat, username=""):
        self.join_chat = join_chat
        self.username = username
    
    def get_messages(self, msg_type):
        """
        Get messages for spamming.
        
        Args:
            msg_type: 1 for args.txt, 2 for config message
            
        Returns:
            List of messages or single message string
        """
        ms = ""
        
        if msg_type == 1:
            # Load from args.txt
            try:
                with open('args.txt', encoding='utf8') as a:
                    ms = a.read().split('\n')
                    new_ms = []
                    for m in ms:
                        if m:
                            new_ms.append(self.username + " " + m)
                    ms = new_ms
                    logger.debug(f"Loaded {len(ms)} messages from args.txt")
            except FileNotFoundError:
                logger.error("args.txt not found!")
                ms = []
        
        elif msg_type == 2:
            # Use config message
            ms = self.username + " " + raid_message
            logger.debug("Using message from config.toml")
        
        return ms
    
    def start_spam(self):
        """Start spam operation based on settings."""
        tg_accounts = os.listdir('accs')
        logger.info(f"Found {len(tg_accounts)} accounts for spam operation")
        
        if not self.join_chat:
            # Regular spam mode
            answ = tgraid.PrepareRaid().questions()
            mentions = False
            
            if answ[2] == 1:
                # Text spam
                print('''
[1] Spam with sentences from args.txt
[2] Repeat phrase from config.toml\n''')
                msg_type = int(input())
                messages = self.get_messages(msg_type)
                
                mentions_q = int(input("[#] Tag chat members?\n[1] Yes\n[2] No\n"))
                if mentions_q == 1:
                    mentions = True
                
                logger.info(f"Starting text spam with {len(tg_accounts)} accounts")
                
                for account in tg_accounts:
                    logger.info(f"Launching spam thread", account)
                    tgraid.RaidGroup(
                        session_name=account,
                        spam_type=answ[2],
                        files='',
                        messages=messages,
                        chat_id=answ[0],
                        msg_tp=msg_type,
                        speed=answ[1],
                        mentions=mentions
                    ).start()
            
            elif answ[2] == 2:
                # Media spam
                msg_type = int(input('''
[1] Spam with sentences from args.txt
[2] Repeat phrase from config.toml\n'''))
                print('Media for spam is taken from folder "raidfiles"')
                
                messages = self.get_messages(msg_type)
                files = os.listdir('raidfiles')
                
                mentions_q = int(input("[#] Tag chat members?\n[1] Yes\n[2] No\n"))
                if mentions_q == 1:
                    mentions = True
                
                logger.info(f"Starting media spam with {len(files)} files and {len(tg_accounts)} accounts")
                
                for account in tg_accounts:
                    logger.info("Launching spam thread", account)
                    tgraid.RaidGroup(
                        session_name=account,
                        spam_type=answ[2],
                        files=files,
                        messages=messages,
                        chat_id=answ[0],
                        msg_tp=msg_type,
                        speed=answ[1],
                        mentions=mentions
                    ).start()
            
            elif answ[2] == 3:
                # Sticker spam
                logger.info(f"Starting sticker spam with {len(tg_accounts)} accounts")
                
                for account in tg_accounts:
                    logger.info("Launching spam thread", account)
                    tgraid.RaidGroup(
                        session_name=account,
                        spam_type=answ[2],
                        files='',
                        messages=[],
                        chat_id=answ[0],
                        msg_tp=0,
                        speed=answ[1],
                        mentions=False
                    ).start()
            
            logger.success(f"All {len(tg_accounts)} accounts launched successfully!")
        
        else:
            # Join chat mode
            link_to_chat = input('[#] Enter chat link: \n')
            captcha_q = int(input('[#] Solve captcha?\n[1] Yes\n[2] No\n'))
            
            captcha = 0
            if captcha_q == 1:
                captcha = int(input('[?] Captcha type:\n[1] Button\n[2] Math example\n'))
            
            logger.info(f"Starting join operation for {len(tg_accounts)} accounts")
            
            for tg_acc in tg_accounts:
                tgraid.ConfJoin(
                    accs=tg_acc,
                    chat_link=link_to_chat,
                    captcha=captcha
                ).start()
                
                if captcha_q == 1:
                    time.sleep(5)  # Wait between captcha solves
            
            logger.success(f"Join operation completed for {len(tg_accounts)} accounts")
