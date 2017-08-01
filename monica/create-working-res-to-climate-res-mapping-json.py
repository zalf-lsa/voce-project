#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# Authors:
# Michael Berg-Mohnicke <michael.berg@zalf.de>
#
# Maintainers:
# Currently maintained by the authors.
#
# This file has been created at the Institute of
# Landscape Systems Analysis at the ZALF.
# Copyright (C: Leibniz Centre for Agricultural Landscape Research (ZALF)

import sys
import json
import time
from collections import defaultdict, OrderedDict
import itertools
from pyproj import Proj, transform
import numpy as np
from scipy.interpolate import NearestNDInterpolator

sys.path.insert(0, "/media/data2/data1/berg/development/python-site-packages")
print sys.path

USER = "xps15"
LOCAL_RUN = True #False

PATHS = {
    "xps15": {
        "PATH_TO_SOIL_DIR": "D:/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": "D:/climate/dwd/csvs/"
    },

    "cluster2": {
        "PATH_TO_SOIL_DIR": "/archiv-daten/md/data/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": "/archiv-daten/md/data/climate/dwd/csvs/"
    }
}

def main():
    "main function"

    config = {
        "user": "xps15",
        "start-row": 1,
        "end-row": 5001
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            k,v = arg.split("=")
            if k in config:
                config[k] = v if k == "user" else int(v)  

    USER = config["user"]

    cdict = {}
    def create_interpolator(path_to_file, wgs84, gk5):
        "read an ascii grid into a map, without the no-data values"
        with open(path_to_file) as file_:
            # skip headerlines
            file_.next()
            file_.next()

            nrows = 938
            ncols = 720

            points = np.zeros((ccols*crows, 2), np.int32)
            values = np.zeros((ccols*crows), np.int32)

            i = -1
            row = -1
            for line in file_:
                row += 1
                col = -1

                for col_str in line.strip().split(" "):
                    col += 1
                    i += 1
                    clat, clon = col_str.split("|")
                    cdict[(row, col)] = (clat, clon)
                    r, h = transform(wgs84, gk5, clon, clat)
                    points[i, 0] = h
                    points[i, 1] = r
                    values[i] = 1000 * row + col
                    #print "row:", row, "col:", col, "clat:", clat, "clon:", clon, "h:", h, "r:", r, "val:", values[i]

            return NearestNDInterpolator(points, values)

    crows = 938
    ccols = 720

    xll = 5137800
    yll = 5562800
    cellsize = 100
    scols = 3653
    srows = 5001

    wgs84 = Proj(init="epsg:4326")
    #gk3 = Proj(init="epsg:31467")
    gk5 = Proj(init="epsg:31469")

    #r, h = transform(wgs84, gk3, 9.426352, 50.359663)
    #lon, lat = transform(gk3, wgs84, r, h)

    interpol = create_interpolator(PATHS[USER]["PATH_TO_CLIMATE_CSVS_DIR"] + "germany-lat-lon-coordinates.grid", wgs84, gk5)

    for srow in range(0, srows):
        for scol in range(0, scols):
            h = yll + (cellsize / 2) + (srows - srow) * cellsize
            r = xll + (cellsize / 2) + scol * cellsize
            inter = interpol(h, r)
            crow = int(inter / 1000)
            ccol = inter - (crow * 1000)
            clat, clon = cdict[(crow, ccol)]
            slon, slat = transform(gk5, wgs84, r, h)
            print "srow:", srow, "scol:", scol, "h:", h, "r:", r, " inter:", interpol(h, r), "crow:", crow, "ccol:", ccol, "slat:", slat, "slon:", slon, "clat:", clat, "clon:", clon

    return


def merge_splitted_mappings():

    to_climate_row_col = {}

    step = 25
    for row in xrange(0, 5001, step):
        with(open("out/working_resolution_to_climate_row-" + str(row) + "-to-row-" + str(row + step) + "_col.json")) as _:
            l = json.load(_)
            for i in xrange(0, len(l), 2):
                to_climate_row_col[tuple(l[i])] = tuple(l[i+1])

    with open("working_resolution_to_climate_row_col.json", "w") as _:
        _.write(json.dumps(to_climate_row_col))

    print "bla"


def load_mapping():

    to_climate_row_col = {}

    with(open("out/working_resolution_to_climate_row_col.json")) as _:
        l = json.load(_)
        for i in xrange(0, len(l), 2):
            to_climate_row_col[tuple(l[i])] = tuple(l[i+1])

    print "bla"



main()
#load_mapping()
