# Requirements Document

## Introduction

This document defines the requirements for a GitHub Actions CI workflow that runs integration tests for the deepagnets-runtime service. The workflow validates that deepagnets-runtime correctly integrates with the zerotouch-platform APIs by deploying the service in a preview Kubernetes environment using the actual platform manifests. This ensures that any breaking changes in the platform APIs are detected before they reach production.

## Glossary

- **deepagnets-runtime**: The Python service that executes LangGraph agents in an event-driven architecture
- **zerotouch-platform**: The platform repository containing Crossplane XRDs and Compositions for infrastructure provisioning
- **Platform API**: Crossplane Custom Resource Definitions (XRDs) that define infrastructure abstractions (EventDrivenService, PostgresInstance, DragonflyInstance)
- **Claim**: A Kubernetes custom resource instance that requests infrastructure via a Platform API
- **Preview Environment**: A temporary Kubernetes cluster created in CI to test deployments
- **Kind**: Kubernetes in Docker - a tool for running local Kubernetes clusters
- **Crossplane**: A Kubernetes extension that provisions infrastructure using declarative APIs
- **External Observer Pattern**: Testing approach where the test consumes existing manifests without creating test-specific configurations
- **CNPG**: CloudNativePG - PostgreSQL operator for Kubernetes
- **KEDA**: Kubernetes Event-Driven Autoscaling - scales workloads based on event metrics
- **NATS JetStream**: Message streaming platform used for event-driven communication
- **Dragonfly**: Redis-compatible in-memory data store
- **Script Hierarchy**: Three-tier script organization (Tier 1: workflow, Tier 2: orchestration, Tier 3: execution)

## Requirements

### Requirement 1

**User Story:** As a platform engineer, I want integration tests to run automatically on every commit to deepagnets-runtime, so that I can catch integration issues early.

#### Acceptance Criteria

1. WHEN code is pushed to the main branch THEN the GitHub Actions workflow SHALL trigger automatically
2. WHEN a pull request is created THEN the GitHub Actions workflow SHALL trigger automatically
3. WHEN the workflow is manually triggered THEN the GitHub Actions workflow SHALL execute on demand
4. WHEN only documentation files change THEN the GitHub Actions workflow SHALL skip execution
5. WHEN deepagnets-runtime code changes THEN the GitHub Actions workflow SHALL execute

### Requirement 2

**User Story:** As a platform engineer, I want the integration tests to use actual platform manifests from zerotouch-platform, so that breaking changes in platform APIs are detected.

#### Acceptance Criteria

1. WHEN the workflow starts THEN the system SHALL clone the zerotouch-platform repository
2. WHEN installing platform components THEN the system SHALL apply XRDs from zerotouch-platform/platform/05-databases/definitions
3. WHEN installing platform components THEN the system SHALL apply Compositions from zerotouch-platform/platform/05-databases/compositions
4. WHEN installing platform components THEN the system SHALL apply XRDs from zerotouch-platform/platform/04-apis/event-driven-service/definitions
5. WHEN installing platform components THEN the system SHALL apply Compositions from zerotouch-platform/platform/04-apis/event-driven-service/compositions

### Requirement 3

**User Story:** As a platform engineer, I want the preview environment to use a Kind cluster with Crossplane, so that the test environment matches production architecture.

#### Acceptance Criteria

1. WHEN setting up the preview environment THEN the system SHALL create a Kind Kubernetes cluster
2. WHEN the Kind cluster is created THEN the system SHALL install Crossplane via Helm
3. WHEN Crossplane is installed THEN the system SHALL install the Crossplane Kubernetes provider
4. WHEN providers are installed THEN the system SHALL wait for all providers to be healthy before proceeding
5. WHEN Crossplane is ready THEN the system SHALL install CloudNativePG operator for PostgreSQL provisioning
6. WHEN setting up the cluster THEN the system SHALL install External Secrets Operator using the Platform's bootstrap configuration
7. WHEN ESO is ready THEN the system SHALL apply the Platform's ClusterSecretStore and inject AWS credentials

### Requirement 4

**User Story:** As a platform engineer, I want the workflow to apply existing claims from deepagnets-runtime, so that tests follow the External Observer Pattern without creating test-specific configurations.

#### Acceptance Criteria

1. WHEN applying claims THEN the system SHALL create the intelligence-deepagents namespace
2. WHEN the namespace exists THEN the system SHALL apply all manifests from deepagnets-runtime/platform/claims/intelligence-deepagents directory
3. WHEN applying claims THEN the system SHALL apply manifests in sync-wave order (wave 0 before wave 2)
4. WHEN a claim references an undefined XRD THEN the system SHALL fail with a clear error message
5. WHEN a claim has invalid schema THEN the system SHALL fail with a validation error

