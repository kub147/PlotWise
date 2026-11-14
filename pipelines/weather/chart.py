"""Chart for the precipitation cross-check: April-September totals per year, one line per product."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"gridMET": "#2a78d6", "PRISM": "#eb6834", "IMERG": "#1baf7a", "POWER": "#eda100"}   # fixed colour per product
INK, MUTED, GRID = "#1a1a19", "#6b6a63", "#e6e4dc"


def crosscheck_chart(cc, field_id, path):
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
    for ax, (window, title) in zip(axes, (("annual", "Annual precipitation"), ("apr_sep", "April–September precipitation"))):
        ends = []
        for product in cc["products"]:
            series = cc["yearly"][window][product]
            years = [int(y) for y in series]
            if not years:
                continue
            values = [series[str(y)] for y in years]
            ax.plot(years, values, color=COLORS[product], linewidth=2, label=product)
            ends.append([values[-1], years[-1], product])
        ends.sort()
        span = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.07
        for i in range(1, len(ends)):               # keep the end labels from overlapping
            ends[i][0] = max(ends[i][0], ends[i - 1][0] + span)
        last_year = max(e[1] for e in ends)
        for y_pos, _, product in ends:      # one label column, so the spacing above holds
            ax.annotate(product, (last_year, y_pos), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.set_ylabel("mm", color=MUTED)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors=MUTED, length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.margins(x=0.02)
    axes[0].legend(loc="upper left", ncol=4, frameon=False, fontsize=9)
    fig.suptitle(f"Four precipitation products at field {field_id}", x=0.065, ha="left", fontsize=13, color=INK)
    fig.subplots_adjust(right=0.9, hspace=0.25, top=0.9)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"   wrote {path}")
