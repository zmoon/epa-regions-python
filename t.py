from __future__ import annotations

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


def get_regions_geopandas():
    import regionmask

    states_rm = regionmask.defined_regions.natural_earth_v5_0_0.us_states_50
    # TODO: other resolution

    states_gp = states_rm.to_geodataframe()

    for (n, office), states in regions.items():
        not_in = set(states) - set(states_gp.abbrevs)
        if not_in:
            print(f"R{n} has unavailable states/territories: {not_in}")
        states_gp.loc[states_gp.abbrevs.isin(states), "epa_region"] = f"R{n}"

    # regions_gp = states_gp[["epa_region", "geometry"]].dissolve(by="epa_region")
    regions_gp = states_gp.dissolve(by="epa_region", aggfunc={"abbrevs": list, "names": list})
    regions_gp["numbers"] = regions_gp.index.str.slice(1, None).astype(int)

    return regions_gp


def get_regions_regionmask():
    import regionmask

    regions_gp = get_regions_geopandas()

    regions_rm = regionmask.from_geopandas(
        regions_gp
        .assign(
            names_="Region " + regions_gp.numbers.astype(str) + " (" + regions_gp.abbrevs.str.join(", ") + ")",
            abbrevs_=regions_gp.index,
        ),
        numbers="numbers",
        names="names_",
        abbrevs="abbrevs_",
    )

    return regions_rm


if __name__ == "__main__":
    import itertools

    import matplotlib.pyplot as plt

    # Some checks
    for ((n1, _), states1), ((n2, _), states2) in itertools.combinations(regions.items(), 2):
        states1_set = set(states1)
        states2_set = set(states2)
        assert len(states1) == len(states1_set), f"R{n1} has duplicates"
        assert len(states2) == len(states2_set), f"R{n2} has duplicates"
        assert not states1_set & states2_set, f"R{n1} and R{n2} share constituents"

    regions_gp = get_regions_geopandas()
    regions_rm = get_regions_regionmask()

    regions_gp.plot(column="numbers", cmap="tab10", legend=False)

    plt.figure()
    regions_rm.plot(add_label=True)

    plt.show()
