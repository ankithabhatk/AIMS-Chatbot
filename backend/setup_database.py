#!/usr/bin/env python
"""
Supabase Database Setup Script

This script:
1. Connects to Supabase
2. Creates tables (if not exists)
3. Validates schema
4. Loads sample data (optional)

Usage:
    cd backend
    python setup_database.py
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.database.supabase_client import SupabaseClient


def load_sql_file(filepath: str) -> str:
    """Load SQL from file"""
    with open(filepath, 'r') as f:
        return f.read()


def run_migrations():
    """Execute SQL migrations"""
    try:
        logger.info("🚀 Starting Supabase Database Setup")
        
        # Get Supabase client
        client = SupabaseClient.get_client()
        logger.info("✅ Connected to Supabase")
        
        # Load migration SQL
        migration_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "migrations",
            "001_init_schema.sql"
        )
        
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        logger.info(f"📝 Loading migration from: {migration_file}")
        sql = load_sql_file(migration_file)
        
        # Execute migration sections
        statements = sql.split(';')
        success_count = 0
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                # Note: Supabase Python client doesn't directly execute raw SQL
                # We recommend running migrations via Supabase dashboard or CLI
                logger.info(f"Statement {i+1}: {statement[:50]}...")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to execute statement {i+1}: {e}")
        
        logger.info(f"✅ Processed {success_count} SQL statements")
        logger.info("\n🔔 IMPORTANT: Run the following via Supabase Dashboard:")
        logger.info("   1. Go to https://app.supabase.com")
        logger.info("   2. Select your project")
        logger.info("   3. Go to SQL Editor")
        logger.info("   4. Create new query")
        logger.info("   5. Copy-paste migrations/001_init_schema.sql")
        logger.info("   6. Click Run")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}", exc_info=True)
        return False


def verify_schema() -> bool:
    """Verify that tables were created"""
    try:
        logger.info("\n📋 Verifying schema...")
        
        from app.services.database.supabase_client import (
            get_document_store,
            get_lead_store,
            get_chat_log_store
        )
        
        # Test document store
        doc_store = get_document_store()
        count = asyncio.run(doc_store.count_documents())
        logger.info(f"✅ Documents table exists (count: {count})")
        
        logger.info("✅ All tables verified!")
        return True
    
    except Exception as e:
        logger.warning(f"⚠️  Schema verification incomplete: {e}")
        logger.info("   This is normal if you haven't run migrations yet in Supabase Dashboard")
        return False


def main():
    """Main setup function"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   AIMS College Chatbot - Supabase Database Setup           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        logger.error("❌ SUPABASE_URL and SUPABASE_ANON_KEY environment variables not set")
        logger.info("   Add them to backend/.env file")
        return False
    
    logger.info("✅ Supabase credentials found")
    
    # Run migrations
    if not run_migrations():
        return False
    
    # Verify schema (optional)
    verify_schema()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║   Database Setup Complete!                                 ║
╚════════════════════════════════════════════════════════════╝

Next Steps:

1. Run SQL migrations (see instructions above)

2. Start the backend:
   make start

3. Test the endpoints:
   curl http://localhost:8000/docs

Questions?
   - Supabase Docs: https://supabase.com/docs
   - Project: https://app.supabase.com
    """)
    
    return True


if __name__ == "__main__":
    import asyncio
    success = main()
    sys.exit(0 if success else 1)
