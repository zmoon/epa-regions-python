from __future__ import annotations

import itertools

import regionmask


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

# Some checks
for ((n1, _), states1), ((n2, _), states2) in itertools.combinations(regions.items(), 2):
    states1_set = set(states1)
    states2_set = set(states2)
    assert len(states1) == len(states1_set), f"R{n1} has duplicates"
    assert len(states2) == len(states2_set), f"R{n2} has duplicates"
    assert not states1_set & states2_set, f"R{n1} and R{n2} share constituents"
