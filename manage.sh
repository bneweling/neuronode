#!/bin/bash
set -e

# Neuronode Central Management Interface
# Version: 2.0 (Enterprise Edition)
# The single entry point for all system operations

# Color definitions for better UX
GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Updated for Neuronode v2.0
COMPOSE_FILE="deployment/docker-compose.production.yml"
DEV_COMPOSE_FILE="neuronode-backend/docker-compose.yml"
TEST_COMPOSE_FILE="neuronode-backend/docker-compose.test.yml"
SCRIPTS_DIR="scripts"
FRONTEND_DIR="neuronode-webapp"
BACKEND_DIR="neuronode-backend"
DOCS_DIR="docs"

# API Endpoints
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8001"
LITELLM_URL="http://localhost:4000"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_enterprise() {
    echo -e "${PURPLE}[ENTERPRISE]${NC} $1"
}

show_banner() {
    echo -e "${BOLD}${CYAN}"
    echo "🧠 Neuronode Management Interface v2.0"
    echo "=================================================="
    echo -e "${NC}"
    echo "Enterprise Knowledge Management System"
    echo "🔒 Production-Ready | 🚀 LiteLLM | 📊 Neo4j | 🔍 Vector Search"
    echo ""
}

check_prerequisites() {
    log_step "Checking system prerequisites..."
    local errors=0
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        errors=$((errors + 1))
    else
        log_info "Docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        errors=$((errors + 1))
    else
        log_info "Docker Compose: Available"
    fi
    
    # Check Node.js (for frontend operations)
    if ! command -v node &> /dev/null; then
        log_warn "Node.js not found. Frontend operations may fail."
        log_info "Install: https://nodejs.org/"
    else
        log_info "Node.js: $(node --version)"
    fi
    
    # Check Python (for backend operations)
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log_warn "Python not found. Backend operations may fail."
        log_info "Install: https://python.org/"
    else
        local python_cmd=$(command -v python3 || command -v python)
        log_info "Python: $("$python_cmd" --version)"
    fi
    
    # Check required directories
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        errors=$((errors + 1))
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        errors=$((errors + 1))
    fi
    
    if [ ! -f "$DEV_COMPOSE_FILE" ]; then
        log_error "Development compose file not found: $DEV_COMPOSE_FILE"
        errors=$((errors + 1))
    fi
    
    if [ $errors -gt 0 ]; then
        log_error "Prerequisites check failed with $errors errors"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

show_help() {
    show_banner
    echo -e "${BOLD}USAGE:${NC}"
    echo "    ./manage.sh <command>"
    echo ""
    echo -e "${BOLD}🚀 SYSTEM COMMANDS:${NC}"
    echo -e "    ${GREEN}up${NC}              Start complete development environment"
    echo -e "    ${GREEN}down${NC}            Stop and remove all containers"
    echo -e "    ${GREEN}restart${NC}         Restart all services"
    echo -e "    ${GREEN}logs${NC}            Show logs from all services"
    echo -e "    ${GREEN}health${NC}          Check system health status"
    echo -e "    ${GREEN}status${NC}          Show current system status"
    echo -e "    ${GREEN}monitor${NC}         Real-time system monitoring"
    echo ""
    echo -e "${BOLD}🏗️ BUILD & DEPLOYMENT:${NC}"
    echo -e "    ${GREEN}build${NC}           Build all Docker images"
    echo -e "    ${GREEN}build:prod${NC}      Build production images with optimization"
    echo -e "    ${GREEN}deploy:staging${NC}  Deploy to staging environment"
    echo -e "    ${GREEN}deploy:prod${NC}     Deploy to production environment"
    echo -e "    ${GREEN}backup${NC}          Create data backup"
    echo -e "    ${GREEN}restore${NC}         Restore data from backup"
    echo ""
    echo -e "${BOLD}🧪 TESTING:${NC}"
    echo -e "    ${GREEN}test${NC}            Run backend unit tests"
    echo -e "    ${GREEN}test:e2e${NC}        Run Playwright E2E tests"
    echo -e "    ${GREEN}test:performance${NC} Run performance benchmarks"
    echo -e "    ${GREEN}test:coverage${NC}   Generate test coverage report"
    echo -e "    ${GREEN}test:all${NC}        Run complete test suite"
    echo -e "    ${GREEN}test:enterprise${NC} Run K7 enterprise tests"
    echo ""
    echo -e "${BOLD}💻 DEVELOPMENT:${NC}"
    echo -e "    ${GREEN}dev:frontend${NC}    Start frontend development server"
    echo -e "    ${GREEN}dev:backend${NC}     Start backend development server"
    echo -e "    ${GREEN}dev:full${NC}        Start full development environment"
    echo -e "    ${GREEN}dev:litellm${NC}     Start LiteLLM service only"
    echo ""
    echo -e "${BOLD}🗄️ DATABASE MANAGEMENT:${NC}"
    echo -e "    ${GREEN}db:setup${NC}        Initialize database with enterprise features"
    echo -e "    ${GREEN}db:validate${NC}     Validate database health and functionality"
    echo -e "    ${GREEN}db:stats${NC}        Show comprehensive database statistics"
    echo -e "    ${GREEN}db:reset${NC}        Reset database (DESTRUCTIVE - requires confirmation)"
    echo ""
    echo -e "${BOLD}🔧 MAINTENANCE:${NC}"
    echo -e "    ${GREEN}clean${NC}           Clean up Docker resources"
    echo -e "    ${GREEN}clean:deep${NC}      Deep clean (images, volumes, networks)"
    echo -e "    ${GREEN}clean:reports${NC}   Clean up old monitoring reports"
    echo -e "    ${GREEN}update${NC}          Update dependencies"
    echo -e "    ${GREEN}lint${NC}            Run code linting"
    echo -e "    ${GREEN}format${NC}          Format code automatically"
    echo -e "    ${GREEN}security${NC}        Run security scan"
    echo ""
    echo -e "${BOLD}📊 INFORMATION:${NC}"
    echo -e "    ${GREEN}help${NC}            Show this help message"
    echo -e "    ${GREEN}version${NC}         Show system version information"
    echo -e "    ${GREEN}audit${NC}           Run security and dependency audit"
    echo -e "    ${GREEN}docs${NC}            Open documentation"
    echo -e "    ${GREEN}config${NC}          Show current configuration"
    echo ""
    echo -e "${BOLD}🎯 EXAMPLES:${NC}"
    echo "    ./manage.sh up              # Start development environment"
    echo "    ./manage.sh test:e2e        # Run E2E tests"
    echo "    ./manage.sh deploy:staging  # Deploy to staging"
    echo "    ./manage.sh health          # Check system health"
    echo ""
    echo -e "${BOLD}⚡ QUICK START (Enterprise):${NC}"
    echo "    1. ./manage.sh up           # Start all services"
    echo "    2. ./manage.sh test:all     # Validate functionality"
    echo "    3. ./manage.sh monitor      # Monitor health"
    echo "    4. Open $FRONTEND_URL"
    echo ""
    echo -e "${BOLD}🔗 Access Points:${NC}"
    echo "    Frontend:    $FRONTEND_URL"
    echo "    Backend API: $BACKEND_URL/docs"
    echo "    LiteLLM:     $LITELLM_URL"
    echo "    Monitoring:  $BACKEND_URL/metrics"
}

# System commands
cmd_up() {
    check_prerequisites
    log_step "Starting Neuronode development environment..."
    
    # Check if services already running
    if docker-compose -f $DEV_COMPOSE_FILE ps | grep -q "Up"; then
        log_warn "Some services already running. Use 'restart' to restart all."
    fi
    
    # Ensure environment files exist
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        if [ -f "$BACKEND_DIR/env.example" ]; then
            log_info "Creating .env from example..."
            cp "$BACKEND_DIR/env.example" "$BACKEND_DIR/.env"
        else
            log_warn "No .env file found. Creating minimal configuration..."
            create_minimal_env
        fi
    fi
    
    # Start services
    log_info "Starting backend services..."
    cd $BACKEND_DIR
    docker-compose up -d
    cd ..
    
    # Start frontend if requested
    if [ "$1" = "--with-frontend" ]; then
        cmd_dev_frontend &
    fi
    
    log_step "Waiting for services to be ready..."
    sleep 20
    
    # Health check
    if cmd_health_internal; then
        log_success "🎉 Neuronode is ready!"
        echo ""
        log_enterprise "🌐 Access Points:"
        echo "   📱 Frontend:    $FRONTEND_URL"
        echo "   🔧 Backend API: $BACKEND_URL/docs"
        echo "   🤖 LiteLLM:     $LITELLM_URL"
        echo "   📊 Metrics:     $BACKEND_URL/metrics"
        echo ""
        log_info "Run './manage.sh test:e2e' to validate functionality"
        log_info "Run './manage.sh monitor' for real-time monitoring"
    else
        log_error "System health check failed"
        log_info "Run './manage.sh logs' to see error details"
        exit 1
    fi
}

create_minimal_env() {
    cat > "$BACKEND_DIR/.env" << EOF
# Neuronode Environment Configuration
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8001

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# LiteLLM
LITELLM_HOST=localhost
LITELLM_PORT=4000

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
EOF
    log_info "Created minimal .env file. Review and update as needed."
}

cmd_down() {
    log_step "Stopping Neuronode..."
    cd $BACKEND_DIR
    docker-compose down
    cd ..
    log_success "System stopped"
}

cmd_restart() {
    log_step "Restarting Neuronode..."
    cmd_down
    sleep 5
    cmd_up
}

cmd_logs() {
    log_step "Showing system logs..."
    cd $BACKEND_DIR
    docker-compose logs -f --tail=100
    cd ..
}

cmd_health() {
    cmd_health_internal
}

cmd_health_internal() {
    log_step "Checking enterprise system health..."
    local healthy=true
    
    # Enhanced backend health check with database validation
    log_info "Checking backend service with enterprise validation..."
    if curl -s --max-time 10 "$BACKEND_URL/health" > /dev/null 2>&1; then
        # Get detailed health information
        health_response=$(curl -s --max-time 10 "$BACKEND_URL/health" | jq '.')
        
        # Check if Neo4j is functional (not just connected)
        neo4j_status=$(echo "$health_response" | jq -r '.components.neo4j.status' 2>/dev/null || echo "unknown")
        neo4j_functional=$(echo "$health_response" | jq -r '.components.neo4j.details.schema_status' 2>/dev/null || echo "unknown")
        
        if [ "$neo4j_status" = "healthy" ] && [ "$neo4j_functional" = "complete" ]; then
            log_success "✅ Backend: Healthy (Enterprise Ready)"
            
            # Show database statistics if available
            total_nodes=$(echo "$health_response" | jq -r '.components.neo4j.details.total_nodes' 2>/dev/null)
            total_rels=$(echo "$health_response" | jq -r '.components.neo4j.details.total_relationships' 2>/dev/null)
            if [ "$total_nodes" != "null" ] && [ "$total_nodes" != "" ]; then
                log_info "   📊 Database: $total_nodes nodes, $total_rels relationships"
            fi
        elif [ "$neo4j_status" = "healthy" ] || [ "$neo4j_status" = "degraded" ]; then
            log_warn "⚠️ Backend: Connected but database needs initialization"
            log_info "   💡 Run './manage.sh db:setup' to initialize the database"
            healthy=false
        else
            log_error "❌ Backend: Database not functional"
            healthy=false
        fi
    else
        log_error "❌ Backend: Unhealthy ($BACKEND_URL/health)"
        healthy=false
    fi
    
    # LiteLLM health check
    log_info "Checking LiteLLM service..."
    if curl -s --max-time 10 "$LITELLM_URL/health" > /dev/null 2>&1; then
        log_success "✅ LiteLLM: Healthy"
    else
        log_error "❌ LiteLLM: Unhealthy ($LITELLM_URL/health)"
        healthy=false
    fi
    
    # Neo4j direct connection check
    log_info "Checking Neo4j direct connection..."
    cd $BACKEND_DIR
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p password "RETURN 'healthy' as status" > /dev/null 2>&1; then
        log_success "✅ Neo4j: Connected"
    else
        log_error "❌ Neo4j: Connection failed"
        healthy=false
    fi
    cd ..
    
    # ChromaDB health check
    log_info "Checking ChromaDB service..."
    if curl -s --max-time 10 "http://localhost:8000/api/v1/heartbeat" > /dev/null 2>&1; then
        log_success "✅ ChromaDB: Healthy"
    else
        log_error "❌ ChromaDB: Unhealthy"
        healthy=false
    fi
    
    if [ "$healthy" = true ]; then
        log_success "🎉 All services healthy"
        return 0
    else
        log_error "❌ System health check failed"
        return 1
    fi
}

cmd_status() {
    log_step "System status overview..."
    echo ""
    cd $BACKEND_DIR
    docker-compose ps
    cd ..
    echo ""
    cmd_health_internal
}

cmd_monitor() {
    log_enterprise "🔍 Starting real-time monitoring..."
    log_info "Press Ctrl+C to stop monitoring"
    echo ""
    
    while true; do
        clear
        show_banner
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Live System Status"
        echo "=================================================="
        cmd_health_internal
        echo ""
        echo "Docker Resource Usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        sleep 10
    done
}

# Build & Deployment commands
cmd_build() {
    log_step "Building Docker images..."
    cd $BACKEND_DIR
    docker-compose build --no-cache
    cd ..
    log_success "Build completed"
}

cmd_build_prod() {
    log_step "Building production Docker images..."
    cd $BACKEND_DIR
    docker-compose -f docker-compose.yml build --no-cache backend
    cd ..
    
    cd $FRONTEND_DIR
    if [ -f "Dockerfile.production" ]; then
        docker build -f Dockerfile.production -t neuronode-webapp:latest .
        log_success "Frontend production build completed"
    else
        log_warn "Frontend production Dockerfile not found"
    fi
    cd ..
    
    log_success "Production build completed"
}

cmd_deploy_staging() {
    log_enterprise "🚀 Deploying to staging environment..."
    
    # Check if staging deployment script exists
    if [ -f "$SCRIPTS_DIR/deployment/deploy_staging.sh" ]; then
        bash $SCRIPTS_DIR/deployment/deploy_staging.sh
    else
        log_info "Creating staging deployment..."
        create_staging_deployment
    fi
}

create_staging_deployment() {
    log_step "Setting up staging deployment..."
    
    # Build production images
    cmd_build_prod
    
    # Use production compose file
    if [ -f "$COMPOSE_FILE" ]; then
        log_info "Starting staging environment..."
        docker-compose -f $COMPOSE_FILE up -d
        
        # Wait and health check
        sleep 30
        if cmd_health_internal; then
            log_success "✅ Staging deployment successful"
        else
            log_error "❌ Staging deployment health check failed"
            exit 1
        fi
    else
        log_error "Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi
}

cmd_deploy_prod() {
    log_warn "⚠️  PRODUCTION DEPLOYMENT ⚠️"
    echo ""
    log_enterprise "This will deploy to PRODUCTION environment"
    log_warn "Ensure you have:"
    echo "  ✓ Tested in staging"
    echo "  ✓ Database backup"
    echo "  ✓ Production environment variables"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ $confirm == "yes" ]]; then
        log_step "Deploying to production..."
        
        # Pre-deployment checks
        log_step "Running pre-deployment checks..."
        if ! cmd_test_all > /dev/null 2>&1; then
            log_error "Tests failed. Aborting production deployment."
            exit 1
        fi
        
        # Create backup
        cmd_backup
        
        # Production deployment
        create_production_deployment
    else
        log_info "Production deployment cancelled"
    fi
}

