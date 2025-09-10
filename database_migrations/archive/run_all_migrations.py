#!/usr/bin/env python3
"""
Comprehensive Database Migration Runner for Red Legion Bot
Handles all database schema migrations with tracking and rollback support.
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import glob

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.settings import get_database_url
from database.connection import resolve_database_url
import psycopg2

class MigrationRunner:
    """Handles database migration execution and tracking."""
    
    def __init__(self):
        self.db_url = get_database_url()
        self.migration_dir = Path(__file__).parent
        self.migrations_applied = 0
        self.migrations_skipped = 0
        self.migrations_failed = 0
        
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        if not self.db_url:
            raise Exception("No database URL available")
        
        resolved_url = resolve_database_url(self.db_url)
        conn = psycopg2.connect(resolved_url)
        
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_name VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    execution_time_ms INTEGER
                );
            """)
            conn.commit()
        
        conn.close()
        print("✅ Migration tracking table ready")
    
    def get_applied_migrations(self):
        """Get list of successfully applied migrations."""
        resolved_url = resolve_database_url(self.db_url)
        conn = psycopg2.connect(resolved_url)
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT migration_name 
                FROM schema_migrations 
                WHERE success = TRUE
                ORDER BY applied_at
            """)
            applied = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return applied
    
    def get_migration_files(self):
        """Get sorted list of migration files."""
        pattern = str(self.migration_dir / "*.sql")
        files = glob.glob(pattern)
        
        # Sort by filename (which should include version numbers)
        migration_files = []
        for file_path in sorted(files):
            file_name = Path(file_path).name
            migration_files.append({
                'name': file_name,
                'path': file_path
            })
        
        return migration_files
    
    def apply_migration(self, migration):
        """Apply a single migration file."""
        migration_name = migration['name']
        migration_path = migration['path']
        
        print(f"🔄 Applying migration: {migration_name}")
        
        # Read migration content
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        resolved_url = resolve_database_url(self.db_url)
        conn = psycopg2.connect(resolved_url)
        
        start_time = datetime.now()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
            conn.commit()
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record successful migration
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO schema_migrations (migration_name, success, applied_at, execution_time_ms) 
                    VALUES (%s, TRUE, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (migration_name) 
                    DO UPDATE SET 
                        success = TRUE, 
                        applied_at = CURRENT_TIMESTAMP, 
                        error_message = NULL,
                        execution_time_ms = %s
                """, (migration_name, int(execution_time), int(execution_time)))
            conn.commit()
            
            print(f"✅ Migration {migration_name} applied successfully ({execution_time:.0f}ms)")
            self.migrations_applied += 1
            return True
            
        except Exception as e:
            conn.rollback()
            
            # Record failed migration
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO schema_migrations (migration_name, success, error_message, applied_at) 
                        VALUES (%s, FALSE, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (migration_name) 
                        DO UPDATE SET 
                            success = FALSE, 
                            error_message = %s, 
                            applied_at = CURRENT_TIMESTAMP
                    """, (migration_name, str(e), str(e)))
                conn.commit()
            except Exception as record_error:
                print(f"⚠️ Could not record migration failure: {record_error}")
            
            print(f"❌ Migration {migration_name} failed: {e}")
            self.migrations_failed += 1
            return False
            
        finally:
            conn.close()
    
    def run_migrations(self, force=False):
        """Run all pending migrations."""
        print("🚀 Red Legion Bot - Database Migration Runner")
        print("=" * 50)
        
        try:
            # Ensure migration table exists
            self.ensure_migration_table()
            
            # Get migration files and applied migrations
            migration_files = self.get_migration_files()
            applied_migrations = self.get_applied_migrations()
            
            print(f"📋 Found {len(migration_files)} migration files")
            print(f"📊 Already applied: {len(applied_migrations)} migrations")
            
            # Apply pending migrations
            pending_migrations = []
            for migration in migration_files:
                if migration['name'] not in applied_migrations or force:
                    if migration['name'] in applied_migrations and force:
                        print(f"🔄 Re-applying migration (force): {migration['name']}")
                    pending_migrations.append(migration)
                else:
                    print(f"⏭️ Skipping already applied: {migration['name']}")
                    self.migrations_skipped += 1
            
            if not pending_migrations:
                print("✅ No pending migrations to apply")
                return True
            
            print(f"🎯 Applying {len(pending_migrations)} pending migrations...")
            print("-" * 40)
            
            # Apply each pending migration
            for migration in pending_migrations:
                success = self.apply_migration(migration)
                if not success:
                    # Check if this is a critical migration
                    critical_migrations = [
                        '00_foundation_schema.sql',
                        '05_fix_event_schema_consistency.sql'
                    ]
                    if migration['name'] in critical_migrations:
                        print(f"💥 Critical migration failed: {migration['name']}")
                        print("🛑 Stopping migration process")
                        return False
                    else:
                        print(f"⚠️ Non-critical migration failed, continuing...")
            
            # Summary
            print("-" * 40)
            print("📊 MIGRATION SUMMARY:")
            print(f"✅ Applied: {self.migrations_applied}")
            print(f"⏭️ Skipped: {self.migrations_skipped}")
            print(f"❌ Failed: {self.migrations_failed}")
            
            if self.migrations_failed > 0:
                print("⚠️ Some migrations failed - check logs above")
                return False
            else:
                print("✅ All migrations completed successfully!")
                return True
            
        except Exception as e:
            print(f"💥 Migration runner failed: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def show_migration_status(self):
        """Show current migration status."""
        print("📊 Migration Status Report")
        print("=" * 30)
        
        try:
            self.ensure_migration_table()
            
            resolved_url = resolve_database_url(self.db_url)
            conn = psycopg2.connect(resolved_url)
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT migration_name, success, applied_at, error_message, execution_time_ms
                    FROM schema_migrations 
                    ORDER BY applied_at
                """)
                
                migrations = cursor.fetchall()
                
                if not migrations:
                    print("No migrations recorded in database")
                    return
                
                print(f"Total migrations recorded: {len(migrations)}")
                print("-" * 60)
                
                for migration in migrations:
                    name, success, applied_at, error_msg, exec_time = migration
                    status = "✅" if success else "❌"
                    time_str = f"{exec_time}ms" if exec_time else "N/A"
                    
                    print(f"{status} {name}")
                    print(f"    Applied: {applied_at}")
                    print(f"    Execution time: {time_str}")
                    if not success and error_msg:
                        print(f"    Error: {error_msg}")
                    print()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not retrieve migration status: {e}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Red Legion Bot Database Migration Runner')
    parser.add_argument('--force', action='store_true', 
                       help='Re-apply all migrations even if already applied')
    parser.add_argument('--status', action='store_true',
                       help='Show migration status without running migrations')
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    
    if args.status:
        runner.show_migration_status()
        return
    
    success = runner.run_migrations(force=args.force)
    
    if success:
        print("\n🎉 Database migrations completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Database migrations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()