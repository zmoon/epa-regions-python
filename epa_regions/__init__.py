"""
EPA region definitions and representations in
GeoPandas and regionmask, derived from Natural Earth shapefiles.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, NamedTuple

logger = logging.getLogger(__name__)

__version__ = "0.0.5"

if TYPE_CHECKING:
    from geopandas import GeoDataFrame  # type: ignore[import-untyped]
    from pandas import Series
    from regionmask import Regions


__all__: Final = [
    "REGIONS",
    "get",
    "look_up",
    "to_regionmask",
    "__version__",
]


class Region(NamedTuple):
    number: int

    office: str
    """Regional office location, e.g. 'Denver'."""

    constituents: list[str]
    """States/territories.
    2-letter codes, e.g. 'CO' (Colorado), 'PR' (Puerto Rico), 'GU' (Guam).
    """


REGIONS: Final[list[Region]] = [
    Region(
        1,
        "Boston",
        [
            "CT",
            "ME",
            "MA",
            "NH",
            "RI",
            "VT",
            # "and 10 Tribal Nations"
        ],
    ),
    Region(
        2,
        "New York City",
        [
            "NJ",
            "NY",
            "PR",  # Puerto Rico
            "VI",  # US Virgin Islands
            # "and eight Indian Nations"
        ],
    ),
    Region(
        3,
        "Philadelphia",
        [
            "DE",
            "DC",  # Washington DC
            "MD",
            "PA",
            "VA",
            "WV",
            # "and 7 federally recognized tribes"
        ],
    ),
    Region(
        4,
        "Atlanta",
        [
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
    ),
    Region(
        5,
        "Chicago",
        [
            "IL",
            "IN",
            "MI",
            "MN",
            "OH",
            "WI",
            # "and 35 Tribes"
        ],
    ),
    Region(
        6,
        "Dallas",
        [
            "AR",
            "LA",
            "NM",
            "OK",
            "TX",
            # "and 66 Tribal Nations"
        ],
    ),
    Region(
        7,
        "Kansas City",
        [
            "IA",
            "KS",
            "MO",
            "NE",
            # "and Nine Tribal Nations"
        ],
    ),
    Region(
        8,
        "Denver",
        [
            "CO",
            "MT",
            "ND",
            "SD",
            "UT",
            "WY",
            # "and 28 Tribal Nations"
        ],
    ),
    Region(
        9,
        "San Francisco",
        [
            "AZ",
            "CA",
            "HI",
            "NV",
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
    ),
    Region(
        10,
        "Seattle",
        [
            "AK",
            "ID",
            "OR",
            "WA",
            # "and 271 Tribal Nations"
        ],
    ),
]
"""Region definitions."""


_OTHER_CODE_TO_ADMIN = {
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
_OTHER_ADMIN_TO_CODE = {v: k for k, v in _OTHER_CODE_TO_ADMIN.items()}


def get(
    *,
    resolution: str = "10m",
    version: str = "v5.1.2",
    states_only: bool = False,
) -> GeoDataFrame:
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
    states_only
        States (and DC) only.
        This only has an effect for the '10m' resolution.
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

    if states_only:
        other = pd.DataFrame()
    else:
        other = (
            gdf.loc[
                gdf["admin"].isin(_OTHER_ADMIN_TO_CODE),
                ["geometry", "name", "admin", "iso_a2"],
            ]
            .dissolve(by="admin", aggfunc={"name": list, "iso_a2": list})
            .rename(columns={"name": "constituent_names"})
            .reset_index(drop=False)
            .assign(abbrev=lambda df: df["admin"].map(_OTHER_ADMIN_TO_CODE.get))
            .rename(columns={"admin": "name"})
        )

        # Check code consistency
        for admin, iso_set in other.set_index("name")["iso_a2"].apply(set).items():
            assert isinstance(admin, str)
            assert len(iso_set) == 1
            assert iso_set.pop() == _OTHER_ADMIN_TO_CODE[admin]

        other = other.drop(columns=["iso_a2"])

    #
    # Combine
    #

    gdf = pd.concat([states, other], ignore_index=True, sort=False)

    #
    # Dissolve to EPA regions
    #

    for r in REGIONS:
        label = f"R{r.number}"
        not_in = set(r.constituents) - set(gdf["abbrev"])
        if states_only:
            not_in -= _OTHER_CODE_TO_ADMIN.keys()
        if not_in:
            logger.info(f"{label} has unavailable states/territories: {not_in}")
        loc = gdf["abbrev"].isin(r.constituents)
        gdf.loc[loc, "epa_region"] = label
        gdf.loc[loc, "epa_region_office"] = r.office

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
    """Convert a GeoDataFrame from the `get` function to regionmask Regions."""
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


def look_up(abbrs: Any, /) -> Series[str]:
    """Look up EPA region from 2-letter state/territory abbreviations,
    e.g. 'CO' (Colorado), 'PR' (Puerto Rico), 'GU' (Guam).

    Parameters
    ----------
    abbrs
        State/territory 2-letter abbreviation strings.
        `abbrs` should be able to be converted to a pandas Series.
    """
    import pandas as pd

    if not isinstance(abbrs, pd.Series):
        abbrs = pd.Series(abbrs)

    map_ = {c: f"R{r.number}" for r in REGIONS for c in r.constituents}
    cats = [f"R{r.number}" for r in REGIONS]

    res: Series[str] = (
        abbrs.map(map_)
        .rename("epa_region")
        .astype(pd.CategoricalDtype(cats, ordered=False))
    )

    return res
