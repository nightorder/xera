import sys
import os
import datetime
import toml
from colorama import Fore, Style, init

init(autoreset=True)

# LOAD CONFIG
LOG_CONFIG = {"level": "INFO", "file_output": False, "file_path": "logs/raid.log"}
BANNER_TEXT = "XERA CORE v2.0"

try:
    if os.path.exists("config.toml"):
        data = toml.load("config.toml")
        LOG_CONFIG.update(data.get("logging", {}))
        BANNER_TEXT = data.get("theme", {}).get("banner_text", BANNER_TEXT)
except:
    pass

LEVELS = {"DEBUG": 10, "INFO": 20, "SUCCESS": 25, "WARNING": 30, "ERROR": 40}
CURRENT_LEVEL = LEVELS.get(LOG_CONFIG["level"].upper(), 20)

class Logger:
    def __init__(self):
        self.file_enabled = LOG_CONFIG["file_output"]
        self.file_path = LOG_CONFIG["file_path"]
        if self.file_enabled:
            log_dir = os.path.dirname(self.file_path) or "logs"
            os.makedirs(log_dir, exist_ok=True)
            self.file_path = os.path.join(log_dir, f"debug_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

    def _log(self, level_name, tag, session, text, color):
        level_val = LEVELS.get(level_name, 20)
        
        if self.file_enabled:
            try:
                if datetime and sys:
                    timestamp_file = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    clean_text = f"{timestamp_file} | {level_name:<7} | {session:<15} | {text}\n"
                    with open(self.file_path, "a", encoding="utf-8") as f:
                        f.write(clean_text)
            except: pass

        if level_val < CURRENT_LEVEL:
            return

        timestamp_console = datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        s_clean = session.replace(".session", "")
        if s_clean == "SYSTEM": s_clean = "SYS"
        
        status_map = {"INFO": "Info", "SUCCESS": "Success", "WARNING": "Pending", "PENDING": "Pending", "ERROR": "Error", "DEBUG": "Debug"}
        status = status_map.get(tag, tag)
        status_part = f"{color}Status [{status}]{Fore.WHITE}"
        
        print(f"{Fore.WHITE}{timestamp_console} {s_clean} - {status_part} - {text}")

    def debug(self, text, session="SYSTEM"): self._log("DEBUG", "DEBUG", session, text, Fore.MAGENTA)
    def info(self, text, session="SYSTEM"): self._log("INFO", "INFO", session, text, Fore.WHITE)
    def success(self, text, session="SYSTEM"): self._log("SUCCESS", "SUCCESS", session, text, Fore.GREEN)
    def warning(self, text, session="SYSTEM"): self._log("WARNING", "WARNING", session, text, Fore.YELLOW)
    def pending(self, text, session="SYSTEM"): self._log("INFO", "PENDING", session, text, Fore.YELLOW)
    def error(self, text, session="SYSTEM"): self._log("ERROR", "ERROR", session, text, Fore.RED)

    def banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{Fore.CYAN}{BANNER_TEXT} {Fore.YELLOW}[STABLE]{Style.RESET_ALL}\n")

logger = Logger()
