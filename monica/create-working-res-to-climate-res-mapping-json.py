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

import json
from pyproj import Proj, transform

def main():
    "main function"

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

    to_climate_index = []
    to_climate_geo = []

    def closest_climate_geocoord(v):
        vi = int(v)
        v_ = v - vi
        return vi + 0.25 if v_ >= 0 and v_ < 0.5 else vi + 0.75

    def climate_index(start, geocoord):
        return int((start - geocoord) * 2)

    for y in range(0, nrows):

        for x in range(0, ncols):

            h = yll + (cellsize / 2) + (241 - y) * 1000
            r = xll + (cellsize / 2) + x * 1000
            lon, lat = transform(gk5, wgs84, r, h)

            cclon = closest_climate_geocoord(lon)
            cclat = closest_climate_geocoord(lat)

            to_climate_geo.append((y, x))
            to_climate_geo.append((cclat, cclon))

            ilon = abs(int((-179.75 - cclon) * 2))
            ilat = abs(int((89.75 - cclat) * 2))

            to_climate_index.append((y, x))
            to_climate_index.append((ilat, ilon))

    with open("working_resolution_to_climate_lat_lon_indices.json", "w") as _:
        _.write(json.dumps(to_climate_index))

    with open("working_resolution_to_climate_lat_lon_geo_coords.json", "w") as _:
        _.write(json.dumps(to_climate_geo))


def load_mapping():

    to_climate_index = {}

    with(open("working_resolution_to_climate_lat_lon_indizes.json")) as _:
        l = json.load(_)
        for i in xrange(0, len(l), 2):
            to_climate_index[tuple(l[i])] = tuple(l[i+1])

    print "bla"



main()
#load_mapping()



