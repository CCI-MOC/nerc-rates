# NERC Rates Testing Guide

This directory contains tests for the NERC (New England Research Cloud) rates and outages system. The tests ensure that our billing and outage tracking systems work correctly.

## What Do These Tests Do?

These tests verify that our system can:
- **Load rates data** correctly from files and URLs
- **Track outages** and their impact on different services
- **Calculate billing periods** accurately, accounting for service interruptions
- **Handle edge cases** that might occur in real-world scenarios

## How to Run the Tests

### Run All Tests
```bash
# From the project root directory
python -m pytest src/nerc_rates/tests/ -v
```

### Run Only Outages Tests
```bash
python -m pytest src/nerc_rates/tests/test_outages.py -v
```

### Run Only Rates Tests
```bash
python -m pytest src/nerc_rates/tests/test_rates.py -v
```

### Run a Specific Test
```bash
python -m pytest src/nerc_rates/tests/test_outages.py::test_multiple_outages_in_range -v
```

## Test Categories Explained

### **Rates Tests** (`test_rates.py`)
These tests ensure our billing rates system works correctly.

**Examples**:
- Testing that CPU rates change correctly over time (e.g., $0.013/hour in 2023, $0.15/hour in 2024)
- Ensuring no duplicate rate names exist
- Validating that date ranges don't overlap

### 🚨 **Outages Tests** (`test_outages.py`)
These tests verify our outage tracking and impact assessment.

## Detailed Test Scenarios

### 1. **Basic Loading** (`test_load_from_file`)
**What it tests**: Can we load outage data from a file?
**Why it matters**: If we can't load the data, nothing else works.
**Example**: "Load the test outages file and find the MGHPCC shutdown from May 22-29, 2024"

### 2. **Multiple Outages** (`test_multiple_outages_in_range`)
**What it tests**: Finding all outages within a time period
**Why it matters**: During busy periods, multiple maintenance windows might overlap
**Example**: "In Q2 2024, NERC OpenStack had both the annual shutdown (May 22-29) and network maintenance (June 10). Make sure we catch both."

### 3. **No Outages** (`test_no_outages_in_range`)
**What it tests**: Handling periods with no outages
**Why it matters**: Most of the time, services run normally
**Example**: "August 2024 had no planned outages for any service. Confirm the system returns an empty list."

### 4. **Partial Overlaps** (`test_partial_overlap_outages`)
**What it tests**: Outages that start before or end after our query period
**Why it matters**: Billing periods don't always align with outage windows
**Example**: "The MGHPCC shutdown runs May 22-29, but if we're calculating bills for May 25-30, we only count the overlap period (May 25-29) for billing adjustments"

### 5. **Service-Specific Impact** (`test_different_affected_services`)
**What it tests**: Different services affected by different outages
**Why it matters**: Not all outages affect all services
**Examples**:
- "Network maintenance affects OpenStack and Kubernetes, but not storage"
- "Storage upgrades only affect storage services, not compute"

### 6. **Non-Existent Services** (`test_service_not_affected`)
**What it tests**: Querying for services that don't exist
**Why it matters**: Prevents errors when someone types a wrong service name
**Example**: "If someone asks about 'NERC NonExistent' service, return empty results instead of crashing"

### 7. **Long Duration Outages** (`test_long_duration_outage`)
**What it tests**: Multi-day outages like major infrastructure upgrades
**Why it matters**: Major upgrades can last a week and affect billing significantly
**Example**: "The 2025 power infrastructure upgrade lasts 7 days and affects all services"

### 8. **Short Duration Outages** (`test_short_duration_outage`)
**What it tests**: Brief maintenance windows (few hours)
**Why it matters**: Short outages still need tracking for SLA compliance
**Example**: "6-hour cooling system maintenance should be accurately tracked"

### 9. **Multiple Timeframes** (`test_multiple_timeframes_same_outage`)
**What it tests**: Outages with multiple maintenance windows
**Why it matters**: Some maintenance happens in phases
**Example**: "Network maintenance has two windows: June 10 (4 hours) and June 17 (2 hours)"

### 10. **Year Boundaries** (`test_year_boundary_outages`)
**What it tests**: Outages spanning across years
**Why it matters**: Annual billing and reporting cross year boundaries
**Example**: "December 2024 security patching and January 2025 power upgrade both affect end-of-year reports"

### 11. **Timezone Handling** (`test_timezone_handling`)
**What it tests**: Correct parsing of UTC/Zulu time
**Why it matters**: NERC operates across time zones; UTC prevents confusion
**Example**: "All times stored as UTC (Zulu time) so Boston and California see the same outage times"

### 12. **All Services Affected** (`test_all_services_affected`)
**What it tests**: Major outages affecting everything
**Why it matters**: Data center-wide outages affect all billing
**Example**: "Power infrastructure upgrade affects OpenStack, OpenShift, Kubernetes, Storage, and Monitoring"

## Test Data

### `test_outages.yaml`
Contains synthetic but representative outage data including:
- **Annual shutdowns** (multi-day)
- **Quarterly maintenance** (multiple windows)
- **Emergency patches** (short duration)
- **Infrastructure upgrades** (affects all services)

All timestamps use **Zulu time (UTC)** format for consistency.
