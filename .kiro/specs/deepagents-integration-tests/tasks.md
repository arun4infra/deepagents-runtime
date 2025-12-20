# Implementation Plan

## Phase 1: Local Preview Cluster Setup

- [x] 1. Create Kind cluster configuration file
  - Create `tests/integration/kind-config.yaml`
  - Configure single control-plane node
  - Add port mappings for NATS (4222), PostgreSQL (5432), Dragonfly (6379)
  - Set cluster name to deepagnets-preview
  - _Requirements: 3.1_

- [x] 2. Create helper script for idempotent operations
  - Create `tests/integration/scripts/helpers.sh`
  - Add function for idempotent namespace creation
  - Add function for idempotent Helm installation
  - Add function for kubectl wait with timeout
  - Add function for resource existence check
  - Add function for artifact collection
  - Source this file in all Tier 3 scripts
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 3. Create Tier 3 setup script
  - Create `tests/integration/scripts/setup-preview-cluster.sh`
  - Add Kind cluster creation with port mappings
  - Add Crossplane installation via Helm
  - Add Crossplane Kubernetes provider installation
  - Add CloudNativePG operator installation
  - Install ESO by applying platform manifest: `kubectl apply -f ${ZEROTOUCH_PLATFORM_DIR}/bootstrap/components/01-eso.yaml`
  - Wait for ESO deployments to be ready: `kubectl wait --for=condition=available deployment -l app.kubernetes.io/name=external-secrets -n external-secrets --timeout=300s`
  - Inject AWS credentials using platform's script: `${ZEROTOUCH_PLATFORM_DIR}/scripts/bootstrap/07-inject-eso-secrets.sh $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY`
  - Apply platform's ClusterSecretStore: `kubectl apply -f ${ZEROTOUCH_PLATFORM_DIR}/platform/01-foundation/aws-secret-store.yaml`
  - Add NATS installation with JetStream enabled
  - Add NATS stream creation (AGENT_EXECUTION, AGENT_RESULTS)
  - Add kubectl wait commands for all components
  - Add idempotent checks for all operations
  - Make script executable
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.1, 8.2, 8.3, 8.4, 8.5, 16.1, 16.2, 16.4, 17.1, 17.2, 17.3_

- [x] **CHECKPOINT 1: Verify Local Preview Cluster Setup**
  - Run: `./tests/integration/scripts/setup-preview-cluster.sh`
  - Verify: `kubectl cluster-info --context kind-deepagnets-preview`
  - Verify: `kubectl get deployment -n crossplane-system`
  - Verify: `kubectl get deployment -n external-secrets -l app.kubernetes.io/name=external-secrets`
  - Verify: `kubectl get deployment -n cnpg-system`
  - Verify: `kubectl get statefulset -n nats`
  - Verify: `kubectl get clustersecretstore aws-parameter-store`
  - **Success:** All components deployed and Ready
  - **Stop here for review before proceeding to Phase 2**

---

## Phase 2: Platform API Installation

- [x] 4. Create Tier 3 platform API installation script
  - Create `tests/integration/scripts/install-platform-apis.sh`
  - Add logic to apply database XRDs from zerotouch-platform
  - Add logic to apply database Compositions from zerotouch-platform
  - Add logic to apply EventDrivenService XRD from zerotouch-platform
  - Add logic to apply EventDrivenService Composition from zerotouch-platform
  - Add kubectl wait for CRDs to be established
  - Add validation that XRDs are registered
  - Add idempotent checks
  - Make script executable
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 16.3, 16.4, 17.3_

- [x] **CHECKPOINT 2: Verify Platform API Installation**
  - Run: `./tests/integration/scripts/install-platform-apis.sh`
  - Verify: `kubectl get xrd xpostgresinstances.database.bizmatters.io`
  - Verify: `kubectl get xrd xdragonflyinstances.database.bizmatters.io`
  - Verify: `kubectl get xrd xeventdrivenservices.platform.bizmatters.io`
  - Verify: `kubectl get composition postgres-instance`
  - Verify: `kubectl get composition dragonfly-instance`
  - Verify: `kubectl get composition event-driven-service`
  - **Success:** All XRDs Established, all Compositions installed
  - **Stop here for review before proceeding to Phase 3**

