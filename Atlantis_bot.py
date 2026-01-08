"""
Atlantis AI - Advanced Maritime Logistics Agent
Main Bot File
"""
import os
import time
import telebot
from datetime import datetime
from config import *
from engine import AtlantisEngine
from handlers import *
from utils import PDFGenerator

# Initialize bot and engine
bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)
engine = AtlantisEngine()

# Register all handlers
register_handlers(bot, engine)

# System Launch
if __name__ == "__main__":
    print("=" * 60)
    print("🌊 ATLANTIS ADVANCED SYSTEM INITIALIZING")
    print("=" * 60)
    print(f"[*] AI Provider: Groq")
    print(f"[*] Model: {engine.model}")
    print(f"[*] Port Database: {len([p for ports in PORTS_DATABASE.values() for p in ports])} ports loaded")
    print(f"[*] Carrier Database: {len(CARRIERS_DATABASE)} companies loaded")
    print(f"[*] Document Analyzer: ✅ AI-powered")
    print(f"[*] PDF Generator: {'✅ Ready' if REPORTLAB_AVAILABLE else '❌ Disabled'}")
    
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.get_updates(offset=-1)
        print("[+] Webhook cleared")
    except Exception as e:
        print(f"[!] Warning: {str(e)}")
    
    print("[+] System Ready!")
    print("[+] Atlantis is LIVE")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(non_stop=True, interval=2, timeout=60, long_polling_timeout=60)
        except telebot.apihelper.ApiException as e:
            error_str = str(e)
            if "401" in error_str:
                print("[!] CRITICAL: Invalid Token!")
                break
            elif "409" in error_str:
                print("[!] Another instance running")
                break
            else:
                print(f"[!] API Error: {error_str}")
                time.sleep(10)
        except Exception as e:
            print(f"[!] Error: {str(e)}")
            time.sleep(10)
    
    print("[!] System stopped")
