from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from geopandas import GeoDataFrame  # type: ignore[import-untyped]

try:
    import pyogrio  # type: ignore[import-untyped]  # noqa: F401
except ImportError:
    ENGINE = "fiona"
else:
    ENGINE = "pyogrio"  # NOTE: much faster


def _get_cache_dir() -> Path:
    """Get cache dir, trying to use the same one as regionmask."""
    # TODO: look for cartopy's too or instead?
    import pooch  # type: ignore[import-untyped]

    try:
        import regionmask

        cache_dir_setting = regionmask.get_options()["cache_dir"]
    except Exception as e:
        msg = f"Failed to get regionmask's cache dir setting ({type(e).__name__}): {e}"
        warnings.warn(msg, stacklevel=2)
        cache_dir_setting = None

    if cache_dir_setting is None:
        cache_dir = pooch.os_cache("regionmask")
    else:
        cache_dir = cache_dir_setting

    return Path(cache_dir).expanduser()


def fetch(version: str, resolution: str, category: str, name: str) -> list[Path]:
    """Retrieve locally the files from a Natural Earth zip file,
    downloading from AWS if necessary.

    Parameters
    ----------
    version
        e.g. 'v4.1.0'
    resolution
        e.g. '50m'
    category
        e.g. 'cultural'
    name
        e.g. 'admin_1_states_provinces_lakes'
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


RESOLUTIONS: Final = ["10m", "50m", "110m"]
VERSIONS: Final = ["v4.1.0", "v5.0.0", "v5.0.1", "v5.1.0", "v5.1.1", "v5.1.2"]


def load(resolution: str, *, version: str = "v5.1.2") -> GeoDataFrame:
    """Load Natural Earth states/provinces/lakes."""
    import geopandas as gpd

    if resolution not in RESOLUTIONS:
        s_allowed = ", ".join(f"'{r}'" for r in RESOLUTIONS)
        raise ValueError(f"resolution must be one of: {s_allowed}. Got {resolution!r}.")

    if version not in VERSIONS:
        s_allowed = ", ".join(f"'{v}'" for v in VERSIONS)
        raise ValueError(f"version must be one of: {s_allowed}. Got {version!r}.")

    ps = fetch(
        version=version,
        resolution=resolution,
        category="cultural",
        name="admin_1_states_provinces_lakes",
    )

    (shp,) = [p for p in ps if p.name.endswith(".shp")]

    return gpd.read_file(shp, encoding="utf8", bbox=None, engine=ENGINE)