### Requirement 5

**User Story:** As a platform engineer, I want the workflow to build and use the deepagnets-runtime image from the current commit, so that tests validate the actual code being changed.

#### Acceptance Criteria

1. WHEN the workflow runs THEN the system SHALL build a Docker image from the deepagnets-runtime Dockerfile
2. WHEN the image is built THEN the system SHALL tag the image as agent-executor:ci-test
3. WHEN the image is tagged THEN the system SHALL load the image into the Kind cluster
4. WHEN applying the EventDrivenService claim THEN the system SHALL patch the image reference to use agent-executor:ci-test
5. WHEN the claim is applied THEN the system SHALL not attempt to pull the image from external registries

### Requirement 6

**User Story:** As a platform engineer, I want the workflow to provision databases using platform APIs, so that database provisioning is tested end-to-end.

#### Acceptance Criteria

1. WHEN the PostgresInstance claim is applied THEN the system SHALL create a CNPG PostgreSQL cluster
2. WHEN the PostgreSQL cluster is created THEN the system SHALL generate a connection secret named agent-executor-db-conn
3. WHEN the DragonflyInstance claim is applied THEN the system SHALL create a Dragonfly StatefulSet
4. WHEN the Dragonfly instance is created THEN the system SHALL generate a connection secret named agent-executor-cache-conn
5. WHEN database claims are applied THEN the system SHALL wait for connection secrets to exist before proceeding

### Requirement 7

**User Story:** As a platform engineer, I want the workflow to deploy deepagnets-runtime using the EventDrivenService API, so that the deployment mechanism is tested.

#### Acceptance Criteria

1. WHEN the EventDrivenService claim is applied THEN the system SHALL create a Kubernetes Deployment
2. WHEN the EventDrivenService claim is applied THEN the system SHALL create a ServiceAccount
3. WHEN the EventDrivenService claim is applied THEN the system SHALL create a KEDA ScaledObject
4. WHEN resources are created THEN the system SHALL verify all expected resources exist
5. WHEN the Deployment is created THEN the system SHALL wait for the agent-executor pod to reach Ready state

### Requirement 8

**User Story:** As a platform engineer, I want the workflow to install NATS JetStream, so that event-driven communication is available for testing.

#### Acceptance Criteria

1. WHEN setting up infrastructure THEN the system SHALL install NATS via Helm chart
2. WHEN NATS is installed THEN the system SHALL enable JetStream functionality
3. WHEN NATS is ready THEN the system SHALL create the AGENT_EXECUTION stream
4. WHEN NATS is ready THEN the system SHALL create the AGENT_RESULTS stream
5. WHEN streams are created THEN the system SHALL verify streams exist before proceeding

### Requirement 9

**User Story:** As a platform engineer, I want the workflow to provide LLM API keys to the service, so that integration tests can execute real agent workflows.

#### Acceptance Criteria

1. WHEN the workflow starts THEN the system SHALL authenticate to AWS using OIDC
2. WHEN AWS authentication succeeds THEN the system SHALL export AWS credentials as environment variables for ESO
3. WHEN AWS credentials are exported THEN the system SHALL mask the credentials in GitHub logs
4. WHEN setting up secrets THEN the system SHALL apply the ExternalSecret manifest from deepagnets-runtime/platform/claims/intelligence-deepagents/external-secrets/llm-keys-es.yaml
5. WHEN the ExternalSecret is applied THEN the system SHALL wait for External Secrets Operator to provision the agent-executor-llm-keys Kubernetes Secret

### Requirement 10

**User Story:** As a platform engineer, I want the workflow to run existing integration tests, so that service functionality is validated end-to-end.

#### Acceptance Criteria

1. WHEN the agent-executor pod is ready THEN the system SHALL execute integration tests from deepagnets-runtime/tests/integration
2. WHEN running tests THEN the system SHALL use pytest with coverage reporting
3. WHEN tests complete THEN the system SHALL generate test result artifacts in JUnit XML format
4. WHEN tests complete THEN the system SHALL generate coverage reports in XML and HTML formats
5. WHEN tests fail THEN the system SHALL exit with a non-zero status code

### Requirement 11

**User Story:** As a platform engineer, I want the workflow to follow the Script Hierarchy Model, so that scripts are maintainable and reusable.

#### Acceptance Criteria

