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

print sys.path
sys.path.append("../../../python-site-packages/")

USER = "xps15"
LOCAL_RUN = True #False

PATHS = {
    "xps15": {
        "PATH_TO_SOIL_DIR": "D:/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": "D:/climate/dwd/csvs/"
    },

    "cluster2": {
        "PATH_TO_SOIL_DIR": "/archiv-daten/md/data/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": " /archiv-daten/md/data/climate/dwd/csvs/"
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

    

    def read_ascii_grid_into_dict(path_to_file):
        "read an ascii grid into a map, without the no-data values"
        with open(path_to_file) as file_:
            # skip headerlines
            file_.next()
            file_.next()

            nrows = 720
            ncols = 938
            row = -1
            d = defaultdict(dict)
            for line in file_:
                row += 1
                col = -1
                for col_str in line.strip().split(" "):
                    col += 1
                    if col_str == "-9999":
                        continue
                    slat, slon = col_str.split("|")
                    d[int(float(slat)*10000)][int(float(slon)*10000)] = (row, col)

            return d


    def find_closest_value(ord_dict, val, obey_borders=True):
        "find the closest key to value val in ordered dict ord_dict"
        if obey_borders:
            vals = ord_dict.keys()
            if val < vals[0] or vals[-1] < val:
                return None

        it1 = ord_dict.iterkeys()
        it2 = ord_dict.iterkeys()
        next(it2, None)

        for (cur, nex) in itertools.izip_longest(it1, it2, fillvalue=None):
            if cur and not nex:
                return cur
            elif cur <= val and nex and val <= nex:
                cur_dist = val - cur
                nex_dist = nex - val
                return cur if cur_dist <= nex_dist else nex

        return None


    def find_closest_lat_lon(ord_dict, lat, lon):
        "find the (row, col) of the closest lat/lon value in dictionary ord_dict"
        closest_lat = find_closest_value(ord_dict, lat)
        if closest_lat:

            lons = ord_dict[closest_lat]
            closest_lon = find_closest_value(lons, lon)
            if closest_lon:
                return lons[closest_lon]

        return (None, None)


    isimip_ord_lat_lon = OrderedDict()
    isimip_lat_lon_unsorted = read_ascii_grid_into_dict(PATHS[USER]["PATH_TO_CLIMATE_CSVS_DIR"] + "germany-lat-lon-coordinates.grid")
    for lat in sorted(isimip_lat_lon_unsorted.keys()):
        isimip_ord_lat_lon[lat] = OrderedDict()
        ulons = isimip_lat_lon_unsorted[lat]
        lons = isimip_ord_lat_lon[lat]
        for lon in sorted(ulons.keys()):
            lons[lon] = isimip_lat_lon_unsorted[lat][lon]


    xll = 5137800
    yll = 5562800
    cellsize = 100
    ncols = 3653
    nrows = 5001

    wgs84 = Proj(init="epsg:4326")
    #gk3 = Proj(init="epsg:31467")
    gk5 = Proj(init="epsg:31469")

    #r, h = transform(wgs84, gk3, 9.426352, 50.359663)
    #lon, lat = transform(gk3, wgs84, r, h)

    to_climate_row_col = []

    for y in range(config["start-row"]-1, config["end-row"]):

        start = time.clock()

        for x in range(0, ncols):

            h = yll + (cellsize / 2) + (nrows - y) * cellsize
            r = xll + (cellsize / 2) + x * cellsize
            lon, lat = transform(gk5, wgs84, r, h)

            crow, ccol = find_closest_lat_lon(isimip_ord_lat_lon, int(lat*10000), int(lon*10000))

            to_climate_row_col.append((y, x))
            to_climate_row_col.append((crow, ccol))

            #print x, " ",

        stop = time.clock()

        print "row[", config["start-row"], "-", config["end-row"], "]", y, "(", stop - start, "s)",

    with open("working_resolution_to_climate_row-" + config["start-row"] + "-to-row-" + config["end-row"] + "_col.json", "w") as _:
        _.write(json.dumps(to_climate_row_col))


def load_mapping():

    to_climate_row_col = {}

    with(open("working_resolution_to_climate_row_col.json")) as _:
        l = json.load(_)
        for i in xrange(0, len(l), 2):
            to_climate_row_col[tuple(l[i])] = tuple(l[i+1])

    print "bla"



main()
#load_mapping()
