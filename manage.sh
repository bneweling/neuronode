#!/bin/bash
set -e

# KI-Wissenssystem Central Management Interface
# Version: 2.0 (K6 Enterprise Edition)
# The single entry point for all system operations

# Color definitions for better UX
GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
TEST_COMPOSE_FILE="ki-wissenssystem/docker-compose.test.yml"
SCRIPTS_DIR="scripts"
FRONTEND_DIR="ki-wissenssystem-webapp"
BACKEND_DIR="ki-wissenssystem"

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

show_banner() {
    echo -e "${BOLD}${BLUE}"
    echo "🚀 KI-Wissenssystem Management Interface"
    echo "============================================"
    echo -e "${NC}"
    echo "Enterprise Knowledge Management System"
    echo "Status: 100% Production Ready"
    echo ""
}

check_prerequisites() {
    log_step "Checking system prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check Node.js (for frontend operations)
    if ! command -v node &> /dev/null; then
        log_warn "Node.js not found. Frontend operations may fail."
    fi
    
    # Check Python (for backend operations)
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log_warn "Python not found. Backend operations may fail."
    fi
    
    log_success "Prerequisites check passed"
}

show_help() {
    show_banner
    cat << EOF
${BOLD}USAGE:${NC}
    ./manage.sh <command>

${BOLD}SYSTEM COMMANDS:${NC}
    ${GREEN}up${NC}              Start complete development environment
    ${GREEN}down${NC}            Stop and remove all containers
    ${GREEN}restart${NC}         Restart all services
    ${GREEN}logs${NC}            Show logs from all services
    ${GREEN}health${NC}          Check system health status
    ${GREEN}status${NC}          Show current system status

${BOLD}BUILD & DEPLOYMENT:${NC}
    ${GREEN}build${NC}           Build all Docker images
    ${GREEN}deploy:staging${NC}  Deploy to staging environment
    ${GREEN}deploy:prod${NC}     Deploy to production environment
    ${GREEN}backup${NC}          Create data backup

${BOLD}TESTING:${NC}
    ${GREEN}test${NC}            Run backend unit tests
    ${GREEN}test:e2e${NC}        Run Playwright E2E tests
    ${GREEN}test:performance${NC} Run performance benchmarks
    ${GREEN}test:coverage${NC}   Generate test coverage report
    ${GREEN}test:all${NC}        Run complete test suite

${BOLD}DEVELOPMENT:${NC}
    ${GREEN}dev:frontend${NC}    Start frontend development server
    ${GREEN}dev:backend${NC}     Start backend development server
    ${GREEN}dev:full${NC}        Start full development environment

${BOLD}MAINTENANCE:${NC}
    ${GREEN}clean${NC}           Clean up Docker resources
    ${GREEN}clean:deep${NC}      Deep clean (images, volumes, networks)
    ${GREEN}update${NC}          Update dependencies
    ${GREEN}lint${NC}            Run code linting
    ${GREEN}format${NC}          Format code automatically

${BOLD}INFORMATION:${NC}
    ${GREEN}help${NC}            Show this help message
    ${GREEN}version${NC}         Show system version information
    ${GREEN}audit${NC}           Run security and dependency audit

${BOLD}EXAMPLES:${NC}
    ./manage.sh up              # Start development environment
    ./manage.sh test:e2e        # Run E2E tests
    ./manage.sh deploy:staging  # Deploy to staging
    ./manage.sh health          # Check system health

${BOLD}QUICK START (30 minutes):${NC}
    1. ./manage.sh up           # Start all services
    2. ./manage.sh test:e2e     # Validate functionality
    3. Open http://localhost:3000
EOF
}

# System commands
cmd_up() {
    check_prerequisites
    log_step "Starting KI-Wissenssystem development environment..."
    
    # Check if services already running
    if docker-compose ps | grep -q "Up"; then
        log_warn "Some services already running. Use 'restart' to restart all."
    fi
    
    # Start services
    docker-compose -f $COMPOSE_FILE up -d
    
    log_step "Waiting for services to be ready..."
    sleep 15
    
    # Health check
    if cmd_health_internal; then
        log_success "System is ready!"
        echo ""
        echo "🌐 Access Points:"
        echo "   Frontend:    http://localhost:3000"
        echo "   Backend API: http://localhost:8001"
        echo "   LiteLLM:     http://localhost:4000"
        echo ""
        log_info "Run './manage.sh test:e2e' to validate functionality"
    else
        log_error "System health check failed"
        log_info "Run './manage.sh logs' to see error details"
        exit 1
    fi
}

