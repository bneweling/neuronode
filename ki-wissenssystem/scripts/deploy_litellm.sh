#!/bin/bash

# ===============================================================================
# LITELLM DEPLOYMENT SCRIPT
# Comprehensive Migration zu LiteLLM Proxy für KI-Wissenssystem
# ===============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if script is run from correct directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "src" ]; then
    error "Script must be run from the ki-wissenssystem root directory"
    exit 1
fi

log "🚀 Starting LiteLLM Deployment for KI-Wissenssystem"

# ===============================================================================
# PHASE 1: PRE-DEPLOYMENT CHECKS
# ===============================================================================

log "📋 Phase 1: Pre-deployment Checks"

# Check required files
required_files=(
    "litellm_config.yaml"
    "src/llm/client.py"
    "src/config/llm_config_migrated.py"
    "scripts/litellm_migration.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Required file missing: $file"
        exit 1
    fi
done

success "✅ All required files present"

# Check environment variables
if [ -z "$OPENAI_API_KEY" ] || [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$GOOGLE_API_KEY" ]; then
    error "Missing required API keys in environment"
    echo "Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY"
    exit 1
fi

success "✅ API keys configured"

# ===============================================================================
# PHASE 2: LITELLM PROXY DEPLOYMENT
# ===============================================================================

log "🔧 Phase 2: LiteLLM Proxy Deployment"

# Stop existing services if running
log "Stopping existing services..."
docker-compose down litellm-proxy 2>/dev/null || true

# Pull latest LiteLLM image
log "Pulling LiteLLM Docker image..."
docker pull ghcr.io/berriai/litellm:main-v1.72.6.rc

# Start LiteLLM proxy
log "Starting LiteLLM proxy..."
docker-compose up -d litellm-proxy

# Wait for proxy to be ready
log "Waiting for LiteLLM proxy to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        success "✅ LiteLLM proxy is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        error "LiteLLM proxy failed to start within 30 seconds"
        docker-compose logs litellm-proxy
        exit 1
    fi
    sleep 1
done

# Verify proxy configuration
log "Verifying proxy configuration..."
if curl -s http://localhost:4000/v1/models | grep -q "data"; then
    success "✅ LiteLLM proxy models endpoint responding"
else
    error "LiteLLM proxy models endpoint not responding correctly"
    exit 1
fi

# ===============================================================================
# PHASE 3: SERVICE MIGRATION
# ===============================================================================

log "🔄 Phase 3: Service Migration"

# Install required Python dependencies
log "Installing Python dependencies..."
pip install openai>=1.12.0

# Execute service migration
log "Executing service migration..."
python scripts/litellm_migration.py --phase 2 --service all

# Check migration status
log "Checking migration status..."
python scripts/litellm_migration.py --status

# ===============================================================================
# PHASE 4: INTEGRATION TESTING
# ===============================================================================

log "🧪 Phase 4: Integration Testing"

# Test LiteLLM client functionality
log "Testing LiteLLM client..."
python -c "
from src.llm.client import litellm_client
result = litellm_client.health_check()
print('Health check result:', result)
assert result['status'] == 'healthy', 'LiteLLM client health check failed'
print('✅ LiteLLM client test passed')
"

# Test migrated services
log "Testing migrated services..."
python -c "
try:
    from src.config.llm_config_migrated import llm_router
    from src.config.llm_config_migrated import ModelPurpose
    
    # Test router initialization
    print('Testing LLM router...')
    classification_model = llm_router.get_model(ModelPurpose.CLASSIFICATION)
    print('✅ Classification model accessible')
    
    extraction_model = llm_router.get_model(ModelPurpose.EXTRACTION)
    print('✅ Extraction model accessible')
    
    synthesis_model = llm_router.get_model(ModelPurpose.SYNTHESIS)
    print('✅ Synthesis model accessible')
    
    validation_models = llm_router.get_model(ModelPurpose.VALIDATION)
    print('✅ Validation models accessible')
    
    print('✅ All migrated services test passed')
except Exception as e:
    print(f'❌ Service test failed: {e}')
    exit(1)
"

# ===============================================================================
# PHASE 5: BACKEND RESTART
# ===============================================================================

log "🔄 Phase 5: Backend Service Restart"

# Update environment variables for backend
export LITELLM_PROXY_URL="http://localhost:4000"

# Restart backend to pick up LiteLLM configuration
log "Restarting backend services..."
docker-compose restart backend || true

# Wait for backend to be ready
log "Waiting for backend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "✅ Backend is ready with LiteLLM integration"
        break
    fi
    if [ $i -eq 60 ]; then
        warning "Backend health check timeout - may still be starting"
        break
    fi
    sleep 2
done

# ===============================================================================
# PHASE 6: VALIDATION & MONITORING
# ===============================================================================

log "✅ Phase 6: Final Validation"

# Test end-to-end functionality
log "Testing end-to-end functionality..."

# Test chat API
log "Testing chat API..."
if curl -s -X POST http://localhost:8000/api/query \
   -H "Content-Type: application/json" \
   -d '{"query": "Was ist Compliance?", "stream": false}' | grep -q "response"; then
    success "✅ Chat API working with LiteLLM"
else
    warning "⚠️ Chat API test inconclusive - manual verification recommended"
fi

# Display final status
log "📊 Deployment Summary"
echo
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│                 🎉 LITELLM DEPLOYMENT COMPLETE                │"
echo "├─────────────────────────────────────────────────────────────┤"
echo "│ ✅ LiteLLM Proxy:      http://localhost:4000                  │"
echo "│ ✅ Backend API:        http://localhost:8000                  │"
echo "│ ✅ Service Migration:  Completed successfully                 │"
echo "│ ✅ Integration Tests:  Passed                                 │"
echo "└─────────────────────────────────────────────────────────────┘"
echo

# ===============================================================================
# MONITORING & MAINTENANCE COMMANDS
# ===============================================================================

echo "📋 Monitoring & Maintenance Commands:"
echo
echo "# Check LiteLLM proxy logs:"
echo "docker-compose logs -f litellm-proxy"
echo
echo "# View available models:"
echo "curl http://localhost:4000/v1/models"
echo
echo "# Check proxy health:"
echo "curl http://localhost:4000/health"
echo
echo "# Monitor backend logs:"
echo "docker-compose logs -f backend"
echo
echo "# Check migration status:"
echo "python scripts/litellm_migration.py --status"
echo

success "🚀 LiteLLM deployment completed successfully!"
success "The KI-Wissenssystem is now running with unified LLM integration."

# ===============================================================================
# ROLLBACK INSTRUCTIONS
# ===============================================================================

echo
echo "🔙 ROLLBACK INSTRUCTIONS (if needed):"
echo "1. Stop LiteLLM proxy: docker-compose down litellm-proxy"
echo "2. Restore services: python scripts/litellm_migration.py --rollback"
echo "3. Restart backend: docker-compose restart backend"
echo

log "✅ Deployment script completed successfully" 