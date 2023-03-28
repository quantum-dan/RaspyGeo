# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 13:31:10 2023

@author: dphilippus
"""

"""
Write Python Reach objects back to HEC-RAS.

HEC-RAS geometry files (i.e. xyz.g01, etc) begin with an overall description,
then junction descriptions.  These are not of interest to RaspyGeo.

Next, there is a reach description, including name, short ID, etc.  This
is followed by a long list of what appear to be cross-section coordinates.
The cross-section is identified by:
River Reach=Compton Creek   ,CC      

The cross-section geometries are of the form:
Type RM Length L Ch R = 1 ,43505   ,139,139,139
BEGIN DESCRIPTION:
Whittier Narrows Dam (D/S Face 441+12.81) u/s limit of project reach
END DESCRIPTION:
XS GIS Cut Line=5
6536310.509547571829544.635834546536310.509547571829544.63583454
6536264.334177741829598.175436616536218.158807921829651.71503868
6536218.158807921829651.71503868
Node Last Edited Time=May/03/2022 10:53:19
#Sta/Elev= 15 
   930.5  207.71   930.5  186.99  968.89  186.99  968.89   184.4  972.85  183.74
  987.95  183.74  993.19  182.43  999.75  182.43 1006.31  182.43 1011.55  183.74
 1026.65  183.74 1030.61   184.4 1030.61  186.99    1069  186.99    1069  207.71
#Mann= 6 ,-1 , 0 
   930.5    .017       0   930.5    .017       0  968.89     .15       0
  987.95    .035       0 1011.55     .15       0 1030.61    .017       0
Bank Sta=930.5,1069
XS Rating Curve= 0 ,0
XS HTab Starting El and Incr=187.49,1, 20 
XS HTab Horizontal Distribution= 5 , 5 , 5 
Exp/Cntr=0,0

The first line includes the river station (second number) and the lengths.
River station is of interest for scenarios.  Further down, after #Sta/Elev= n,
there are n coordinate pairs.  Next is #Mann= n,??,??, identifying the
number of Manning's n change points, and then trios of numbers identifying
those (station, n, ???).  Next there are the bank stations.
It appears likely that the second flag in #Mann is the type of variation,
where 0 is LOB/ROB/MC and -1 is horizontally varying.

For writing, an existing file will be taken as a template, and cross-section
portions corrected only as needed.

This requires identifying cross-section portions and editing #Sta/Elev through
to Bank Sta.  In that portion the numbers of Sta/Elev, the full #Mann string,
and the Bank Sta will need to be corrected.  The coordinate pairs for geometry
and roughness will also need to be set.

Geometry is ten fixed-width, space-delimited columns (two decimal place
precision).  The columns alternate X and Y.  Each column is eight characters
wide, filled with spaces at the beginning.

Manning's columns are also eight characters wide.  There are nine columns,
in trios of location, roughness (with no leading zero, up to three decimals),
and then a zero.

#Sta/Elev= is followed by three characters (possibly leading spaces) as an
integer, followed by a trailing space.

#Mann= is followed by ten characters.  For our purposes, it is ` N ,-1 , 0 `
where N is the number of roughness points.
Bank Sta=left,right (floats, two decimals) with no special formatting.

In general, floats should use the minimum required number of decimal places,
and no more than two (three for Manning's).
"""


from RaspyGeo.parse_geo import first_line, rest_lines, get_rs, parse


def fmt_num(x):
    return "% 8.2f" % x


def fmt_mann(x):
    return "% 8.3f" % x


def fmt_nsta(x):
    if x > 99:
        return str(x)
    else:
        return "% 2d" % x


def flatten(ls):
    return [i for x in ls for i in x]


def blockify(ls, N):
    return '\n'.join([
        ''.join(ls[k:min(k+N, len(ls))])
        for k in range(0, len(ls), N)
        ])


def coordinates(coords):
    # Convert coordinates [(X,Y)] to the geometry block (10 fixed-width
    # columns)
    # with header #Sta/Elev= N
    allcol = [fmt_num(x) for x in flatten(coords)]
    block = blockify(allcol, 10) if len(allcol) > 10 else ''.join(allcol)
    npt = fmt_nsta(len(coords))
    return "#Sta/Elev= %d \n%s" % (len(coords), block)


def mann(ro):
    allcol = flatten([(fmt_num(x[0]),
                       fmt_mann(x[1]),
                       '       0') for x in ro])
    block = blockify(allcol, 9)
    header = '#Mann=%s%d ,-1 , 0 ' % (
        '' if len(ro) > 9 else ' ',
        len(ro))
    return '%s\n%s' % (header, block)


def banksta(banks):
    return 'Bank Sta=%.2f,%.2f' % banks


def edit_block(original,
               newgeo):
    # Takes a Geometry object as an input in addition to the original
    # text block.
    geos = newgeo.restore()
    # Find Manning's block, since the next block is not fixed.
    # Each Manning's roughness occupies exactly 24 characters,
    # plus one for each time there are more than 3.
    # The title block has exactly 18 characters (including newline).
    mix = original.find('#Mann')
    mann_n = int(original[mix:][:20]
                 .split("=")[1]
                 .split(',')[0]
                 .strip())
    nnewln = 1 + int((mann_n - 1) / 3)
    nch = 24 * mann_n + nnewln + 18
    # origina[endman:] starts right after Manning's (without leading newline)
    endman = mix + nch
    # Next, identify the bank station block
    bankix = original.find('Bank Sta=')
    endbank = bankix + original[bankix:].find('\n') + 1
    # Assemble slices
    slices = [
        # #Sta/Elev is easy.
        original[:(original.find('#Sta/Elev')-1)],
        coordinates(geos["coordinates"]),
        mann(geos["roughness"]),
        # Middle bit (may be '', hence filtering)
        original[endman:bankix],
        banksta(geos["banks"]),
        original[endbank:]
        ]
    return "\n".join([slc for slc in slices if slc != ''])


def proc_reach(name, text, reaches):
    # The processor function gets a name, which is the reach name
    # (first line), and the remaining reach text.
    # It should then be possible to loop through XS blocks,
    # edit them accordingly, and rebuild the file.
    # Reaches (e.g. returned by parse) have the `name` values as their
    # keys, so that makes it easy.  Cross-sections have get_rs(block), for
    # each block, as their key within Reach.geometries, also conveniently.
    rch = reaches[name]
    sep = "Type RM Length L Ch R = "
    chunks = text.split(sep)
    header = chunks[0]
    return name + "\n" + sep.join([header] + [
        edit_block(block, rch.geometries[get_rs(block)])
        for block in chunks[1:]
        ])


def read_write(file, reaches, out=None):
    # Read the file path, then separate it into
    # {reach: fn(name, text)}
    out = out if out is not None else file
    with open(file, "r") as f:
        raw = f.read()
    with open(file + ".bak", "w") as f:
        f.write(raw)
    chunks = raw.split("River Reach=")
    data = "River Reach=".join([chunks[0]] + [
        proc_reach(first_line(x), rest_lines(x), reaches)
        for x in chunks[1:]])
    with open(out, "w") as f:
        f.write(data)


def read_modify(file, modfns, out=None):
    # modfns => {reach name: f(Reach)} where f modifies the Reach as desired.
    reaches = parse(file)
    newrch = {rch: modfns[rch](reaches[rch])
              if rch in modfns else reaches[rch]
              for rch in reaches}
    read_write(file, newrch, out)
