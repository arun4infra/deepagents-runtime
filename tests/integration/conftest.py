"""
Pytest configuration for integration tests.

This module sets up environment variables BEFORE any test modules are imported,
ensuring that the FastAPI app and its dependencies use the correct test configuration.
"""

import os

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================
# Read TEST_* env vars (set by test-talos.sh) or use defaults for Docker Compose
# Using variables makes it easy to validate and debug configuration

# NATS Configuration
NATS_URL = os.environ.get("TEST_NATS_URL", "nats://localhost:14222")

# PostgreSQL Configuration
POSTGRES_HOST = os.environ.get("TEST_POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("TEST_POSTGRES_PORT", "15433")
POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "test_db")
POSTGRES_USER = os.environ.get("TEST_POSTGRES_USER", "test_user")
POSTGRES_PASSWORD = os.environ.get("TEST_POSTGRES_PASSWORD", "test_pass")
POSTGRES_SCHEMA = "public"

# Redis/Dragonfly Configuration
REDIS_HOST = os.environ.get("TEST_REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("TEST_REDIS_PORT", "16380")
REDIS_PASSWORD = os.environ.get("TEST_REDIS_PASSWORD", None)

# Other Configuration
DISABLE_VAULT_AUTH = "true"

# ============================================================================
# SET ENVIRONMENT VARIABLES
# ============================================================================
# Set environment variables BEFORE any imports
# This ensures CloudEventEmitter, NATSConsumer, and other components
# read the correct URLs when they're initialized during app startup

os.environ["DISABLE_VAULT_AUTH"] = DISABLE_VAULT_AUTH
os.environ["NATS_URL"] = NATS_URL

os.environ["POSTGRES_HOST"] = POSTGRES_HOST
os.environ["POSTGRES_PORT"] = POSTGRES_PORT
os.environ["POSTGRES_DB"] = POSTGRES_DB
os.environ["POSTGRES_USER"] = POSTGRES_USER
os.environ["POSTGRES_PASSWORD"] = POSTGRES_PASSWORD
os.environ["POSTGRES_SCHEMA"] = POSTGRES_SCHEMA

os.environ["DRAGONFLY_HOST"] = REDIS_HOST
os.environ["DRAGONFLY_PORT"] = REDIS_PORT
if REDIS_PASSWORD:
    os.environ["DRAGONFLY_PASSWORD"] = REDIS_PASSWORD

# ============================================================================
# PRINT CONFIGURATION FOR DEBUGGING
# ============================================================================
print("\n" + "=" * 80)
print("INTEGRATION TEST ENVIRONMENT CONFIGURATION")
print("=" * 80)
print(f"NATS:")
print(f"  URL:              {NATS_URL}")
print(f"\nPostgreSQL:")
print(f"  Host:             {POSTGRES_HOST}")
print(f"  Port:             {POSTGRES_PORT}")
print(f"  Database:         {POSTGRES_DB}")
print(f"  User:             {POSTGRES_USER}")
print(f"  Password:         {'*' * len(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else 'None'}")
print(f"  Schema:           {POSTGRES_SCHEMA}")
print(f"\nRedis/Dragonfly:")
print(f"  Host:             {REDIS_HOST}")
print(f"  Port:             {REDIS_PORT}")
print(f"  Password:         {'*' * len(REDIS_PASSWORD) if REDIS_PASSWORD else 'None'}")
print(f"\nOther:")
print(f"  Vault Auth:       Disabled")
print("=" * 80 + "\n")
