import datetime
import os
import pathlib

from nerc_rates import outages

# Path to the test outages YAML file
TEST_OUTAGES_FILE = pathlib.Path(__file__).parent / "test_outages.yaml"


def test_load_from_file():
    """Test basic loading functionality from file"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test the first outage (MGHPCC Shutdown 2024)
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"), datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"))
    ]
    result = o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
    assert result == expected_output

    # Test partial range overlap
    expected_output = [
        (datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"), datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"))
    ]
    result = o.get_outages_during("2024-05-25", "2024-06-01", affected_service="NERC OpenStack")
    assert result == expected_output


def test_multiple_outages_in_range():
    """Test finding multiple outages within a date range"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test multiple outages for NERC OpenStack in Q2 2024
    result = o.get_outages_during("2024-05-01", "2024-07-01", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"), datetime.datetime.fromisoformat("2024-05-29T03:00:00Z")),
        (datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"), datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"))
    ]
    assert result == expected


def test_no_outages_in_range():
    """Test when no outages exist in the specified date range"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test a range with no outages (August 2024)
    result = o.get_outages_during("2024-08-01", "2024-08-31", "NERC OpenStack")
    assert result == []


def test_partial_overlap_outages():
    """Test outages that partially overlap with the query range"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test range that starts during an outage
    result = o.get_outages_during("2024-05-25", "2024-05-30", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"), datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"))
    ]
    assert result == expected

    # Test range that ends during an outage
    result = o.get_outages_during("2024-05-20", "2024-05-25", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"), datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"))
    ]
    assert result == expected


def test_different_affected_services():
    """Test filtering by different affected services"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test NERC Kubernetes outages
    result = o.get_outages_during("2024-06-01", "2024-07-01", "NERC Kubernetes")
    expected = [
        (datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"), datetime.datetime.fromisoformat("2024-06-10T06:00:00Z")),
        (datetime.datetime.fromisoformat("2024-06-17T02:00:00Z"), datetime.datetime.fromisoformat("2024-06-17T04:00:00Z"))
    ]
    assert result == expected

    # Test NERC Storage outages
    result = o.get_outages_during("2024-09-01", "2024-12-31", "NERC Storage")
    expected = [
        (datetime.datetime.fromisoformat("2024-09-15T20:00:00Z"), datetime.datetime.fromisoformat("2024-09-16T08:00:00Z")),
        (datetime.datetime.fromisoformat("2024-12-22T01:00:00Z"), datetime.datetime.fromisoformat("2024-12-22T03:00:00Z"))
    ]
    assert result == expected


def test_service_not_affected():
    """Test service that is not affected by any outages in range"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test a service that doesn't exist in any outages in this range
    result = o.get_outages_during("2024-05-01", "2024-06-01", "NERC NonExistent")
    assert result == []


def test_long_duration_outage():
    """Test handling of long-duration outages (multi-day)"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test the 7-day power infrastructure upgrade outage
    result = o.get_outages_during("2025-01-01", "2025-01-31", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"), datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"))
    ]
    assert result == expected


def test_short_duration_outage():
    """Test handling of short-duration outages (few hours)"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test the 6-hour cooling system maintenance
    result = o.get_outages_during("2025-03-01", "2025-03-02", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2025-03-01T10:00:00Z"), datetime.datetime.fromisoformat("2025-03-01T16:00:00Z"))
    ]
    assert result == expected


def test_multiple_timeframes_same_outage():
    """Test outages with multiple timeframes (e.g., Network Maintenance Q2 2024)"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test both timeframes of Network Maintenance
    result = o.get_outages_during("2024-06-01", "2024-06-30", "NERC Kubernetes")
    expected = [
        (datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"), datetime.datetime.fromisoformat("2024-06-10T06:00:00Z")),
        (datetime.datetime.fromisoformat("2024-06-17T02:00:00Z"), datetime.datetime.fromisoformat("2024-06-17T04:00:00Z"))
    ]
    assert result == expected


def test_year_boundary_outages():
    """Test outages that span across year boundaries"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # Test winter 2024 to early 2025 period
    result = o.get_outages_during("2024-12-01", "2025-02-01", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2024-12-20T01:00:00Z"), datetime.datetime.fromisoformat("2024-12-20T05:00:00Z")),
        (datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"), datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"))
    ]
    assert result == expected


def test_timezone_handling():
    """Test that timezone information is handled correctly"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    # The MGHPCC shutdown has UTC time, verify it's parsed correctly
    result = o.get_outages_during("2024-05-22", "2024-05-23", "NERC OpenStack")
    expected = [
        (datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"), datetime.datetime.fromisoformat("2024-05-23T00:00:00Z"))
    ]
    assert result == expected


def test_all_services_affected():
    """Test outages that affect all services (Power Infrastructure Upgrade)"""
    o = outages.load_from_file(str(TEST_OUTAGES_FILE))

    services = ["NERC OpenStack", "NERC OpenShift", "NERC Kubernetes", "NERC Storage", "NERC Monitoring"]

    for service in services:
        result = o.get_outages_during("2025-01-01", "2025-01-31", service)
        expected = [
            (datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"), datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"))
        ]
        assert result == expected, f"Service {service} should be affected by Power Infrastructure Upgrade"


def test_load_from_url_original():
    """Keep one original test that uses URL loading for backwards compatibility"""
    import requests_mock

    mock_response_text = """
    - name: MGHPCC Shutdown 2024
      url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
      timeframes:
        - from: "2024-05-22T08:00:00Z"
          until: "2024-05-28T23:00:00Z"
          affected_services:
            - NERC OpenStack
            - NERC OpenShift
    """
    with requests_mock.Mocker() as m:
        m.get(outages.DEFAULT_OUTAGES_URL, text=mock_response_text)
        o = outages.load_from_url()

        expected_output = [
            (datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
        ]
        assert o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack") == expected_output
