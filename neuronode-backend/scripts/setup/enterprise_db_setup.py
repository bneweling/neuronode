#!/usr/bin/env python3
"""
Enterprise Neo4j Database Setup Script
Provides comprehensive database initialization for production environments
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.storage.neo4j_client import Neo4jClient
    from src.config.settings import settings
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("💡 Make sure you're running from the neuronode-backend directory")
    print("💡 And that all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enterprise_db_setup.log', mode='a') if Path('logs').exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseDBSetup:
    """Enterprise-grade database setup with validation and monitoring"""
    
    def __init__(self):
        self.neo4j_client = None
        self.setup_stats = {
            "start_time": time.time(),
            "operations": [],
            "errors": [],
            "warnings": []
        }
    
    def run_setup(self, force_reload: bool = False, validate_only: bool = False):
        """Run complete enterprise database setup"""
        logger.info("🚀 Starting Enterprise Neo4j Database Setup")
        logger.info(f"📋 Configuration: force_reload={force_reload}, validate_only={validate_only}")
        
        try:
            # Step 1: Initialize connection
            self._initialize_connection()
            
            # Step 2: Validate or setup database
            if validate_only:
                return self._validate_database()
            else:
                return self._setup_database(force_reload)
                
        except Exception as e:
            logger.error(f"❌ Enterprise setup failed: {e}")
            self.setup_stats["errors"].append(str(e))
            return False
        finally:
            self._generate_setup_report()
            if self.neo4j_client:
                self.neo4j_client.close()
    
    def _initialize_connection(self):
        """Initialize Neo4j connection with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Connecting to Neo4j (attempt {attempt}/{max_retries})")
                logger.info(f"   URI: {settings.neo4j_uri}")
                logger.info(f"   User: {settings.neo4j_user}")
                
                self.neo4j_client = Neo4jClient()
                
                # Test basic connectivity
                with self.neo4j_client.driver.session() as session:
                    result = session.run("RETURN 'Connection successful' as message")
                    message = result.single()["message"]
                
                logger.info(f"✅ Neo4j connection established: {message}")
                self.setup_stats["operations"].append("connection_established")
                return
                
            except Exception as e:
                logger.warning(f"⚠️ Connection attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"Failed to connect to Neo4j after {max_retries} attempts: {e}")
    
    def _validate_database(self) -> bool:
        """Comprehensive database validation"""
        logger.info("🔍 Running comprehensive database validation...")
        
        validation_results = {
            "connectivity": False,
            "schema_complete": False,
            "data_present": False,
            "functional": False
        }
        
        try:
            # Get health status using the enhanced Neo4j client
            health_status = self.neo4j_client.get_health_status()
            
            validation_results["connectivity"] = health_status["is_connected"]
            validation_results["schema_complete"] = health_status["schema_status"] == "complete"
            validation_results["data_present"] = not health_status["is_empty"]
            validation_results["functional"] = health_status["is_functional"]
            
            # Log detailed results
            logger.info("📊 Validation Results:")
            logger.info(f"   ✅ Connectivity: {validation_results['connectivity']}")
            logger.info(f"   ✅ Schema Complete: {validation_results['schema_complete']}")
            logger.info(f"   ✅ Data Present: {validation_results['data_present']}")
            logger.info(f"   ✅ Functional: {validation_results['functional']}")
            
            if health_status["node_counts"]:
                logger.info("📈 Database Statistics:")
                for label, count in health_status["node_counts"].items():
                    logger.info(f"   - {label}: {count} nodes")
            
            if health_status["relationship_counts"]:
                logger.info("🔗 Relationship Statistics:")
                for rel_type, count in health_status["relationship_counts"].items():
                    logger.info(f"   - {rel_type}: {count} relationships")
            
            overall_health = all(validation_results.values())
            
            if overall_health:
                logger.info("🎉 Database validation PASSED - System is production ready!")
            else:
                logger.warning("⚠️ Database validation FAILED - Manual setup required")
                
            self.setup_stats["operations"].append(f"validation_{'passed' if overall_health else 'failed'}")
            return overall_health
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.setup_stats["errors"].append(f"validation_error: {e}")
            return False
    
    def _setup_database(self, force_reload: bool) -> bool:
        """Setup database with schema and data"""
        logger.info("🛠️ Setting up enterprise database...")
        
        try:
            # Check current state
            health_status = self.neo4j_client.get_health_status()
            
            if health_status["is_functional"] and not force_reload:
                logger.info("✅ Database is already functional - skipping setup")
                logger.info("💡 Use --force-reload to reinitialize anyway")
                return True
            
            if force_reload and not health_status["is_empty"]:
                logger.warning("🔄 Force reload requested - clearing existing data...")
                self._clear_database()
            
            # The Neo4j client auto-initialization should handle everything
            # But we can force a re-initialization here
            logger.info("🔧 Re-initializing database with enterprise features...")
            
            # Force re-initialization by creating a new client
            self.neo4j_client.close()
            self.neo4j_client = Neo4jClient()  # This triggers _ensure_database_ready()
            
            # Validate the setup
            return self._validate_database()
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            self.setup_stats["errors"].append(f"setup_error: {e}")
            return False
    
    def _clear_database(self):
        """Clear all data from database (use with caution!)"""
        logger.warning("⚠️ CLEARING ALL DATABASE DATA - This cannot be undone!")
        
        with self.neo4j_client.driver.session() as session:
            # Remove all relationships and nodes
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("🗑️ All nodes and relationships deleted")
            
        self.setup_stats["operations"].append("database_cleared")
    
    def _generate_setup_report(self):
        """Generate comprehensive setup report"""
        duration = time.time() - self.setup_stats["start_time"]
        
        logger.info("📋 Enterprise Database Setup Report")
        logger.info("=" * 50)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Operations: {len(self.setup_stats['operations'])}")
        logger.info(f"Errors: {len(self.setup_stats['errors'])}")
        logger.info(f"Warnings: {len(self.setup_stats['warnings'])}")
        
        if self.setup_stats["operations"]:
            logger.info("\n✅ Completed Operations:")
            for op in self.setup_stats["operations"]:
                logger.info(f"   - {op}")
        
        if self.setup_stats["errors"]:
            logger.info("\n❌ Errors:")
            for error in self.setup_stats["errors"]:
                logger.info(f"   - {error}")
        
        if self.setup_stats["warnings"]:
            logger.info("\n⚠️ Warnings:")
            for warning in self.setup_stats["warnings"]:
                logger.info(f"   - {warning}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Enterprise Neo4j Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate database health
  python enterprise_db_setup.py --validate-only
  
  # Setup database (safe - won't overwrite existing data)
  python enterprise_db_setup.py
  
  # Force complete re-initialization
  python enterprise_db_setup.py --force-reload
  
  # Detailed validation with verbose output
  python enterprise_db_setup.py --validate-only --verbose
        """
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate database health, don't make changes"
    )
    
    parser.add_argument(
        "--force-reload",
        action="store_true",
        help="Force complete database re-initialization (DESTRUCTIVE!)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Warning for destructive operations
    if args.force_reload:
        print("⚠️  WARNING: --force-reload will DELETE ALL existing data!")
        print("   This operation cannot be undone.")
        confirm = input("   Type 'YES' to continue: ")
        if confirm != "YES":
            print("❌ Operation cancelled")
            sys.exit(1)
    
    # Run setup
    setup = EnterpriseDBSetup()
    success = setup.run_setup(
        force_reload=args.force_reload,
        validate_only=args.validate_only
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 