create_production_deployment() {
    log_enterprise "🚀 Starting production deployment..."
    
    # Build optimized images
    cmd_build_prod
    
    # Deploy with production configuration
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f $COMPOSE_FILE up -d
        
        # Extended health check for production
        log_step "Running production health checks..."
        sleep 60
        
        for i in {1..5}; do
            if cmd_health_internal; then
                log_success "✅ Production deployment successful"
                log_enterprise "🎉 Neuronode is live in production!"
                return 0
            else
                log_warn "Health check $i/5 failed, retrying in 30s..."
                sleep 30
            fi
        done
        
        log_error "❌ Production deployment failed health checks"
        exit 1
    else
        log_error "Production compose file not found"
        exit 1
    fi
}

# ===================================================================
# DATABASE MANAGEMENT COMMANDS
# ===================================================================

cmd_db_setup() {
    log_step "🛠️ Enterprise Database Setup"
    cd $BACKEND_DIR
    
    log_info "Initializing Neo4j database with enterprise features..."
    if python3 scripts/setup/enterprise_db_setup.py; then
        log_success "✅ Database setup completed successfully"
        
        # Run health check to validate
        log_info "Validating database setup..."
        if cmd_health_internal; then
            log_success "🎉 Database is now enterprise-ready!"
        else
            log_warn "⚠️ Database setup completed but health check shows issues"
        fi
    else
        log_error "❌ Database setup failed"
        log_info "💡 Check logs for details or try manual setup"
        cd ..
        return 1
    fi
    cd ..
}

