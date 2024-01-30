# epa-regions-python

[EPA regions](https://www.epa.gov/aboutepa/regional-and-geographic-offices) with [GeoPandas](https://geopandas.org) / [regionmask](https://regionmask.readthedocs.io).

[![Version on PyPI](https://img.shields.io/pypi/v/epa-regions.svg)](https://pypi.org/project/epa-regions/)

![image](https://github.com/zmoon/epa-regions-python/assets/15079414/003d3c54-bb78-4d44-9c78-5717a935dd41)

### Installation

```
conda activate ...
conda install -c conda-forge geopandas regionmask pooch pyogrio
pip install epa-regions
```

### Usage

```python
import epa_regions

# GeoPandas GeoDataFrame
df = epa_regions.get(resolution="50m")

# regionmask Regions
reg = epa_regions.to_regionmask(df)
```
