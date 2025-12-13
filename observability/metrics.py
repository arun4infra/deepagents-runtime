"""
Prometheus metrics for Agent Executor Service.

This module defines and exports all Prometheus metrics used by the service.
Metrics are exposed via the /metrics endpoint for Prometheus scraping.

Metrics:
    - agent_executor_jobs_total: Counter for total jobs processed (labels: status)
    - agent_executor_job_duration_seconds: Histogram for job execution duration
    - agent_executor_db_connection_errors_total: Counter for database connection errors
    - agent_executor_redis_publish_total: Counter for Redis stream events published
    - agent_executor_redis_publish_errors_total: Counter for Redis publish errors
    - agent_executor_nats_messages_processed_total: Counter for NATS messages processed
    - agent_executor_nats_messages_failed_total: Counter for NATS messages failed

References:
    - Tasks: Task 1.6, 9.3 (Add Prometheus metrics)
    - Requirements: 17.5, Observable pillar
    - Design: Section 2.8 (Observability Design)
"""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY

# Use a separate registry for tests to avoid conflicts
import os
if os.getenv('PYTEST_CURRENT_TEST'):
    # Create a separate registry for tests
    test_registry = CollectorRegistry()
    registry = test_registry
else:
    # Use the default registry for production
    registry = REGISTRY

# Job execution metrics
agent_executor_jobs_total = Counter(
    'agent_executor_jobs_total',
    'Total number of agent execution jobs processed',
    ['status'],  # status=completed|failed
    registry=registry
)

agent_executor_job_duration_seconds = Histogram(
    'agent_executor_job_duration_seconds',
    'Duration of agent execution jobs in seconds',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=registry
)

# Infrastructure metrics
agent_executor_db_connection_errors_total = Counter(
    'agent_executor_db_connection_errors_total',
    'Total number of database connection errors',
    registry=registry
)

# Redis metrics (optional but useful for monitoring)
agent_executor_redis_publish_total = Counter(
    'agent_executor_redis_publish_total',
    'Total number of Redis stream events published',
    ['event_type'],  # event_type=on_llm_stream|on_tool_start|on_tool_end|end|unknown
    registry=registry
)

agent_executor_redis_publish_errors_total = Counter(
    'agent_executor_redis_publish_errors_total',
    'Total number of Redis publish errors',
    registry=registry
)

# NATS metrics
agent_executor_nats_messages_processed_total = Counter(
    'agent_executor_nats_messages_processed_total',
    'Total number of NATS messages processed successfully',
    registry=registry
)

agent_executor_nats_messages_failed_total = Counter(
    'agent_executor_nats_messages_failed_total',
    'Total number of NATS messages that failed processing',
    registry=registry
)


def get_metrics() -> tuple[bytes, str]:
    """
    Generate Prometheus metrics in text format.

    This function collects all registered metrics and formats them according
    to the Prometheus text exposition format for scraping by Prometheus server.

    Returns:
        Tuple of (metrics_bytes, content_type) where:
        - metrics_bytes: Prometheus metrics in text format (bytes)
        - content_type: MIME type for Prometheus metrics format

    Example:
        >>> metrics_data, content_type = get_metrics()
        >>> print(content_type)
        text/plain; version=0.0.4; charset=utf-8

    References:
        - Tasks: Task 9.3
        - Requirements: Observable pillar
    """
    return generate_latest(registry), CONTENT_TYPE_LATEST
