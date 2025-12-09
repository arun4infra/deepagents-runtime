# Integration Test Scripts

This directory contains Tier 3 execution scripts for the deepagents-runtime integration test workflow.

## Script Hierarchy

The integration test workflow follows a three-tier script hierarchy:

- **Tier 1**: GitHub Actions workflow (`.github/workflows/deepagnets-integration-tests.yml`)
- **Tier 2**: Orchestration script (`scripts/ci/run-integration-tests.sh`)
- **Tier 3**: Execution scripts (this directory)

## Helper Functions

### helpers.sh

The `helpers.sh` file provides reusable functions for idempotent Kubernetes operations. All Tier 3 scripts should source this file:

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/helpers.sh"
```

#### Available Functions

##### Logging Functions

- `log_info <message>` - Log informational message in green
- `log_warn <message>` - Log warning message in yellow
- `log_error <message>` - Log error message in red

##### Idempotent Operations

- `create_namespace_idempotent <namespace>` - Create namespace if it doesn't exist
- `helm_install_idempotent <release> <chart> <namespace> [extra_args...]` - Install Helm chart if release doesn't exist
- `kubectl_wait_with_timeout <resource_type> <resource_name> <condition> <timeout> [namespace]` - Wait for resource condition with timeout
- `resource_exists <resource_type> <resource_name> [namespace]` - Check if resource exists
- `collect_artifacts <artifacts_dir>` - Collect debugging artifacts from cluster

##### Convenience Wrappers

- `wait_for_deployment_ready <deployment> <namespace> [timeout]` - Wait for deployment to be available
- `wait_for_pod_ready <selector> <namespace> [timeout]` - Wait for pod to be ready
- `wait_for_crd_established <crd> [timeout]` - Wait for CRD to be established

#### Usage Examples

```bash
# Create namespace idempotently
create_namespace_idempotent "intelligence-deepagents"

# Install Helm chart idempotently
helm_install_idempotent "crossplane" "crossplane-stable/crossplane" "crossplane-system" \
    --create-namespace \
    --wait

# Wait for deployment with timeout
wait_for_deployment_ready "crossplane" "crossplane-system" 300

# Wait for pod with selector
wait_for_pod_ready "-l app=agent-executor" "intelligence-deepagents" 300

# Wait for CRD to be established
wait_for_crd_established "postgresinstances.database.bizmatters.io" 120

# Check if resource exists
if resource_exists "secret" "agent-executor-db-conn" "intelligence-deepagents"; then
    log_info "Database connection secret exists"
fi

# Collect artifacts for debugging
collect_artifacts "/tmp/artifacts"
```

## Testing Helper Functions

Run the test script to verify helper functions work correctly:

```bash
./tests/integration/scripts/test-helpers.sh
```

This test validates:
- Logging functions
- Parameter validation
- Directory creation
- Function structure

Note: Full integration tests require a Kubernetes cluster. The test script only verifies function structure and parameter validation.

## Design Principles

### Idempotency

All operations should be idempotent - running a script multiple times should produce the same result without errors. This is achieved by:

- Checking if resources exist before creating them
- Using `kubectl apply` instead of `kubectl create`
- Using Helm's built-in idempotency checks

### Fast Failure

Scripts should fail fast when errors occur:

- Use `set -euo pipefail` in all scripts
- Validate prerequisites before starting expensive operations
- Return appropriate exit codes for different failure types

### Retry with Timeout

Instead of fixed sleep commands, use `kubectl wait` with timeouts:

- Resources proceed immediately when ready
- Clear error messages when timeouts are exceeded
- Configurable timeout values

### Artifact Collection

Always collect debugging artifacts, even on failure:

- Pod status and logs
- KEDA ScaledObject descriptions
- Crossplane claim status
- Cluster events
- ExternalSecrets status

## Exit Codes

Tier 3 scripts should use consistent exit codes:

- `0` - Success
- `1` - Setup/configuration failure
- `2` - Platform API installation failure
- `3` - Deployment failure
- `4` - Test failure

## Requirements

The helper functions implement the following requirements:

- **16.1**: Idempotent namespace creation
- **16.2**: Idempotent Helm installation
- **16.3**: Idempotent manifest application (via kubectl apply)
- **16.4**: Scripts can be run multiple times without errors
- **17.1**: kubectl wait for deployments with timeout
- **17.2**: kubectl wait for pods with timeout
- **17.3**: kubectl wait for CRDs with timeout
- **17.4**: Immediate proceeding when resources are ready
- **17.5**: Clear error messages on timeout
- **18.1-18.5**: Artifact collection for debugging
