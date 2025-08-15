import datetime
import textwrap

import pytest

from nerc_rates import outages_loader


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-05-01",
            "2024-06-01",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
                )
            ],
        )
    ],
)
def test_single_outage_in_range(tmp_path, yaml_text, start, end, service, expected):
    """Ensures a single outage fully within the range is returned for the requested service."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        # Start during outage
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-05-25",
            "2024-05-30",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
                )
            ],
        ),
        # End during outage
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-05-20",
            "2024-05-25",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"),
                )
            ],
        ),
    ],
)
def test_partial_overlap_outages(tmp_path, yaml_text, start, end, service, expected):
    """Verifies partial overlaps are clipped to the requested start or end date boundaries."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            - name: Network Maintenance Q2 2024
              url: https://nerc.mghpcc.org/event/network-maintenance-q2-2024/
              timeframes:
                - from: "2024-06-10T02:00:00Z"
                  until: "2024-06-10T06:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-05-01",
            "2024-07-01",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-05-22T12:00:00Z"),
                    datetime.datetime.fromisoformat("2024-05-29T03:00:00Z"),
                ),
                (
                    datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"),
                ),
            ],
        )
    ],
)
def test_multiple_outages_in_range(tmp_path, yaml_text, start, end, service, expected):
    """Confirms multiple outages within the range are returned in chronological order for the service."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-08-01",
            "2024-08-31",
            "NERC OpenStack",
            [],
        )
    ],
)
def test_no_outages_in_range(tmp_path, yaml_text, start, end, service, expected):
    """Asserts no outages are returned when none occur within the requested date range."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        # Kubernetes outages
        (
            """
            - name: Network Maintenance Q2 2024
              url: https://nerc.mghpcc.org/event/network-maintenance-q2-2024/
              timeframes:
                - from: "2024-06-10T02:00:00Z"
                  until: "2024-06-10T06:00:00Z"
                  affected_services:
                    - NERC Kubernetes
                - from: "2024-06-17T02:00:00Z"
                  until: "2024-06-17T04:00:00Z"
                  affected_services:
                    - NERC Kubernetes
            """,
            "2024-06-01",
            "2024-07-01",
            "NERC Kubernetes",
            [
                (
                    datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"),
                ),
                (
                    datetime.datetime.fromisoformat("2024-06-17T02:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-17T04:00:00Z"),
                ),
            ],
        ),
        # Storage outages
        (
            """
            - name: Storage Upgrade Fall 2024
              url: https://nerc.mghpcc.org/event/storage-upgrade-fall-2024/
              timeframes:
                - from: "2024-09-15T20:00:00Z"
                  until: "2024-09-16T08:00:00Z"
                  affected_services:
                    - NERC Storage
            - name: Security Patching Winter 2024
              url: https://nerc.mghpcc.org/event/security-patching-winter-2024/
              timeframes:
                - from: "2024-12-22T01:00:00Z"
                  until: "2024-12-22T03:00:00Z"
                  affected_services:
                    - NERC Storage
            """,
            "2024-09-01",
            "2024-12-31",
            "NERC Storage",
            [
                (
                    datetime.datetime.fromisoformat("2024-09-15T20:00:00Z"),
                    datetime.datetime.fromisoformat("2024-09-16T08:00:00Z"),
                ),
                (
                    datetime.datetime.fromisoformat("2024-12-22T01:00:00Z"),
                    datetime.datetime.fromisoformat("2024-12-22T03:00:00Z"),
                ),
            ],
        ),
    ],
)
def test_different_affected_services(
    tmp_path, yaml_text, start, end, service, expected
):
    """Checks filtering by affected service across outages with differing services and timeframes."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: MGHPCC Shutdown 2024
              url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
              timeframes:
                - from: "2024-05-22T12:00:00Z"
                  until: "2024-05-29T03:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-05-01",
            "2024-06-01",
            "NERC NonExistent",
            [],
        )
    ],
)
def test_service_not_affected(tmp_path, yaml_text, start, end, service, expected):
    """Ensures an unrelated service yields no matching outages within the range."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: Network Maintenance Q2 2024
              url: https://nerc.mghpcc.org/event/network-maintenance-q2-2024/
              timeframes:
                - from: "2024-06-10T02:00:00Z"
                  until: "2024-06-10T06:00:00Z"
                  affected_services:
                    - NERC Kubernetes
                - from: "2024-06-17T02:00:00Z"
                  until: "2024-06-17T04:00:00Z"
                  affected_services:
                    - NERC Kubernetes
            """,
            "2024-06-01",
            "2024-06-30",
            "NERC Kubernetes",
            [
                (
                    datetime.datetime.fromisoformat("2024-06-10T02:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-10T06:00:00Z"),
                ),
                (
                    datetime.datetime.fromisoformat("2024-06-17T02:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-17T04:00:00Z"),
                ),
            ],
        )
    ],
)
def test_multiple_timeframes_same_outage(
    tmp_path, yaml_text, start, end, service, expected
):
    """Validates all timeframes under a single outage entry are returned for the service."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: Security Patching Winter 2024
              url: https://nerc.mghpcc.org/event/security-patching-winter-2024/
              timeframes:
                - from: "2024-12-20T01:00:00Z"
                  until: "2024-12-20T05:00:00Z"
                  affected_services:
                    - NERC OpenStack
            - name: Power Infrastructure Upgrade 2025
              url: https://nerc.mghpcc.org/event/power-infrastructure-upgrade-2025/
              timeframes:
                - from: "2025-01-05T06:00:00Z"
                  until: "2025-01-12T18:00:00Z"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-12-01",
            "2025-02-01",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-12-20T01:00:00Z"),
                    datetime.datetime.fromisoformat("2024-12-20T05:00:00Z"),
                ),
                (
                    datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"),
                    datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"),
                ),
            ],
        )
    ],
)
def test_year_boundary_outages(tmp_path, yaml_text, start, end, service, expected):
    """Tests that outages spanning a year boundary are handled and returned correctly."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: Offset Outage Example
              url: https://example.org/outage/offset-example
              timeframes:
                - from: "2024-06-01T09:00:00-04:00"
                  until: "2024-06-01T11:30:00-04:00"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-06-01",
            "2024-06-02",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-06-01T13:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-01T15:30:00Z"),
                )
            ],
        )
    ],
)
def test_timezone_offset_handling(tmp_path, yaml_text, start, end, service, expected):
    """Ensures non-UTC timezone offsets are normalized to UTC in returned outage intervals."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "yaml_text, start, end, service, expected",
    [
        (
            """
            - name: Offset Outage Example
              url: https://example.org/outage/offset-example
              timeframes:
                - from: "2024-06-01T09:00:00-04:00"
                  until: "2024-06-01T11:30:00-04:00"
                  affected_services:
                    - NERC OpenStack
            """,
            "2024-06-01",
            "2024-06-02",
            "NERC OpenStack",
            [
                (
                    datetime.datetime.fromisoformat("2024-06-01T13:00:00Z"),
                    datetime.datetime.fromisoformat("2024-06-01T15:30:00Z"),
                )
            ],
        )
    ],
)
def test_timezone_offset_emits_warning(
    tmp_path, yaml_text, start, end, service, expected
):
    """Emits a warning when non-UTC timezone offsets are detected while loading outages."""
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    with pytest.warns(UserWarning, match="Non-UTC timezone detected"):
        outages = outages_loader.load_from_file(str(path))
    assert outages.get_outages_during(start, end, service) == expected


