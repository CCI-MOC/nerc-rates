import datetime
import textwrap

import pytest
import requests_mock

from nerc_rates import outages_loader
from nerc_rates.models.outages import Outages

import logging
from pydantic import ValidationError


# Factory fixtures for building test data
@pytest.fixture
def outage_factory():
    """Factory for creating outage data structures"""

    def _factory(name, url, timeframes):
        return {
            "name": name,
            "url": url,
            "timeframes": timeframes,
        }

    return _factory


@pytest.fixture
def timeframe_factory():
    """Factory for creating timeframe data structures"""

    def _factory(from_dt, until_dt, affected_services):
        return {
            "from": from_dt,
            "until": until_dt,
            "affected_services": affected_services,
        }

    return _factory


# Fixtures for common outage data structures
@pytest.fixture
def example_mghpcc_shutdown_2024(outage_factory, timeframe_factory):
    """Example MGHPCC Shutdown 2024 outage data for testing"""
    return [
        outage_factory(
            "MGHPCC Shutdown 2024",
            "https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/",
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ],
        )
    ]


@pytest.fixture
def example_multiple_timeframes_outage(outage_factory, timeframe_factory):
    """Example outage with multiple timeframes for testing"""
    return [
        outage_factory(
            "Network Maintenance Q2 2024",
            "https://nerc.mghpcc.org/event/network-maintenance-q2-2024/",
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC Service"]
                ),
                timeframe_factory(
                    "2024-06-17T02:00:00Z", "2024-06-17T04:00:00Z", ["NERC Service"]
                ),
            ],
        )
    ]


@pytest.fixture
def example_multiple_events_outages(outage_factory, timeframe_factory):
    """Example multiple separate outages for testing"""
    return [
        outage_factory(
            "Storage Upgrade Fall 2024",
            "https://nerc.mghpcc.org/event/storage-upgrade-fall-2024/",
            [
                timeframe_factory(
                    "2024-09-15T20:00:00Z", "2024-09-16T08:00:00Z", ["NERC Service"]
                )
            ],
        ),
        outage_factory(
            "Security Patching Winter 2024",
            "https://nerc.mghpcc.org/event/security-patching-winter-2024/",
            [
                timeframe_factory(
                    "2024-12-22T01:00:00Z", "2024-12-22T03:00:00Z", ["NERC Service"]
                )
            ],
        ),
    ]


@pytest.fixture
def example_multiple_outages_2024(outage_factory, timeframe_factory):
    """Example multiple outages for testing chronological ordering"""
    return [
        outage_factory(
            "MGHPCC Shutdown 2024",
            "https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/",
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ],
        ),
        outage_factory(
            "Network Maintenance Q2 2024",
            "https://nerc.mghpcc.org/event/network-maintenance-q2-2024/",
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC OpenStack"]
                )
            ],
        ),
    ]


@pytest.fixture
def example_year_boundary_outages(outage_factory, timeframe_factory):
    """Example outages spanning year boundary for testing"""
    return [
        outage_factory(
            "Security Patching Winter 2024",
            "https://nerc.mghpcc.org/event/security-patching-winter-2024/",
            [
                timeframe_factory(
                    "2024-12-20T01:00:00Z", "2024-12-20T05:00:00Z", ["NERC OpenStack"]
                )
            ],
        ),
        outage_factory(
            "Power Infrastructure Upgrade 2025",
            "https://nerc.mghpcc.org/event/power-infrastructure-upgrade-2025/",
            [
                timeframe_factory(
                    "2025-01-05T06:00:00Z", "2025-01-12T18:00:00Z", ["NERC OpenStack"]
                )
            ],
        ),
    ]


@pytest.fixture
def example_timezone_offset_outage(outage_factory, timeframe_factory):
    """Example outage with timezone offset for testing timezone handling"""
    return [
        outage_factory(
            "Offset Outage Example",
            "https://example.org/outage/offset-example",
            [
                timeframe_factory(
                    "2024-06-01T09:00:00-04:00",
                    "2024-06-01T11:30:00-04:00",
                    ["NERC OpenStack"],
                )
            ],
        )
    ]


