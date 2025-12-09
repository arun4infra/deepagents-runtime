#!/bin/bash
# Test script to verify helper functions work correctly
# This script tests the helper functions without requiring a Kubernetes cluster

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the helpers
# shellcheck source=./helpers.sh
source "$SCRIPT_DIR/helpers.sh"

echo "=========================================="
echo "Testing Helper Functions"
echo "=========================================="
echo ""

# Test 1: Logging functions
echo "Test 1: Logging functions"
log_info "This is an info message"
log_warn "This is a warning message"
log_error "This is an error message"
echo "✓ Logging functions work"
echo ""

# Test 2: Function parameter validation
echo "Test 2: Function parameter validation"
if create_namespace_idempotent "" 2>/dev/null; then
    echo "✗ create_namespace_idempotent should fail with empty namespace"
    exit 1
else
    echo "✓ create_namespace_idempotent validates parameters"
fi

if helm_install_idempotent "" "" "" 2>/dev/null; then
    echo "✗ helm_install_idempotent should fail with empty parameters"
    exit 1
else
    echo "✓ helm_install_idempotent validates parameters"
fi

if kubectl_wait_with_timeout "" "" "" "" 2>/dev/null; then
    echo "✗ kubectl_wait_with_timeout should fail with empty parameters"
    exit 1
else
    echo "✓ kubectl_wait_with_timeout validates parameters"
fi

if resource_exists "" "" 2>/dev/null; then
    echo "✗ resource_exists should fail with empty parameters"
    exit 1
else
    echo "✓ resource_exists validates parameters"
fi

if collect_artifacts "" 2>/dev/null; then
    echo "✗ collect_artifacts should fail with empty parameters"
    exit 1
else
    echo "✓ collect_artifacts validates parameters"
fi
echo ""

# Test 3: Artifact collection (without cluster)
echo "Test 3: Artifact collection directory creation"
TEST_ARTIFACTS_DIR="/tmp/test-artifacts-$$"
if collect_artifacts "$TEST_ARTIFACTS_DIR" 2>/dev/null; then
    if [[ -d "$TEST_ARTIFACTS_DIR" ]]; then
        echo "✓ collect_artifacts creates artifacts directory"
        rm -rf "$TEST_ARTIFACTS_DIR"
    else
        echo "✗ collect_artifacts did not create directory"
        exit 1
    fi
else
    # It's okay if it fails due to no cluster, as long as directory was created
    if [[ -d "$TEST_ARTIFACTS_DIR" ]]; then
        echo "✓ collect_artifacts creates artifacts directory (cluster commands failed as expected)"
        rm -rf "$TEST_ARTIFACTS_DIR"
    else
        echo "✗ collect_artifacts did not create directory"
        exit 1
    fi
fi
echo ""

echo "=========================================="
echo "All helper function tests passed!"
echo "=========================================="
echo ""
echo "Note: Full integration tests require a Kubernetes cluster"
echo "These tests only verify function structure and parameter validation"
