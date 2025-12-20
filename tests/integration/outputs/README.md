# Test Outputs

This directory contains test execution artifacts from integration tests.

## Structure

Each test run creates a subdirectory `run_YYYYMMDD_HHMMSS/` containing all related artifacts:

```
outputs/
├── run_20251212_212748/          # Single test run directory
│   ├── test_run.log              # Complete test execution log
│   ├── all_events.json           # All streaming events captured
│   ├── checkpoints.json          # PostgreSQL checkpoints
│   ├── cloudevent.json           # Final CloudEvent emitted
│   ├── specialist_timeline.json  # Specialist execution timeline
│   └── summary.txt               # Human-readable execution summary
└── run_20251212_193045/          # Another test run
    └── ...
```

## Benefits

- **Easy to find**: All artifacts for a single test run are in one directory
- **Easy to clean**: Delete entire run directory to remove all related files
- **Easy to compare**: Compare directories to see differences between runs
- **Easy to share**: Zip a single directory to share test results

## Cleanup

These directories are generated during test runs and can be safely deleted.
They are useful for debugging test failures and analyzing agent behavior.

To clean up old test runs:
```bash
# Remove all test runs
rm -rf run_*

# Remove test runs older than 7 days
find . -name "run_*" -type d -mtime +7 -exec rm -rf {} +
```
