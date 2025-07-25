# NERC Rates
This repository stores rates and invoicing configuration for the New England
Research Cloud.

The values are stored in `rates.yaml` as a list with each item under the
following format. Each item in the list contains a `name` and `history`.
`history` is itself a list containing `value` (required), `from` (required),
and `until` (optional).

```yaml
- name: CPU SU Rate
  history:
    - value: 0.013
      from: 2023-06
      until: 2024-06
    - value: 0.15
      from: 2024-07
```

To make use of the rates and outages data, install the package and import the modules:

## Usage

### Loading Rates
```python
from nerc_rates import rates_loader as rates
rate_data = rates.load_from_url()
rate_data.get_value_at("CPU SU Rate", "2024-06", Decimal)
```

### Loading Outages
```python
from nerc_rates import outages_loader as outages
outage_data = outages.load_from_url()
outage_data.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
```

### Loading Rates from file
```python
from nerc_rates import rates_loader as rates
rate_data = rates.load_from_file("rates.yaml")
rate_data.get_value_at("CPU SU Rate", "2024-06", Decimal)
```

### Loading Outages from file
```python
from nerc_rates import outages_loader as outages
outage_data = outages.load_from_file("outages.yaml")
outage_data.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
```
