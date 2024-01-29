import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--info", action="store_true")
parser.add_argument("--resolution", "-r", default="10m")

args = parser.parse_args()

if args.info:
    import logging

    logging.basicConfig(level="INFO")

import matplotlib.pyplot as plt
import numpy as np

from . import get

regions = get(resolution=args.resolution)

fig, ax = plt.subplots(constrained_layout=True, figsize=(8, 4))
regions.plot(column="number", cmap="tab10", ax=ax)

xs = np.linspace(0.8, 0.98, 3)
ys = np.linspace(0.98, 0.75, 4)

i = 1
for y in ys:
    for x in xs:
        if i == 10 and not x == xs[-1]:
            continue
        ax.text(
            x,
            y,
            f"R{i}",
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=13,
            color=plt.cm.tab10.colors[i - 1],
            # weight="bold",
        )
        i += 1

plt.show()
