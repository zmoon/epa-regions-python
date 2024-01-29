from epa_regions import regions
from epa_regions.load import VERSIONS


def test_regions_def():
    import itertools

    for ((n1, _), states1), ((n2, _), states2) in itertools.combinations(
        regions.items(), 2
    ):
        states1_set = set(states1)
        states2_set = set(states2)
        assert len(states1) == len(states1_set), f"R{n1} has duplicates"
        assert len(states2) == len(states2_set), f"R{n2} has duplicates"
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
