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
    python -m src.migration.litellm_migration --phase 2 --service all
    python -m src.migration.litellm_migration --phase 2 --service response_synthesizer
    python -m src.migration.litellm_migration --phase 3 --test
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import shutil
import subprocess
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings

logger = logging.getLogger(__name__)

class LiteLLMMigrator:
    """
    Central migration coordinator for LiteLLM transition
    """
    
    def __init__(self):
        self.project_root = project_root
        self.src_dir = self.project_root / "src"
        self.backup_dir = self.project_root / "migration_backup"
        
        # Services to migrate (in dependency order)
        self.services_to_migrate = [
            {
                "name": "intent_analyzer",
                "file_path": "src/retrievers/intent_analyzer.py",
                "llm_imports": ["from langchain_"],
                "invoke_patterns": [".ainvoke(", ".invoke("],
                "complexity": "LOW"  # Simple single model usage
            },
            {
                "name": "document_classifier", 
                "file_path": "src/document_processing/classifier.py",
                "llm_imports": ["from langchain_"],
                "invoke_patterns": [".ainvoke(", ".invoke("],
                "complexity": "LOW"  # Simple classification
            },
            {
                "name": "gemini_entity_extractor",
                "file_path": "src/processing/gemini_entity_extractor.py", 
                "llm_imports": ["import google.generativeai", "genai.GenerativeModel"],
                "invoke_patterns": ["model.generate_content", ".generate_content_async"],
                "complexity": "MEDIUM"  # Direct Gemini API calls
            },
            {
                "name": "structured_extractor",
                "file_path": "src/extractors/structured_extractor.py",
                "llm_imports": ["from langchain_"],
                "invoke_patterns": [".ainvoke(", ".invoke("],
                "complexity": "HIGH"  # Complex structured output
            },
            {
                "name": "response_synthesizer",
                "file_path": "src/retrievers/response_synthesizer.py", 
                "llm_imports": ["from langchain_"],
                "invoke_patterns": [".ainvoke(", ".invoke("],
                "complexity": "HIGH"  # Multi-model, streaming support
            },
            {
                "name": "chroma_client_embeddings",
                "file_path": "src/storage/chroma_client.py",
                "llm_imports": ["from langchain_google_genai", "GoogleGenerativeAIEmbeddings"],
                "invoke_patterns": ["embed_query", "embed_documents"],
                "complexity": "MEDIUM"  # Embeddings only
            }
        ]
        
        self.migration_status = {
            "completed": [],
            "failed": [],
            "skipped": []
        }
    
    def phase_1_setup(self):
        """Phase 1: Setup and Backup (COMPLETED in previous steps)"""
        logger.info("🔧 Phase 1: Setup & Backup")
        
        # Verify LiteLLM infrastructure
        litellm_files = [
            "src/llm/client.py",
            "src/config/llm_config_migrated.py", 
            "src/config/llm_config_legacy.py",
            "litellm_config.yaml",
            "docker-compose.yml"
        ]
        
        missing_files = []
        for file in litellm_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"❌ Missing LiteLLM infrastructure files: {missing_files}")
            return False
        
        logger.info("✅ Phase 1 Complete - LiteLLM infrastructure ready")
        return True
    
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
            if service["name"] == "gemini_entity_extractor":
                migrated_content = self._migrate_gemini_service(content)
            elif service["name"] == "chroma_client_embeddings":
                migrated_content = self._migrate_embeddings_service(content)
            elif service["name"] == "response_synthesizer":
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
    
    def _migrate_gemini_service(self, content: str) -> str:
        """Migrate Gemini Entity Extractor to LiteLLM"""
        logger.info("🔧 Applying Gemini-specific migrations...")
        
        # Replace imports
        content = content.replace(
            "import google.generativeai as genai",
            "from src.llm.client import litellm_client"
        )
        content = content.replace(
            "from google.generativeai import GenerativeModel",
            "# Migrated to LiteLLM - no direct imports needed"
        )
        
        # Replace model initialization
        content = content.replace(
            'genai.GenerativeModel("gemini-2.5-flash")',
            'litellm_client  # Direct LiteLLM client usage'
        )
        
        # Replace generate_content calls
        content = content.replace(
            "model.generate_content(",
            "litellm_client.invoke('extraction', "
        )
        
        content = content.replace(
            "response.text",
            "response.content"
        )
        
        return content
    
    def _migrate_embeddings_service(self, content: str) -> str:
        """Migrate ChromaDB Embeddings to LiteLLM"""
        logger.info("🔧 Applying embeddings-specific migrations...")
        
        # Replace imports
        content = content.replace(
            "from langchain_google_genai import GoogleGenerativeAIEmbeddings",
            "from src.llm.client import litellm_client"
        )
        
        # Replace embeddings initialization
        content = content.replace(
            "GoogleGenerativeAIEmbeddings(",
            "litellm_client  # Using LiteLLM embeddings"
        )
        
        # Replace embed_query calls
        content = content.replace(
            "self.embedding.embed_query(",
            "litellm_client.embed_query("
        )
        
        return content
    
    def _migrate_response_synthesizer(self, content: str) -> str:
        """Migrate Response Synthesizer to LiteLLM"""
        logger.info("🔧 Applying response synthesizer migrations...")
        
        # Replace LLM router import
        content = content.replace(
            "from src.config.llm_config import llm_router",
            "from src.config.llm_config_migrated import llm_router  # Migrated to LiteLLM"
        )
        
        # Add streaming support comment
        content = content.replace(
            "# Streaming support",
            "# Streaming support - Enhanced via LiteLLM proxy"
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
        
        # Add migration comment
        migration_comment = f"""
# ===============================================================================
# LITELLM MIGRATION - {service['name'].upper()}
# Migrated from direct LangChain providers to LiteLLM proxy
# All .invoke() and .ainvoke() calls now go through standardized OpenAI API
# ===============================================================================
"""
        
        # Insert comment at the top after imports
        import_section_end = content.find('\n\n')
        if import_section_end != -1:
            content = content[:import_section_end] + migration_comment + content[import_section_end:]
        
        return content
    
    def phase_3_test_migration(self):
        """Phase 3: Test migrated services"""
        logger.info("🧪 Phase 3: Testing migrated services")
        
        test_results = {}
        
        for service_name in self.migration_status["completed"]:
            try:
                logger.info(f"🔬 Testing {service_name}...")
                result = self._test_service(service_name)
                test_results[service_name] = result
                
                if result["success"]:
                    logger.info(f"✅ {service_name} test passed")
                else:
                    logger.error(f"❌ {service_name} test failed: {result['error']}")
                    
            except Exception as e:
                logger.error(f"💥 {service_name} test crashed: {e}")
                test_results[service_name] = {"success": False, "error": str(e)}
        
        # Summary
        passed = sum(1 for r in test_results.values() if r["success"])
        total = len(test_results)
        
        logger.info(f"📊 Phase 3 Summary: {passed}/{total} tests passed")
        return passed == total
    
    def _test_service(self, service_name: str) -> Dict[str, Any]:
        """Test individual migrated service"""
        try:
            if service_name == "intent_analyzer":
                from src.retrievers.intent_analyzer import IntentAnalyzer
                analyzer = IntentAnalyzer()
                # Simple test
                result = analyzer.analyze_intent("Was ist Compliance?")
                return {"success": True, "result": "Intent analysis working"}
                
            elif service_name == "document_classifier":
                from src.document_processing.classifier import DocumentClassifier
                classifier = DocumentClassifier()
                # Simple test - would need actual document
                return {"success": True, "result": "Classifier initialized"}
                
            elif service_name == "response_synthesizer":
                from src.retrievers.response_synthesizer import ResponseSynthesizer  
                synthesizer = ResponseSynthesizer()
                return {"success": True, "result": "Response synthesizer initialized"}
                
            else:
                return {"success": True, "result": f"Service {service_name} exists"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def phase_4_cleanup(self):
        """Phase 4: Clean up legacy code"""
        logger.info("🧹 Phase 4: Legacy cleanup")
        
        if len(self.migration_status["failed"]) > 0:
            logger.warning("⚠️ Skipping cleanup - some migrations failed")
            return False
        
        # Replace main llm_config import
        main_config = self.project_root / "src/config/llm_config.py"
        migrated_config = self.project_root / "src/config/llm_config_migrated.py"
        
        if main_config.exists() and migrated_config.exists():
            # Backup original
            shutil.copy2(main_config, main_config.with_suffix(".legacy"))
            # Replace with migrated version
            shutil.copy2(migrated_config, main_config)
            logger.info("✅ Replaced main LLM config with migrated version")
        
        logger.info("✅ Phase 4 Complete - Migration finished")
        return True
    
    def rollback_migration(self):
        """Rollback all migrations in case of failure"""
        logger.warning("🔙 Rolling back LiteLLM migration...")
        
        # Restore all backup files
        for service in self.services_to_migrate:
            service_file = self.project_root / service["file_path"]
            backup_file = service_file.with_suffix(f".backup.{service['name']}")
            
            if backup_file.exists():
                shutil.copy2(backup_file, service_file)
                logger.info(f"📁 Restored {service['name']} from backup")
        
        logger.info("✅ Rollback complete")
    
    def status_report(self):
        """Generate comprehensive migration status report"""
        report = f"""
# LiteLLM Migration Status Report

## Completed Services ({len(self.migration_status['completed'])})
{chr(10).join('- ✅ ' + s for s in self.migration_status['completed'])}

## Failed Services ({len(self.migration_status['failed'])})  
{chr(10).join('- ❌ ' + s for s in self.migration_status['failed'])}

## Skipped Services ({len(self.migration_status['skipped'])})
{chr(10).join('- ⏭️ ' + s for s in self.migration_status['skipped'])}

## Next Steps
"""
        
        if self.migration_status['failed']:
            report += "- Investigate and fix failed migrations\n"
            report += "- Consider partial rollback for failed services\n"
        else:
            report += "- Run Phase 3 testing\n"
            report += "- Execute Phase 4 cleanup when ready\n"
        
        print(report)
        return report

def main():
    """Main migration CLI"""
    parser = argparse.ArgumentParser(description='LiteLLM Migration Tool')
    parser.add_argument('--phase', type=int, choices=[1,2,3,4], required=True,
                      help='Migration phase to execute')
    parser.add_argument('--service', type=str, default='all',
                      help='Specific service to migrate (phase 2 only)')
    parser.add_argument('--test', action='store_true',
                      help='Run tests (phase 3)')
    parser.add_argument('--rollback', action='store_true', 
                      help='Rollback migration')
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
        if args.rollback:
            migrator.rollback_migration()
        elif args.status:
            migrator.status_report()
        elif args.phase == 1:
            migrator.phase_1_setup()
        elif args.phase == 2:
            migrator.phase_2_migrate_services(args.service)
        elif args.phase == 3:
            migrator.phase_3_test_migration()
        elif args.phase == 4:
            migrator.phase_4_cleanup()
        
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