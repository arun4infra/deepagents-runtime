# Verify Deliverables Tool

## Overview

The `verify_deliverables` tool performs Quality Control (QC) checks after each specialist agent completes, verifying that all mandatory deliverable files exist in the filesystem.

## Purpose

This tool prevents the workflow from proceeding when a specialist agent fails to create required files, catching issues early before they cascade to downstream agents.

## Usage

### Basic Usage

```python
verify_deliverables(agent_name="Impact Analysis Agent")
```

### Available Agents

- `"Guardrail Agent"`
- `"Impact Analysis Agent"`
- `"Workflow Spec Agent"`
- `"Agent Spec Agent"`
- `"Multi-Agent Compiler Agent"`

## Mandatory Deliverables Per Agent

### Guardrail Agent
- **Files:** `/guardrail_assessment.md`
- **Description:** Guardrail assessment document with security and policy validation
- **Content Validation:**
  - Must contain: `## Overall Assessment`
  - Must contain: `Status:`
  - Must contain: `## Contextual Guardrails`

### Impact Analysis Agent
- **Files:** `/impact_assessment.md`
- **Description:** Impact assessment with file-by-file implementation plan
- **Content Validation:**
  - Must contain: `requirements.md`
  - Must contain: `constitution.md`
  - Must contain: `plan.md`
  - Must contain: `## File-by-File Implementation Plan`
  - Must contain: `## Constitutional Compliance Analysis`

### Workflow Spec Agent
- **Files:**
  - `/THE_SPEC/constitution.md`
  - `/THE_SPEC/plan.md`
  - `/THE_SPEC/requirements.md`
- **Description:** Workflow-level specification files (constitution, plan, requirements)
- **Content Validation:** None (existence check only)

### Agent Spec Agent
- **Files:** `/THE_CAST/` (directory must exist and contain at least one file)
- **Description:** Agent specification files in /THE_CAST/ directory
- **Content Validation:** Each `.md` file must contain:
  - `## System Prompt` section
  - `## Tools` section

### Multi-Agent Compiler Agent
- **Files:** `/definition.json`
- **Description:** Compiled workflow definition
- **Content Validation:** None (already validated by validate_definition tool)

## Return Values

### Success
```
✓ QC PASSED: All mandatory deliverables verified for Impact Analysis Agent
```

### Failure (Missing Files)
```
✗ QC FAILED: Deliverable validation failed for Impact Analysis Agent

Expected: Impact assessment with file-by-file implementation plan

Missing files:
  - /impact_assessment.md

REQUIRED ACTION:
Re-invoke the Impact Analysis Agent with a detailed prompt specifying what needs to be fixed.
The agent must create the missing files before proceeding to the next step.

Example revision prompt:
"The QC check failed. You must create the following missing files:
   - /impact_assessment.md

Please generate these files now according to the implementation plan."
```

### Failure (Content Validation)
```
✗ QC FAILED: Deliverable validation failed for Impact Analysis Agent

Expected: Impact assessment with file-by-file implementation plan

Content validation failures:
  - /impact_assessment.md: Missing required content 'requirements.md'
  - /impact_assessment.md: Missing required content '## File-by-File Implementation Plan'

REQUIRED ACTION:
Re-invoke the Impact Analysis Agent with a detailed prompt specifying what needs to be fixed.
The agent must fix the content validation issues before proceeding to the next step.

Example revision prompt:
"The QC check failed. You must fix the following content issues:
   - /impact_assessment.md: Missing required content 'requirements.md'
   - /impact_assessment.md: Missing required content '## File-by-File Implementation Plan'

Please generate/update these files now according to the implementation plan."
```

## Integration with Orchestrator

The orchestrator is configured to call this tool after each specialist completes:

```markdown
**Step 3: Conduct Impact Analysis.**
a.  Invoke the `ImpactAnalysisAgent`
b.  **QC Check:** Use `verify_deliverables(agent_name="Impact Analysis Agent")`
c.  **QA Gate:** If QC fails, re-invoke the agent with the missing files list
```

## Implementation Details

### File Path Handling
- Tool expects paths starting with `/` (e.g., `/THE_SPEC/plan.md`)
- Internally converts to relative paths for filesystem checks
- Supports both file and directory checks

### Directory Checks
- Paths ending with `/` are treated as directory checks
- Verifies directory exists AND contains at least one file
- Example: `/THE_CAST/` checks for non-empty directory

### Content Validation
- **Two-Phase Validation:** First checks file existence, then validates content
- **Case-Insensitive:** All content checks are case-insensitive
- **Agent-Specific:** Different agents have different content requirements
- **Optional:** Only configured agents have content validation
- **Detailed Errors:** Reports exactly which required strings are missing

### Content Validation Rules
1. **Guardrail Agent:** Checks for required sections (Overall Assessment, Status, Contextual Guardrails)
2. **Impact Analysis Agent:** Ensures implementation plan mentions all critical files (requirements.md, constitution.md, plan.md)
3. **Workflow Spec Agent:** No content validation (existence only)
4. **Agent Spec Agent:** Validates each agent file has System Prompt and Tools sections
5. **Multi-Agent Compiler Agent:** No content validation (already validated by validate_definition tool)

### Error Messages
- Clear indication of what's missing (files or content)
- Separate sections for file existence vs content validation failures
- Actionable guidance for fixing the issue
- Example revision prompt included in output

## Testing

Run the test suite:

```bash
cd deepagents-runtime
python -m pytest tests/integration/test_verify_deliverables.py -v --no-cov
```

## Benefits

1. **Early Detection** - Catches missing files immediately after agent execution
2. **Clear Feedback** - Provides specific list of missing files
3. **Actionable Guidance** - Includes example prompts for fixing issues
4. **Prevents Cascading Failures** - Stops workflow before downstream agents fail
5. **Automated QC** - No manual file checking required

## Example Workflow

```
1. Orchestrator invokes Impact Analysis Agent
2. Agent completes and returns success message
3. Orchestrator calls verify_deliverables(agent_name="Impact Analysis Agent")
4. Tool checks filesystem for /impact_assessment.md
5a. If file exists: Returns "✓ QC PASSED", workflow continues
5b. If file missing: Returns "✗ QC FAILED" with details
6. Orchestrator re-invokes agent with missing files list
7. Agent creates missing file
8. Orchestrator verifies again before proceeding
```

## Configuration

Deliverables are configured in `verify_deliverables.py`:

```python
AGENT_DELIVERABLES = {
    "Impact Analysis Agent": {
        "files": ["/impact_assessment.md"],
        "description": "Impact assessment with file-by-file implementation plan"
    },
    # ... other agents
}
```

To add a new agent or modify deliverables, update this dictionary.