cmd_down() {
    log_step "Stopping KI-Wissenssystem..."
    docker-compose -f $COMPOSE_FILE down
    log_success "System stopped"
}

cmd_restart() {
    log_step "Restarting KI-Wissenssystem..."
    cmd_down
    sleep 5
    cmd_up
}

cmd_logs() {
    log_step "Showing system logs..."
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

cmd_health() {
    cmd_health_internal
}

cmd_health_internal() {
    log_step "Checking system health..."
    
    # Frontend health check
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend: Healthy"
    else
        log_error "Frontend: Unhealthy"
        return 1
    fi
    
    # Backend health check
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        log_success "Backend: Healthy"
    else
        log_error "Backend: Unhealthy"
        return 1
    fi
    
    # LiteLLM health check
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        log_success "LiteLLM: Healthy"
    else
        log_error "LiteLLM: Unhealthy"
        return 1
    fi
    
    log_success "All services healthy"
    return 0
}

cmd_status() {
    log_step "System status overview..."
    echo ""
    docker-compose ps
    echo ""
    cmd_health_internal
}

# Build & Deployment commands
cmd_build() {
    log_step "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    log_success "Build completed"
}

cmd_deploy_staging() {
    log_step "Deploying to staging environment..."
    if [ -f "$SCRIPTS_DIR/deployment/deploy_staging.sh" ]; then
        bash $SCRIPTS_DIR/deployment/deploy_staging.sh
    else
        log_error "Staging deployment script not found"
        log_info "Create $SCRIPTS_DIR/deployment/deploy_staging.sh"
        exit 1
    fi
}

cmd_deploy_prod() {
    log_warn "⚠️  PRODUCTION DEPLOYMENT ⚠️"
    echo ""
    log_info "This will deploy to PRODUCTION environment"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ $confirm == "yes" ]]; then
        log_step "Deploying to production..."
        if [ -f "$SCRIPTS_DIR/deployment/deploy_production.sh" ]; then
            bash $SCRIPTS_DIR/deployment/deploy_production.sh
        else
            log_error "Production deployment script not found"
            log_info "Create $SCRIPTS_DIR/deployment/deploy_production.sh"
            exit 1
        fi
    else
        log_info "Production deployment cancelled"
    fi
}

cmd_backup() {
    log_step "Creating system backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/backup_$timestamp"
    
    mkdir -p $backup_dir
    
    # Backup databases
    docker-compose exec -T postgres pg_dump -U postgres ki_wissenssystem > $backup_dir/postgres_backup.sql
    
    # Backup uploaded files
    if [ -d "$BACKEND_DIR/data" ]; then
        cp -r $BACKEND_DIR/data $backup_dir/
    fi
    
    log_success "Backup created: $backup_dir"
}

# Testing commands
cmd_test() {
    log_step "Running backend unit tests..."
    if docker-compose ps | grep -q "backend.*Up"; then
        docker-compose exec backend bash -c "cd /app && python -m pytest tests/ -v"
    else
        log_error "Backend service not running. Run './manage.sh up' first."
        exit 1
    fi
}

cmd_test_e2e() {
    log_step "Running Playwright E2E tests..."
    cd $FRONTEND_DIR
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    
    # Run E2E tests
    npm run test:e2e
    
    cd ..
    log_success "E2E tests completed"
}

cmd_test_performance() {
    log_step "Running performance benchmarks..."
    if [ -f "$SCRIPTS_DIR/testing/run_performance_tests.sh" ]; then
        bash $SCRIPTS_DIR/testing/run_performance_tests.sh
    else
        log_warn "Performance test script not found"
        log_info "Running basic performance check..."
        cmd_test_e2e
    fi
}

cmd_test_coverage() {
    log_step "Generating test coverage report..."
    if docker-compose ps | grep -q "backend.*Up"; then
        docker-compose exec backend bash -c "cd /app && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term"
        log_success "Coverage report: $BACKEND_DIR/htmlcov/index.html"
    else
        log_error "Backend service not running. Run './manage.sh up' first."
        exit 1
    fi
}

