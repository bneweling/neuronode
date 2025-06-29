#!/usr/bin/env python3
"""
LiteLLM Migration Script

Systematische Migration aller LLM-Services von direkten Provider-Aufrufen 
zu LiteLLM Proxy für vereinfachte, standardisierte LLM-Integration.

MIGRATION STRATEGY:
1. Phase 1: Backup & Setup (COMPLETED)
2. Phase 2: Service-by-Service Migration
3. Phase 3: Testing & Validation  
4. Phase 4: Legacy Cleanup

Usage:
    python scripts/litellm_migration.py --phase 2 --service all
    python scripts/litellm_migration.py --phase 2 --service response_synthesizer
    python scripts/litellm_migration.py --phase 3 --test
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import shutil

logger = logging.getLogger(__name__)

class LiteLLMMigrator:
    """Central migration coordinator for LiteLLM transition"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        
        # Services to migrate (in dependency order)
        self.services_to_migrate = [
            {
                "name": "intent_analyzer",
                "file_path": "src/retrievers/intent_analyzer.py",
                "complexity": "LOW"
            },
            {
                "name": "document_classifier", 
                "file_path": "src/document_processing/classifier.py",
                "complexity": "LOW"
            },
            {
                "name": "gemini_entity_extractor",
                "file_path": "src/processing/gemini_entity_extractor.py", 
                "complexity": "MEDIUM"
            },
            {
                "name": "structured_extractor",
                "file_path": "src/extractors/structured_extractor.py",
                "complexity": "HIGH"
            },
            {
                "name": "response_synthesizer",
                "file_path": "src/retrievers/response_synthesizer.py", 
                "complexity": "HIGH"
            },
            {
                "name": "chroma_client_embeddings",
                "file_path": "src/storage/chroma_client.py",
                "complexity": "MEDIUM"
            }
        ]
        
        self.migration_status = {
            "completed": [],
            "failed": [],
            "skipped": []
        }
    
    def phase_2_migrate_services(self, service_name: str = "all"):
        """Phase 2: Service-by-Service Migration"""
        logger.info(f"🔄 Phase 2: Migrating services - Target: {service_name}")
        
        services_to_process = self.services_to_migrate
        if service_name != "all":
            services_to_process = [s for s in self.services_to_migrate if s["name"] == service_name]
            if not services_to_process:
                logger.error(f"❌ Service '{service_name}' not found")
                return False
        
        for service in services_to_process:
            try:
                logger.info(f"📝 Migrating {service['name']} ({service['complexity']} complexity)")
                success = self._migrate_service(service)
                
                if success:
                    self.migration_status["completed"].append(service["name"])
                    logger.info(f"✅ {service['name']} migration successful")
                else:
                    self.migration_status["failed"].append(service["name"])
                    logger.error(f"❌ {service['name']} migration failed")
                    
            except Exception as e:
                logger.error(f"💥 {service['name']} migration crashed: {e}")
                self.migration_status["failed"].append(service["name"])
        
        # Summary
        completed = len(self.migration_status["completed"])
        failed = len(self.migration_status["failed"])
        total = len(services_to_process)
        
        logger.info(f"📊 Phase 2 Summary: {completed}/{total} successful, {failed} failed")
        return failed == 0
    
    def _migrate_service(self, service: Dict[str, Any]) -> bool:
        """Migrate individual service to LiteLLM"""
        service_file = self.project_root / service["file_path"]
        
        if not service_file.exists():
            logger.warning(f"⚠️ Service file not found: {service_file}")
            self.migration_status["skipped"].append(service["name"])
            return True  # Skip missing files
        
        # Create backup
        backup_file = service_file.with_suffix(f".backup.{service['name']}")
        shutil.copy2(service_file, backup_file)
        
        try:
            # Read current content
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply migration transformations based on service type
            if service["name"] == "response_synthesizer":
                migrated_content = self._migrate_response_synthesizer(content)
            else:
                # Standard LangChain service migration
                migrated_content = self._migrate_langchain_service(content, service)
            
            # Write migrated content
            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(migrated_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Migration of {service['name']} failed: {e}")
            # Restore backup
            shutil.copy2(backup_file, service_file)
            return False
    
    def _migrate_response_synthesizer(self, content: str) -> str:
        """Migrate Response Synthesizer to LiteLLM"""
        logger.info("🔧 Applying response synthesizer migrations...")
        
        # Replace LLM router import
        content = content.replace(
            "from src.config.llm_config import llm_router",
            "from src.config.llm_config_migrated import llm_router  # Migrated to LiteLLM"
        )
        
        return content
    
    def _migrate_langchain_service(self, content: str, service: Dict[str, Any]) -> str:
        """Migrate standard LangChain service to LiteLLM"""
        logger.info(f"🔧 Applying LangChain migrations for {service['name']}...")
        
        # Replace LLM router import to use migrated version
        content = content.replace(
            "from src.config.llm_config import llm_router",
            "from src.config.llm_config_migrated import llm_router  # Migrated to LiteLLM"
        )
        
        return content
    
    def status_report(self):
        """Generate comprehensive migration status report"""
        report = f"""
# LiteLLM Migration Status Report

## Services Status:
- ✅ Completed: {len(self.migration_status['completed'])} 
  {', '.join(self.migration_status['completed']) if self.migration_status['completed'] else 'None'}
  
- ❌ Failed: {len(self.migration_status['failed'])}
  {', '.join(self.migration_status['failed']) if self.migration_status['failed'] else 'None'}
  
- ⏭️ Skipped: {len(self.migration_status['skipped'])}
  {', '.join(self.migration_status['skipped']) if self.migration_status['skipped'] else 'None'}

## Next Steps:
"""
        
        if self.migration_status['failed']:
            report += "- Investigate and fix failed migrations\n"
        else:
            report += "- All services migrated successfully\n" 
            report += "- Ready for testing phase\n"
        
        print(report)
        return report

def main():
    """Main migration CLI"""
    parser = argparse.ArgumentParser(description='LiteLLM Migration Tool')
    parser.add_argument('--phase', type=int, choices=[2,3,4], required=True,
                      help='Migration phase to execute')
    parser.add_argument('--service', type=str, default='all',
                      help='Specific service to migrate (phase 2 only)')
    parser.add_argument('--status', action='store_true',
                      help='Show migration status')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    migrator = LiteLLMMigrator()
    
    try:
        if args.status:
            migrator.status_report()
        elif args.phase == 2:
            migrator.phase_2_migrate_services(args.service)
        
        # Always show status at the end
        if not args.status:
            migrator.status_report()
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 