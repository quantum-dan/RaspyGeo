# RaspyGeo
Automated geometry scenario runner (loosely analogous to the Geometry Editor tool) for HEC-RAS.  Depends on Raspy (`raspy-auto` on PyPI).

# Usage

Currently, there is not a scenario runner, so the workflow does involve a manual
step.  The basic workflow is:

1. Specify a list of scenarios to run as geometry functions (see example in
`iterate.py`).
2. Use `iterate.py`'s `run` function to run through geometry scenarios.
3. Keeping the HEC-RAS model, geometry editor, runner, and profile summary viewer
open, for each scenario, reopen the geometry file, run, and retrieve results.
4. Come back to Python and hit enter to set the next scenario.

# Plans

The idea is to be able to automatically run through (and retrieve results for) many iterations of some geometry scenario in HEC-RAS.  This can be partially automated (editing the geometry) with the Geometry Editor, but that built-in tool, while very useful, is also quite limited and still requires a manual edit-run-analyze workflow.

The Geometry Editor is the best approach if you have a handful of scenarios, and RaspyGeo does not aim to compete with it.  However, that workflow becomes a major bottleneck when that scales to dozens or hundreds of variations, especially when those require complex modifications to datum, bank stations, etc, followed by exporting and post-processing data.  This project is in response to the developer spending far too much time running geometry scenarios for research.

So the plan is, the user specifies:

- Scenario location (i.e. reach and river stations)
- Data retrieval location
- Datum adjustments at both ends; for now, just linearly interpolate the adjustment
- New geometry; for now, just trapezoidal
- Slope-to-daylight

RaspyGeo runs the specified scenarios, then retrieves profile data.

In addition, as an advanced feature, the developer will consider implementing functionaly to fit and export rating curve functions (main channel and overbanks; depth, velocity, and shear) and apply those to discharge scenarios, as this would allow a "one-stop shop" for running and analyzing scenarios.