---

## Phase 3: Service Deployment

- [x] 5. Create Tier 3 deployment script
  - Create `tests/integration/scripts/deploy-service.sh`
  - Add Docker image build for deepagents-runtime
  - Add image tagging as agent-executor:ci-test
  - Add kind load docker-image command
  - Add namespace creation (intelligence-deepagents)
  - Add logic to apply ExternalSecret manifests from deepagents-runtime/platform/claims/intelligence-deepagents/external-secrets/ (only llm-keys-es.yaml, skip image-pull-secret-es.yaml since image is loaded into Kind)
  - Add kubectl wait for ExternalSecrets to sync (check status.conditions)
  - Add kubectl wait for Kubernetes secrets to be created (agent-executor-llm-keys)
  - Add logic to apply claims in sync-wave order
  - Add kubectl wait for database connection secrets
  - Add kubectl wait for agent-executor pod ready
  - Add resource verification checks
  - Add idempotent checks
  - Make script executable
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 9.4, 9.5, 16.1, 16.4, 17.1, 17.2, 17.4_

- [x] **CHECKPOINT 3: Verify Service Deployment**
  - Run: `./tests/integration/scripts/deploy-service.sh`
  - Verify: `kubectl get namespace intelligence-deepagents`
  - Verify: `kubectl get externalsecret agent-executor-llm-keys -n intelligence-deepagents`
  - Verify: `kubectl get secret agent-executor-llm-keys -n intelligence-deepagents`
  - Verify: `kubectl get postgresinstance agent-executor-db -n intelligence-deepagents`
  - Verify: `kubectl get dragonflyinstance agent-executor-cache -n intelligence-deepagents`
  - Verify: `kubectl get secret agent-executor-db-conn -n intelligence-deepagents`
  - Verify: `kubectl get secret agent-executor-cache-conn -n intelligence-deepagents`
  - Verify: `kubectl get eventdrivenservice deepagents-runtime -n intelligence-deepagents`
  - Verify: `kubectl get deployment deepagents-runtime -n intelligence-deepagents`
  - Verify: `kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=deepagents-runtime -n intelligence-deepagents --timeout=300s`
  - **Success:** All claims applied, all secrets created, pod Running and Ready
  - **Stop here for review before proceeding to Phase 4**

---

## Phase 4: Integration Tests

- [ ] 6. Create Tier 3 test execution script
  - Create `tests/integration/scripts/run-tests.sh`
  - Add port-forwarding setup for services
  - Add environment variable configuration for tests
  - Add pytest execution with coverage
  - Add JUnit XML test result generation
  - Add coverage report generation (XML and HTML)
  - Add proper exit code handling
  - Make script executable
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 7. Update existing integration tests for CI environment
  - Review `tests/integration/test_api.py`
  - Ensure tests work with Kind cluster networking
  - Update connection strings if needed
  - Verify tests use environment variables correctly
  - _Requirements: 10.1, 10.2_

- [ ] **CHECKPOINT 4: Verify Integration Tests Pass**
  - Run: `./tests/integration/scripts/run-tests.sh`
  - Verify: `cat tests/integration/test-results.xml` (JUnit XML exists)
  - Verify: `cat tests/integration/coverage.xml` (Coverage report exists)
  - Verify: All tests pass (exit code 0)
  - **Success:** All integration tests pass, artifacts generated
  - **Stop here for review before proceeding to Phase 5**

---

## Phase 5: Orchestration & Cleanup

- [ ] 8. Create Tier 3 cleanup script
  - Create `tests/integration/scripts/cleanup.sh`
  - Add artifact collection (pod status, KEDA, claims, logs)
  - Add Kind cluster deletion
  - Add Docker resource cleanup
  - Add temporary file cleanup
  - Ensure script always succeeds (exit 0)
  - Make script executable
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 9. Create Tier 2 orchestration script
  - Create `scripts/ci/run-integration-tests.sh`
  - Add environment variable validation
  - Add zerotouch-platform clone logic
  - Add calls to Tier 3 scripts in correct order
  - Add error handling and exit code propagation
  - Add cleanup on failure
  - Make script executable
  - _Requirements: 11.1, 11.2, 11.4, 11.5_

