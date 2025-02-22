from __future__ import annotations

from pathlib import Path

from epa_regions import get


def write(resolution: str = "50m", *, version: str = "v5.1.2") -> Path:
    """Write zip-archive shapefile to CWD."""

    from tempfile import TemporaryDirectory
    from zipfile import ZipFile

    gdf = get(resolution=resolution, version=version).rename(
        columns={
            "epa_region": "region",
            "constituents": "consts",
            "epa_region_office": "office",
        }
    )[
        [
            "region",
            "number",
            "consts",
            "office",
            "geometry",
        ]
    ]

    # Note shapefile column names must be <= 10 characters
    assert all(len(c) <= 10 for c in gdf.columns)

    with TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)

        stem = f"epa-regions_ne-{version.replace('.', '-')}_{resolution}"
        assert "." not in stem
        gdf.to_file(d / f"{stem}.shp")

        z = Path.cwd() / f"{stem}.zip"
        with ZipFile(z, "w") as zf:
            for f in Path(tmpdir).rglob(f"{stem}.*"):
                zf.write(f, f.name)

    return z


if __name__ == "__main__":
    for res in ["10m", "50m", "110m"]:
        print(write(res))
