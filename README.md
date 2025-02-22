# epa-regions-python

[EPA regions](https://www.epa.gov/aboutepa/regional-and-geographic-offices)
from [Natural Earth](https://www.naturalearthdata.com) data
with [GeoPandas](https://geopandas.org) / [regionmask](https://regionmask.readthedocs.io).

[![Version on PyPI](https://img.shields.io/pypi/v/epa-regions.svg)](https://pypi.org/project/epa-regions/)

![regions](https://github.com/zmoon/epa-regions-python/assets/15079414/003d3c54-bb78-4d44-9c78-5717a935dd41)

<details><summary>Code</summary>

```sh
python -m epa_regions -r 50m --states-only --save
```
</details>

## Installation

With `conda` (recommended):

<!--pytest.mark.skip-->

```
conda activate ...
conda install -c conda-forge geopandas regionmask pooch pyogrio
pip install epa-regions
```

`pip install epa-regions` does not install any dependencies,
as it is expected that you will have installed them with `conda`.

* `geopandas`: needed if you want to use `epa_regions.get()`
* `pooch`: for downloading/caching the shapefiles for `epa_regions.get()`
* `pyogrio`: for faster reading of shapefiles
* `regionmask`: needed if you want to use `epa_regions.to_regionmask()`

Note that `epa_regions.look_up()` requires only `pandas`,
and you can access the region definitions
(region number, office, and state/territory constituents)
at `epa_regions.REGIONS` without any 3rd-party dependencies.

`python -m epa_regions` needs `matplotlib`.

## Usage

```python
import epa_regions

# GeoPandas GeoDataFrame
epa = epa_regions.get(resolution="50m")

# Convert to regionmask Regions for use with gridded data
epa = epa_regions.to_regionmask(epa)
```

### Point data

![points](https://github.com/zmoon/epa-regions-python/assets/15079414/990dccc8-096b-4eb1-9e90-ec3920518aed)

<details><summary>Code</summary>

```python
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

import epa_regions

rng = np.random.default_rng(seed=123)

epa = epa_regions.get(resolution="50m")

# CONUS
lonmin, lonmax = -125, -66
latmin, latmax = 24, 50
n = 250
lon = rng.uniform(lonmin, lonmax, n)
lat = rng.uniform(latmin, latmax, n)
points = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(lon, lat, crs="EPSG:4326")
)

fig, ax = plt.subplots(constrained_layout=True, figsize=(4, 2.5))

epa.plot(column="number", ax=ax, alpha=0.6)
points.sjoin(epa, predicate="within").plot(column="number", ax=ax, ec="0.3", lw=1)

ax.set(xlim=(lonmin, lonmax), ylim=(latmin, latmax))
ax.axis("off")

fig.savefig("points.png", dpi="figure", bbox_inches="tight")
```
</details>

### Gridded data

![gridded](https://github.com/zmoon/epa-regions-python/assets/15079414/832087e1-456a-4cd5-8fd7-15342e12f73f)

<details><summary>Code</summary>

```python
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

import epa_regions

epa = epa_regions.to_regionmask(epa_regions.get(resolution="50m"))

# CONUS
lonmin, lonmax = -125, -66
latmin, latmax = 24, 50

ds = (
    xr.tutorial.open_dataset("air_temperature")
    .sel(lon=slice(lonmin + 360, lonmax + 360), lat=slice(latmax, latmin))
)
mask = epa.mask(ds.isel(time=0))

proj = ccrs.LambertConformal(central_longitude=-100)
tran = ccrs.PlateCarree()

fig = plt.figure(figsize=(6, 6), constrained_layout=True)

ax = fig.add_subplot(3, 1, (1, 2), projection=proj)

mask.plot.pcolormesh(
    levels=np.arange(mask.min() - 0.5, mask.max() + 1),
    ax=ax,
    transform=ccrs.PlateCarree(),
    cmap="tab10",
    cbar_kwargs=dict(
        orientation="horizontal",
        fraction=0.075,
        pad=0.05,
        ticks=np.arange(mask.min(), mask.max() + 1),
        format="R{x:.0f}",
        label="EPA Region",
    ),
)

ax.add_feature(cfeature.STATES, linewidth=0.7, edgecolor="0.3")
ax.coastlines()
ax.set_extent([lonmin, lonmax - 2, latmin, latmax], crs=tran)
ax.set_title("")

ax = fig.add_subplot(3, 1, 3)

(dt,) = np.unique(ds.time.diff("time"))

window = pd.Timedelta("30D")
(
    ds["air"].groupby(mask)
    .mean()
    .rolling(time=int(window / dt), center=True)
    .mean()
    .plot(
        hue="mask",
        ax=ax,
        add_legend=False,
    )
)

ax.set_xlabel("")
ax.text(
    0.01,
    0.97,
    f"{window.total_seconds() / 86400:g}-day rolling mean",
    ha="left",
    va="top",
    transform=ax.transAxes,
    fontsize=11,
)

fig.savefig("gridded.png", dpi="figure", bbox_inches="tight")
```
</details>
