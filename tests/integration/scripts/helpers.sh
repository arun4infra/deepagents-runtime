#!/bin/bash
# Helper functions for idempotent Kubernetes operations
# This file should be sourced by all Tier 3 scripts

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Function: create_namespace_idempotent
# Creates a Kubernetes namespace if it doesn't already exist
# Arguments:
#   $1 - namespace name
# Returns:
#   0 - Success (namespace created or already exists)
#   1 - Failure
create_namespace_idempotent() {
    local namespace="$1"
    
    if [[ -z "$namespace" ]]; then
        log_error "Namespace name is required"
        return 1
    fi
    
    if kubectl get namespace "$namespace" >/dev/null 2>&1; then
        log_info "Namespace '$namespace' already exists"
        return 0
    fi
    
    log_info "Creating namespace '$namespace'"
    if kubectl create namespace "$namespace"; then
        log_info "Namespace '$namespace' created successfully"
        return 0
    else
        log_error "Failed to create namespace '$namespace'"
        return 1
    fi
}

# Function: helm_install_idempotent
# Installs a Helm chart if the release doesn't already exist
# Arguments:
#   $1 - release name
#   $2 - chart name/path
#   $3 - namespace
#   $4+ - additional helm install arguments (optional)
# Returns:
#   0 - Success (chart installed or already exists)
#   1 - Failure
helm_install_idempotent() {
    local release="$1"
    local chart="$2"
    local namespace="$3"
    shift 3
    local extra_args=("$@")
    
    if [[ -z "$release" ]] || [[ -z "$chart" ]] || [[ -z "$namespace" ]]; then
        log_error "Release name, chart, and namespace are required"
        return 1
    fi
    
    # Check if release already exists
    if helm list -n "$namespace" 2>/dev/null | grep -q "^${release}[[:space:]]"; then
        log_info "Helm release '$release' already exists in namespace '$namespace'"
        return 0
    fi
    
    log_info "Installing Helm chart '$chart' as release '$release' in namespace '$namespace'"
    if helm install "$release" "$chart" -n "$namespace" "${extra_args[@]}"; then
        log_info "Helm release '$release' installed successfully"
        return 0
    else
        log_error "Failed to install Helm release '$release'"
        return 1
    fi
}

# Function: kubectl_wait_with_timeout
# Waits for a Kubernetes resource to meet a condition with timeout
# Arguments:
#   $1 - resource type (e.g., deployment, pod, crd)
#   $2 - resource name or selector
#   $3 - condition (e.g., condition=Ready, condition=Established)
#   $4 - timeout in seconds
#   $5 - namespace (optional, use "" for cluster-scoped resources)
# Returns:
#   0 - Success (condition met)
#   1 - Failure (timeout or error)
kubectl_wait_with_timeout() {
    local resource_type="$1"
    local resource_name="$2"
    local condition="$3"
    local timeout="$4"
    local namespace="${5:-}"
    
    if [[ -z "$resource_type" ]] || [[ -z "$resource_name" ]] || [[ -z "$condition" ]] || [[ -z "$timeout" ]]; then
        log_error "Resource type, name, condition, and timeout are required"
        return 1
    fi
    
    local ns_flag=""
    if [[ -n "$namespace" ]]; then
        ns_flag="-n $namespace"
    fi
    
    log_info "Waiting for $resource_type/$resource_name to meet $condition (timeout: ${timeout}s)"
    
    # shellcheck disable=SC2086
    if kubectl wait "$resource_type" "$resource_name" \
        --for="$condition" \
        --timeout="${timeout}s" \
        $ns_flag 2>&1; then
        log_info "$resource_type/$resource_name is ready"
        return 0
    else
        log_error "Timeout waiting for $resource_type/$resource_name to meet $condition"
        return 1
    fi
}

# Function: resource_exists
# Checks if a Kubernetes resource exists
# Arguments:
#   $1 - resource type (e.g., deployment, pod, secret)
#   $2 - resource name
#   $3 - namespace (optional, use "" for cluster-scoped resources)
# Returns:
#   0 - Resource exists
#   1 - Resource does not exist
resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="${3:-}"
    
    if [[ -z "$resource_type" ]] || [[ -z "$resource_name" ]]; then
        log_error "Resource type and name are required"
        return 1
    fi
    
    local ns_flag=""
    if [[ -n "$namespace" ]]; then
        ns_flag="-n $namespace"
    fi
    
    # shellcheck disable=SC2086
    if kubectl get "$resource_type" "$resource_name" $ns_flag >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function: collect_artifacts
