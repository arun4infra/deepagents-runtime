# Centralized In-Cluster Testing Framework

This directory contains a centralized framework for running integration tests in Kubernetes clusters. This approach eliminates the brittleness of port-forwarding and provides production-like testing environments.

## 🎯 Benefits

- **Reliability**: Native Kubernetes networking vs brittle port-forwarding
- **Production Parity**: Tests run in the same environment as production
- **Consistency**: All test suites use the same infrastructure approach
- **Reusability**: Write once, use for any agent/service
- **Maintainability**: Single source of truth for test configuration

## 📁 Framework Components

### Core Scripts

- **`in-cluster-test.sh`** - Main script for running any test suite in-cluster
- **`test-job-template.yaml`** - Kubernetes Job template for test execution
- **`test.sh`** - Legacy script (being phased out)

### GitHub Workflows

- **`in-cluster-test.yml`** - Reusable workflow for in-cluster testing
- **`nats_events.yml`** - NATS events tests (uses reusable workflow)
- **`spec-gen-in-cluster.yml`** - Example of spec generation tests

### Python Configuration

- **`tests/integration/in_cluster_conftest.py`** - Centralized test configuration
- **`tests/integration/conftest.py`** - Updated to use centralized config

## 🚀 Quick Start

### For New Test Suites

1. **Create a GitHub workflow** that uses the reusable workflow:

```yaml
name: My Agent Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  my-agent-tests:
    uses: ./.github/workflows/in-cluster-test.yml
    with:
      test-path: "tests/integration/test_my_agent.py"
      test-name: "my-agent"
      timeout: 600
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      BOT_GITHUB_TOKEN: ${{ secrets.BOT_GITHUB_TOKEN }}
```

2. **Update your test conftest.py** to use centralized configuration:

```python
# At the top of your conftest.py
from tests.integration.in_cluster_conftest import setup_in_cluster_environment
setup_in_cluster_environment()
```

3. **That's it!** Your tests will automatically use in-cluster services.

### For Local Development

Run tests locally using the centralized script:

```bash
# Run NATS events tests
./scripts/ci/in-cluster-test.sh tests/integration/test_nats_events_integration.py

# Run specific test with custom timeout
./scripts/ci/in-cluster-test.sh tests/integration/test_my_agent.py my-agent 900
```

## 🔧 Configuration

### Environment Variables

The framework automatically configures these environment variables:

| Variable | In-Cluster Value | Local Fallback |
|----------|------------------|----------------|
| `POSTGRES_HOST` | `deepagents-runtime-db-rw` | `localhost` |
| `POSTGRES_PORT` | `5432` | `15433` |
| `DRAGONFLY_HOST` | `deepagents-runtime-cache` | `localhost` |
| `DRAGONFLY_PORT` | `6379` | `16380` |
| `NATS_URL` | `nats://nats.nats.svc:4222` | `nats://localhost:14222` |

### Service Detection

The framework automatically detects if it's running in-cluster by checking:

1. Kubernetes service account token (`/var/run/secrets/kubernetes.io/serviceaccount/token`)
2. `KUBERNETES_SERVICE_HOST` environment variable
3. In-cluster DNS names in existing environment variables

## 📋 Usage Examples

### Basic Test Execution

```bash
# Run all integration tests
./scripts/ci/in-cluster-test.sh tests/integration/

# Run specific test file
./scripts/ci/in-cluster-test.sh tests/integration/test_nats_events_integration.py

# Run with custom name and timeout
./scripts/ci/in-cluster-test.sh tests/integration/test_agent_generation_workflow.py agent-gen 900
```

### GitHub Workflow Examples

#### Simple Test Suite

```yaml
jobs:
  integration-tests:
    uses: ./.github/workflows/in-cluster-test.yml
    with:
      test-path: "tests/integration/"
      test-name: "integration"
```

#### LLM-Based Tests

```yaml
jobs:
  llm-tests:
    uses: ./.github/workflows/in-cluster-test.yml
    with:
      test-path: "tests/integration/test_agent_generation_workflow.py"
      test-name: "agent-generation"
      timeout: 900
      use-real-llm: true
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## 🔍 Monitoring and Debugging

### Test Progress Monitoring

The framework provides real-time progress updates:

```
[INFO] [60s/600s] Job: Pending, Pod: Running, Ready: true
[INFO] Recent logs:
  tests/integration/test_nats_events_integration.py::test_cloudevent_format_compliance PASSED [ 14%]