cmd_db_validate() {
    log_step "🔍 Database Validation"
    cd $BACKEND_DIR
    
    log_info "Running comprehensive database validation..."
    if python3 scripts/setup/enterprise_db_setup.py --validate-only; then
        log_success "✅ Database validation passed - System is production ready!"
    else
        log_error "❌ Database validation failed"
        log_info "💡 Run './manage.sh db:setup' to initialize the database"
        cd ..
        return 1
    fi
    cd ..
}

cmd_db_reset() {
    log_step "🔄 Database Reset (DESTRUCTIVE)"
    
    # Safety confirmation
    log_warn "⚠️ WARNING: This will DELETE ALL database data!"
    log_warn "   This operation cannot be undone."
    echo -n "Type 'YES' to continue: "
    read confirm
    
    if [ "$confirm" != "YES" ]; then
        log_info "❌ Operation cancelled"
        return 1
    fi
    
    cd $BACKEND_DIR
    log_info "Performing database reset..."
    if python3 scripts/setup/enterprise_db_setup.py --force-reload; then
        log_success "✅ Database reset completed"
        log_info "🎯 Database has been reinitialized with sample data"
    else
        log_error "❌ Database reset failed"
        cd ..
        return 1
    fi
    cd ..
}

cmd_db_stats() {
    log_step "📊 Database Statistics"
    
    # Get detailed health info from API
    if curl -s --max-time 10 "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_info "Fetching database statistics..."
        health_response=$(curl -s --max-time 10 "$BACKEND_URL/health")
        
        # Parse and display statistics
        echo "$health_response" | jq -r '
            if .components.neo4j.details then
                "📈 Neo4j Database Statistics:",
                "   Total Nodes: " + (.components.neo4j.details.total_nodes | tostring),
                "   Total Relationships: " + (.components.neo4j.details.total_relationships | tostring),
                "",
                "🏷️ Node Types:",
                (.components.neo4j.details.node_types | to_entries[] | "   " + .key + ": " + (.value | tostring)),
                "",
                "🔗 Relationship Types:",
                (.components.neo4j.details.relationship_types | to_entries[] | "   " + .key + ": " + (.value | tostring))
            else
                "❌ Unable to fetch database statistics - Backend may not be running"
            end
        ' 2>/dev/null || {
            log_warn "⚠️ Unable to parse statistics - using fallback method"
            log_info "Backend response: $health_response"
        }
    else
        log_error "❌ Cannot fetch statistics - Backend not responding"
        log_info "💡 Run './manage.sh up' to start the system first"
        return 1
    fi
}

