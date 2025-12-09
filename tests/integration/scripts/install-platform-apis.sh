#!/bin/bash
# Tier 3 Script: Install Platform APIs
# Installs Crossplane XRDs and Compositions from zerotouch-platform
#
# Environment Variables (required):
#   ZEROTOUCH_PLATFORM_DIR - Path to zerotouch-platform repository
#
# Exit Codes:
#   0 - Success
#   1 - Environment validation failed
#   2 - XRD installation failed
#   3 - Composition installation failed

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source helper functions
# shellcheck source=./helpers.sh
source "$SCRIPT_DIR/helpers.sh"

# Validate required environment variables
if [[ -z "${ZEROTOUCH_PLATFORM_DIR:-}" ]]; then
    log_error "ZEROTOUCH_PLATFORM_DIR environment variable is required"
    exit 1
fi

if [[ ! -d "$ZEROTOUCH_PLATFORM_DIR" ]]; then
    log_error "ZEROTOUCH_PLATFORM_DIR does not exist: $ZEROTOUCH_PLATFORM_DIR"
    exit 1
fi

log_info "Starting platform API installation..."
log_info "Platform directory: $ZEROTOUCH_PLATFORM_DIR"

# Define paths to XRDs and Compositions
POSTGRES_XRD="$ZEROTOUCH_PLATFORM_DIR/platform/05-databases/definitions/postgres-xrd.yaml"
DRAGONFLY_XRD="$ZEROTOUCH_PLATFORM_DIR/platform/05-databases/definitions/dragonfly-xrd.yaml"
EVENT_DRIVEN_XRD="$ZEROTOUCH_PLATFORM_DIR/platform/04-apis/event-driven-service/definitions/xeventdrivenservices.yaml"

POSTGRES_COMPOSITION="$ZEROTOUCH_PLATFORM_DIR/platform/05-databases/compositions/postgres-composition.yaml"
DRAGONFLY_COMPOSITION="$ZEROTOUCH_PLATFORM_DIR/platform/05-databases/compositions/dragonfly-composition.yaml"
EVENT_DRIVEN_COMPOSITION="$ZEROTOUCH_PLATFORM_DIR/platform/04-apis/event-driven-service/compositions/event-driven-service-composition.yaml"

# ============================================================================
# Step 1: Install Database XRDs
# ============================================================================
log_info "Step 1: Installing database XRDs..."

# Install PostgreSQL XRD
log_info "Installing PostgreSQL XRD..."
if [[ ! -f "$POSTGRES_XRD" ]]; then
    log_error "PostgreSQL XRD not found: $POSTGRES_XRD"
    exit 2
fi

if resource_exists "compositeresourcedefinition.apiextensions.crossplane.io" "xpostgresinstances.database.bizmatters.io" ""; then
    log_info "PostgreSQL XRD already exists, updating..."
    kubectl apply -f "$POSTGRES_XRD"
else
    log_info "Creating PostgreSQL XRD..."
    kubectl apply -f "$POSTGRES_XRD"
fi

# Install Dragonfly XRD
log_info "Installing Dragonfly XRD..."
if [[ ! -f "$DRAGONFLY_XRD" ]]; then
    log_error "Dragonfly XRD not found: $DRAGONFLY_XRD"
    exit 2
fi

if resource_exists "compositeresourcedefinition.apiextensions.crossplane.io" "xdragonflyinstances.database.bizmatters.io" ""; then
    log_info "Dragonfly XRD already exists, updating..."
    kubectl apply -f "$DRAGONFLY_XRD"
else
    log_info "Creating Dragonfly XRD..."
    kubectl apply -f "$DRAGONFLY_XRD"
fi

log_info "Database XRDs installed successfully"

# ============================================================================
# Step 2: Install EventDrivenService XRD
# ============================================================================
log_info "Step 2: Installing EventDrivenService XRD..."

if [[ ! -f "$EVENT_DRIVEN_XRD" ]]; then
    log_error "EventDrivenService XRD not found: $EVENT_DRIVEN_XRD"
    exit 2
fi

if resource_exists "compositeresourcedefinition.apiextensions.crossplane.io" "xeventdrivenservices.platform.bizmatters.io" ""; then
    log_info "EventDrivenService XRD already exists, updating..."
    kubectl apply -f "$EVENT_DRIVEN_XRD"
