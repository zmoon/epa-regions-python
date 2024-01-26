from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

try:
    import pyogrio  # noqa: F401
except ImportError:
    ENGINE = "fiona"
else:
    ENGINE = "pyogrio"  # NOTE: much faster


def _get_cache_dir() -> Path:
    import pooch
    import regionmask

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
    import pooch

    base_url = "https://naturalearth.s3.amazonaws.com"

    bname = f"ne_{resolution}_{name}"
    fname = f"{bname}.zip"

    aws_version = version.replace("v", "")

    # The 4.1.0 data is available under 4.1.1, according to regionmask
    if aws_version == "4.1.0":
        aws_version = "4.1.1"

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


VERSIONS = ["v4.1.0", "v5.0.0", "v5.0.1", "v5.1.0", "v5.5.1", "v5.1.2"]
# TODO: test that lists the dirs in the S3 bucket and compares to this


class _NaturalEarthFeature(NamedTuple):
    # Based on:
    # https://github.com/regionmask/regionmask/blob/e74cb22e976925ccd6c8ecaac8a9bfaadab44574/regionmask/defined_regions/_natural_earth.py#L126

    short_name: str
    title: str
    resolution: str
    category: str
    name: str

    def fetch(self, version: str) -> list[Path]:
        if version not in VERSIONS:
            versions = ", ".join(VERSIONS)
            raise ValueError(f"version must be one of {versions}. Got {version}.")

        return _fetch_aws(version, self.resolution, self.category, self.name)

    def shapefile(self, version: str) -> Path:
        ps = self.fetch(version)

        (p,) = filter(lambda x: x.name.endswith(".shp"), ps)

        return p

    def read(self, version: str) -> GeoDataFrame:
        """
        Parameters
        ----------
        version
            Natural Earth version. For example, "v4.1.0", "v5.2.1".
            See https://github.com/nvkelso/natural-earth-vector/releases ,
            though not all versions are necessarily available on AWS.
        """
        import geopandas as gpd

        shp = self.shapefile(version=version)

        return gpd.read_file(shp, encoding="utf8", bbox=None, engine=ENGINE)


CODE_TO_ADMIN = {
    "PR": "Puerto Rico",
    "VI": "United States Virgin Islands",
    #
    "AS": "American Samoa",
    "MP": "Northern Mariana Islands",
    "GU": "Guam",
    "UM": "United States Minor Outlying Islands",
    "FM": "Federated States of Micronesia",
    "MH": "Marshall Islands",
    "PW": "Palau",
}


def get_regions(version: str = "v5.1.2") -> GeoDataFrame:
    _states_provinces_lakes_10 = _NaturalEarthFeature(
        short_name="states_provinces_lakes_10",
        title="Natural Earth: States, Provinces, and Lakes, 10-m",
        resolution="10m",
        category="cultural",
        name="admin_1_states_provinces_lakes",
    )
    # NOTE: seems Guam only available in the 10-m, probably the case for some of the other islands as well
    # NOTE: sov_a3 = 'US1' includes Guam and PR
    # NOTE: iso_a2 is the 2-letter code

    gdf = _states_provinces_lakes_10.read(version)

    rs = []
    for code, admin in CODE_TO_ADMIN.items():
        gdf_ = gdf.query(f"admin == '{admin}'")[["geometry", "name", "iso_a2"]]
        assert gdf_["iso_a2"].eq(code).all()
        r = gdf_.dissolve(aggfunc={"name": list})
        r = r.rename(columns={"name": "constituent_names"})
        r["name"] = admin
        rs.append(r)

    return pd.concat(rs).reset_index(drop=True)


if __name__ == "__main__":
    from pprint import pprint

    import pandas as pd

    pd.set_option("display.max_rows", 100)

    print(type(_get_cache_dir()), _get_cache_dir())

    pprint(_fetch_aws("v5.0.0", "50m", "cultural", "admin_1_states_provinces_lakes"))

    gdf = get_regions()