# Collects debugging artifacts from the cluster
# Arguments:
#   $1 - artifacts directory path
# Returns:
#   0 - Success
#   1 - Failure
collect_artifacts() {
    local artifacts_dir="$1"
    
    if [[ -z "$artifacts_dir" ]]; then
        log_error "Artifacts directory path is required"
        return 1
    fi
    
    log_info "Collecting artifacts to '$artifacts_dir'"
    
    # Create artifacts directory if it doesn't exist
    mkdir -p "$artifacts_dir"
    
    # Collect pod status from all namespaces
    log_info "Collecting pod status..."
    kubectl get pods --all-namespaces -o wide > "$artifacts_dir/pods.txt" 2>&1 || true
    
    # Collect KEDA ScaledObjects if they exist
    log_info "Collecting KEDA ScaledObjects..."
    if kubectl get crd scaledobjects.keda.sh >/dev/null 2>&1; then
        kubectl get scaledobjects --all-namespaces -o yaml > "$artifacts_dir/keda-scaledobjects.yaml" 2>&1 || true
        kubectl describe scaledobjects --all-namespaces > "$artifacts_dir/keda-scaledobjects.txt" 2>&1 || true
    fi
    
    # Collect Crossplane claims
    log_info "Collecting Crossplane claims..."
    {
        echo "=== PostgresInstances ==="
        kubectl get postgresinstances --all-namespaces -o yaml 2>&1 || echo "No PostgresInstances found"
        echo ""
        echo "=== DragonflyInstances ==="
        kubectl get dragonflyinstances --all-namespaces -o yaml 2>&1 || echo "No DragonflyInstances found"
        echo ""
        echo "=== EventDrivenServices ==="
        kubectl get eventdrivenservices --all-namespaces -o yaml 2>&1 || echo "No EventDrivenServices found"
    } > "$artifacts_dir/crossplane-claims.yaml"
    
    # Collect pod logs for agent-executor if it exists
    log_info "Collecting agent-executor logs..."
    if kubectl get pods -n intelligence-deepagents -l app.kubernetes.io/name=deepagents-runtime >/dev/null 2>&1; then
        kubectl logs -n intelligence-deepagents -l app.kubernetes.io/name=deepagents-runtime --tail=1000 > "$artifacts_dir/agent-executor-logs.txt" 2>&1 || true
    fi
    
    # Collect events from all namespaces
    log_info "Collecting cluster events..."
    kubectl get events --all-namespaces --sort-by='.lastTimestamp' > "$artifacts_dir/events.txt" 2>&1 || true
    
    # Collect ExternalSecrets status if ESO is installed
    log_info "Collecting ExternalSecrets status..."
    if kubectl get crd externalsecrets.external-secrets.io >/dev/null 2>&1; then
        kubectl get externalsecrets --all-namespaces -o yaml > "$artifacts_dir/external-secrets.yaml" 2>&1 || true
    fi
    
    log_info "Artifacts collected successfully to '$artifacts_dir'"
    return 0
}

# Function: wait_for_deployment_ready
# Convenience wrapper for waiting on deployments
# Arguments:
#   $1 - deployment name
#   $2 - namespace
#   $3 - timeout in seconds (optional, default: 300)
# Returns:
#   0 - Success
#   1 - Failure
wait_for_deployment_ready() {
    local deployment="$1"
    local namespace="$2"
    local timeout="${3:-300}"
    
    kubectl_wait_with_timeout "deployment" "$deployment" "condition=Available" "$timeout" "$namespace"
}

# Function: wait_for_pod_ready
# Convenience wrapper for waiting on pods
# Arguments:
#   $1 - pod selector (e.g., -l app=myapp)
#   $2 - namespace
#   $3 - timeout in seconds (optional, default: 300)
# Returns:
#   0 - Success
#   1 - Failure
wait_for_pod_ready() {
    local selector="$1"
    local namespace="$2"
    local timeout="${3:-300}"
    
    kubectl_wait_with_timeout "pod" "$selector" "condition=Ready" "$timeout" "$namespace"
}

# Function: wait_for_crd_established
# Convenience wrapper for waiting on CRDs
# Arguments:
#   $1 - CRD name
#   $2 - timeout in seconds (optional, default: 120)
# Returns:
#   0 - Success
#   1 - Failure
wait_for_crd_established() {
    local crd="$1"
    local timeout="${3:-120}"
    
    kubectl_wait_with_timeout "crd" "$crd" "condition=Established" "$timeout" ""
}

log_info "Helper functions loaded successfully"
