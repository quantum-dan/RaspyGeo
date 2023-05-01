# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 10:07:44 2023

@author: dphilippus
"""

"""
Iterate through scenarios and retrieve results.
"""

from RaspyGeo.write_geo import read_modify
from RaspyGeo.geofun import set_afp, set_lfc
from raspy_auto import API, Ras


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

Test proj has 10 profiles.
"""


cols = "Scenario,ID,River,Reach,RS,Q,shear.lob,shear.mc,shear.rob,\
vel.lob,vel.mc,vel.rob,depth.lob,depth.mc,depth.rob\n"


def row_join(row):
    return ",".join([str(r) for r in row])


def twovalfix(vals, maxC=False, av=False):
    # Sometimes HEC-RAS will return just two values.  This fixes it to
    # distribute them across the overbanks and MC.
    # If maxC (max center), the max value goes in the MC, and the missing
    # value is set to 0.
    # If av (average), then all three are set to the mean.
    # If both are false, then it just returns three NAs.
    if len(vals) == 3:
        return vals
    if len(vals) == 1:
        return [0, vals[0], 0]
    if maxC:
        if vals[0] > vals[1]:  # larger is left
            return [0] + vals
        else:  # larger is right
            return vals + [0]
    if av:
        mean = sum(vals)/len(vals)
        return [mean, mean, mean]
    else:
        return ["NA", "NA", "NA"]


def loc_data(ras, nprof, loc, scenario):
    # loc -> [identifier, river, reach, rs]
    # Returns [formatted row according to `cols`] for a single location
    # flow_data: {profile: SimData}, where SimData has
    # velocity, maxDepth, flow, shear as lists of [l, c, r]
    ident = loc[0]
    riv = loc[1].strip()
    rch = loc[2].strip()
    rs = loc[3].strip()
    flow_data = ras.data.allFlowDist(riv,
                                     rch,
                                     rs,
                                     nprof)
    return [row_join(
        [scenario, ident, riv, rch, rs,
         sum(fd.flow)] +
        twovalfix(fd.shear, av=True) +
        twovalfix(fd.velocity, maxC=True) +
        twovalfix(fd.maxDepth, maxC=True)
        ) for fd in flow_data.values()]


def scenario_data(ras, nprof, locations, scenario):
    # locations -> [[identifier, river, reach, rs]]
    # nprof -> number of flow profiles
    # Returns [formatted row according to `cols`]
    return [
        row for loc in locations
        for row in loc_data(ras, nprof, loc, scenario)
        ]


def run(projPath, ingeo, outgeo, outfile, locations, nprof, scenarios,
        which="507"):
    # projPath -> project location
    # locations -> [[identifier, river, reach, rs]] for data retrieval
    # Loop through scenarios, set geometry, run simulation, and retrieve data.
    # Scenarios should be a dictionary with labels.  These are used for
    # writing.
    # `outfile` will be overwritten.
    ras = API(Ras(projPath, which=which))
    with open(outfile, "w") as f:
        f.write(cols)
        for scen in scenarios:
            read_modify(ingeo, scenarios[scen], outgeo)
            ras.ops.openProject(projPath)
            ras.ops.compute()
            f.write("\n".join(
                scenario_data(ras, nprof, locations, scen)) + "\n")
