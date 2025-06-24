import sqlite3
import os
from typing import Dict, List, Optional

def initialize_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            profile_complete BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            age_group TEXT,
            income_range TEXT,
            savings_style TEXT,
            marital_status TEXT,
            financial_style TEXT,
            monthly_expenses TEXT,
            investment_experience TEXT,
            debt_status TEXT,
            financial_goals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            category TEXT,
            subcategory TEXT,
            date DATE NOT NULL,
            source TEXT,
            raw_text TEXT,
            ai_confidence REAL,
            location TEXT,
            merchant TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # AI insights table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            priority INTEGER DEFAULT 1,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recommendation_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            action_items TEXT,
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Gmail integration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmail_integration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email_id TEXT UNIQUE NOT NULL,
            subject TEXT,
            sender TEXT,
            body TEXT,
            processed BOOLEAN DEFAULT FALSE,
            transaction_extracted BOOLEAN DEFAULT FALSE,
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # SMS integration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sms_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            transaction_extracted BOOLEAN DEFAULT FALSE,
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_user_profile(user_id: int) -> Optional[Dict]:
    """Get user profile data"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM user_profiles WHERE user_id = ?
        """, (user_id,))
        
        profile_data = cursor.fetchone()
        
        if profile_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, profile_data))
        
        return None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def save_user_profile(user_id: int, profile_data: Dict):
    """Save user profile data"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        # Check if profile exists
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE user_profiles SET
                name = ?, age_group = ?, income_range = ?, savings_style = ?,
                marital_status = ?, financial_style = ?, monthly_expenses = ?,
                investment_experience = ?, debt_status = ?, financial_goals = ?
                WHERE user_id = ?
            """, (
                profile_data.get('name'),
                profile_data.get('age_group'),
                profile_data.get('income_range'),
                profile_data.get('savings_style'),
                profile_data.get('marital_status'),
                profile_data.get('financial_style'),
                profile_data.get('monthly_expenses'),
                profile_data.get('investment_experience'),
                profile_data.get('debt_status'),
                profile_data.get('financial_goals'),
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profiles 
                (user_id, name, age_group, income_range, savings_style, marital_status,
                 financial_style, monthly_expenses, investment_experience, debt_status, financial_goals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                profile_data.get('name'),
                profile_data.get('age_group'),
                profile_data.get('income_range'),
                profile_data.get('savings_style'),
                profile_data.get('marital_status'),
                profile_data.get('financial_style'),
                profile_data.get('monthly_expenses'),
                profile_data.get('investment_experience'),
                profile_data.get('debt_status'),
                profile_data.get('financial_goals')
            ))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def save_transaction(user_id: int, transaction_data: Dict):
    """Save transaction data"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, transaction_type, amount, description, category, subcategory,
             date, source, raw_text, ai_confidence, location, merchant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            transaction_data.get('transaction_type'),
            transaction_data.get('amount'),
            transaction_data.get('description'),
            transaction_data.get('category'),
            transaction_data.get('subcategory'),
            transaction_data.get('date'),
            transaction_data.get('source'),
            transaction_data.get('raw_text'),
            transaction_data.get('ai_confidence'),
            transaction_data.get('location'),
            transaction_data.get('merchant')
        ))
        
        conn.commit()
        return cursor.lastrowid
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_user_transactions(user_id: int, limit: int = 100) -> List[Dict]:
    """Get user transactions"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC, created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        transactions = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, transaction)) for transaction in transactions]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def save_ai_insight(user_id: int, insight_data: Dict):
    """Save AI insight"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO ai_insights 
            (user_id, insight_type, title, description, category, priority, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            insight_data.get('insight_type'),
            insight_data.get('title'),
            insight_data.get('description'),
            insight_data.get('category'),
            insight_data.get('priority', 1),
            insight_data.get('confidence')
        ))
        
        conn.commit()
        return cursor.lastrowid
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_user_insights(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user AI insights"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM ai_insights 
            WHERE user_id = ? 
            ORDER BY priority DESC, created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        insights = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, insight)) for insight in insights]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def delete_transaction(transaction_id: int):
        """Delete a transaction by ID"""
        conn = sqlite3.connect('finai.db')
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Delete error: {e}")
        finally:
            conn.close()

