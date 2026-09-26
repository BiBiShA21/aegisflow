import os
import sqlite3

def login(username, password):
    # VULNERABILITY 1: Hardcoded Secret!
    API_KEY = "sk_live_1234567890abcdef"
    
    # VULNERABILITY 2: SQL Injection!
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    print(f"Using API Key: {API_KEY}")
    return cursor.fetchone()
