#!/bin/bash
# K6 Phase 6.3b: Automated Report Cleanup Strategy
# Automatisierte Archivierung und Bereinigung von Quality Reports

set -e

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QUALITY_DIR="ki-wissenssystem/quality_assurance"
ARCHIVE_DIR="$QUALITY_DIR/archive"
DAYS_TO_KEEP=30
MAX_REPORTS_PER_COMPONENT=5

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_step "Starting automated report cleanup..."

# Erstelle Archive-Verzeichnisse falls nicht vorhanden
mkdir -p "$ARCHIVE_DIR/monitoring"
mkdir -p "$ARCHIVE_DIR/reports"

# 1. Archiviere alte Monitoring Reports (>30 Tage)
log_step "Archiving old monitoring reports (>$DAYS_TO_KEEP days)..."

monitoring_archived=0
if [ -d "$QUALITY_DIR/monitoring" ]; then
    # Finde und archiviere alte Monitoring Reports
    while IFS= read -r -d '' file; do
        if [ -f "$file" ]; then
            mv "$file" "$ARCHIVE_DIR/monitoring/"
            ((monitoring_archived++))
            log_info "Archived: $(basename "$file")"
        fi
    done < <(find "$QUALITY_DIR/monitoring" -name "monitoring_report_*.json" -mtime +$DAYS_TO_KEEP -print0 2>/dev/null)
fi

log_info "Monitoring reports archived: $monitoring_archived"

# 2. Quality Reports: Behalte nur die neuesten N pro Komponente
log_step "Keeping only latest $MAX_REPORTS_PER_COMPONENT reports per component..."

components=("DocumentClassifier" "GeminiEntityExtractor")
quality_archived=0

for component in "${components[@]}"; do
    if [ -d "$QUALITY_DIR/reports" ]; then
        # Finde alle Reports für diese Komponente, sortiert nach Datum (neueste zuerst)
        reports=($(ls -t "$QUALITY_DIR/reports/quality_report_${component}_"*.json 2>/dev/null || true))
        
        if [ ${#reports[@]} -gt $MAX_REPORTS_PER_COMPONENT ]; then
            # Archiviere alle bis auf die neuesten N
            for (( i=$MAX_REPORTS_PER_COMPONENT; i<${#reports[@]}; i++ )); do
                if [ -f "${reports[i]}" ]; then
                    mv "${reports[i]}" "$ARCHIVE_DIR/reports/"
                    ((quality_archived++))
                    log_info "Archived: $(basename "${reports[i]}")"
                fi
            done
        fi
    fi
done

log_info "Quality reports archived: $quality_archived"

# 3. Bereinige leere Archive-Verzeichnisse (falls keine Dateien archiviert wurden)
if [ $monitoring_archived -eq 0 ] && [ $quality_archived -eq 0 ]; then
    log_warn "No reports found for archiving"
fi

# 4. Zeige aktuelle Status
log_step "Current report status:"

if [ -d "$QUALITY_DIR/monitoring" ]; then
    monitoring_count=$(ls -1 "$QUALITY_DIR/monitoring"/*.json 2>/dev/null | wc -l || echo "0")
    log_info "Active monitoring reports: $monitoring_count"
fi

if [ -d "$QUALITY_DIR/reports" ]; then
    quality_count=$(ls -1 "$QUALITY_DIR/reports"/*.json 2>/dev/null | wc -l || echo "0")
    log_info "Active quality reports: $quality_count"
fi

if [ -d "$ARCHIVE_DIR" ]; then
    archived_monitoring=$(ls -1 "$ARCHIVE_DIR/monitoring"/*.json 2>/dev/null | wc -l || echo "0")
    archived_quality=$(ls -1 "$ARCHIVE_DIR/reports"/*.json 2>/dev/null | wc -l || echo "0")
    log_info "Archived monitoring reports: $archived_monitoring"
    log_info "Archived quality reports: $archived_quality"
fi

log_info "✅ Report cleanup completed successfully"

# 5. Empfehlung für .gitignore
if [ $monitoring_archived -gt 0 ] || [ $quality_archived -gt 0 ]; then
    echo ""
    log_step "💡 Recommendation: Add archive directory to .gitignore:"
    echo "   ki-wissenssystem/quality_assurance/archive/"
fi 