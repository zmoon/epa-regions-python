import itertools
# import logging; logging.basicConfig(level="INFO")

import matplotlib.pyplot as plt

from . import regions, get_regions_geopandas, get_regions_regionmask

# Some checks
for ((n1, _), states1), ((n2, _), states2) in itertools.combinations(
    regions.items(), 2
):
    states1_set = set(states1)
    states2_set = set(states2)
    assert len(states1) == len(states1_set), f"R{n1} has duplicates"
    assert len(states2) == len(states2_set), f"R{n2} has duplicates"
    assert not states1_set & states2_set, f"R{n1} and R{n2} share constituents"

regions_gp = get_regions_geopandas()
regions_rm = get_regions_regionmask()

fig, ax = plt.subplots(constrained_layout=True, figsize=(6, 3.1))
regions_gp.plot(column="number", cmap="tab10", legend=False, ax=ax)

fig = plt.figure(constrained_layout=True, figsize=fig.get_size_inches())
regions_rm.plot(add_label=True)

plt.show()