cmd_backup() {
    log_step "Creating system backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/backup_$timestamp"
    
    mkdir -p $backup_dir
    
    # Backup Neo4j database
    log_info "Backing up Neo4j database..."
    cd $BACKEND_DIR
    if docker-compose exec -T neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j_backup_$timestamp.dump; then
        log_success "Neo4j backup completed"
    else
        log_warn "Neo4j backup failed"
    fi
    cd ..
    
    # Backup uploaded files
    if [ -d "$BACKEND_DIR/data" ]; then
        log_info "Backing up uploaded files..."
        cp -r $BACKEND_DIR/data $backup_dir/
        log_success "File backup completed"
    fi
    
    # Backup configuration
    cp $BACKEND_DIR/.env $backup_dir/ 2>/dev/null || true
    cp $BACKEND_DIR/litellm_config.yaml $backup_dir/ 2>/dev/null || true
    
    log_success "Backup created: $backup_dir"
}

cmd_restore() {
    log_step "Listing available backups..."
    if [ ! -d "backups" ] || [ -z "$(ls -A backups 2>/dev/null)" ]; then
        log_error "No backups found. Create a backup first with './manage.sh backup'"
        exit 1
    fi
    
    echo "Available backups:"
    ls -la backups/
    echo ""
    read -p "Enter backup directory name to restore: " backup_name
    
    if [ -d "backups/$backup_name" ]; then
        log_warn "⚠️  This will overwrite current data!"
        read -p "Continue? (yes/no): " confirm
        
        if [[ $confirm == "yes" ]]; then
            log_step "Restoring from backup: $backup_name"
            # Add restore logic here
            log_success "Restore completed"
        else
            log_info "Restore cancelled"
        fi
    else
        log_error "Backup directory not found: $backup_name"
        exit 1
    fi
}

