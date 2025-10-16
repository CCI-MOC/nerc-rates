import datetime
import textwrap

import pytest
import requests_mock

from nerc_rates import outages
from nerc_rates.models.outages_model import Outages

from pydantic import ValidationError


def get_timeframe(start: str, end: str) -> tuple[datetime.datetime, datetime.datetime]:
    """Helper to create a timeframe tuple from ISO date strings"""
    return (
        datetime.datetime.fromisoformat(start),
        datetime.datetime.fromisoformat(end),
    )


# Factory fixtures for building test data
@pytest.fixture
def outage_factory():
    """Factory for creating outage data structures"""

    def _factory(timeframes, url="https://example.org/test-outage"):
        return {
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
def example_single_outage(outage_factory, timeframe_factory):
    """Example single outage data for testing"""
    return [
        outage_factory(
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ]
        )
    ]


@pytest.fixture
def example_multiple_timeframes_outage(outage_factory, timeframe_factory):
    """Example outage with multiple timeframes for testing"""
    return [
        outage_factory(
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC Service"]
                ),
                timeframe_factory(
                    "2024-06-17T02:00:00Z", "2024-06-17T04:00:00Z", ["NERC Service"]
                ),
            ]
        )
    ]


@pytest.fixture
def example_multiple_outages(outage_factory, timeframe_factory):
    """Example multiple separate outages for testing multiple outage scenarios"""
    return [
        outage_factory(
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ],
            url="https://example.org/outage-1",
        ),
        outage_factory(
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC OpenStack"]
                )
            ],
            url="https://example.org/outage-2",
        ),
    ]


@pytest.fixture
def example_year_boundary_outages(outage_factory, timeframe_factory):
    """Example outages spanning year boundary for testing"""
    return [
        outage_factory(
            [
                timeframe_factory(
                    "2024-12-20T01:00:00Z", "2024-12-20T05:00:00Z", ["NERC OpenStack"]
                )
            ],
            url="https://example.org/year-boundary-outage-1",
        ),
        outage_factory(
            [
                timeframe_factory(
                    "2025-01-05T06:00:00Z", "2025-01-12T18:00:00Z", ["NERC OpenStack"]
                )
            ],
            url="https://example.org/year-boundary-outage-2",
        ),
    ]


@pytest.fixture
def example_timezone_offset_outage(outage_factory, timeframe_factory):
    """Example outage with timezone offset for testing timezone handling"""
    return [
        outage_factory(
            [
                timeframe_factory(
                    "2024-06-01T09:00:00-04:00",
                    "2024-06-01T11:30:00-04:00",
                    ["NERC OpenStack"],
                )
            ]
        )
    ]


@pytest.fixture
def sample_outage_yaml_text():
    """Sample outage YAML text for testing loading mechanisms"""
    return """
    - url: https://example.org/test-outage
      timeframes:
        - from: "2024-05-22T08:00:00Z"
          until: "2024-05-28T23:00:00Z"
          affected_services:
            - NERC OpenStack
    """


@pytest.mark.parametrize(
    "start, end, expected",
    [
        # Single outage fully within range
        (
            "2024-05-01",
            "2024-06-01",
            [get_timeframe("2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z")],
        ),
        # Start during outage (partial overlap)
        (
            "2024-05-25",
            "2024-05-30",
            [get_timeframe("2024-05-25T00:00:00Z", "2024-05-29T03:00:00Z")],
        ),
        # End during outage (partial overlap)
        (
            "2024-05-20",
            "2024-05-25",
            [get_timeframe("2024-05-22T12:00:00Z", "2024-05-25T00:00:00Z")],
        ),
        # No outages in range
        (
            "2024-08-01",
            "2024-08-31",
            [],
        ),
        # Query range completely within outage (Outage is longer than the date range we're checking)
        (
            "2024-05-24",
            "2024-05-28",
            [get_timeframe("2024-05-24T00:00:00Z", "2024-05-28T00:00:00Z")],
        ),
    ],
)
def test_outages_in_date_range(example_single_outage, start, end, expected):
    """Tests various scenarios for retrieving outages within date ranges.

    Covers:
    - Single outage fully within range
    - Partial overlaps clipped to date boundaries
    - No outages in requested range
    """
    outages = Outages.model_validate(example_single_outage)
    assert outages.get_outages_during(start, end, "NERC OpenStack") == expected


