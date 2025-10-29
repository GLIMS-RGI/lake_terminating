from matplotlib import patches, collections
import numpy as np


def stretch_img(img, vmin, vmax):
    stretch = img.copy()
    for vn, vx, b in zip(vmin, vmax, range(img.shape[0])):
        stretch[b][stretch[b] < vn] = vn
        stretch[b][stretch[b] > vx] = vx
        stretch[b] = (stretch[b] - vn) / (vx - vn)

    return stretch

def add_bbox(ax, bar, ann):
    left, right = ann

    bbox_left = ax.transData.inverted().transform(left.get_window_extent())
    bbox_right = ax.transData.inverted().transform(right.get_window_extent())

    text_bot = min(bbox_left[:, 1].tolist() + bbox_right[:, 1].tolist())
    bar_top = bar.xy[1] + bar.get_height()

    text_left = min(bbox_left[:, 0])
    text_right = max(bbox_right[:, 0])

    width = text_right - text_left
    height = bar_top - text_bot

    bbox = patches.Rectangle((text_left - 0.05 * width, text_bot - 0.05 * height), 1.1*width, 1.3*height,
                             facecolor='w', edgecolor='k', alpha=0.9, capstyle='round', zorder=2.5)

    return bbox


def add_scalebar(ax):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    xscale = xmax - xmin
    yscale = ymax - ymin

    sb_length = max(np.floor(0.2 * xscale / 1000), 1) * 1000

    sbx = xmin + xscale * 0.08
    sby = ymin + yscale * 0.08

    hfact = 0.01 # 1% of the axis extent
    pad = 0.4

    # create the background box
    left = ax.text(sbx, sby - 0.01 * yscale, '0 km',
                   va='top', ha='center', size=10, color='k', zorder=2.5)
    right = ax.text(sbx + sb_length, sby - 0.01 * yscale, f"{int(sb_length / 1000)} km",
                    va='top', ha='center', size=10, color='k', zorder=2.5)

    full_bar = patches.Rectangle((sbx, sby), sb_length, hfact * yscale, color='k')
    half_bar = patches.Rectangle((sbx + 0.5 * sb_length, sby + pad/2 * hfact * yscale),
                                 0.495 * sb_length, (1-pad) * hfact * yscale, facecolor='w', edgecolor='none')

    bbox = add_bbox(ax, full_bar, (left, right))
    scalebar = collections.PatchCollection([bbox, full_bar, half_bar], match_original=True, zorder=2.5)
    ax.add_collection(scalebar)

    left.set_zorder(10)
    right.set_zorder(10)
