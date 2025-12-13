# Orchestrator Prompt Updates - Tool-Based Validation & User-Friendly HALT

## Overview

Updated the orchestrator prompt to eliminate redundant manual validation, implement automatic retry logic, and provide user-friendly error messages that hide internal implementation details.

## Changes Made

### 1. Removed Redundant Manual Validation

**Before:**
```markdown
**QA Gate 1:** If QC passes, use `ReadFile` to review the `guardrail_assessment.md` 
artifact. If it fails, `HALT`.

**QA Gate 3a:** If QC passes, verify its success string and use `ListFiles` to 
confirm the deliverables. If it fails, `HALT`.
```

**After:**
```markdown
**QA Gate 1 (Retry Logic):** 
- If QC returns "✓ QC PASSED": Proceed to Step 3.
- If QC returns "✗ QC FAILED": Re-invoke the agent with error details. Repeat up to 3 times.
- If still failing after 3 attempts: HALT with user-friendly message.
```

**Rationale:**
- `verify_deliverables` tool already checks file existence AND content
- Manual `ReadFile` and `ListFiles` checks are redundant
- Tool provides detailed error messages for retries

### 2. Implemented Automatic Retry Logic

**New Pattern (Applied to All 5 QA Gates):**

```markdown
**QA Gate X (Retry Logic):**
- If QC returns "✓ QC PASSED": Proceed to next step.
- If QC returns "✗ QC FAILED": Re-invoke the agent with error details from tool.
- Repeat up to 3 times.
- If still failing after 3 attempts: HALT with user-friendly message.
```

**Features:**
- **Automatic Retry:** Orchestrator automatically re-invokes specialist on failure
- **Error Propagation:** Passes exact error details from tool to specialist
- **Re-Verification:** Calls `verify_deliverables` again after each retry
- **Retry Budget:** Maximum 3 attempts per specialist (existing budget reused)
- **Smart Progression:** Only proceeds if validation passes

### 3. User-Friendly HALT Messages

**Before (Internal Details Exposed):**
```
HALT: The WorkflowSpecAgent failed to create /THE_SPEC/requirements.md. 
The verify_deliverables tool reported missing files.
```

**After (User-Centric):**
```
HALT: Unable to complete workflow specification generation. 
Please review your request and try again.
```

**HALT Messages by Step:**

| Step | Specialist | User-Friendly HALT Message |
|------|-----------|---------------------------|
| 2 | Guardrail Agent | "Unable to complete workflow planning due to incomplete safety assessment." |
| 3 | Impact Analysis Agent | "Unable to complete workflow planning due to incomplete implementation blueprint." |
| 4 | Workflow Spec Agent | "Unable to complete workflow specification generation." |
| 5 | Agent Spec Agent | "Unable to complete agent specification generation." |
| 6 | Multi-Agent Compiler Agent | "Unable to complete workflow compilation." |

**Characteristics:**
- ✅ No mention of specialist agent names
- ✅ No mention of tool names (verify_deliverables)
- ✅ No technical file paths
- ✅ Generic, user-friendly terms
- ✅ Actionable guidance ("review your request and try again")

### 4. Updated Rules of Engagement

**Added:**
```markdown
**User-Friendly Error Messages:** When halting due to failures, your HALT message 
must be user-centric and avoid internal implementation details. Do NOT mention 
specialist agent names, tool names, or technical internals. Use generic terms like 
"workflow planning", "specification generation", or "validation" instead.
```

**Updated:**
```markdown
**Handle Revisions Intelligently:** When `verify_deliverables` reports validation 
failures, you must manage the revision process:
1. Re-invoke the specialist with the exact error details from the tool's output.
2. After re-invocation, call `verify_deliverables` again to verify the fix.
3. This revision loop has a strict budget of three (3) attempts per specialist.
```

### 5. Added Important Reminders

**New Section at End:**
```markdown
**Important Reminders:**
- Always use `verify_deliverables` tool for validation (never manual file checks)
- Always re-invoke specialists with exact error details from the tool
- Always verify again after each retry
- Keep HALT messages user-friendly (no internal terminology)
```

## Workflow Changes

### Before (Manual Validation)
```
1. Invoke specialist
2. Call verify_deliverables
3. If fails → manually check with ReadFile/ListFiles
4. If still fails → HALT with technical details
```

### After (Tool-Based Validation)
```
1. Invoke specialist
2. Call verify_deliverables
3. If fails → auto-retry with tool's error details (up to 3x)
4. Call verify_deliverables again after each retry
5. If passes → proceed
6. If all retries fail → HALT with user-friendly message
```

## Benefits

### 1. Eliminates Redundancy
- No duplicate file checking (tool handles everything)
- Single source of truth for validation
- Consistent validation logic

### 2. Automatic Error Recovery
- Specialists get multiple chances to fix issues
- Detailed error messages guide corrections
- Reduces false failures from transient issues

### 3. Better User Experience
- No confusing internal terminology
- Clear, actionable error messages
- Professional, polished output

### 4. Simplified Orchestrator Logic
- Less manual validation code
- Clear retry pattern
- Easier to maintain

## Example Execution Flow

### Scenario: Impact Analysis Agent Missing Content

**Attempt 1:**
```
1. Orchestrator invokes Impact Analysis Agent
2. Agent creates impact_assessment.md (but missing "requirements.md" mention)
3. Orchestrator calls verify_deliverables(agent_name="Impact Analysis Agent")
4. Tool returns: "✗ QC FAILED: Missing required content 'requirements.md'"
5. Orchestrator re-invokes agent with error details
```

**Attempt 2:**
```
6. Agent updates impact_assessment.md to include "requirements.md"
7. Orchestrator calls verify_deliverables again
8. Tool returns: "✓ QC PASSED"
9. Orchestrator proceeds to Step 4
```

**If All Attempts Failed:**
```
10. After 3 failed attempts
11. Orchestrator outputs: "HALT: Unable to complete workflow planning due to 
    incomplete implementation blueprint. Please review your request and try again."
12. User sees friendly message (no internal details)
```

## Testing Recommendations

1. **Test Retry Logic:** Verify orchestrator retries up to 3 times
2. **Test Error Propagation:** Confirm tool errors reach specialist
3. **Test Re-Verification:** Ensure tool called after each retry
4. **Test HALT Messages:** Verify no internal terminology in output
5. **Test Success Path:** Confirm normal flow still works

## Files Modified

1. ✅ `deepagents-runtime/tests/mock/prompts/builder_agent_orchestrator.md` (UPDATED)
2. ✅ `deepagents-runtime/tests/mock/ORCHESTRATOR_PROMPT_UPDATES.md` (NEW)

## Summary

The orchestrator now:
- ✅ Uses ONLY `verify_deliverables` tool for validation
- ✅ Automatically retries on failures (up to 3x per specialist)
- ✅ Provides user-friendly HALT messages
- ✅ Hides all internal implementation details
- ✅ Maintains quality through tool-based validation
- ✅ Reduces redundancy and complexity
