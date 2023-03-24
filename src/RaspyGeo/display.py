# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 09:38:05 2023

@author: dphilippus
"""

"""
Display utilities and testing.
"""

import matplotlib.pyplot as plt
from parse_geo import parse
from geofun import set_afp, set_lfc
from write_geo import read_modify


cols = 'bgrcmk'


tkeys = ['Compton Creek   ,CC              ',
         'Rio Hondo Chnl  ,RHC             ',
         'Upper LA River  ,Above RH        ',
         'Upper LA River  ,RH to CC        ',
         'LA River        ,Below CC        ']


test_mods = {
    tkeys[0]: lambda x: x
                .adjust_geometry(
                set_afp(4, 1, 2, lambda w: w/3, 4, 0.1, 0.15, 0.1, 0.035)),
    tkeys[1]: lambda x: x
                .adjust_geometry(
                set_afp(8, 2, 4, lambda w: 10, 2, 0.1, 0.15, 0.1, 0.5),
                10000, 40000),
    tkeys[2]: lambda x: x
                .adjust_datums(0, -10, 80000, 120000)
                .adjust_geometry(
                set_afp(16, 0.5, 1, lambda w: w*0.75, 6, 0.017, 0.2, 0.1, 0.5))
    }


def testrun():
    read_modify('../../test.geo', test_mods, '../../test.edit.geo')


def test_afp():
    return set_afp(6, 1, 4, lambda w: w/2, 6, 0.017, 0.15, 0.1, 0.035)


def test_lfc():
    return set_lfc(10, 1, 4, 0.035, 0.1)


def test_reach():
    geo = parse("../../test.geo")
    return geo[list(geo.keys())[1]]


def test_xses():
    return list(test_reach().geometries.values())


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
        ax.plot(x, y, color=cols[ix], label=nm)
        ax.scatter(bst_x, bst_y, color=cols[ix], label=nm + " Banks")
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


def test_mod():
    rch = test_reach()
    old = rch.geometries.values()
    newr = rch.adjust_datums(0, -5, 10000, 25000).adjust_datums(
        -5, 5, 25001, 35000).adjust_datums(
        5, 0, 35001, 45000).adjust_geometry(
        test_afp(), 20000, 40000)
    new = newr.geometries.values()
    plot_profiles({"Original": rch, "New": newr})
    plot_xspairs(old, new)