def test_multiple_outages_in_range(example_multiple_outages):
    """Confirms multiple outages within the range are returned for the service."""
    outages = Outages.model_validate(example_multiple_outages)
    expected = [
        get_timeframe("2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z"),
        get_timeframe("2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z"),
    ]
    assert (
        outages.get_outages_during("2024-05-01", "2024-07-01", "NERC OpenStack")
        == expected
    )


def test_service_not_affected(example_single_outage):
    """Ensures an unrelated service yields no matching outages within the range."""
    outages = Outages.model_validate(example_single_outage)
    assert (
        outages.get_outages_during("2024-05-01", "2024-06-01", "NERC NonExistent") == []
    )


def test_multiple_timeframes_same_outage(example_multiple_timeframes_outage):
    """Validates all timeframes under a single outage entry are returned for the service."""
    outages = Outages.model_validate(example_multiple_timeframes_outage)
    expected = [
        get_timeframe("2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z"),
        get_timeframe("2024-06-17T02:00:00Z", "2024-06-17T04:00:00Z"),
    ]
    assert (
        outages.get_outages_during("2024-06-01", "2024-06-30", "NERC Service")
        == expected
    )


def test_multiple_separate_outages(example_multiple_outages):
    """Tests filtering across multiple separate outage events with different service."""
    # Modify the fixture to use a different service name for diversity
    test_data = example_multiple_outages.copy()
    for outage in test_data:
        for timeframe in outage["timeframes"]:
            timeframe["affected_services"] = ["NERC Service"]

    outages = Outages.model_validate(test_data)
    expected = [
        get_timeframe("2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z"),
        get_timeframe("2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z"),
    ]
    assert (
        outages.get_outages_during("2024-05-01", "2024-07-01", "NERC Service")
        == expected
    )


def test_year_boundary_outages(example_year_boundary_outages):
    """Tests that outages spanning a year boundary are handled and returned correctly."""
    outages = Outages.model_validate(example_year_boundary_outages)
    expected = [
        get_timeframe("2024-12-20T01:00:00Z", "2024-12-20T05:00:00Z"),
        get_timeframe("2025-01-05T06:00:00Z", "2025-01-12T18:00:00Z"),
    ]
    assert (
        outages.get_outages_during("2024-12-01", "2025-02-01", "NERC OpenStack")
        == expected
    )


def test_timezone_offset_handling(example_timezone_offset_outage):
    """Ensures non-UTC timezone offsets raises a ValidationError."""
    with pytest.raises(
        ValidationError,
        match="Non-UTC timezone detected in outages data; Please convert to UTC or provide a UTC timezone.",
    ):
        Outages.model_validate(example_timezone_offset_outage)


def test_multiple_services_affected(example_single_outage):
    """Checks that outages affecting multiple services work correctly."""
    example_single_outage[0]["timeframes"][0]["affected_services"] = [
        "NERC OpenStack",
        "NERC Kubernetes",
        "NERC Storage",
    ]
    outages = Outages.model_validate(example_single_outage)
    expected = [get_timeframe("2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z")]
    # Test a few different services to ensure they all work the same
    for service in ["NERC OpenStack", "NERC Kubernetes", "NERC Storage"]:
        result = outages.get_outages_during("2024-05-01", "2024-05-31", service)
        assert result == expected


def test_naive_datetime_validation_error(example_single_outage):
    """Test that naive datetimes (datetimes without timezone info) raise validation errors."""
    # Modify the fixture to use naive datetimes (no timezone)
    example_single_outage[0]["timeframes"][0]["from"] = (
        "2024-05-22T12:00:00"  # No Z suffix
    )
    example_single_outage[0]["timeframes"][0]["until"] = (
        "2024-05-29T03:00:00"  # No Z suffix
    )

    # Should raise validation error for naive datetime
    with pytest.raises(ValidationError) as exc_info:
        Outages.model_validate(example_single_outage)

    validation_error = exc_info.value
    assert "Naive datetime without timezone information is not allowed" in str(
        validation_error
    )


