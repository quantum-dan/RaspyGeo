# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 10:32:54 2023

@author: dphilippus
"""

"""
Functions to modify XS geometry.
All geo. functions take coordinates, roughness, banks
and return a tuple of the same, in that order.

coordinates: [(x,y)], no offset or datum (left bank at 0 and lowest point at 0)
roughness: [(x, n)], no offset, applied from the left
banks: (xleft, xright), no offset

Users can define their own geometry functions as well.
"""


def daylight(xs0, ys0, start, starty, z, dirx):
    """
    This function identifies the x-coordinate of the daylight point
    in the given direction (dirx, positive for right and negative for left).
    This is looking for where a line going out from start at z slope (x:y)
    will intersect with the existing geometry specified by xs0,ys0.
    There are several possibilities:
        - Daylight line is always below current geometry.  Return 0.1 units
        inwards from outermost point, with near-vertical correction from there.
        - Daylight line is always above current geometry.  Return the point
        at which it reaches the maximum elevation of current geometry, with
        horizontal correction from there.
        - Daylight line intersects current geometry at some point.  This is
        the assumption.  We test this by iteratively checking for intersection
        between the daylight line and each segment of the current geometry.
        If we find something, then we interpolate to find the point of inter-
        section.  If we hit the outer edge, then it is always below.  If we
        hit the top, then it is always above.
    We can check for intersection straightforwardly: the inner end of the
    daylight segment will be above/below the inner end of the original segment,
    and the outer ends the opposite.  That, or the inner ends are equal.  If
    the inner ends are equal to within 0.1 units (for floating point accuracy),
    we set the daylight point to the same elevation, 0.1 units in, so there
    are no duplicate points.
    """
    def fpcheck(ydl, y0):
        # Returns 1, 0, -1: ydl is ? relative to y0 (to within 0.1 units).
        if abs(ydl - y0) < 0.1:
            return 0
        elif ydl > y0:
            return 1
        else:
            return -1

    def dheight(x):
        # Compute height of daylight line at a point.
        return starty + abs(x - start) / z
    # Identify side of interest (left of point or right of point)
    xs = [x for x in xs0 if (dirx < 0 and x < start) or
          (dirx > 0 and x > start)]
    # Set direction accordingly, so start of list is closest
    xs = xs[::dirx]
    ys = ys0[:len(xs)][::-1] if dirx < 0 else ys0[-len(xs):]
    # Now... iterate!
    for ix in range(len(xs)-1):
        x = xs[ix]
        xn = xs[ix+1]
        y = ys[ix]
        yn = ys[ix+1]
        dy = dheight(x)
        dyn = dheight(xn)
        inner = fpcheck(dy, y)
        outer = fpcheck(dyn, yn)
        if inner == 0:
            return x - dirx * 0.1  # minus if right, plus if left (inwards)
        elif abs(inner - outer) == 2:
            # Compute interpolation.
            # We want the total gap in X such that the current difference
            # in elevation is equal to x/(difference in slopes).
            # However, the difference in slopes needs to be computed in terms
            # of y/x and then converted back (i.e. something like a harmonic
            # mean).
            # This has three cases:
            # Both z nonzero: gap x/y = 1/(y'/x' - y/x)
            # Zero current z: daylight is right there
            # Zero AFP z: gap closes at original rate
            delta_y = abs(dy - y)
            sl_current = dirx * (xn - x) / (yn - y)
            # delta_z = abs(z - sl_current)
            if sl_current == 0:
                return x
            elif z == 0:
                return x + dirx * sl_current * delta_y
            else:
                delta_z = 1/abs(1/z - 1/sl_current)
                return x + dirx * delta_z * delta_y
        elif dyn >= max(ys):
            # Daylight line is above current geometry.
            # Interpolate x s.t. dy == max(ys)
            return start + dirx * z * (max(ys) - starty)
        else:
            # Same side (or equal at next), don't do anything
            pass
    # If AFP is too wide...
    return start + dirx * 0.1


def set_afp(
        lfc_w,
        lfc_h,
        lfc_z,
        afp_wfun,
        afp_z,
        afpside_n,
        afp_n,
        lfcside_n,
        lfc_n
        ):
    """
    This is the main function for setting active floodplain-style
    geometry.  It returns a function for setting geometry given the usual
    set of arguments, i.e. returns a geofun.
    The new channel is assumed to consist of two nested trapezoids,
    a smaller low-flow channel which cuts into a larger active floodplain.
    It is also assumed to be symmetrical.
    Thus, the user specifies:
        - Low-flow channel bottom width, depth, and side slope (x:y)
        - Active floodplain side slope (x:y); if the AFP edges are above the
            current channel, then it will fill up to the maximum channel
            height.
        - Active floodplain width as a function of available channel width
            (allowing either constant
            or fraction, etc.)  This is provided as half-width, i.e.
            available per side.
        - Daylight slope (AFP side slope) roughness
        - AFP roughness
        - LFC side slope roughness
        - LFC bottom roughness
    Bank stations are set at the top edges of the LFC.
    Units are assumed to be consistent with geometry and not accounted for.
    """
    def geofun(coordinates, roughness, banks):
        xs0 = [co[0] for co in coordinates]
        ys0 = [co[1] for co in coordinates]
        rox0 = [ro[0] for ro in roughness]
        ron0 = [ro[1] for ro in roughness]
        # First: identify center
        centx = 0.5*(min(xs0) + max(xs0))
        # Now,  build fixed geometry
        # LFC bottom
        lfc_bleft = centx - lfc_w / 2
        lfc_bright = centx + lfc_w / 2
        lfc_by = min(ys0)
        # LFC side slopes
        lfc_sw = lfc_z * lfc_h
        lfc_tleft = lfc_bleft - lfc_sw
        lfc_tright = lfc_bright + lfc_sw
        lfc_ty = lfc_by + lfc_h
        # This gives us the new bank stations, conveniently
        nbanks = (lfc_tleft, lfc_tright)
        # Now the complications begin: AFP width
        # First, identify available width.  This is not as simple as one
        # would expect, as a naive channel width minus LFC width results in
        # running out of room for daylighting.
        # Instead, we must also account for the width of the LFC side slopes.
        # The maximum width these can have is if they must reach all the way
        # up to the top of the channel.
        # For convenience, we compute available width
        # max_ss = afp_z * (max(ys0) - lfc_ty)
        avail = 0.5 * (max(xs0) - min(xs0) - (
            lfc_tright - lfc_tleft))
        afp_w = afp_wfun(avail)
        # AFP bottom
        afp_bleft = lfc_tleft - afp_w
        afp_bright = lfc_tright + afp_w
        # Now the trickiest part: where do the side slopes intersect with
        # the existing channel (where do they daylight?)  Identifying
        # the daylight point gets its own function, for simplicity.
        # daylight(x, y, start, z, direction) returns the x-coordinate of
        # daylight.
        afp_tleft = daylight(xs0, ys0, afp_bleft,
                             lfc_ty, afp_z, -1) if avail > 0 else \
            afp_bleft - 0.1
        afp_tright = daylight(xs0, ys0, afp_bright,
                              lfc_ty, afp_z, 1) if avail > 0 else \
            afp_bright + 0.1
        # Compute height based on side slope width and slope
        afp_tyleft = lfc_ty + (afp_bleft - afp_tleft) / afp_z if \
            avail > 0 else lfc_ty
        afp_tyright = lfc_ty + (afp_tright - afp_bright) / afp_z if \
            avail > 0 else lfc_ty
        # We now have all key points.  Next, we rebuild the coordinates
        # and specify roughness.
        # The first step is to determine what, if any, of the channel is kept.
        # Also need a way to account for [near-]vertical walls at daylight
        keepl = [(x, ys0[ix]) for (ix, x) in enumerate(xs0)
                 if x < (afp_tleft - 0.1) or
                 (
                    # Very close horizontally and not close vertically
                    x <= afp_tleft and
                    (ys0[ix] - afp_tyleft) > 0.1
                     )]
        keepr = [(x, ys0[ix]) for (ix, x) in enumerate(xs0)
                 if x > (afp_tright + 0.1) or
                 (
                     x >= afp_tright and
                    (ys0[ix] - afp_tyright) > 0.1
                    )
                 ]
        # Now, build the new geometry coordinates.
        co_new = [
            (afp_tleft, afp_tyleft),
            (afp_bleft, lfc_ty),
            (lfc_tleft, lfc_ty),
            (lfc_bleft, lfc_by),
            (lfc_bright, lfc_by),
            (lfc_tright, lfc_ty),
            (afp_bright, lfc_ty),
            (afp_tright, afp_tyright)
            ]
        co_new = co_new if avail > 0 else co_new[2:-2]
        # co_out = sorted(keepl + co_new + keepr,
        #                 key = lambda x: x[0])
        co_out = keepl + co_new + keepr
        # Next, the roughness coordinates.  As before, we keep any
        # sets in the kept geometry from the left.  From the right it is
        # more complicated, as we must also propagate correctly.
        nkeepl = keepl = [(x, ron0[rox0.index(x)]) for x in rox0
                          if x < afp_tleft]
        nkeepr = keepl = [(x, ron0[rox0.index(x)]) for x in rox0
                          if x > afp_tright]
        # Right-most coordinate that is left of the AFP edge.
        proprox = [rx for rx in rox0 if rx <= afp_tright][-1]
        propn = ron0[rox0.index(proprox)]
        # Now we can build the new geometry.
        ro_new = [
            (afp_tleft, afpside_n),
            (afp_bleft, afp_n),
            (lfc_tleft, lfcside_n),
            (lfc_bleft, lfc_n),
            (lfc_bright, lfcside_n),
            (lfc_tright, afp_n),
            (afp_bright, afpside_n),
            (afp_tright, propn)
            ]
        ro_out = sorted(nkeepl + ro_new + nkeepr,
                        key = lambda x: x[0])
        return (co_out, ro_out, nbanks)
    return geofun


def set_lfc(
        lfc_w,
        lfc_h,
        lfc_z,
        bot_n,
        side_n):
    """
    Simplified geometry function building just an LFC with horizontal
    daylighting.
    """
    def geofun(coordinates, roughness, banks):
        xs0 = [co[0] for co in coordinates]
        ys0 = [co[1] for co in coordinates]
        rox0 = [ro[0] for ro in roughness]
        ron0 = [ro[1] for ro in roughness]
        # First: identify center
        centx = 0.5*(min(xs0) + max(xs0))
        # Now,  build fixed geometry
        # LFC bottom
        lfc_bleft = centx - lfc_w / 2
        lfc_bright = centx + lfc_w / 2
        lfc_by = min(ys0)
        # LFC side slopes
        lfc_sw = lfc_z * lfc_h
        lfc_tleft = lfc_bleft - lfc_sw
        lfc_tright = lfc_bright + lfc_sw
        lfc_ty = lfc_by + lfc_h
        # This gives us the new bank stations, conveniently
        nbanks = (lfc_tleft, lfc_tright)
        keepl = [(x, ys0[ix]) for (ix, x) in enumerate(xs0)
                 if x < (lfc_tleft - 0.1)]
        keepr = [(x, ys0[ix]) for (ix, x) in enumerate(xs0)
                 if x > (lfc_tright + 0.1)]
        # Now, build the new geometry coordinates.
        co_new = [
            (keepl[-1][0], lfc_ty),
            (lfc_tleft, lfc_ty),
            (lfc_bleft, lfc_by),
            (lfc_bright, lfc_by),
            (lfc_tright, lfc_ty),
            (keepr[0][0], lfc_ty)
            ]
        # co_out = sorted(keepl + co_new + keepr,
        #                 key = lambda x: x[0])
        co_out = keepl[:-1] + co_new + keepr[1:]
        nkeepl = keepl = [(x, ron0[rox0.index(x)]) for x in rox0
                          if x < (lfc_tleft - 0.1)]
        nkeepr = keepl = [(x, ron0[rox0.index(x)]) for x in rox0
                          if x > (lfc_tright + 0.1)]
        # Right-most coordinate that is left of the AFP edge.
        proprox = [rx for rx in rox0 if rx <= lfc_tright][-1]
        propn = ron0[rox0.index(proprox)]
        # Now we can build the new geometry.
        ro_new = [
            (lfc_tleft, side_n),
            (lfc_bleft, bot_n),
            (lfc_bright, side_n)
            ]
        ro_out = sorted(nkeepl + ro_new + nkeepr,
                        key = lambda x: x[0])
        return (co_out, ro_out, nbanks)
    return geofun
