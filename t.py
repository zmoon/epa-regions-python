from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import geopandas as gpd
import pooch
import regionmask


try:
    import pyogrio  # noqa: F401

    ENGINE = "pyogrio"
except ImportError:
    ENGINE = "fiona"



def _get_cache_dir() -> Path:
    try:
        cache_dir_setting = regionmask.get_options()["cache_dir"]
    except Exception:
        cache_dir_setting = None

    if cache_dir_setting is None:
        cache_dir = pooch.os_cache("regionmask")
    else:
        cache_dir = cache_dir_setting

    return Path(cache_dir).expanduser()


def _fetch_aws(version: str, resolution: str, category: str, name: str) -> list[Path]:

    base_url = "https://naturalearth.s3.amazonaws.com"

    bname = f"ne_{resolution}_{name}"
    fname = f"{bname}.zip"

    aws_version = version.replace("v", "")
    # NOTE: the 4.1.0 data is available under 4.1.1
    aws_version = aws_version.replace("4.1.0", "4.1.1")

    url = f"{base_url}/{aws_version}/{resolution}_{category}/{bname}.zip"

    path = _get_cache_dir() / f"natural_earth/{version}"
    unzipper = pooch.Unzip(extract_dir=bname)

    fns = pooch.retrieve(
        url,
        None,
        fname=fname,
        path=path,
        processor=unzipper,
    )

    return [Path(f) for f in fns]


VERSIONS = ["v4.1.0", "v5.0.0", "v5.1.2"]


class _NaturalEarthFeature(NamedTuple):
    # https://github.com/regionmask/regionmask/blob/e74cb22e976925ccd6c8ecaac8a9bfaadab44574/regionmask/defined_regions/_natural_earth.py#L126

    short_name: str
    title: str
    resolution: str
    category: str
    name: str

    def fetch(self, version):

        if version not in VERSIONS:

            versions = ", ".join(VERSIONS)
            raise ValueError(f"version must be one of {versions}. Got {version}.")

        return _fetch_aws(version, self.resolution, self.category, self.name)

    def shapefilename(self, version):

        ps = self.fetch(version)

        (p,) = filter(lambda x: x.name.endswith(".shp"), ps)

        return p

    def read(self, version, bbox=None):
        shpfilename = self.shapefilename(version=version)

        df = gpd.read_file(shpfilename, encoding="utf8", bbox=bbox, engine=ENGINE)

        return df


_us_states_50 = _NaturalEarthFeature(
    short_name="us_states_50",
    title="Natural Earth: US States 50m",
    resolution="50m",
    category="cultural",
    name="admin_1_states_provinces_lakes",
)
_us_states_10 = _NaturalEarthFeature(
    short_name="us_states_10",
    title="Natural Earth: US States 10m",
    resolution="10m",
    category="cultural",
    name="admin_1_states_provinces_lakes",
)




print(type(_get_cache_dir()), _get_cache_dir())

from pprint import pprint

pprint(_fetch_aws("v5.0.0", "50m", "cultural", "admin_1_states_provinces_lakes"))

import pandas as pd; pd.set_option("display.max_rows", 100)

# NOTE: seems Guam only available in the 10m
gdf = _us_states_10.read("v5.1.2")

# sov_a3 = US1 includes Guam and PR
# Guam's iso_a2 is GU and admin is Guam

# Palauli
# gdf.dropna(subset="name")[gdf.name.str.contains("Palau").dropna()].T
# has sov_a3 = WSM and admin = Samoa

# There is a 'Northern Mariana Islands' admin
# And a 'American Samoa' admin (and 'Samoa' as well)
# And a 'Marshall Islands' admin
# And 'Palau' admin
# No 'Micronesia' admin, it includes the above, but 'Federated States of Micronesia'
# Also 'United States Minor Outlying Islands' (UM) should be included according to https://www.epa.gov/pi
