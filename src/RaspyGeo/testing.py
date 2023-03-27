# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 09:38:05 2023

@author: dphilippus
"""

"""
Display utilities and testing.
"""

from parse_geo import parse
from geofun import set_afp, set_lfc
from write_geo import read_modify
from display import *
from scenario import *


tkeys = ['Compton Creek   ,CC              ',
         'Rio Hondo Chnl  ,RHC             ',
         'Upper LA River  ,Above RH        ',
         'Upper LA River  ,RH to CC        ',
         'LA River        ,Below CC        ']


rpath = r"C:\Users\dphilippus\Dropbox\Home\Research\RaspyDev\RaspyGeo\TestProj\test.prj"


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


def test_reach(path="../../test.geo", ix=1):
    geo = parse(path)
    return geo[list(geo.keys())[ix]]


def test_xses(path="../../test.geo", ix=1):
    return test_reach(path, ix).geometries


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


geopath = "../../TestProj/test.g01"
geobase = '../../TestProj/test.g02'


def r1l(geo):
    return geo  .adjust_datums(0, 100, 500, 2000) \
                .adjust_geometry(
                    set_afp(10, 3, 4, lambda x: x/2,
                            2, 0.123, 0.246, 0.035, 0.017))


def r1u(geo):
    return geo.adjust_datums(200, 250)


mods = {'RiverOne        ,Upper           ': r1u,
 'RiverOne        ,Lower           ': r1l}


def testit():
    read_modify(geobase, mods, geopath)
