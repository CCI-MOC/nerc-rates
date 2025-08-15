# NERC Rates Testing Guide

This directory contains tests for the NERC (New England Research Cloud) rates and outages system. The tests ensure that our billing and outage tracking systems work correctly.

## What Do These Tests Do?

These tests verify that our system can:
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
