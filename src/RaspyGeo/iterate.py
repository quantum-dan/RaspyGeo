# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 10:07:44 2023

@author: dphilippus
"""

"""
Interactive use happens here.
"""

from write_geo import read_modify
from geofun import set_afp, set_lfc


"""
Example scenarios:
def r1l(geo):
    return geo  .adjust_datums(0, 100, 500, 2000) \
                .adjust_geometry(
                    set_afp(10, 3, 4, lambda x: x/2,
                            2, 0.123, 0.246, 0.035, 0.017))


def r1u(geo):
    return geo.adjust_datums(200, 250)


# The argument to `run`
mods = {'RiverOne        ,Upper           ': r1u,
 'RiverOne        ,Lower           ': r1l}
"""


def run(inpath, outpath, scenarios):
    # Loops through scenarios, waiting for the user to confirm they
    # have run each.
    # It is up to the user to retrieve data in between and run scenarios.
    for scen in scenarios:
        read_modify(inpath, scen, outpath)
        input("Hit Enter when done ")
