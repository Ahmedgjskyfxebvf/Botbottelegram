import telebot
from telebot import types
import subprocess
import os
import sqlite3
import time
import psutil
import threading
import sys
import re
import requests

# تثبيت مكتبة Gemini
def install_and_import(package):
    try:
        import(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
install_and_import('google-generativeai')
import google.generativeai as genai

TOKEN = '7943906999:AAFBza-x_iTGvAAoOMNfpmb6P7txg0ULozk'
ADMIN_ID = 7577607150
AI_API_KEY = 'AIzaSyCmKcXSx1qVWh_gAJJVkp2bTmfMr_f5M1Y'
DEV_NAME = "بوخابية أحمد"
SUPPORT_CHANNEL = 'https://t.me/djjhvvsjjccs'
MAX_FILES_PER_USER = 10

genai.configure(api_key=AI_API_KEY)
bot = telebot.TeleBot(TOKEN)
user_states = {}
last_activity = {}

# قاعدة البيانات
conn = sqlite3.connect('pyhost.db', check_same_thread=False)
def db_execute(query, params=(), fetch=False):
    cur = conn.cursor()
    cur.execute(query, params)
    res = cur.fetchall() if fetch else None
    conn.commit()
    cur.close()
    return res

db_execute('''CREATE TABLE IF NOT EXISTS bots
             (user_id INTEGER, bot_name TEXT, bot_file TEXT, is_running INTEGER DEFAULT 0)''')
db_execute('''CREATE TABLE IF NOT EXISTS admins
             (user_id INTEGER PRIMARY KEY)''')
db_execute('''CREATE TABLE IF NOT EXISTS banned
             (user_id INTEGER PRIMARY KEY)''')
db_execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY)''')
db_execute('''CREATE TABLE IF NOT EXISTS disabled_buttons
             (button TEXT PRIMARY KEY, is_disabled INTEGER DEFAULT 0)''')
db_execute(f"INSERT OR IGNORE INTO admins (user_id) VALUES ({ADMIN_ID})")
db_execute(f"INSERT OR IGNORE INTO users (user_id) VALUES ({ADMIN_ID})")

if not os.path.exists('uploaded_bots'):
    os.makedirs('uploaded_bots')

# وظائف مساعدة
def is_admin(user_id): return bool(db_execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,), True))
def is_banned(user_id): return bool(db_execute("SELECT 1 FROM banned WHERE user_id=?", (user_id,), True))
def add_bot(user_id, bot_name, bot_file): db_execute("INSERT INTO bots (user_id, bot_name, bot_file) VALUES (?, ?, ?)", (user_id, bot_name, bot_file))
def delete_bot(user_id, bot_name): db_execute("DELETE FROM bots WHERE user_id=? AND bot_name=?", (user_id, bot_name))
def update_bot_status(bot_name, status): db_execute("UPDATE bots SET is_running=? WHERE bot_name=?", (status, bot_name))
def get_user_bots(user_id): return db_execute("SELECT bot_name, is_running FROM bots WHERE user_id=?", (user_id,), True)
def get_bot_file(bot_name): res = db_execute("SELECT bot_file FROM bots WHERE bot_name=?", (bot_name,), True); return res[0][0] if res else None
def get_bot_owner(bot_name): res = db_execute("SELECT user_id FROM bots WHERE bot_name=?", (bot_name,), True); return res[0][0] if res else None
def stop_bot_process(bot_name):
    stopped = False
    for proc in psutil.process_iter():
        try:
            cmdline = proc.cmdline()
            if len(cmdline) >= 2 and cmdline[0].endswith('python3') and bot_name in cmdline[1]:
                proc.kill()
                stopped = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return stopped

def get_stats():
    total_files = db_execute("SELECT COUNT(*) FROM bots", fetch=True)[0][0]
    total_users = db_execute("SELECT COUNT(*) FROM users", fetch=True)[0][0]
    running_files = db_execute("SELECT COUNT(*) FROM bots WHERE is_running=1", fetch=True)[0][0]
    return total_users, total_files, running_files
def get_all_users():
    return [row[0] for row in db_execute("SELECT user_id FROM users", fetch=True) if row[0] != ADMIN_ID]
def get_all_banned():
    return [row[0] for row in db_execute("SELECT user_id FROM banned", fetch=True)]