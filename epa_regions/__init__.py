"""
EPA region definitions and representations in
regionmask and GeoPandas.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

logger = logging.getLogger(__name__)

__version__ = "0.0.1"

if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from regionmask import Regions


__all__: Final = [
    "regions",
    "get_regions_geopandas",
    "get_regions_regionmask",
    "__version__",
]


regions: Final[dict[tuple[int, str], list[str]]] = {
    # (number, regional office): [states/territories]
    # TODO: refactor to number: (regional office, [states/territories]), maybe with named tuple
    (1, "Boston"): [
        "CT",
        "ME",
        "MA",
        "NH",
        "RI",
        "VT",
        # "and 10 Tribal Nations"
    ],
    (2, "New York City"): [
        "NJ",
        "NY",
        "PR",  # Puerto Rico
        "VI",  # US Virgin Islands
        # "and eight Indian Nations"
    ],
    (3, "Philadelphia"): [
        "DE",
        "DC",  # Washington DC
        "MD",
        "PA",
        "VA",
        "WV",
        # "and 7 federally recognized tribes"
    ],
    (4, "Atlanta"): [
        "AL",
        "FL",
        "GA",
        "KY",
        "MS",
        "NC",
        "SC",
        "TN",
        # "and 6 Tribes"
    ],
    (5, "Chicago"): [
        "IL",
        "IN",
        "MI",
        "MN",
        "OH",
        "WI",
        # "and 35 Tribes"
    ],
    (6, "Dallas"): [
        "AR",
        "LA",
        "NM",
        "OK",
        "TX",
        # "and 66 Tribal Nations"
    ],
    (7, "Kansas City"): [
        "IA",
        "KS",
        "MO",
        "NE",
        # "and Nine Tribal Nations"
    ],
    (8, "Denver"): [
        "CO",
        "MT",
        "ND",
        "SD",
        "UT",
        "WY",
        # "and 28 Tribal Nations"
    ],
    (9, "San Francisco"): [
        "AZ",
        "CA",
        "HI",
        "NV",
        # TODO: strict=True option to include these and PR/VI
        # https://www.epa.gov/pi
        "AS",  # American Samoa
        "MP",  # Northern Mariana Islands
        "GU",  # Guam
        "UM",  # United States Minor Outlying Islands
        "FM",  # Federated States of Micronesia (independent from US since 1986?)
        "MH",  # Marshall Islands
        "PW",  # Palau
        # "and 148 Tribal Nations"
    ],
    (10, "Seattle"): [
        "AK",
        "ID",
        "OR",
        "WA",
        # "and 271 Tribal Nations"
    ],
}


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


def get(*, resolution: str = "10m", version: str = "v5.1.2") -> GeoDataFrame:
    """Load EPA regions as GeoPandas GeoDataFrame.

    The Natural Earth shapefiles are downloaded from AWS S3 and cached locally.

    pyogrio will be used as the read engine if available, for speed.

    Parameters
    ----------
    resolution
        Resolution of the map corresponding to the Natural Earth shapefiles
        (https://www.naturalearthdata.com/downloads/).
        Either '110m' (low-res), '50m' (medium) or '10m' (high-res, default).
        NOTE: Islands are only included with 10-m resolution.
    version
        Natural Earth version. For example, "v4.1.0", "v5.1.1".
        See https://github.com/nvkelso/natural-earth-vector/releases ,
        though not all versions are necessarily available on AWS.
    """
    import pandas as pd

    from .load import load

    gdf = load(resolution, version=version)
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
        gdf.loc[
            gdf["admin"].isin(CODE_TO_ADMIN.values()),
            ["geometry", "name", "admin", "iso_a2"],
        ]
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
    # Dissolve to EPA regions
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
    gdf = (
        gdf.assign(number=gdf["epa_region"].str.slice(1).astype(int))
        .sort_values(by="number")
        .reset_index(drop=True)
    )

    gdf = gdf[
        [
            "epa_region",
            "geometry",
            "number",
            "constituents",
            "constituent_names",
            "epa_region_office",
        ]
    ]

    return gdf


def to_regionmask(gdf: GeoDataFrame) -> Regions:
    """Convert to regionmask Regions."""
    import regionmask

    rm = regionmask.from_geopandas(
        gdf.assign(
            name_="Region "
            + gdf["number"].astype(str)
            + " ("
            + gdf["constituents"].str.join(", ")
            + ")",
            abbrev_=gdf["epa_region"],
        ),
        numbers="number",
        names="name_",
        abbrevs="abbrev_",
        name="EPA Regions",
        source=(
            "Natural Earth (https://www.naturalearthdata.com) / "
            "EPA (https://www.epa.gov/aboutepa/regional-and-geographic-offices)"
        ),    
        overlap=False,
    )

    return rm
