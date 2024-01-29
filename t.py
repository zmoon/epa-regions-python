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
    """Get cache dir, trying to use the same one as regionmask."""
    # TODO: look for cartopy's too or instead?
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


def _fetch(version: str, resolution: str, category: str, name: str) -> list[Path]:
    """Retrieve locally the files from a Natural Earth zip file,
    downloading from AWS if necessary.
    """
    import pooch

    base_url = "https://naturalearth.s3.amazonaws.com"

    zip_stem = f"ne_{resolution}_{name}"
    fname = f"{zip_stem}.zip"

    aws_version = version.lstrip("v")

    # The 4.1.0 data is available under 4.1.1, according to regionmask
    if aws_version == "4.1.0":
        aws_version = "4.1.1"

    url = f"{base_url}/{aws_version}/{resolution}_{category}/{fname}"

    path = _get_cache_dir() / f"natural_earth/{version}"
    unzipper = pooch.Unzip(extract_dir=zip_stem)

    fns = pooch.retrieve(
        url,
        None,
        fname=fname,
        path=path,
        processor=unzipper,
    )

    return [Path(f) for f in fns]


RESOLUTIONS = ["10m", "50m", "110m"]
VERSIONS = ["v4.1.0", "v5.0.0", "v5.0.1", "v5.1.0", "v5.1.1", "v5.1.2"]


def _load(resolution: str, *, version: str = "v5.1.2") -> GeoDataFrame:
    import geopandas as gpd

    if resolution not in RESOLUTIONS:
        s_allowed = ", ".join(f"'{r}'" for r in RESOLUTIONS)
        raise ValueError(f"resolution must be one of: {s_allowed}. Got {resolution!r}.")

    if version not in VERSIONS:
        s_allowed = ", ".join(f"'{v}'" for v in VERSIONS)
        raise ValueError(f"version must be one of: {s_allowed}. Got {version!r}.")

    ps = _fetch(version=version, resolution=resolution, category="cultural", name="admin_1_states_provinces_lakes",)

    (shp,) = [p for p in ps if p.name.endswith(".shp")]

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
ADMIN_TO_CODE = {v: k for k, v in CODE_TO_ADMIN.items()}


def get_regions(*, resolution: str = "10m", version: str = "v5.1.2") -> GeoDataFrame:
    """
    Parameters
    ----------
    resolution : str
        Resolution of the map corresponding to the Natural Earth shapefiles
        (https://www.naturalearthdata.com/downloads/).
        Either '110m' (low-res), '50m' (medium) or '10m' (high-res, default).
        NOTE: Islands are only included with 10-m resolution.
    version : str
        Natural Earth version. For example, "v4.1.0", "v5.1.1".
        See https://github.com/nvkelso/natural-earth-vector/releases ,
        though not all versions are necessarily available on AWS.
    """
    from epa_regions import regions, logger

    gdf = _load(resolution, version=version)
    # NOTE: sov_a3 = 'US1' includes Guam and PR
    # NOTE: iso_a2 is the 2-letter country code

    gdf.columns = gdf.columns.str.lower()

    #
    # States + DC
    #

    states = (
        gdf[["geometry", "name", "admin", "postal"]]
        .query("admin == 'United States of America'")
        .drop(columns=["admin"])
        .rename(columns={"postal": "abbrev"})
    )

    #
    # Other
    #

    other = (
        gdf[["geometry", "name", "admin", "iso_a2"]]
        [gdf["admin"].isin(CODE_TO_ADMIN.values())]
        .dissolve(by="admin", aggfunc={"name": list, "iso_a2": list})
        .rename(columns={"name": "constituent_names"})
        .reset_index(drop=False)
        .assign(abbrev=lambda df: df["admin"].map(ADMIN_TO_CODE.get))
        .rename(columns={"admin": "name"})
    )

    # Check code consistency
    for admin, iso_set in other.set_index("name")["iso_a2"].apply(set).items():
        assert len(iso_set) == 1
        assert iso_set.pop() == ADMIN_TO_CODE[admin]

    other = other.drop(columns=["iso_a2"])

    #
    # Combine
    #

    gdf = pd.concat([states, other], ignore_index=True, sort=False)

    #
    # EPA regions
    #

    for (n, office), states in regions.items():
        not_in = set(states) - set(gdf.abbrev)
        if not_in:
            logger.info(f"R{n} has unavailable states/territories: {not_in}")
        loc = gdf.abbrev.isin(states)
        gdf.loc[loc, "epa_region"] = f"R{n}"
        gdf.loc[loc, "epa_region_office"] = office

    gdf = gdf.dissolve(
        by="epa_region",
        aggfunc={"abbrev": list, "name": list, "epa_region_office": "first"},
    )

    gdf = gdf.rename(
        columns={
            "abbrev": "constituents",
            "name": "constituent_names",
        }
    )

    gdf = gdf.reset_index(drop=False)
    gdf = gdf.assign(number=gdf["epa_region"].str.slice(1).astype(int)).sort_values(by="number").reset_index(drop=True)

    gdf = gdf[["epa_region", "geometry", "number", "constituents", "constituent_names", "epa_region_office",]]

    return gdf


if __name__ == "__main__":
    from pprint import pprint

    import pandas as pd

    pd.set_option("display.max_rows", 100)

    print(type(_get_cache_dir()), _get_cache_dir())

    pprint(_fetch("v5.0.0", "50m", "cultural", "admin_1_states_provinces_lakes"))

    import logging; logging.basicConfig(level="INFO")
    gdf = get_regions(resolution="110m")
