"""
EPA region definitions and representations in
regionmask and GeoPandas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from regionmask import Regions


__all__ = [
    "regions",
    "get_regions_geopandas",
    "get_regions_regionmask",
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
    ],
    (2, "New York City"): [
        "NJ",
        "NY",
        "PR",  # Puerto Rico
        "VI",  # US Virgin Islands
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
    ],
    (5, "Chicago"): [
        "IL",
        "IN",
        "MI",
        "MN",
        "OH",
        "WI",
    ],
    (6, "Dallas"): [
        "AR",
        "LA",
        "NM",
        "OK",
        "TX",
    ],
    (7, "Kansas City"): [
        "IA",
        "KS",
        "MO",
        "NE",
    ],
    (8, "Denver"): [
        "CO",
        "MT",
        "ND",
        "SD",
        "UT",
        "WY",
    ],
    (9, "San Francisco"): [
        "AZ",
        "CA",
        "HI",
        "NV",
        # American Samoa
        # Northern Mariana Islands
        # Micronesia
        # Guam
        # Marshall Islands
        # Palau
    ],
    (10, "Seattle"): [
        "AK",
        "ID",
        "OR",
        "WA",
        # "and 271 native tribes"
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
            print(f"note: R{n} has unavailable states/territories: {not_in}")
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
