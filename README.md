# RaspyGeo

Automated geometry scenario runner (loosely analogous to the Geometry Modification tool) for HEC-RAS.  Depends on Raspy (`raspy-auto` on PyPI).  Currently works for steady-state simulations. RaspyGeo is available on PyPI as [RaspyGeo](https://pypi.org/project/RaspyGeo/).

# Updates and Added Features

If additional capabilities would be useful to you, open an Issue and I will check
into it.  Otherwise, I develop updates as I need them.

# Usage

Scenario running is fully automated through `run`.  The HEC-RAS project must
already be set up with a reference (baseline) geometry **and** a new (scenario)
geometry file, and the current plan must be set up to run the scenario geometry.
Then, the user specifies:

- HEC-RAS project path, which needs to be a full path, not relative
- Input (baseline) geometry file, which can be a relative path
- Output (scenario) geometry file, which can be a relative path
- Scenario data output file, which will contain shear, velocity, and depth
for main channel and overbanks
- Data retrieval locations, which is a list of lists: `[[identifier, river, reach, rs]]`, where
`identifier` is the user's name for the spot and the rest are HEC-RAS location
information.
- Number of flow profiles being modeled (steady state)
- Scenario specification
- [Optional] HEC-RAS version (default: "507", for 5.0.7; 6.3.1 would be "631", etc.)

The complicated part is the scenario specification.  This is set up as nested
dictionaries.  The outer dictionary is scenarios, where the key is the name
of the scenario (do not use any commas).  The inner dictionaries have the keys
as `River Name,Reach Name` (no separating spaces, etc), and the values are the
actual geometry specifications.  These are simply functions that take a `Reach`
object (see `hecgeo.py`) and return an updated `Reach`; the user can specify
this however they wish.

The default approach is to design functions that can be passed to
`Reach.adjust_geometry` and to specify datum adjustments with `Reach.adjust_datums`.
Both of these modify any
cross-sections either within a given stretch of the reach or for the whole reach.
Geometry adjustment functions receive coordinates, roughness locations, and bank
stations and return the same.  In the provided coordinates, the low point is zero
elevation and the left edge is station zero; offsets and datums are stored and
added back in before writing.

Coordinates are formatted as `[(station, elevation)]`.  Roughness is, as HEC-RAS
handles it, applied from the left point going rightwards, and formatted as
`[(station, new roughness)]`.  The bank stations are just `[left, right]`.

Specifying geometry modifiers can be quite complicated.  Look at `geofun.py` for
some examples.  Two modifier functions are provided by default: `set_afp` and
`set_lfc`, which are tailored to the developer's use case.  LFC specifies a
low-flow channel, or trapezoidal channel within the main channel.  AFP specifies
an LFC which then has a wider flat floodplain, active floodplain (AFP), around
it.  These are both meant to cut/fill into existing geometry and then daylight.
It would be much more straightforward to design, for example, a constant shape
that ignores the original channel or just adjusts width based on it, etc.  The
complications mainly have to do with connecting the new design with the old.

Using `set_afp`, a full example is included below.  This would work similarly
with the user's own geometry functions.

```
from RaspyGeo import set_afp, run, parse
import matplotlib.pyplot as plt


rpath = r"C:\Users\dphilippus\longpathstuff\TestProj\test.prj"
ingeo = "TestProj/test.g02"
outgeo = "TestProj/test.g01"
outpath = "output.txt"


def buildscen(bwidth, tdatum):
    return lambda geo: geo.adjust_datums(0, tdatum).adjust_geometry(
        set_afp(bwidth, 1, 2, lambda x: 0.5*x, 3, 0.05, 0.05, 0.035, 0.035))


def prepscens(bwidth, tdatum):
    return {
        "RiverOne,Lower": buildscen(bwidth, tdatum),
        "RiverOne,Upper": buildscen(bwidth*0.75, tdatum*2)
        }


scens = {"Width %d Datum %d" % (w, d): prepscens(w, d) for w in range(1, 6)
         for d in [1, 2, 3]}

# [[identifier, river, reach, rs]]
locations = [
    ['R1U', 'RiverOne', 'Upper', '2200'],
    ['R1L', 'RiverOne', 'Lower', '401'],
    ['TH', 'Thingy', 'OnlyOne', '100']
    ]

nprof = 10


def runner():
    run(rpath, ingeo, outgeo, outpath, locations, nprof, scens)
```

# Bugs

Note that HEC-RAS geometry files can have various optional components that I
may not have tested for, and these may produce odd crashes or similar.  If you
are running into such a bug, please attach the relevant geometry input file to
the Issue.

# Summary

The idea is to be able to automatically run through (and retrieve results for) many iterations of some geometry scenario in HEC-RAS.  This can be partially automated (editing the geometry) with the Geometry Editor, but that built-in tool, while very useful, is also quite limited and still requires a manual edit-run-analyze workflow.

The Geometry Editor is the best approach if you have a handful of scenarios, and RaspyGeo does not aim to compete with it.  However, that workflow becomes a major bottleneck when that scales to dozens or hundreds of variations, especially when those require complex modifications to datum, bank stations, etc, followed by exporting and post-processing data.  This project is in response to the developer spending far too much time running geometry scenarios for research.

So the plan is, the user specifies:

- Scenario location (i.e. reach and river stations)
- Data retrieval location
- Datum adjustments at both ends; for now, just linearly interpolate the adjustment
- New geometry
- Slope-to-daylight

RaspyGeo runs the specified scenarios, then retrieves profile data.
