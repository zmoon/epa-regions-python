import itertools

import geopandas as gpd
import pytest

from epa_regions import get, REGIONS, to_regionmask
from epa_regions.load import RESOLUTIONS, VERSIONS

versions_test = ["v4.1.0", "v5.0.0", "v5.1.2"]


def test_versions_test_ok():
    assert set(versions_test) <= set(VERSIONS)
    assert versions_test[-1] == VERSIONS[-1]


def test_regions_def():
    assert len(REGIONS) == 10

    assert [r.number for r in REGIONS] == list(range(1, 11))

    for (n1, consts1), (n2, consts2) in itertools.combinations(
        [
            (r.number, r.constituents)
            for r in REGIONS
        ],
        2,
    ):
        states1_set = set(consts1)
        states2_set = set(consts2)
        assert len(consts1) == len(states1_set), f"R{n1} has duplicates"
        assert len(consts2) == len(states2_set), f"R{n2} has duplicates"
        assert not states1_set & states2_set, f"R{n1} and R{n2} share constituents"


def test_ne_s3_versions():
    import re
    from pathlib import Path

    import s3fs

    s3 = s3fs.S3FileSystem(anon=True)
    objs = s3.ls("naturalearth")

    re_ver = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
    version_dirs = []
    for o in objs:
        p = Path(o)
        d = s3.info(o)
        if d["type"] == "directory" and re_ver.fullmatch(p.name):
            version_dirs.append(p)

    versions = [
        f"v4.1.0" if p.name == "4.1.1" else f"v{p.name}"
        for p in version_dirs
    ]
    se_versions_set = set(versions)

    versions_set = set(VERSIONS)
    assert len(versions_set) == len(VERSIONS), "should be unique"

    assert versions_set == se_versions_set


@pytest.mark.parametrize(
    "resolution, version",
    list(itertools.product(RESOLUTIONS, versions_test)),
)
def test_get(resolution, version):
    gdf = get(resolution=resolution, version=version)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == len(REGIONS) == 10
    assert list(gdf) == [
        "epa_region",
        "geometry",
        "number",
        "constituents",
        "constituent_names",
        "epa_region_office",
    ]

    rm = to_regionmask(gdf)
    assert len(rm) == 10


def test_get_invalid():
    with pytest.raises(ValueError, match="resolution must be one of"):
        get(resolution="invalid", version="v5.1.2")

    with pytest.raises(ValueError, match="version must be one of"):
        get(resolution="50m", version="invalid")