1. WHEN organizing scripts THEN the system SHALL implement a Tier 1 GitHub Actions workflow file
2. WHEN organizing scripts THEN the system SHALL implement a Tier 2 orchestration script in scripts/ci directory
3. WHEN organizing scripts THEN the system SHALL implement Tier 3 execution scripts in tests/integration/scripts directory
4. WHEN the workflow executes THEN Tier 1 SHALL call Tier 2 which SHALL call Tier 3 scripts
5. WHEN scripts fail THEN the system SHALL propagate exit codes correctly through all tiers

### Requirement 12

**User Story:** As a platform engineer, I want the workflow to detect breaking changes in platform APIs, so that incompatibilities are caught before production deployment.

#### Acceptance Criteria

1. WHEN a platform XRD schema changes incompatibly THEN the claim application SHALL fail with a validation error
2. WHEN a platform Composition changes and produces different resources THEN the deployment verification SHALL fail
3. WHEN database connection secret format changes THEN the pod startup SHALL fail with a clear error
4. WHEN the EventDrivenService API changes required fields THEN the claim validation SHALL fail
5. WHEN any breaking change occurs THEN the workflow SHALL fail and prevent merge

### Requirement 13

**User Story:** As a platform engineer, I want the workflow to clean up resources after testing, so that CI environments remain clean.

#### Acceptance Criteria

1. WHEN tests complete successfully THEN the system SHALL delete the Kind cluster
2. WHEN tests fail THEN the system SHALL delete the Kind cluster
3. WHEN the workflow is cancelled THEN the system SHALL delete the Kind cluster
4. WHEN cleanup runs THEN the system SHALL remove all Docker containers created by Kind
5. WHEN cleanup completes THEN the system SHALL not leave any persistent resources

### Requirement 14

**User Story:** As a platform engineer, I want test results uploaded as artifacts, so that I can review test outcomes and coverage.

#### Acceptance Criteria

1. WHEN tests complete THEN the system SHALL upload test results in JUnit XML format
2. WHEN tests complete THEN the system SHALL upload coverage reports in XML format
3. WHEN tests complete THEN the system SHALL upload coverage reports in HTML format
4. WHEN uploading artifacts THEN the system SHALL upload artifacts even if tests fail
5. WHEN pull requests are created THEN the system SHALL comment test results on the PR

### Requirement 15

**User Story:** As a platform engineer, I want the workflow to complete within a reasonable time, so that CI feedback is timely.

#### Acceptance Criteria

1. WHEN the workflow runs THEN the system SHALL complete within 45 minutes
2. WHEN the workflow exceeds 45 minutes THEN the system SHALL timeout and fail
3. WHEN installing components THEN the system SHALL use caching to speed up repeated installations
4. WHEN waiting for resources THEN the system SHALL use efficient polling intervals
5. WHEN components are ready THEN the system SHALL proceed immediately without unnecessary delays

### Requirement 16

**User Story:** As a platform engineer, I want scripts to be idempotent, so that they can be run multiple times without causing errors or leaving dirty state.

#### Acceptance Criteria

1. WHEN creating a namespace THEN the system SHALL check if the namespace exists before creating it
2. WHEN installing a Helm chart THEN the system SHALL check if the release exists before installing
3. WHEN applying a manifest THEN the system SHALL use kubectl apply which is idempotent
4. WHEN a script is run twice THEN the system SHALL produce the same result without errors
5. WHEN a resource already exists THEN the system SHALL not fail but continue execution

### Requirement 17

**User Story:** As a platform engineer, I want scripts to use retry loops with timeouts instead of fixed sleep commands, so that tests are both fast and reliable.

#### Acceptance Criteria

1. WHEN waiting for a deployment THEN the system SHALL use kubectl wait with a timeout instead of sleep
2. WHEN waiting for a pod THEN the system SHALL use kubectl wait for condition=Ready with a timeout
3. WHEN waiting for a CRD THEN the system SHALL use kubectl wait for condition=Established with a timeout
4. WHEN a resource becomes ready early THEN the system SHALL proceed immediately without waiting for the full timeout
5. WHEN a timeout is exceeded THEN the system SHALL fail with a clear error message indicating which resource failed

### Requirement 18

**User Story:** As a platform engineer, I want the workflow to save state artifacts for debugging, so that I can troubleshoot failures without re-running tests.

#### Acceptance Criteria

1. WHEN tests complete THEN the system SHALL save pod status from all namespaces to artifacts directory
2. WHEN tests complete THEN the system SHALL save KEDA ScaledObject descriptions to artifacts directory
3. WHEN tests complete THEN the system SHALL save Crossplane claim status to artifacts directory
4. WHEN tests complete THEN the system SHALL save pod logs for the agent-executor pod to artifacts directory
5. WHEN artifacts are saved THEN the system SHALL upload the artifacts directory even if tests fail
