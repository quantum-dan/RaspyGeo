# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 09:38:05 2023

@author: dphilippus
"""

"""
Display utilities and testing.
"""

import matplotlib.pyplot as plt


cols = 'bgrcmk'


def plot_xs(xses):
    # Plot up to 6 cross-sections provided as a dictionary
    # of {name: hecgeo.Geometry}.  XSes are plotted on the same axes.
    fig, ax = plt.subplots()
    for (ix, nm) in enumerate(xses):
        geo = xses[nm].restore()
        x = [i[0] for i in geo["coordinates"]]
        y = [i[1] for i in geo["coordinates"]]
        bst_x = geo["banks"]
        bst_y = [y[x.index(bx)] if bx in x else 0 for bx in bst_x]
        ax.plot(x, y, color=cols[ix % len(cols)], label=nm)
        ax.scatter(bst_x, bst_y, color=cols[ix % len(cols)], label=nm + " Banks")
    ax.set(xlabel='Station', ylabel='Elevation')
    ax.legend()
    fig.show()


def plot_xspairs(old, new):
    for (o, n) in zip(old, new):
        plot_xs({"Original": o, "New": n})
        # plot_xs({"New": n})


def plot_profiles(reaches):
    # Plot up to 6 reach profiles (datum profiles) provided as a dictionary
    # of {name: hecgeo.Reach}.
    fig, ax = plt.subplots()
    for (ix, nm) in enumerate(reaches):
        ax.plot(
            reaches[nm].get_sta(),
            reaches[nm].datums,
            color=cols[ix], label=nm
            )
    ax.set(xlabel='River Station', ylabel='Datum Elevation')
    ax.legend()
    fig.show()