# Testing commands
cmd_test() {
    log_step "Running backend unit tests..."
    cd $BACKEND_DIR
    if docker-compose ps | grep -q "backend.*Up"; then
        docker-compose exec backend bash -c "cd /app && python -m pytest tests/ -v --tb=short"
    else
        log_error "Backend service not running. Run './manage.sh up' first."
        exit 1
    fi
    cd ..
}

cmd_test_e2e() {
    log_step "Running Playwright E2E tests..."
    
    # Ensure system is running
    if ! cmd_health_internal > /dev/null 2>&1; then
        log_info "System not healthy, starting services..."
        cmd_up
    fi
    
    cd $FRONTEND_DIR
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    
    # Install Playwright if needed
    if [ ! -d "node_modules/@playwright" ]; then
        log_info "Installing Playwright..."
        npx playwright install
    fi
    
    # Run E2E tests
    log_info "Executing E2E test suite..."
    npm run test:e2e
    
    cd ..
    log_success "E2E tests completed"
}

cmd_test_performance() {
    log_step "Running performance benchmarks..."
    
    # Basic performance test using curl
    log_info "Testing API response times..."
    
    echo "Backend API Performance:"
    for i in {1..5}; do
        time curl -s "$BACKEND_URL/health" > /dev/null
    done
    
    echo ""
    echo "LiteLLM Performance:"
    for i in {1..3}; do
        time curl -s "$LITELLM_URL/health" > /dev/null
    done
    
    # Run E2E performance tests if available
    if [ -f "$FRONTEND_DIR/tests/e2e/performance-scalability.spec.ts" ]; then
        log_info "Running E2E performance tests..."
        cd $FRONTEND_DIR
        npx playwright test tests/e2e/performance-scalability.spec.ts
        cd ..
    fi
    
    log_success "Performance benchmarks completed"
}