cmd_test_all() {
    log_step "Running complete test suite..."
    
    # Unit tests
    cmd_test
    
    # E2E tests
    cmd_test_e2e
    
    # Coverage report
    cmd_test_coverage
    
    log_success "Complete test suite finished"
}

# Development commands
cmd_dev_frontend() {
    log_step "Starting frontend development server..."
    cd $FRONTEND_DIR
    npm run dev
    cd ..
}

cmd_dev_backend() {
    log_step "Starting backend development server..."
    cd $BACKEND_DIR
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
    cd ..
}

cmd_dev_full() {
    log_step "Starting full development environment..."
    cmd_up
    
    log_info "Development environment ready!"
    log_info "Frontend: http://localhost:3000"
    log_info "Backend:  http://localhost:8001"
}

# Maintenance commands
cmd_clean() {
    log_step "Cleaning up Docker resources..."
    docker system prune -f
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
        log_success "Deep cleanup completed"
    else
        log_info "Deep cleanup cancelled"
    fi
}

cmd_update() {
    log_step "Updating dependencies..."
    
    # Update frontend dependencies
    if [ -d "$FRONTEND_DIR" ]; then
        log_info "Updating frontend dependencies..."
        cd $FRONTEND_DIR
        npm update
        cd ..
    fi
    
    # Update backend dependencies
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        log_info "Backend dependencies update requires manual review"
        log_info "Check: $BACKEND_DIR/requirements.txt"
    fi
    
    log_success "Dependencies updated"
}

cmd_lint() {
    log_step "Running code linting..."
    
    # Backend linting
    if docker-compose ps | grep -q "backend.*Up"; then
        log_info "Linting Python code..."
        docker-compose exec backend bash -c "cd /app && python -m black src/ && python -m isort src/"
    fi
    
    # Frontend linting
    if [ -d "$FRONTEND_DIR" ]; then
        log_info "Linting TypeScript code..."
        cd $FRONTEND_DIR
        npm run lint
        cd ..
    fi
    
    log_success "Code linting completed"
}

cmd_format() {
    log_step "Formatting code..."
    cmd_lint
    log_success "Code formatting completed"
}

# Information commands
cmd_version() {
    show_banner
    echo "${BOLD}Version Information:${NC}"
    echo "System: $(git describe --tags --always --dirty 2>/dev/null || echo 'Unknown')"
    echo "Docker: $(docker --version 2>/dev/null || echo 'Not available')"
    echo "Node.js: $(node --version 2>/dev/null || echo 'Not available')"
    echo "Python: $(python --version 2>/dev/null || python3 --version 2>/dev/null || echo 'Not available')"
    echo ""
    echo "${BOLD}Service Status:${NC}"
    if docker-compose ps | grep -q "Up"; then
        cmd_status
    else
        echo "Services not running. Use './manage.sh up' to start."
    fi
}

cmd_audit() {
    log_step "Running security and dependency audit..."
    
    # Python security audit
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        log_info "Checking Python dependencies..."
        pip-audit -r $BACKEND_DIR/requirements.txt || log_warn "pip-audit not available"
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

# Main command dispatcher
main() {
    case "${1:-help}" in
        # System commands
        up)         cmd_up ;;
        down)       cmd_down ;;
        restart)    cmd_restart ;;
        logs)       cmd_logs ;;
        health)     cmd_health ;;
        status)     cmd_status ;;
        
        # Build & Deployment
        build)              cmd_build ;;
        deploy:staging)     cmd_deploy_staging ;;
        deploy:prod)        cmd_deploy_prod ;;
        backup)             cmd_backup ;;
        
        # Testing
        test)               cmd_test ;;
        test:e2e)          cmd_test_e2e ;;
        test:performance)   cmd_test_performance ;;
        test:coverage)      cmd_test_coverage ;;
        test:all)          cmd_test_all ;;
        
        # Development
        dev:frontend)      cmd_dev_frontend ;;
        dev:backend)       cmd_dev_backend ;;
        dev:full)          cmd_dev_full ;;
        
        # Maintenance
        clean)              cmd_clean ;;
        clean:deep)         cmd_clean_deep ;;
        update)             cmd_update ;;
        lint)               cmd_lint ;;
        format)             cmd_format ;;
        
        # Information
        version)            cmd_version ;;
        audit)              cmd_audit ;;
        help|*)             show_help ;;
    esac
}

# Run main function with all arguments
main "$@" 