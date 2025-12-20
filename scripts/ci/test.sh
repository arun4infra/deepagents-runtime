#!/bin/bash
set -euo pipefail

# ==============================================================================
# Tier 2 CI Script: Run Tests
# ==============================================================================
# Purpose: Execute tests (unit or integration) against deployed service
# Called by: GitHub Actions workflow
# Usage: ./scripts/ci/test.sh <test_directory>
# ==============================================================================

TEST_DIR="${1:-tests/integration}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACTS_DIR="${REPO_ROOT}/artifacts"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo "================================================================================"
echo "Running Tests: ${TEST_DIR}"
echo "================================================================================"

# Create artifacts directory
mkdir -p "${ARTIFACTS_DIR}"

# Validate required environment variables (skip if using mock mode)
if [ "${USE_MOCK_LLM:-false}" != "true" ]; then
    REQUIRED_VARS=("OPENAI_API_KEY")
    MISSING_VARS=()

    for var in "${REQUIRED_VARS[@]}"; do
        # Use :- to provide empty default, preventing unbound variable error
        if [ -z "${!var:-}" ]; then
            MISSING_VARS+=("$var")
        fi
    done

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        log_error "Missing required environment variables:"
        printf '  - %s\n' "${MISSING_VARS[@]}"
        exit 1
    fi
else
    log_info "🤖 Running in mock mode - skipping API key validation"
    export OPENAI_API_KEY="mock-key-for-testing"
fi

# Optional: ANTHROPIC_API_KEY (warn if missing)
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    log_info "⚠️  ANTHROPIC_API_KEY not set - Anthropic tests will be skipped"
fi

# Run integration tests against deployed K8s services
if [[ "${TEST_DIR}" == *"integration"* ]]; then
    NAMESPACE="intelligence-deepagents"
    
    log_info "🏗️  Running in-cluster integration tests"
    
    # In-cluster: credentials should be available as environment variables
    DB_USER="${POSTGRES_USER}"
    DB_PASS="${POSTGRES_PASSWORD}"
    DB_NAME="${POSTGRES_DB}"
    REDIS_PASS="${DRAGONFLY_PASSWORD}"
    
    log_info "Database: ${DB_NAME} (user: ${DB_USER}) - in-cluster"
    log_info "Cache: Dragonfly (authenticated with password) - in-cluster"
    
    # In-cluster: use Kubernetes service DNS names
    export TEST_POSTGRES_HOST="deepagents-runtime-db-rw"
    export TEST_POSTGRES_PORT="5432"
    export TEST_POSTGRES_USER="$DB_USER"
    export TEST_POSTGRES_PASSWORD="$DB_PASS"
    export TEST_POSTGRES_DB="$DB_NAME"
    export TEST_REDIS_HOST="deepagents-runtime-cache"
    export TEST_REDIS_PORT="6379"
    export TEST_REDIS_PASSWORD="$REDIS_PASS"
    export TEST_NATS_URL="nats://nats.nats.svc:4222"
    
    # Also set standard env vars for the app
    export POSTGRES_HOST="deepagents-runtime-db-rw"
    export POSTGRES_PORT="5432"
    export POSTGRES_USER="$DB_USER"
    export POSTGRES_PASSWORD="$DB_PASS"
    export POSTGRES_DB="$DB_NAME"
    export POSTGRES_SCHEMA="public"
    export DRAGONFLY_HOST="deepagents-runtime-cache"
    export DRAGONFLY_PORT="6379"
    export DRAGONFLY_PASSWORD="$REDIS_PASS"
    export REDIS_PASSWORD="$REDIS_PASS"
    export NATS_URL="nats://nats.nats.svc:4222"
    
    log_info "✅ In-cluster service discovery configured"
fi

# Run tests with pytest
log_info "Executing pytest tests on ${TEST_DIR}..."
cd "${REPO_ROOT}"

# Use the provided test directory/file path directly
TEST_PATH="${TEST_DIR}"

python -m pytest "${TEST_PATH}" \
    -v \
    --tb=short \
    --timeout=300 \
    --junit-xml="${ARTIFACTS_DIR}/test-results.xml" \
    --cov=. \
    --cov-report=xml:"${ARTIFACTS_DIR}/coverage.xml" \
    --cov-report=html:"${ARTIFACTS_DIR}/htmlcov"

EXIT_CODE=$?

# Collect debugging artifacts
log_info "Collecting debugging artifacts..."
kubectl get pods --all-namespaces -o wide > "${ARTIFACTS_DIR}/pods.txt" 2>&1 || true
kubectl get scaledobjects --all-namespaces > "${ARTIFACTS_DIR}/keda-scaledobjects.txt" 2>&1 || true
kubectl get postgresinstances,dragonflyinstances,eventdrivenservices --all-namespaces > "${ARTIFACTS_DIR}/crossplane-claims.txt" 2>&1 || true
kubectl logs -n intelligence-deepagents -l app.kubernetes.io/name=deepagents-runtime --tail=1000 > "${ARTIFACTS_DIR}/deepagents-runtime-logs.txt" 2>&1 || true

if [ ${EXIT_CODE} -eq 0 ]; then
    log_success "Tests passed successfully: ${TEST_DIR}"
else
    log_error "Tests failed with exit code ${EXIT_CODE}: ${TEST_DIR}"
fi

exit ${EXIT_CODE}