@pytest.mark.parametrize(
    "service",
    [
        "NERC OpenStack",
        "NERC OpenShift",
        "NERC Kubernetes",
        "NERC Storage",
        "NERC Monitoring",
    ],
)
def test_all_services_affected(tmp_path, service):
    """Checks that all listed services are reported as affected for the outage in the given window."""
    yaml_text = """
    - name: Power Infrastructure Upgrade 2025
      url: https://nerc.mghpcc.org/event/power-infrastructure-upgrade-2025/
      timeframes:
        - from: "2025-01-05T06:00:00Z"
          until: "2025-01-12T18:00:00Z"
          affected_services:
            - NERC OpenStack
            - NERC OpenShift
            - NERC Kubernetes
            - NERC Storage
            - NERC Monitoring
    """
    path = tmp_path / "outages.yaml"
    path.write_text(textwrap.dedent(yaml_text).strip() + "\n")
    outages = outages_loader.load_from_file(str(path))
    expected = [
        (
            datetime.datetime.fromisoformat("2025-01-05T06:00:00Z"),
            datetime.datetime.fromisoformat("2025-01-12T18:00:00Z"),
        )
    ]
    result = outages.get_outages_during("2025-01-01", "2025-01-31", service)
    assert result == expected, (
        f"Service {service} should be affected by Power Infrastructure Upgrade"
    )


def test_load_from_url():
    """Testing if outages can be fetched from URL using load_from_url"""
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