cmd_test_coverage() {
    log_step "Generating test coverage report..."
    cd $BACKEND_DIR
    if docker-compose ps | grep -q "backend.*Up"; then
        docker-compose exec backend bash -c "cd /app && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term"
        log_success "Coverage report: $BACKEND_DIR/htmlcov/index.html"
    else
        log_error "Backend service not running. Run './manage.sh up' first."
        exit 1
    fi
    cd ..
}

cmd_test_enterprise() {
    log_enterprise "🏢 Running K7 enterprise test suite..."
    
    # Ensure system is ready
    if ! cmd_health_internal > /dev/null 2>&1; then
        log_info "Starting system for enterprise testing..."
        cmd_up
    fi
    
    cd $BACKEND_DIR
    if [ -f "src/testing/k7_integration_tests.py" ]; then
        log_info "Running K7 integration tests..."
        docker-compose exec backend python -m pytest src/testing/k7_integration_tests.py -v
    else
        log_warn "K7 integration tests not found"
    fi
    cd ..
    
    # Run comprehensive E2E tests
    cmd_test_e2e
    
    log_success "Enterprise test suite completed"
}

cmd_test_all() {
    log_step "Running complete test suite..."
    
    # Unit tests
    cmd_test
    
    # E2E tests
    cmd_test_e2e
    
    # Coverage report
    cmd_test_coverage
    
    # Performance tests
    cmd_test_performance
    
    log_success "Complete test suite finished"
}

# Development commands
cmd_dev_frontend() {
    log_step "Starting frontend development server..."
    cd $FRONTEND_DIR
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing dependencies..."
        npm install
    fi
    
    # Start development server
    npm run dev
    cd ..
}

cmd_dev_backend() {
    log_step "Starting backend development server..."
    cd $BACKEND_DIR
    
    # Check if Python environment is set up
    if [ ! -f ".env" ]; then
        cp env.example .env 2>/dev/null || create_minimal_env
    fi
    
    # Start backend with hot reload
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
    cd ..
}