- [ ] **CHECKPOINT 5: Verify Full Local Workflow**
  - Set env: `export AWS_ACCESS_KEY_ID="test" AWS_SECRET_ACCESS_KEY="test" PLATFORM_BRANCH="main"`
  - Run: `./scripts/ci/run-integration-tests.sh`
  - Verify: Script clones zerotouch-platform
  - Verify: All Tier 3 scripts execute in order
  - Verify: Exit code 0 on success
  - Verify: Cleanup runs even on failure
  - **Success:** Full workflow runs end-to-end locally
  - **Stop here for review before proceeding to Phase 6**

---

## Phase 6: GitHub Actions Integration

- [ ] 10. Configure AWS IAM and GitHub secrets
  - Create AWS IAM role for GitHub Actions OIDC
  - Configure trust policy for GitHub repository
  - Add SSM parameter read permissions
  - Add AWS_ROLE_ARN to GitHub repository secrets
  - Verify OPENAI_API_KEY exists in AWS Parameter Store
  - _Requirements: 9.1, 9.2_

- [x] 11. Create GitHub Actions workflow file
  - Create `.github/workflows/deepagnets-integration-tests.yml`
  - Configure trigger conditions (push, pull_request, workflow_dispatch)
  - Set up AWS OIDC authentication
  - Add step to export AWS credentials as environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
  - Add step to checkout deepagents-runtime repository
  - Add step to clone zerotouch-platform repository
  - Add step to execute Tier 2 orchestration script (with AWS credentials available)
  - Configure artifact upload for test results and coverage
  - Add PR comment step for test results
  - Set 45-minute timeout
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 14.1, 14.2, 14.3, 14.5, 15.1, 15.2_

- [ ] **CHECKPOINT 6: Verify GitHub Actions Manual Trigger**
  - Push workflow to GitHub
  - Go to Actions tab → Select workflow → Run workflow (manual)
  - Verify: AWS OIDC authentication succeeds
  - Verify: All workflow steps complete
  - Verify: Artifacts uploaded (test results, coverage)
  - Verify: Workflow completes within 45 minutes
  - **Success:** Workflow runs successfully via manual trigger
  - **Stop here for review before proceeding to Phase 7**

---

## Phase 7: Full CI/CD Automation

- [ ] 12. Test workflow locally
  - Install Kind, kubectl, helm locally
  - Run setup-preview-cluster.sh manually
  - Run install-platform-apis.sh manually
  - Run deploy-service.sh manually
  - Run run-tests.sh manually
  - Run cleanup.sh manually
  - Verify all scripts are idempotent
  - _Requirements: 16.4, 16.5_

- [ ] 13. Test workflow in GitHub Actions
  - Push workflow to feature branch
  - Trigger workflow manually
  - Monitor execution and timing
  - Review artifacts
  - Fix any issues
  - _Requirements: 1.3, 15.1, 15.2_

- [ ] 14. Enable workflow for pull requests
  - Update workflow triggers
  - Test on a sample PR
  - Verify PR comments work
  - Verify branch protection integration
  - _Requirements: 1.2, 14.5_

- [ ] 15. Create documentation
  - Create `tests/integration/README.md`
  - Document workflow architecture
  - Document script hierarchy
  - Document local testing instructions
  - Document troubleshooting steps
  - Add examples of running scripts manually
  - _Requirements: All_

- [ ] **CHECKPOINT 7: Verify Full CI/CD Integration**
  - Make test change: `echo "# Test" >> README.md`
  - Commit and push to trigger workflow
  - Create PR to main branch
  - Verify: Workflow triggers on push
  - Verify: Workflow triggers on PR
  - Verify: Path filtering works
  - Verify: PR comment shows test results
  - Verify: Branch protection requires workflow pass
  - **Success:** Full CI/CD automation working
  - **Final review and merge**

- [ ] 16. Final validation and documentation
  - Run full workflow end-to-end
  - Verify breaking change detection works
  - Update main README with CI badge
  - Document CI workflow in project docs
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
