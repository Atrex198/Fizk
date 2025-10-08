"""
Nonce Database for Replay Attack Prevention
===========================================

Persistent storage of used nonces to prevent proof replay attacks.
Uses SQLite for efficient storage and querying.
"""

import sqlite3
import time
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class NonceDatabase:
    """
    Persistent nonce storage for replay protection
    
    Features:
    - SQLite backend for persistence
    - Fast nonce lookup (indexed)
    - Automatic cleanup of expired nonces
    - Thread-safe operations
    """
    
    def __init__(self, db_path: str = "nonces.db", retention_days: int = 7):
        """
        Initialize nonce database
        
        Args:
            db_path: Path to SQLite database file
            retention_days: Days to keep nonces before cleanup (default: 7)
        """
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()
        logger.info(f"✅ Nonce database initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create database schema"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS used_nonces (
                nonce TEXT PRIMARY KEY,
                timestamp_ns INTEGER NOT NULL,
                client_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        
        # Create indexes for fast lookups
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON used_nonces(timestamp_ns)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_client ON used_nonces(client_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created ON used_nonces(created_at)
        """)
        
        self.conn.commit()
    
    def is_nonce_used(self, nonce: str) -> bool:
        """
        Check if nonce was already used
        
        Args:
            nonce: Nonce to check
            
        Returns:
            True if nonce exists in database, False otherwise
        """
        cursor = self.conn.execute(
            "SELECT 1 FROM used_nonces WHERE nonce = ? LIMIT 1",
            (nonce,)
        )
        result = cursor.fetchone()
        return result is not None
    
    def store_nonce(
        self,
        nonce: str,
        client_id: str,
        round_number: int,
        timestamp_ns: Optional[int] = None
    ):
        """
        Store nonce in database
        
        Args:
            nonce: Nonce to store
            client_id: Client that used this nonce
            round_number: Round number
            timestamp_ns: Proof timestamp (nanoseconds), defaults to current time
        """
        if timestamp_ns is None:
            timestamp_ns = time.time_ns()
        
        created_at = int(time.time())
        
        try:
            self.conn.execute("""
                INSERT INTO used_nonces (nonce, timestamp_ns, client_id, round_number, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (nonce, timestamp_ns, client_id, round_number, created_at))
            self.conn.commit()
            logger.debug(f"Nonce stored: {nonce[:16]}... for {client_id} round {round_number}")
        except sqlite3.IntegrityError:
            logger.warning(f"Nonce {nonce[:16]}... already exists (duplicate insert attempt)")
    
    def cleanup_old_nonces(self):
        """
        Remove nonces older than retention period
        
        Returns:
            Number of nonces deleted
        """
        cutoff_time = int(time.time()) - (self.retention_days * 24 * 3600)
        
        cursor = self.conn.execute(
            "DELETE FROM used_nonces WHERE created_at < ?",
            (cutoff_time,)
        )
        self.conn.commit()
        
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old nonces (older than {self.retention_days} days)")
        
        return deleted
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM used_nonces")
        total_nonces = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(DISTINCT client_id) FROM used_nonces")
        unique_clients = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT MAX(round_number) FROM used_nonces")
        max_round = cursor.fetchone()[0] or 0
        
        return {
            'total_nonces': total_nonces,
            'unique_clients': unique_clients,
            'max_round': max_round,
            'db_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Nonce database connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.conn.close()
        except:
            pass