```

### Artifact Collection

Test artifacts are automatically collected:

- `artifacts/test-results.xml` - JUnit test results
- `artifacts/coverage.xml` - Coverage report
- `artifacts/htmlcov/` - HTML coverage report

### Debugging Failed Tests

```bash
# Check job status
kubectl get job <test-job-name> -n intelligence-deepagents

# View pod logs
kubectl logs job/<test-job-name> -n intelligence-deepagents

# Describe pod for detailed status
kubectl describe pod -l job-name=<test-job-name> -n intelligence-deepagents
```

## 🔄 Migration Guide

### From Docker Compose to In-Cluster

1. **Replace Docker Compose steps** in GitHub workflows:

```yaml
# OLD: Docker Compose approach
- name: Start Infrastructure Services
  run: |
    docker compose -f docker-compose.test.yml up -d

# NEW: In-cluster approach
- uses: ./.github/workflows/in-cluster-test.yml
  with:
    test-path: "tests/integration/test_my_service.py"
    test-name: "my-service"
```

2. **Update test configuration**:

```python
# OLD: Manual environment setup
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "15433"

# NEW: Centralized configuration
from tests.integration.in_cluster_conftest import setup_in_cluster_environment
setup_in_cluster_environment()
```

3. **Remove port-forwarding logic** from test scripts

### From Port-Forwarding to In-Cluster

1. **Replace port-forward commands**:

```bash
# OLD: Port forwarding
kubectl port-forward svc/postgres 15433:5432 &

# NEW: Use in-cluster DNS
# No port-forwarding needed - tests run inside cluster
```

2. **Update connection strings**:

```python
# OLD: localhost connections
DATABASE_URL = "postgresql://user:pass@localhost:15433/db"

# NEW: in-cluster connections (automatic)
DATABASE_URL = get_database_url()  # Returns in-cluster URL
```

## 🛠 Customization

### Custom Test Job Configuration

Override the default test job template by creating your own:

```bash
# Use custom job template
export TEST_JOB_TEMPLATE="/path/to/my-test-job.yaml"
./scripts/ci/in-cluster-test.sh tests/integration/test_my_service.py
```

### Custom Environment Variables

Add service-specific environment variables:

```python
# In your test conftest.py
from tests.integration.in_cluster_conftest import setup_in_cluster_environment

# Set up base configuration
setup_in_cluster_environment()

# Add custom variables
os.environ["MY_SERVICE_URL"] = "http://my-service.default.svc:8080"
```

### Custom Resource Requirements

Modify resource requests/limits in the test job template:

```yaml
resources:
  requests:
    memory: "1Gi"      # Increase for memory-intensive tests
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## 🔒 Security Considerations

- **Secrets**: Use Kubernetes secrets for sensitive data
- **RBAC**: Tests run with minimal required permissions
- **Network Policies**: In-cluster networking is isolated
- **Resource Limits**: Tests have CPU/memory limits to prevent resource exhaustion

## 📊 Performance

### Typical Test Execution Times

| Test Suite | Setup Time | Execution Time | Total Time |
|------------|------------|----------------|------------|
| NATS Events | ~2 minutes | ~2 minutes | ~4 minutes |
| Agent Generation | ~2 minutes | ~5-15 minutes | ~7-17 minutes |
| Full Integration | ~2 minutes | ~10-30 minutes | ~12-32 minutes |

### Resource Usage

- **CPU**: 250m request, 500m limit per test pod
- **Memory**: 512Mi request, 1Gi limit per test pod
- **Storage**: Ephemeral volumes for artifacts

## 🤝 Contributing

When adding new test suites:

1. Use the reusable workflow pattern
2. Follow the naming convention: `<service>-<type>-tests`
3. Set appropriate timeouts for your test complexity
4. Document any special requirements
5. Test both in-cluster and local development scenarios

## 📚 Related Documentation

- [Kubernetes Testing Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)
- [GitHub Actions Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [pytest Configuration](https://docs.pytest.org/en/stable/reference/customize.html)