def test_outages_loader_from_url(sample_outage_yaml_text):
    """Tests loading outages from URL."""
    expected = [get_timeframe("2024-05-22T08:00:00Z", "2024-05-28T23:00:00Z")]

    with requests_mock.Mocker() as m:
        m.get(outages.DEFAULT_OUTAGES_URL, text=sample_outage_yaml_text)
        outages_loaded = outages.load_from_url()

    assert (
        outages_loaded.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
        == expected
    )


def test_outages_loader_from_file(sample_outage_yaml_text, tmp_path):
    """Tests loading outages from file."""
    expected = [get_timeframe("2024-05-22T08:00:00Z", "2024-05-28T23:00:00Z")]

    # Write the sample YAML to a temporary file
    outages_file = tmp_path / "outages.yaml"
    outages_file.write_text(textwrap.dedent(sample_outage_yaml_text).strip() + "\n")

    outages_loaded = outages.load_from_file(str(outages_file))

    assert (
        outages_loaded.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
        == expected
    )


def test_no_duplicates_in_affected_services(example_single_outage):
    """Testing that Pydantic validation catches duplicate affected services"""
    example_single_outage[0]["timeframes"][0]["affected_services"] = [
        "NERC OpenStack",
        "NERC OpenStack",
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outages.model_validate(example_single_outage)

    validation_error = exc_info.value
    assert "affected_services must be unique" in str(validation_error)


def test_pydantic_validation_invalid_format():
    """Testing that Pydantic validation catches invalid outage YAML format."""

    # Invalid format - missing required fields, wrong types, etc.
    invalid_outage_data = [
        {
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
            "url": "not-a-valid-url",  # Invalid URL format
            "timeframes": "not-a-list",  # Wrong type - should be list
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outages.model_validate(invalid_outage_data)

    validation_error = exc_info.value

    # Verify that the validation error contains expected information
    error_details = str(validation_error)
    assert "validation error" in error_details.lower()

    # Verify we caught the expected types of errors (using sorted lists to catch duplicates)
    error_types = [error["type"] for error in validation_error.errors()]
    expected_error_types = [
        "missing",
        "value_error",
        "url_parsing",
        "list_type",
    ]
    assert sorted(error_types) == sorted(expected_error_types), (
        f"Expected error types {sorted(expected_error_types)}, got {sorted(error_types)}"
    )


def test_duplicate_url_validation(outage_factory, timeframe_factory):
    """Testing that Pydantic validation catches duplicate URLs in outages list."""
    duplicate_url = "https://example.org/duplicate-outage"

    duplicate_outage_data = [
        outage_factory(
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ],
            url=duplicate_url,
        ),
        outage_factory(
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC Service"]
                )
            ],
            url=duplicate_url,  # Same URL as first outage
        ),
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outages.model_validate(duplicate_outage_data)

    validation_error = exc_info.value
    assert f'found duplicate url "{duplicate_url}" in outages list' in str(
        validation_error
    )


def test_unique_urls_validation_passes(outage_factory, timeframe_factory):
    """Testing that unique URLs pass validation successfully."""
    unique_outage_data = [
        outage_factory(
            [
                timeframe_factory(
                    "2024-05-22T12:00:00Z", "2024-05-29T03:00:00Z", ["NERC OpenStack"]
                )
            ],
            url="https://example.org/outage-1",
        ),
        outage_factory(
            [
                timeframe_factory(
                    "2024-06-10T02:00:00Z", "2024-06-10T06:00:00Z", ["NERC Service"]
                )
            ],
            url="https://example.org/outage-2",
        ),
    ]

    # Should not raise any validation errors
    outages = Outages.model_validate(unique_outage_data)
    assert len(outages.root) == 2
