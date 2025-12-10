# Integration Test Scripts

Tier 3 execution scripts for deepagents-runtime integration tests.

## Script Hierarchy

- **Tier 1**: GitHub Actions workflow (`.github/workflows/deepagnets-integration-tests.yml`)
- **Tier 2**: Orchestration script (`scripts/ci/deploy-and-test.sh`)
- **Tier 3**: Execution scripts (this directory)

## Available Scripts

- `deploy-service.sh` - Deploys deepagents-runtime using Crossplane claims
- `helpers.sh` - Reusable helper functions for Kubernetes operations
- `test-helpers.sh` - Validation tests for helper functions

## Platform Bootstrap

Platform setup (Kind cluster, Crossplane, ESO, NATS, etc.) is handled by `zerotouch-platform/scripts/bootstrap/01-master-bootstrap.sh --mode preview`.

## Helper Functions

Source helpers in scripts:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/helpers.sh"
```

### Logging
- `log_info <message>` - Green info message
- `log_warn <message>` - Yellow warning
- `log_error <message>` - Red error

### Idempotent Operations
- `create_namespace_idempotent <namespace>`
- `helm_install_idempotent <release> <chart> <namespace> [args...]`
- `resource_exists <type> <name> [namespace]`
- `wait_for_deployment_ready <deployment> <namespace> [timeout]`
- `wait_for_pod_ready <selector> <namespace> [timeout]`
- `wait_for_crd_established <crd> [timeout]`

### Usage Examples
```bash
# Create namespace
create_namespace_idempotent "intelligence-deepagents"

# Wait for deployment
wait_for_deployment_ready "crossplane" "crossplane-system" 300

# Check resource exists
if resource_exists "secret" "db-conn" "my-namespace"; then
    log_info "Secret exists"
fi
```

## Design Principles

### Idempotency
- Check resources exist before creating
- Use `kubectl apply` not `kubectl create`
- Scripts can run multiple times safely

### Fast Failure
- Use `set -euo pipefail`
- Validate prerequisites early
- Return appropriate exit codes

### Timeouts
- Use `kubectl wait` with timeouts
- No fixed sleep commands
- Clear error messages on timeout

## Exit Codes
- `0` - Success
- `1` - Setup failure
- `2` - Platform API failure
- `3` - Deployment failure
- `4` - Test failure

## Testing
```bash
./test-helpers.sh  # Validate helper functions
```