else
    log_info "Creating EventDrivenService XRD..."
    kubectl apply -f "$EVENT_DRIVEN_XRD"
fi

log_info "EventDrivenService XRD installed successfully"

# ============================================================================
# Step 3: Wait for XRDs to be Established
# ============================================================================
log_info "Step 3: Waiting for XRDs to be established..."

log_info "Waiting for PostgreSQL XRD..."
if ! kubectl wait xrd/xpostgresinstances.database.bizmatters.io \
    --for=condition=Established \
    --timeout=120s; then
    log_error "PostgreSQL XRD did not become established"
    exit 2
fi

log_info "Waiting for Dragonfly XRD..."
if ! kubectl wait xrd/xdragonflyinstances.database.bizmatters.io \
    --for=condition=Established \
    --timeout=120s; then
    log_error "Dragonfly XRD did not become established"
    exit 2
fi

log_info "Waiting for EventDrivenService XRD..."
if ! kubectl wait xrd/xeventdrivenservices.platform.bizmatters.io \
    --for=condition=Established \
    --timeout=120s; then
    log_error "EventDrivenService XRD did not become established"
    exit 2
fi

log_info "All XRDs established successfully"

# ============================================================================
# Step 4: Install Database Compositions
# ============================================================================
log_info "Step 4: Installing database Compositions..."

# Install PostgreSQL Composition
log_info "Installing PostgreSQL Composition..."
if [[ ! -f "$POSTGRES_COMPOSITION" ]]; then
    log_error "PostgreSQL Composition not found: $POSTGRES_COMPOSITION"
    exit 3
fi

if resource_exists "composition.apiextensions.crossplane.io" "postgres-instance" ""; then
    log_info "PostgreSQL Composition already exists, updating..."
    kubectl apply -f "$POSTGRES_COMPOSITION"
else
    log_info "Creating PostgreSQL Composition..."
    kubectl apply -f "$POSTGRES_COMPOSITION"
fi

# Install Dragonfly Composition
log_info "Installing Dragonfly Composition..."
if [[ ! -f "$DRAGONFLY_COMPOSITION" ]]; then
    log_error "Dragonfly Composition not found: $DRAGONFLY_COMPOSITION"
    exit 3
fi

if resource_exists "composition.apiextensions.crossplane.io" "dragonfly-instance" ""; then
    log_info "Dragonfly Composition already exists, updating..."
    kubectl apply -f "$DRAGONFLY_COMPOSITION"
else
    log_info "Creating Dragonfly Composition..."
    kubectl apply -f "$DRAGONFLY_COMPOSITION"
fi

log_info "Database Compositions installed successfully"

# ============================================================================
# Step 5: Install EventDrivenService Composition
# ============================================================================
log_info "Step 5: Installing EventDrivenService Composition..."

if [[ ! -f "$EVENT_DRIVEN_COMPOSITION" ]]; then
    log_error "EventDrivenService Composition not found: $EVENT_DRIVEN_COMPOSITION"
    exit 3
fi

if resource_exists "composition.apiextensions.crossplane.io" "event-driven-service" ""; then
    log_info "EventDrivenService Composition already exists, updating..."
    kubectl apply -f "$EVENT_DRIVEN_COMPOSITION"
else
    log_info "Creating EventDrivenService Composition..."
    kubectl apply -f "$EVENT_DRIVEN_COMPOSITION"
fi

log_info "EventDrivenService Composition installed successfully"

# ============================================================================
# Step 6: Validate Installation
# ============================================================================
log_info "Step 6: Validating platform API installation..."

# Verify XRDs are registered
log_info "Verifying XRDs..."
kubectl get xrd xpostgresinstances.database.bizmatters.io
kubectl get xrd xdragonflyinstances.database.bizmatters.io
kubectl get xrd xeventdrivenservices.platform.bizmatters.io

# Verify Compositions are installed
log_info "Verifying Compositions..."
kubectl get composition postgres-instance
kubectl get composition dragonfly-instance
kubectl get composition event-driven-service

log_info "✓ Platform API installation completed successfully!"
log_info "XRDs: PostgresInstance, DragonflyInstance, EventDrivenService"
log_info "Compositions: postgres-instance, dragonfly-instance, event-driven-service"

exit 0
