"""
EPA region definitions and representations in
regionmask and GeoPandas.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

__version__ = "0.0.1"

if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from regionmask import Regions


__all__ = [
    "regions",
    "get_regions_geopandas",
    "get_regions_regionmask",
    "__version__",
]


regions: dict[tuple[int, str], list[str]] = {
    # (number, regional office): [states/territories]
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


def get_regions_geopandas(*, resolution: str = "50m") -> GeoDataFrame:
    """
    Parameters
    ----------
    resolution : str
        Resolution of the map. Either '50m' (medium, default) or '10m' (high-res).
        https://www.naturalearthdata.com/downloads/
    """
    import regionmask

    if resolution == "50m":
        states_rm = regionmask.defined_regions.natural_earth_v5_0_0.us_states_50
    elif resolution == "10m":
        states_rm = regionmask.defined_regions.natural_earth_v5_0_0.us_states_10
    else:
        raise ValueError(
            f"unknown or unsupported resolution {resolution!r}. "
            "Try '50m' (medium) or '10m' (high-res)."
        )

    states_gp = states_rm.to_geodataframe()

    for (n, office), states in regions.items():
        not_in = set(states) - set(states_gp.abbrevs)
        if not_in:
            logger.info(f"R{n} has unavailable states/territories: {not_in}")
        loc = states_gp.abbrevs.isin(states)
        states_gp.loc[loc, "epa_region"] = f"R{n}"
        states_gp.loc[loc, "epa_region_office"] = office

    regions_gp = states_gp.dissolve(
        by="epa_region",
        aggfunc={"abbrevs": list, "names": list},
    )
    regions_gp["number"] = regions_gp.index.str.slice(1, None).astype(int)
    regions_gp = regions_gp.rename(
        columns={
            "abbrevs": "constituents",
            "names": "constituent_names",
        }
    )

    return regions_gp


def get_regions_regionmask(*, resolution: str = "50m") -> Regions:
    """
    Parameters
    ----------
    resolution : str
        Resolution of the map. Either "50m" (medium, default) or "10m" (high-res).
        https://www.naturalearthdata.com/downloads/
    """
    import regionmask

    regions_gp = get_regions_geopandas(resolution=resolution)

    regions_rm = regionmask.from_geopandas(
        regions_gp.assign(
            name_="Region "
            + regions_gp["number"].astype(str)
            + " ("
            + regions_gp["constituents"].str.join(", ")
            + ")",
            abbrev_=regions_gp.index,
        ),
        numbers="number",
        names="name_",
        abbrevs="abbrev_",
        overlap=False,
    )

    return regions_rm