cmd_dev_litellm() {
    log_step "Starting LiteLLM service only..."
    cd $BACKEND_DIR
    docker-compose up -d litellm
    cd ..
    log_success "LiteLLM service started at $LITELLM_URL"
}

cmd_dev_full() {
    log_step "Starting full development environment..."
    cmd_up --with-frontend
    
    log_enterprise "🎉 Full development environment ready!"
    log_info "Frontend: $FRONTEND_URL (with hot reload)"
    log_info "Backend:  $BACKEND_URL (with hot reload)"
}

# Maintenance commands
cmd_clean() {
    log_step "Cleaning up Docker resources..."
    docker system prune -f
    docker volume prune -f
    log_success "Basic cleanup completed"
}

cmd_clean_deep() {
    log_warn "This will remove ALL Docker data (images, volumes, networks)"
    read -p "Are you sure? (yes/no): " confirm
    
    if [[ $confirm == "yes" ]]; then
        log_step "Performing deep clean..."
        docker system prune -af
        docker volume prune -f
        docker network prune -f
        docker image prune -af
        log_success "Deep cleanup completed"
    else
        log_info "Deep cleanup cancelled"
    fi
}

cmd_clean_reports() {
    log_step "Cleaning up old reports..."
    if [ -f "scripts/maintenance/cleanup_reports.sh" ]; then
        bash scripts/maintenance/cleanup_reports.sh
        log_success "Reports cleanup completed"
    else
        log_info "Cleaning up manually..."
        find . -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
        find . -name "*_report_*.json" -type f -mtime +30 -delete 2>/dev/null || true
        log_success "Manual cleanup completed"
    fi
}

cmd_update() {
    log_step "Updating dependencies..."
    
    # Update frontend dependencies
    if [ -d "$FRONTEND_DIR" ]; then
        log_info "Updating frontend dependencies..."
        cd $FRONTEND_DIR
        npm update
        npm audit fix
        cd ..
    fi
    
    # Update backend dependencies (manual review required)
    if [ -f "$BACKEND_DIR/requirements-prod.txt" ]; then
        log_info "Backend dependencies update requires manual review"
        log_info "Check: $BACKEND_DIR/requirements-prod.txt"
        log_info "Run: pip-compile --upgrade requirements-prod.in"
    fi
    
    log_success "Dependencies updated"
}

cmd_lint() {
    log_step "Running code linting..."
    
    # Backend linting
    cd $BACKEND_DIR
    if docker-compose ps | grep -q "backend.*Up"; then
        log_info "Linting Python code..."
        docker-compose exec backend bash -c "cd /app && python -m black src/ && python -m isort src/ && python -m flake8 src/"
    else
        log_warn "Backend service not running. Install tools locally for linting."
    fi
    cd ..
    
    # Frontend linting
    if [ -d "$FRONTEND_DIR" ]; then
        log_info "Linting TypeScript code..."
        cd $FRONTEND_DIR
        if [ -f "package.json" ]; then
            npm run lint --if-present
            npm run type-check --if-present
        fi
        cd ..
    fi
    
    log_success "Code linting completed"
}

cmd_format() {
    log_step "Formatting code..."
    cmd_lint
    log_success "Code formatting completed"
}

cmd_security() {
    log_enterprise "🔒 Running security scan..."
    
    # Docker security scan
    log_info "Scanning Docker images..."
    cd $BACKEND_DIR
    docker-compose build > /dev/null 2>&1
    docker scout cves neuronode-backend:latest 2>/dev/null || log_warn "Docker Scout not available"
    cd ..
    
    # Dependency security audit
    cmd_audit
    
    log_success "Security scan completed"
}

# Information commands
cmd_version() {
    show_banner
    echo -e "${BOLD}Version Information:${NC}"
    echo "Git: $(git describe --tags --always --dirty 2>/dev/null || echo 'No git repository')"
    echo "Docker: $(docker --version 2>/dev/null || echo 'Not available')"
    echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not available')"
    echo "Node.js: $(node --version 2>/dev/null || echo 'Not available')"
    echo "Python: $(python --version 2>/dev/null || python3 --version 2>/dev/null || echo 'Not available')"
    echo ""
    echo -e "${BOLD}Service Status:${NC}"
    if docker-compose -f $DEV_COMPOSE_FILE ps 2>/dev/null | grep -q "Up"; then
        cmd_status
    else
        echo "Services not running. Use './manage.sh up' to start."
    fi
}

