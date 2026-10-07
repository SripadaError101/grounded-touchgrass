import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "grounded_journal.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                species_name TEXT NOT NULL,
                scientific_name TEXT,
                confidence REAL,
                location_name TEXT,
                latitude REAL,
                longitude REAL,
                notes TEXT,
                acoustic_data TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expeditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                title TEXT NOT NULL,
                objective TEXT NOT NULL,
                sensory_prompt TEXT,
                duration_mins INTEGER NOT NULL,
                status TEXT DEFAULT 'dispatched',
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def add_observation(
    category: str,
    species_name: str,
    scientific_name: str = "",
    confidence: float = 0.0,
    location_name: str = "Trailside",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    notes: str = "",
    acoustic_data: str = ""
) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO observations (
                timestamp, category, species_name, scientific_name,
                confidence, location_name, latitude, longitude,
                notes, acoustic_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now, category, species_name, scientific_name,
            confidence, location_name, latitude, longitude,
            notes, acoustic_data, now
        ))
        conn.commit()
        return cursor.lastrowid

def get_observations(limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM observations ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_observation(obs_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM observations WHERE id = ?", (obs_id,))
        conn.commit()
        return cursor.rowcount > 0

def add_expedition(
    activity_type: str,
    title: str,
    objective: str,
    sensory_prompt: str,
    duration_mins: int,
    notes: str = ""
) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expeditions (
                timestamp, activity_type, title, objective,
                sensory_prompt, duration_mins, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'dispatched', ?, ?)
        """, (
            now, activity_type, title, objective,
            sensory_prompt, duration_mins, notes, now
        ))
        conn.commit()
        return cursor.lastrowid

def get_expeditions(limit: int = 20) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expeditions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def complete_expedition(expedition_id: int, notes: str = "") -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expeditions SET status = 'completed', notes = ? WHERE id = ?
        """, (notes, expedition_id))
        conn.commit()
        return cursor.rowcount > 0
