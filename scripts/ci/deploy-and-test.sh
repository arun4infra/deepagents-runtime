#!/bin/bash
#
# Tier 2 Script: Deploy Service and Run Tests
#
# This script deploys deepagents-runtime to the preview cluster and runs integration tests.
#
# Exit Codes:
#   0 - Success
#   1 - Deployment failure
#   2 - Test failure

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TIER3_SCRIPTS_DIR="${PROJECT_ROOT}/tests/integration/scripts"

# Artifacts directory
ARTIFACTS_DIR="${PROJECT_ROOT}/artifacts"
mkdir -p "${ARTIFACTS_DIR}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$*${NC}"
    echo -e "${BLUE}========================================${NC}"
}

log_section "DeepAgents Runtime - Deploy and Test"

# Step 1: Deploy service
log_section "Step 1: Deploying DeepAgents Runtime"
if [ -f "${TIER3_SCRIPTS_DIR}/deploy-service.sh" ]; then
    bash "${TIER3_SCRIPTS_DIR}/deploy-service.sh" || {
        log_error "Service deployment failed"
        exit 1
    }
else
    log_error "deploy-service.sh not found at ${TIER3_SCRIPTS_DIR}/deploy-service.sh"
    exit 1
fi

# Step 2: Run tests
log_section "Step 2: Running Integration Tests"
log_info "Running Python integration tests..."
cd "${PROJECT_ROOT}"
python -m pytest tests/integration/ -v --tb=short || {
    log_error "Tests failed"
    exit 2
}

log_success "All steps completed successfully!"
exit 0
