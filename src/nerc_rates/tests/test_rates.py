import datetime
from decimal import Decimal

import pytest
import requests_mock
from pydantic import ValidationError

from nerc_rates import rates
from nerc_rates.rates.models import Rates, RateItem, RateValue, RateType


def test_load_from_url():
    mock_response_text = """
    - name: CPU SU Rate
      type: "Decimal"
      history:
        - value: "0.013"
          from: 2023-06
    """
    with requests_mock.Mocker() as m:
        m.get(rates.DEFAULT_RATES_URL, text=mock_response_text)
        rates_obj = rates.load_from_url()
        assert isinstance(rates_obj.root["CPU SU Rate"], RateItem)


def test_invalid_date_order():
    rate = {"value": "1", "from": "2020-04", "until": "2020-03"}
    with pytest.raises(
        ValidationError, match="date_until must be after date_from"
    ):
        RateValue.model_validate(rate)


def test_invalid_rate_item_type():
    rate = {"name": "Test Rate", "type": "invalid_type",
            "history": [
            {"value": "1", "from": "2020-01"},
        ],
    }
    with pytest.raises(
        ValidationError, match="Input should be 'str', 'Decimal' or 'bool'"
    ):
        RateItem.model_validate(rate)


def test_missing_type_field():
    rate = {
        "name": "Test Rate Missing Type",
        "history": [
            {"value": "1.23", "from": "2023-01"},
        ],
    }
    with pytest.raises(
        ValidationError, match="type\n  Field required"
    ):
        RateItem.model_validate(rate)


@pytest.mark.parametrize(
    "rate",
    [
        # Two values with no end date
        {
            "name": "Test Rate",
            "type": "Decimal",
            "history": [
                {"value": "1", "from": "2020-01"},
                {"value": "2", "from": "2020-03"},
            ],
        },
        # Second value overlaps first value at end
        {
            "name": "Test Rate",
            "type": "Decimal",
            "history": [
                {"value": "1", "from": "2020-01", "until": "2020-04"},
                {"value": "2", "from": "2020-03"},
            ],
        },
        # Second value overlaps first value at start
        {
            "name": "Test Rate",
            "type": "Decimal",
            "history": [
                {"value": "1", "from": "2020-04", "until": "2020-06"},
                {"value": "2", "from": "2020-03", "until": "2020-05"},
            ],
        },
        # Second value is contained by first value
        {
            "name": "Test Rate",
            "type": "Decimal",
            "history": [
                {"value": "1", "from": "2020-01", "until": "2020-06"},
                {"value": "2", "from": "2020-03", "until": "2020-05"},
            ],
        },
    ],
)
def test_invalid_date_overlap(rate):
    with pytest.raises(ValidationError, match="date ranges overlap"):
        RateItem.model_validate(rate)


def test_rates_get_value_at():
    r = Rates.model_validate(
        [
            {
                "name": "Test Rate",
                "type": "str",
                "history": [
                    {"value": "1", "from": "2020-01", "until": "2020-12"},
                    {"value": "2", "from": "2021-01"},
                ],
            }
        ]
    )
    assert r.get_value_at("Test Rate", "2020-01", str) == "1"
    assert r.get_value_at("Test Rate", "2020-12", str) == "1"
    assert r.get_value_at("Test Rate", "2021-01", str) == "2"
    with pytest.raises(ValueError):
        assert r.get_value_at("Test Rate", "2019-01", str)


def test_fail_with_duplicate_names():
    with pytest.raises(
        ValidationError, match=r"found duplicate name .* in list"
    ):
        Rates.model_validate(
            [
                {
                    "name": "Test Rate",
                    "type": "Decimal",
                    "history": [
                        {"value": "1", "from": "2020-01", "until": "2020-12"},
                        {"value": "2", "from": "2021-01"},
                    ],
                },
                {
                    "name": "Test Rate",
                    "type": "Decimal",
                    "history": [
                        {"value": "1", "from": "2020-01", "until": "2020-12"},
                        {"value": "2", "from": "2021-01"},
                    ],
                },
            ]
        )


@pytest.fixture
def sample_rates():
    return Rates.model_validate(
        [
            # Decimal-typed RateItem
            {
                "name": "Decimal Rate",
                "type": "Decimal",
                "history": [{"value": "1.23", "from": "2020-01"}],
            },
            # Boolean-typed RateItem
            {
                "name": "Boolean Rate",
                "type": "bool",
                "history": [{"value": "true", "from": "2020-01"}],
            },
            # String-typed RateItem
            {
                "name": "String Rate",
                "type": "str",
                "history": [{"value": "standard", "from": "2020-01"}],
            },
        ]
    )


@pytest.mark.parametrize(
    "name, query_date, datatype, expected, raises",
    [
        ("Decimal Rate", "2020-01", Decimal, Decimal("1.23"), None),
        ("Boolean Rate", "2020-01", bool, True, None),
        ("String Rate", "2020-01", str, "standard", None),
        ("Decimal Rate", "2020-01", bool, None, TypeError),
        ("Boolean Rate", "2020-01", Decimal, None, TypeError),
    ],
)


def test_get_value_at_cases(sample_rates, name, query_date, datatype, expected, raises):
    if raises:
        with pytest.raises(raises):
            sample_rates.get_value_at(name, query_date, datatype)
    else:
        result = sample_rates.get_value_at(name, query_date, datatype)
        assert result == expected