@pytest.fixture
def example_power_infrastructure_upgrade(outage_factory, timeframe_factory):
    """Example power infrastructure upgrade affecting all services for testing"""
    return [
        outage_factory(
            "Power Infrastructure Upgrade 2025",
            "https://nerc.mghpcc.org/event/power-infrastructure-upgrade-2025/",
            [
                timeframe_factory(
                    "2025-01-05T06:00:00Z",
                    "2025-01-12T18:00:00Z",
                    [
                        "NERC OpenStack",
                        "NERC OpenShift",
                        "NERC Kubernetes",
                        "NERC Storage",
                        "NERC Monitoring",
                    ],
                )
            ],
        )
    ]


def test_single_outage_in_range(example_mghpcc_shutdown_2024):
    """Ensures a single outage fully within the range is returned for the requested service."""
    outages = Outages.model_validate(example_mghpcc_shutdown_2024)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
            datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
        )
    ]
    assert (
        outages.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
        == expected
    )


@pytest.mark.parametrize(
    "start, end, expected",
    [
        # Start during outage
        (
            "2024-05-25",
            "2024-05-30",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
                )
            ],
        ),
        # End during outage
        (
            "2024-05-20",
            "2024-05-25",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"),
                )
            ],
        ),
    ],
)
def test_partial_overlap_outages(example_mghpcc_shutdown_2024, start, end, expected):
    """Verifies partial overlaps are clipped to the requested start or end date boundaries."""
    outages = Outages.model_validate(example_mghpcc_shutdown_2024)
    assert outages.get_outages_during(start, end, "NERC OpenStack") == expected


def test_multiple_outages_in_range(example_multiple_outages_2024):
    """Confirms multiple outages within the range are returned in chronological order for the service."""
    outages = Outages.model_validate(example_multiple_outages_2024)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
            datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
        ),
        (
            datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"),
            datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"),
        ),
    ]
    assert (
        outages.get_outages_during("2024-05-01", "2024-07-01", "NERC OpenStack")
        == expected
    )


def test_no_outages_in_range(example_mghpcc_shutdown_2024):
    """Asserts no outages are returned when none occur within the requested date range."""
    outages = Outages.model_validate(example_mghpcc_shutdown_2024)
    assert (
        outages.get_outages_during("2024-08-01", "2024-08-31", "NERC OpenStack") == []
    )


def test_service_not_affected(example_mghpcc_shutdown_2024):
    """Ensures an unrelated service yields no matching outages within the range."""
    outages = Outages.model_validate(example_mghpcc_shutdown_2024)
    assert (
        outages.get_outages_during("2024-05-01", "2024-06-01", "NERC NonExistent") == []
    )


def test_multiple_timeframes_same_outage(example_multiple_timeframes_outage):
    """Validates all timeframes under a single outage entry are returned for the service."""
    outages = Outages.model_validate(example_multiple_timeframes_outage)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"),
            datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"),
        ),
        (
            datetime.datetime.fromisoformat("2024-06-17T02:00:00Z"),
            datetime.datetime.fromisoformat("2024-06-17T04:00:00Z"),
        ),
    ]
    assert (
        outages.get_outages_during("2024-06-01", "2024-06-30", "NERC Service")
        == expected
    )


def test_multiple_separate_outages(example_multiple_events_outages):
    """Tests filtering across multiple separate outage events."""
    outages = Outages.model_validate(example_multiple_events_outages)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-09-15T20:00:00Z"),
            datetime.datetime.fromisoformat("2024-09-16T08:00:00Z"),
        ),
        (
            datetime.datetime.fromisoformat("2024-12-22T01:00:00Z"),
            datetime.datetime.fromisoformat("2024-12-22T03:00:00Z"),
        ),
    ]
    assert (
        outages.get_outages_during("2024-09-01", "2024-12-31", "NERC Service")
        == expected
    )


def test_year_boundary_outages(example_year_boundary_outages):
    """Tests that outages spanning a year boundary are handled and returned correctly."""
    outages = Outages.model_validate(example_year_boundary_outages)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-12-20T01:00:00Z"),
            datetime.datetime.fromisoformat("2024-12-20T05:00:00Z"),
        ),
        (
            datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"),
            datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"),
        ),
    ]
    assert (
        outages.get_outages_during("2024-12-01", "2025-02-01", "NERC OpenStack")
        == expected
    )


