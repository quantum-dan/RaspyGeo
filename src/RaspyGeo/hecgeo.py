# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 16:11:08 2023

@author: dphilippus
"""

"""
Define HEC-RAS geometry class(es) as a standardized format.
"""


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
