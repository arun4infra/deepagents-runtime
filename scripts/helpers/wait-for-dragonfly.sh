#!/bin/bash
# Wait for Dragonfly cache to be ready
# Usage: ./wait-for-dragonfly.sh <claim-name> <namespace> [timeout]

set -euo pipefail

CLAIM_NAME="${1:?DragonflyInstance claim name required}"
NAMESPACE="${2:?Namespace required}"
TIMEOUT="${3:-300}"

ELAPSED=0
INTERVAL=10

echo "Waiting for Dragonfly cache $CLAIM_NAME to be ready..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if DragonflyInstance exists
    if ! kubectl get dragonflyinstance "$CLAIM_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
        echo "  DragonflyInstance $CLAIM_NAME not found yet... (${ELAPSED}s elapsed)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
        continue
    fi
    
    # Check if StatefulSet exists
    STS_NAME=$(kubectl get dragonflyinstance "$CLAIM_NAME" -n "$NAMESPACE" -o jsonpath='{.status.statefulSetName}' 2>/dev/null || echo "")
    
    if [ -z "$STS_NAME" ]; then
        echo "  Waiting for StatefulSet to be created... (${ELAPSED}s elapsed)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
        continue
    fi
    
    # Check StatefulSet status
    READY_REPLICAS=$(kubectl get statefulset "$STS_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    TOTAL_REPLICAS=$(kubectl get statefulset "$STS_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    echo "  StatefulSet: $STS_NAME | Ready: $READY_REPLICAS/$TOTAL_REPLICAS (${ELAPSED}s elapsed)"
    
    if [ "$READY_REPLICAS" = "$TOTAL_REPLICAS" ] && [ "$READY_REPLICAS" != "0" ]; then
        echo "✓ Dragonfly cache $STS_NAME is ready"
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "✗ Timeout waiting for Dragonfly cache after ${TIMEOUT}s"
echo "DragonflyInstance details:"
kubectl describe dragonflyinstance "$CLAIM_NAME" -n "$NAMESPACE" 2>/dev/null || echo "Not found"
exit 1
