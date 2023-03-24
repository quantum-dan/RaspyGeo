# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 16:11:08 2023

@author: dphilippus
"""

"""
Define HEC-RAS geometry class(es) as a standardized format.
"""


from copy import deepcopy


def rs2float(rs):
    # Convert river station to float (because interpolated
    # stations are nnn.*)
    if rs[-1:] == "*":
        return float(rs[:-1])
    else:
        return float(rs)


class Geometry(object):
    # For consistency, all coordinates are adjusted so that 0 is the left
    # extreme and 0 is the minimum elevation.  However, datum and offset
    # are stored so real coordinates can be recalculated later.
    def __init__(self, coord, mann, banksta):
        # Coord: X-Y pairs [(sta, elev)]
        # Mann: X-n pairs [(sta, manning)]
        # Banksta: (left, right)
        #
        # Offset: for consistency, left bank = 0; store the offset, though,
        # to recreate later.
        # Likewise datum => minimum elevation.
        self.offset = coord[0][0]
        self.datum = min([co[1] for co in coord])
        self.coordinates = [
            (co[0] - self.offset, co[1] - self.datum) for co in coord
            ]
        self.roughness = [(mn[0] - self.offset, mn[1]) for mn in mann]
        self.banks = (banksta[0] - self.offset, banksta[1] - self.offset)

    def restore(self):
        # Recreate HEC-RAS-style coordinates (with offset and datum)
        return {
            "coordinates":
                [(co[0] + self.offset, co[1] + self.datum)
                 for co in self.coordinates],
            "roughness":
                [(mn[0] + self.offset, mn[1]) for mn in self.roughness],
            "banks":
                (self.banks[0] + self.offset, self.banks[1] + self.offset)
            }

    def update(self, geofun):
        # Update (in place) with a geometry function
        (self.coordinates, self.roughness, self.banks) = geofun(
            self.coordinates, self.roughness, self.banks)
        return self

    def adjusted(self, geofun):
        # Return updated copy with geometry function
        return deepcopy(self).update(geofun)


class Reach(object):
    # Define a Reach class to easily track datums, etc.
    def __init__(self, name, geometries):
        # Geometries should be a dictionary of {station: geometry}
        self.name = name
        self.geometries = geometries  # dictionary
        # Store both numeric value (for sorting, etc) and string value
        # for exact identification (no float errors)
        self.stations = {rs2float(x): x for x in geometries}
        self.upstream = max(self.stations)
        self.downstream = min(self.stations)
        self.re_datums()  # compute datums

    def __repr__(self):
        return "Reach %s: length %.2f units with %d cross-sections" % (
            self.name.strip(), max(self.stations) - min(self.stations),
            len(self.stations))

    def re_datums(self):
        # Recalculate datums after changing geometries
        # Make sure they are in order
        self.datums = [self.geometries[self.stations[x]].datum
                       for x in sorted(self.stations)]

    def get_sta(self, first=None, last=None):
        # Retrieve ordered, _numerical_ list of stations (i.e. float not str)
        first = min(self.stations) if first is None else first
        last = max(self.stations) if last is None else last
        return [sta
                for sta in sorted(self.stations)
                if sta >= first and sta <= last]

    def set_datums(self, delta, first=None, last=None):
        # Update datums by a specified amount
        # If first/last are not specified, will use upstream and downstream
        # stations.
        # Order is from downstream to upstream.
        # Modifies object in-place.
        to_update = [self.stations[sta] for sta in self.get_sta(first, last)]
        if len(to_update) != len(delta) and len(delta) != 1:
            raise ValueError("length of delta != number of stations")
        for ix in range(len(to_update)):
            self.geometries[to_update[ix]].datum += (
                delta[ix] if len(delta) != 1 else delta[0])
        self.re_datums()
        return self

    def adjust_datums(self, down_adj, up_adj=None, first=None, last=None):
        # Update datums from first to last.
        # If up_adj is None, update everything by down_adj.
        # Otherwise, linearly interpolate the adjustment based on the lengths.
        # Modifies and returns a copy.
        if up_adj is None:
            return self.set_datums([down_adj], first, last)
        else:
            to_update = self.get_sta(first, last)
            tot_len = max(to_update) - min(to_update)
            # For interpolation
            slope = (up_adj - down_adj) / tot_len
            lengths = [sta - to_update[0] for sta in to_update]
            delta = [down_adj + slope * dist for dist in lengths]
            return deepcopy(self).set_datums(delta, first, last)

    def set_geometry(self, geofun, first=None, last=None):
        # Apply a geometry adjustment function to selected cross-sections
        # Modifies in place.
        to_update = [self.stations[sta] for sta in self.get_sta(first, last)]
        for ud in to_update:
            self.geometries[ud] = self.geometries[ud].update(geofun)
        self.re_datums()
        return self

    def adjust_geometry(self, geofun, first=None, last=None):
        # Like set_geometry; returns a copy.
        return deepcopy(self).set_geometry(geofun, first, last)
