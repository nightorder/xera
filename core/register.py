"""
Registration Module - Async
"""
import datetime
import re
import os
import asyncio
from telethon import TelegramClient, functions
from utils.logger import logger
import toml

with open("config.toml") as file:
    config = toml.load(file)
api_id = config["authorization"]["api_id"]
api_hash = config["authorization"]["api_hash"]

async def register_session(session_name):
    """Interactive registration (Note: Difficult to do fully async with blocking inputs for code)"""
    client = TelegramClient(f"accs/{session_name}", api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        phone = await asyncio.to_thread(input, "Phone number: ")
        try:
            await client.send_code_request(phone)
            code = await asyncio.to_thread(input, "Enter code: ")
            await client.sign_in(phone, code)
            logger.success("Authorized!", session_name)
        except Exception as e:
             logger.error(f"Auth failed: {e}", session_name)
    else:
        logger.success("Already authorized", session_name)
    
    await client.disconnect()

async def get_otp_code(session_name):
    # Logic to get OTP from 777000
    pass 
