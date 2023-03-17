# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 16:10:25 2023

@author: dphilippus
"""

"""
Parse HEC-RAS geometry files into a Python-friendly structure.

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

In order to run the required analysis for scenarios, it is necessary to
retrieve roughness, geometry, and location.  From these can be computed
the datum, etc, but that is best left to hecgeo.

To write, it will be necessary to:
    - Read the whole geometry file
    - Identify and edit relevant cross-sections
    - Correct Sta/Elev and Mann headers and data
    - Write the new file
"""


from hecgeo import Geometry, Reach


def first_line(text):
    return text[:text.find("\n")]


def rest_lines(text):
    return text[(text.find("\n")+1):]


def make_geo(text):
    # Cross-section text => Geometry object.
    # Geometry arguments: coordinates [(x, y)], roughness [(x, mann)],
    # bank stations (left, right)
    statext = rest_lines(text[text.find("#Sta/Elev="):text.find("#Mann=")])
    # Need to work with remaining text for Manning's.
    rtx = rest_lines(text[text.find("#Mann="):])
    manntext = rtx[:rtx.find("=")]
    # Weirdness: cut off at the _last_ newline
    manntext = manntext[:(len(manntext) - manntext[::-1].find("\n")-1)]
    banktext = first_line(text[text.find("Bank Sta="):]).split("=")[1]
    # Process station data
    # Excluding very long chunks: sometimes when one is too long it spills
    # over; this tends to occur in high-density survey data, so excluding
    # one point should not be a huge problem.
    stalist = [x for x in statext.split(" ") if x and len(x) <= 7]
    sta = [(float(stalist[i]), float(stalist[i+1]))
           for i in range(0, len(stalist)-1, 2)]
    # Process Manning's data
    mannlist = [x for x in manntext.split(" ") if x]
    mann = [(float(mannlist[i]), float(mannlist[i+1]))
            for i in range(0, len(mannlist)-2, 3)]
    # Proces bank stations
    banklist = banktext.split(",")
    banks = (float(banklist[0]), float(banklist[1]))
    return Geometry(sta, mann, banks)


def sep_inner(name, text):
    # Reach-specific text => Reach
    # Reach-specific text is between two pairs of "River Reach=", excluding
    # that particular row.
    def get_rs(block):
        # First line will be `1 ,43505   ,139,139,139` or similar
        return first_line(block).split(",")[1].strip()
    return Reach(name, {
        get_rs(x): make_geo(rest_lines(x))
        for x in text.split("Type RM Length L Ch R = ")[1:]
        })


def parse(file):
    # Read the file path, then separate it into
    # {reach: Reach}
    with open(file, "r") as f:
        raw = f.read()
    return {
        first_line(x):
            sep_inner(first_line(x), rest_lines(x))
        for x in raw.split("River Reach=")[1:]
        }
