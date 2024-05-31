import datetime

import requests_mock

from nerc_rates import outages

def test_load_from_url():
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

        expected_output = [
            (datetime.datetime.fromisoformat("2024-05-25T00:00:00Z"), datetime.datetime.fromisoformat("2024-05-28T23:00:00Z"))
        ]
        assert o.get_outages_during("2024-05-25", "2024-06-01", affected_service="NERC OpenStack") == expected_output
