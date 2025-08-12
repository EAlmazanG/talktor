#!/usr/bin/env python3
"""
Migration script to update feedback table structure
Drops the old table and creates the new comprehensive feedback table
"""
import sys
import os
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk up from start until a directory containing 'backend' is found."""
    p = start.resolve()
    while p != p.parent:
        if (p / "backend").exists():
            return p
        p = p.parent
    return start.resolve()

# Ensure backend is on sys.path regardless of where the script is executed from
repo_root = _find_repo_root(Path(__file__).parent)
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from db.database import get_db_session, engine
from db.models import Base
from core.logging import get_logger

logger = get_logger(__name__)

def migrate_feedback_table():
    """Drop old feedback table and create new one"""
    try:
        logger.info("🔄 Starting feedback table migration...")
        
        with get_db_session() as db:
            # Drop the old feedback table
            logger.info("🗑️ Dropping old feedback table...")
            db.execute(text("DROP TABLE IF EXISTS feedback CASCADE;"))
            db.commit()
            logger.info("✅ Old feedback table dropped")
            
            # Create new feedback table with updated structure
            logger.info("🏗️ Creating new feedback table...")
            Base.metadata.create_all(engine, tables=[Base.metadata.tables['feedback']])
            logger.info("✅ New feedback table created")
            
            # Verify the new structure
            result = db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'feedback' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            logger.info(f"📊 New feedback table has {len(columns)} columns:")
            for col_name, col_type in columns:
                logger.info(f"   • {col_name}: {col_type}")
            
        logger.info("🎉 Feedback table migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        with get_db_session() as db:
            # Check if new columns exist
            result = db.execute(text("""
                SELECT COUNT(*) as column_count
                FROM information_schema.columns 
                WHERE table_name = 'feedback' 
                AND column_name IN (
                    'feedback_general', 'overall_score',
                    'pronunciation_score', 'pronunciation_resumen',
                    'fluency_score', 'fluency_resumen',
                    'grammar_score', 'grammar_resumen',
                    'expressions_score', 'expressions_resumen',
                    'vocabulary_score', 'vocabulary_resumen',
                    'comprehension_score', 'comprehension_resumen'
                );
            """))
            
            count = result.fetchone()[0]
            expected_columns = 12  # 6 pillars × 2 (score + resumen) + general + overall
            
            if count >= expected_columns:
                logger.info(f"✅ Migration verification passed: {count} key columns found")
                return True
            else:
                logger.error(f"❌ Migration verification failed: only {count} key columns found, expected {expected_columns}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Feedback Table Migration")
    logger.info("=" * 60)
    
    # Run migration
    if migrate_feedback_table():
        # Verify migration
        if verify_migration():
            logger.info("🎉 Migration completed and verified successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)
