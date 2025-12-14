#!/bin/bash
# Wait for PostgreSQL cluster to be ready
# Usage: ./wait-for-postgres.sh <claim-name> <namespace> [timeout]

set -euo pipefail

CLAIM_NAME="${1:?PostgresInstance claim name required}"
NAMESPACE="${2:?Namespace required}"
TIMEOUT="${3:-300}"

ELAPSED=0
INTERVAL=10

echo "Waiting for PostgreSQL cluster $CLAIM_NAME to be ready..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if PostgresInstance exists
    if ! kubectl get postgresinstance "$CLAIM_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
        echo "  PostgresInstance $CLAIM_NAME not found yet... (${ELAPSED}s elapsed)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
        continue
    fi
    
    # Check if CNPG cluster exists
    CLUSTER_NAME=$(kubectl get postgresinstance "$CLAIM_NAME" -n "$NAMESPACE" -o jsonpath='{.status.clusterName}' 2>/dev/null || echo "")
    
    if [ -z "$CLUSTER_NAME" ]; then
        echo "  Waiting for CNPG cluster to be created... (${ELAPSED}s elapsed)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
        continue
    fi
    
    # Check cluster status
    CLUSTER_STATUS=$(kubectl get cluster "$CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    READY_INSTANCES=$(kubectl get cluster "$CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyInstances}' 2>/dev/null || echo "0")
    TOTAL_INSTANCES=$(kubectl get cluster "$CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.status.instances}' 2>/dev/null || echo "0")
    
    echo "  Cluster: $CLUSTER_NAME | Status: $CLUSTER_STATUS | Ready: $READY_INSTANCES/$TOTAL_INSTANCES (${ELAPSED}s elapsed)"
    
    if [ "$CLUSTER_STATUS" = "Cluster in healthy state" ] && [ "$READY_INSTANCES" = "$TOTAL_INSTANCES" ] && [ "$READY_INSTANCES" != "0" ]; then
        echo "✓ PostgreSQL cluster $CLUSTER_NAME is ready"
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "✗ Timeout waiting for PostgreSQL cluster after ${TIMEOUT}s"
echo "PostgresInstance details:"
kubectl describe postgresinstance "$CLAIM_NAME" -n "$NAMESPACE" 2>/dev/null || echo "Not found"
exit 1
