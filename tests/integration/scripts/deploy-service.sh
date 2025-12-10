#!/bin/bash
# Tier 3 Script: Deploy Service
# Deploys deepagents-runtime using platform claims
#
# Environment Variables (required):
#   AWS_ACCESS_KEY_ID - AWS access key for ESO (inherited from setup)
#   AWS_SECRET_ACCESS_KEY - AWS secret key for ESO (inherited from setup)
#
# Exit Codes:
#   0 - Success
#   1 - Image build failed
#   2 - Claim application failed
#   3 - Resource creation failed
#   4 - Pod not ready

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Source helper functions
# shellcheck source=./helpers.sh
source "$SCRIPT_DIR/helpers.sh"

# Configuration
NAMESPACE="intelligence-deepagents"
IMAGE_NAME="agent-executor"
IMAGE_TAG="ci-test"
CLUSTER_NAME="zerotouch-preview"
CLAIMS_DIR="$REPO_ROOT/platform/claims/intelligence-deepagents"
EXTERNAL_SECRETS_DIR="$CLAIMS_DIR/external-secrets"

log_info "Starting service deployment..."
log_info "Repository root: $REPO_ROOT"
log_info "Claims directory: $CLAIMS_DIR"

# Validate claims directory exists
if [[ ! -d "$CLAIMS_DIR" ]]; then
    log_error "Claims directory not found: $CLAIMS_DIR"
    exit 2
fi

# ============================================================================
# Step 1: Build Docker Image
# ============================================================================
log_info "Step 1: Building Docker image..."

log_info "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
if ! docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" "$REPO_ROOT"; then
    log_error "Failed to build Docker image"
    exit 1
fi

log_info "Docker image built successfully"

# ============================================================================
# Step 2: Load Image into Kind Cluster
# ============================================================================
log_info "Step 2: Loading image into Kind cluster..."

log_info "Loading image into cluster: $CLUSTER_NAME"
if ! kind load docker-image "${IMAGE_NAME}:${IMAGE_TAG}" --name "$CLUSTER_NAME"; then
    log_error "Failed to load image into Kind cluster"
    exit 1
fi

log_info "Image loaded successfully into Kind cluster"

# ============================================================================
# Step 3: Create Namespace
# ============================================================================
log_info "Step 3: Creating namespace..."

if ! create_namespace_idempotent "$NAMESPACE"; then
    log_error "Failed to create namespace"
    exit 2
fi

log_info "Namespace ready"

# ============================================================================
# Step 4: Apply ExternalSecret for LLM Keys
# ============================================================================
log_info "Step 4: Applying ExternalSecret for LLM keys..."

kubectl apply -f "$EXTERNAL_SECRETS_DIR/llm-keys-es.yaml"

log_info "Waiting for secret to be created (timeout: 120s)..."

# First wait for ExternalSecret to be ready (shows actual ESO errors)
log_info "Checking ExternalSecret status..."
for i in {1..24}; do
    STATUS=$(kubectl get externalsecret -n "$NAMESPACE" agent-executor-llm-keys -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
    REASON=$(kubectl get externalsecret -n "$NAMESPACE" agent-executor-llm-keys -o jsonpath='{.status.conditions[?(@.type=="Ready")].reason}' 2>/dev/null || echo "")
    MESSAGE=$(kubectl get externalsecret -n "$NAMESPACE" agent-executor-llm-keys -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}' 2>/dev/null || echo "")
    
    if [ "$STATUS" = "True" ]; then
        log_info "ExternalSecret is ready"
        break
    elif [ "$STATUS" = "False" ]; then
        log_error "ExternalSecret failed: $REASON - $MESSAGE"
        kubectl get externalsecret -n "$NAMESPACE" agent-executor-llm-keys -o yaml
        exit 2
    fi
    
    log_info "ExternalSecret status: $STATUS (attempt $i/24)..."
    sleep 5
done

# Now wait for the actual secret
kubectl wait secret/agent-executor-llm-keys \
    -n "$NAMESPACE" \
    --for=jsonpath='{.data}' \
    --timeout=60s || {
    log_error "ExternalSecret failed to create secret"
    kubectl get externalsecret -n "$NAMESPACE" agent-executor-llm-keys -o yaml
    exit 2
}

log_info "Secret created successfully"

# ============================================================================
# Step 5: Apply Database Claims
# ============================================================================
log_info "Step 5: Applying database claims..."

kubectl apply -f "$CLAIMS_DIR/postgres-claim.yaml"
kubectl apply -f "$CLAIMS_DIR/dragonfly-claim.yaml"

log_info "Database claims applied"

# ============================================================================
# Step 6: Wait for Database Connection Secrets
# ============================================================================
log_info "Step 6: Waiting for database connection secrets (timeout: 5min)..."

kubectl wait secret/agent-executor-db-conn \
    -n "$NAMESPACE" \
    --for=jsonpath='{.data}' \
    --timeout=300s || {
    log_error "PostgreSQL secret not created"
    kubectl get postgresinstance -n "$NAMESPACE" agent-executor-db -o yaml
    exit 3
}

kubectl wait secret/agent-executor-cache-conn \
    -n "$NAMESPACE" \
    --for=jsonpath='{.data}' \
    --timeout=300s || {
    log_error "Dragonfly secret not created"
    kubectl get dragonflyinstance -n "$NAMESPACE" agent-executor-cache -o yaml
    exit 3
}

log_info "Database secrets ready"

# ============================================================================
# Step 7: Apply EventDrivenService Claim
# ============================================================================
log_info "Step 7: Applying EventDrivenService claim..."

TEMP_CLAIM=$(mktemp)
sed "s|image: ghcr.io/arun4infra/agent-executor:latest|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" \
    "$CLAIMS_DIR/agent-executor-deployment.yaml" | \
sed '/imagePullSecrets:/,+1d' > "$TEMP_CLAIM"

kubectl apply -f "$TEMP_CLAIM"
rm -f "$TEMP_CLAIM"

log_info "Waiting for deployment to be created (timeout: 60s)..."
kubectl wait deployment/deepagents-runtime \
    -n "$NAMESPACE" \
    --for=condition=Available=False \
    --timeout=60s || {
    log_error "Deployment not created"
    kubectl get eventdrivenservice -n "$NAMESPACE" agent-executor -o yaml
    exit 3
}

log_info "Deployment created"

# ============================================================================
# Step 8: Wait for Pod to be Ready
# ============================================================================
log_info "Step 8: Waiting for pod to be ready (timeout: 5min)..."

kubectl wait pod \
    -l app.kubernetes.io/name=deepagents-runtime \
    -n "$NAMESPACE" \
    --for=condition=Ready \
    --timeout=300s || {
    log_error "Pod not ready"
    kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=deepagents-runtime
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/name=deepagents-runtime --tail=50
    exit 4
}

log_info "Pod ready"

log_info "✓ Service deployed successfully"
log_info "Namespace: $NAMESPACE | Image: ${IMAGE_NAME}:${IMAGE_TAG}"

exit 0