def test_timezone_offset_handling(example_timezone_offset_outage):
    """Ensures non-UTC timezone offsets are normalized to UTC in returned outage intervals."""
    outages = Outages.model_validate(example_timezone_offset_outage)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-06-01T13:00:00Z"),
            datetime.datetime.fromisoformat("2024-06-01T15:30:00Z"),
        )
    ]
    assert (
        outages.get_outages_during("2024-06-01", "2024-06-02", "NERC OpenStack")
        == expected
    )


def test_timezone_offset_emits_warning(example_timezone_offset_outage):
    """Emits a warning when non-UTC timezone offsets are detected while loading outages."""
    with pytest.warns(UserWarning, match="Non-UTC timezone detected"):
        outages = Outages.model_validate(example_timezone_offset_outage)
    expected = [
        (
            datetime.datetime.fromisoformat("2024-06-01T13:00:00Z"),
            datetime.datetime.fromisoformat("2024-06-01T15:30:00Z"),
        )
    ]
    assert (
        outages.get_outages_during("2024-06-01", "2024-06-02", "NERC OpenStack")
        == expected
    )


def test_multiple_services_affected(example_power_infrastructure_upgrade):
    """Checks that outages affecting multiple services work correctly."""
    outages = Outages.model_validate(example_power_infrastructure_upgrade)
    expected = [
        (
            datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"),
            datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"),
        )
    ]
    # Test a few different services to ensure they all work the same
    for service in ["NERC OpenStack", "NERC Kubernetes", "NERC Storage"]:
        result = outages.get_outages_during("2025-01-01", "2025-01-31", service)
        assert result == expected


def test_load_from_url():
    """Testing if outages can be fetched from URL using load_from_url"""
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
        m.get(outages_loader.DEFAULT_OUTAGES_URL, text=mock_response_text)
        o = outages_loader.load_from_url()

        expected_output = [
            (
                datetime.datetime.fromisoformat("2024-05-22T08:00:00Z"),
                datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"),
            )
        ]
        assert (
            o.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
            == expected_output
        )


def test_load_from_file(tmp_path):
    """Testing if outages can be loaded from file using load_from_file"""
    yaml_text = """
    - name: Test Outage
      url: https://example.org/test-outage
      timeframes:
        - from: "2024-01-01T00:00:00Z"
          until: "2024-01-02T00:00:00Z"
          affected_services:
            - NERC OpenStack
    """
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))

    expected = [
        (
            datetime.datetime.fromisoformat("2024-01-01T00:00:00Z"),
            datetime.datetime.fromisoformat("2024-01-02T00:00:00Z"),
        )
    ]
    assert (
        outages.get_outages_during("2024-01-01", "2024-01-03", "NERC OpenStack")
        == expected
    )


def test_pydantic_validation_invalid_format(caplog):
    """Testing that Pydantic validation catches invalid outage YAML format, run pytest with --log-cli-level=ERROR flag to see the errors"""

    # Invalid format - missing required fields, wrong types, etc.
    invalid_outage_data = [
        {
            # Missing 'name' field (required)
            "url": "https://example.org/test-outage",
            "timeframes": [
                {
                    "from": "invalid-date-format",  # Invalid date format
                    "until": "2024-01-02T00:00:00Z",
                    # Missing 'affected_services' field (required)
                }
            ],
        },
        {
            "name": 123,  # Wrong type - should be string
            "url": "not-a-valid-url",  # Invalid URL format
            "timeframes": "not-a-list",  # Wrong type - should be list
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outages.model_validate(invalid_outage_data)

    # Log the validation errors for visibility
    validation_error = exc_info.value
    logging.error(
        f"Pydantic caught {len(validation_error.errors())} validation errors:"
    )
    for i, error in enumerate(validation_error.errors(), 1):
        logging.error(
            f"  {i}. Location: {' -> '.join(str(loc) for loc in error['loc'])}"
        )
        logging.error(f"     Error: {error['msg']}")
        logging.error(f"     Type: {error['type']}")
        logging.error(f"     Input: {error['input']}")

    # Verify that the validation error contains expected information
    error_details = str(validation_error)
    assert "validation error" in error_details.lower()

    # Verify we caught the expected types of errors
    error_types = {error["type"] for error in validation_error.errors()}
    expected_error_types = {
        "missing",
        "value_error",
        "string_type",
        "url_parsing",
        "list_type",
    }
    assert expected_error_types.issubset(error_types), (
        f"Expected error types {expected_error_types}, got {error_types}"
    )
