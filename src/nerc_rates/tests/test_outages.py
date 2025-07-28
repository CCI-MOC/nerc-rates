import datetime
import os
from pathlib import Path

from nerc_rates import outages
from nerc_rates.outages.models import Outages

TEST_DIR = Path(__file__).parent
TEST_OUTAGES_FILE = TEST_DIR / "test-outages.yaml"


def test_load_from_url():
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query for May 2024 outage (MGHPCC Shutdown)
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack") == expected_output

    # Test partial overlap query
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-25", "2024-06-01", affected_service="NERC OpenStack") == expected_output


def test_get_outages_during_no_overlap():
    """Test querying for outages outside the outage timeframe returns empty list"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query before May outage
    assert o.get_outages_during("2024-04-01", "2024-05-21", "NERC OpenStack") == []

    # Query after August outage
    assert o.get_outages_during("2024-09-01", "2024-09-30", "NERC OpenStack") == []


def test_get_outages_during_different_services():
    """Test querying for different affected services"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test OpenStack service (May outage)
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack") == expected_output

    # Test OpenShift service (May outage)
    assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenShift") == expected_output

    # Test Storage service (August outage)
    expected_output = [
        (datetime.datetime.fromisoformat("2024-08-05T10:00:00Z"), datetime.datetime.fromisoformat("2024-08-05T16:00:00Z"))
    ]
    assert o.get_outages_during("2024-08-01", "2024-08-31", "NERC Storage") == expected_output

    # Test non-existent service
    assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC Compute") == []


def test_get_outages_during_multiple_outages():
    """Test querying when there are multiple outages"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query spanning May and June outages
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z")),
        (datetime.datetime.fromisoformat("2024-06-15T10:00:00Z"), datetime.datetime.fromisoformat("2024-06-15T18:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-01", "2024-06-30", "NERC OpenStack") == expected_output

    # Query only June outage
    expected_output = [
        (datetime.datetime.fromisoformat("2024-06-15T10:00:00Z"), datetime.datetime.fromisoformat("2024-06-15T18:00:00Z"))
    ]
    assert o.get_outages_during("2024-06-01", "2024-06-30", "NERC OpenStack") == expected_output


def test_get_outages_during_multiple_timeframes():
    """Test outage with multiple timeframes"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query spanning both timeframes in July (Extended Maintenance)
    expected_output = [
        (datetime.datetime.fromisoformat("2024-07-10T08:00:00Z"), datetime.datetime.fromisoformat("2024-07-10T18:00:00Z")),
        (datetime.datetime.fromisoformat("2024-07-12T08:00:00Z"), datetime.datetime.fromisoformat("2024-07-12T18:00:00Z"))
    ]
    assert o.get_outages_during("2024-07-01", "2024-07-31", "NERC OpenStack") == expected_output

    # Query only first timeframe
    expected_output = [
        (datetime.datetime.fromisoformat("2024-07-10T08:00:00Z"), datetime.datetime.fromisoformat("2024-07-10T18:00:00Z"))
    ]
    assert o.get_outages_during("2024-07-10", "2024-07-11", "NERC OpenStack") == expected_output


def test_get_outages_during_boundary_conditions():
    """Test edge cases with exact boundary conditions"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query that starts exactly when May outage starts
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-22T08:00:00Z", "2024-06-01", "NERC OpenStack") == expected_output

    # Query that ends exactly when May outage ends
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-01", "2024-05-28T23:00:00Z", "NERC OpenStack") == expected_output


def test_get_outages_during_partial_overlap():
    """Test partial overlap scenarios with query window adjustments"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Query window starts after May outage starts but ends before outage ends
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"), datetime.datetime.fromisoformat("2024-05-27T00:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-25", "2024-05-27", "NERC OpenStack") == expected_output

    # Query window starts before May outage but ends during outage
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-20", "2024-05-25", "NERC OpenStack") == expected_output


def test_load_from_file():
    """Test loading outages from file"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test that we can load and query May outage
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
    ]
    assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack") == expected_output


def test_empty_outages():
    """Test behavior with empty outages list"""
    # Create empty outages object for testing
    empty_outages = Outages([])

    # Should return empty list for any query
    assert empty_outages.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack") == []
    assert empty_outages.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenShift") == []
