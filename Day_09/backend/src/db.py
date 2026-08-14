import sqlite3
import json
from datetime import datetime

DB_PATH = "memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_caller(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": json.loads(row[3]) if row[3] else {},
            "last_interaction": row[4]
        }
    return None

def save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    c.execute("SELECT facts FROM callers WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    
    if row:
        existing_facts = json.loads(row[0]) if row[0] else {}
        existing_facts.update(facts)
        facts_str = json.dumps(existing_facts)
        
        c.execute('''
            UPDATE callers
            SET name = ?, language_preference = ?, facts = ?, last_interaction = ?
            WHERE user_id = ?
        ''', (name, language_preference, facts_str, now, user_id))
    else:
        facts_str = json.dumps(facts)
        c.execute('''
            INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, language_preference, facts_str, now))
        
    conn.commit()
    conn.close()