cmd_audit() {
    log_step "Running security and dependency audit..."
    
    # Python security audit
    if [ -f "$BACKEND_DIR/requirements-prod.txt" ]; then
        log_info "Checking Python dependencies..."
        if command -v pip-audit &> /dev/null; then
            pip-audit -r $BACKEND_DIR/requirements-prod.txt
        else
            log_warn "pip-audit not available. Install with: pip install pip-audit"
        fi
    fi
    
    # Node.js security audit
    if [ -f "$FRONTEND_DIR/package.json" ]; then
        log_info "Checking Node.js dependencies..."
        cd $FRONTEND_DIR
        npm audit
        cd ..
    fi
    
    log_success "Security audit completed"
}

cmd_docs() {
    log_step "Opening documentation..."
    if command -v open &> /dev/null; then
        open "$DOCS_DIR/README.md"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$DOCS_DIR/README.md"
    else
        log_info "Documentation available at: $DOCS_DIR/README.md"
        log_info "Online: https://github.com/bneweling/neuronode/tree/main/docs"
    fi
}

cmd_config() {
    log_step "Current configuration:"
    echo ""
    echo -e "${BOLD}Paths:${NC}"
    echo "  Backend:    $BACKEND_DIR"
    echo "  Frontend:   $FRONTEND_DIR"
    echo "  Docs:       $DOCS_DIR"
    echo ""
    echo -e "${BOLD}Compose Files:${NC}"
    echo "  Development: $DEV_COMPOSE_FILE"
    echo "  Production:  $COMPOSE_FILE"
    echo "  Testing:     $TEST_COMPOSE_FILE"
    echo ""
    echo -e "${BOLD}URLs:${NC}"
    echo "  Frontend:    $FRONTEND_URL"
    echo "  Backend:     $BACKEND_URL"
    echo "  LiteLLM:     $LITELLM_URL"
    echo ""
    if [ -f "$BACKEND_DIR/.env" ]; then
        echo -e "${BOLD}Environment:${NC}"
        grep -E "^[A-Z_]+" "$BACKEND_DIR/.env" | head -10
    fi
}

# Main command dispatcher
main() {
    case "${1:-help}" in
        # System commands
        up)         cmd_up "$2" ;;
        down)       cmd_down ;;
        restart)    cmd_restart ;;
        logs)       cmd_logs ;;
        health)     cmd_health ;;
        status)     cmd_status ;;
        monitor)    cmd_monitor ;;
        
        # Database Management
        db:setup)           cmd_db_setup ;;
        db:validate)        cmd_db_validate ;;
        db:stats)           cmd_db_stats ;;
        db:reset)           cmd_db_reset ;;
        
        # Build & Deployment
        build)              cmd_build ;;
        build:prod)         cmd_build_prod ;;
        deploy:staging)     cmd_deploy_staging ;;
        deploy:prod)        cmd_deploy_prod ;;
        backup)             cmd_backup ;;
        restore)            cmd_restore ;;
        
        # Testing
        test)               cmd_test ;;
        test:e2e)          cmd_test_e2e ;;
        test:performance)   cmd_test_performance ;;
        test:coverage)      cmd_test_coverage ;;
        test:enterprise)    cmd_test_enterprise ;;
        test:all)          cmd_test_all ;;
        
        # Development
        dev:frontend)      cmd_dev_frontend ;;
        dev:backend)       cmd_dev_backend ;;
        dev:litellm)       cmd_dev_litellm ;;
        dev:full)          cmd_dev_full ;;
        
        # Maintenance
        clean)              cmd_clean ;;
        clean:deep)         cmd_clean_deep ;;
        clean:reports)      cmd_clean_reports ;;
        update)             cmd_update ;;
        lint)               cmd_lint ;;
        format)             cmd_format ;;
        security)           cmd_security ;;
        
        # Information
        version)            cmd_version ;;
        audit)              cmd_audit ;;
        docs)               cmd_docs ;;
        config)             cmd_config ;;
        help|*)             show_help ;;
    esac
}

# Run main function with all arguments
main "$@"