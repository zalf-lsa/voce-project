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

import time
import os
import math
import json
import pickle
import csv
import itertools
#import copy
from StringIO import StringIO
from datetime import date, datetime, timedelta
from collections import defaultdict, OrderedDict
#import types
import sys
print sys.path
#import zmq
#print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

from netCDF4 import Dataset
import numpy as np

def create_regnie_dicts():
    "create a nested ordered dicts which map regnie lat/lon coordinates to y/x coordinates"
    ydelta_grad = 1.0 / 120.0
    xdelta_grad = 1.0 / 60.0
    regnie_lat_lon = OrderedDict()
    for y in range(971):
        lat = (55.0 + 10.0 * ydelta_grad) - (y - 1) * ydelta_grad
        for x in range(611):
            lon = (6.0 - 10.0 * xdelta_grad) + (x - 1) * xdelta_grad
            if not lat in regnie_lat_lon:
                regnie_lat_lon[lat] = OrderedDict()
            regnie_lat_lon[lat][lon] = (y, x)
    return regnie_lat_lon

def convert_regnie_pixel_to_geographic_coordinates(cartesian_point_regnie): # y, x
    " Berechnungsfunktion"
    xdelta_grad = 1.0 /  60.0
    ydelta_grad = 1.0 / 120.0
    lat = (55.0 + 10.0 * ydelta_grad) - (cartesian_point_regnie[0] - 1) * ydelta_grad
    lon = ( 6.0 - 10.0 * xdelta_grad) + (cartesian_point_regnie[1] - 1) * xdelta_grad
    return lat, lon


def read_daily_regnie_ascii_grid(path_to_file):
    "read an ascii grid into a map, without the no-data values"
    with open(path_to_file) as file_:
        data = {}
        row = 0
        for line in file_:
            if line[0] == " ":
                continue
            col = 0
            for i in range(0, len(line)-1, 4):
                val = int(line[i:i+4])
                if val != -999:
                    data[(row, col)] = val / 10.0
                col += 1
            row += 1
        return data



def main():

    config = {
        "path_to_data": "m:/data/climate/dwd/grids/germany/daily/",
        "path_to_output": "m:/data/climate/dwd/csvs/germany/",
        "start": 1,
        "end": 938
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = int(vvv)

    path_to_data = config["path_to_data"]
    path_to_output = config["path_to_output"]

    ref_data = Dataset(path_to_data + "tavg_199501_daymean.nc")
    #no_of_days = len(ref_data.variables["time"])

    # first create a mapping of regnie cells to netcdf cells based on lat/lon proximity
    nc_to_regnie = {}
    for f in os.listdir("out"):
        with open("out/" + f) as _:
            dic = pickle.load(_)
            nc_to_regnie.update(dic)


    len_ys = len(ref_data.dimensions["y"])
    len_xs = len(ref_data.dimensions["x"])

    # put all precip data of current month into dict for easy access like with netcdfs
    regnie = {}
    for day in range(no_of_days):
        path_to_regniefile = path_to_data + "../daily-regnie/ra" + str(year) + "m/ra" + date(year, month, day+1).strftime("%y%m%d")
        regnie[day] = read_daily_regnie_ascii_grid(path_to_regniefile)

    for y in range(len_ys):
        for x in range(len_xs):

            lat = ref_data.variables["lat"][y, x]
            lon = ref_data.variables["lon"][y, x]
            reg_row, reg_col = find_closest_lat_lon(regnie_lat_lon, lat, lon)
            reg_coord = (reg_row, reg_col) if reg_row and reg_col else None

            if not reg_coord:
                print "year: ", year, " month: ", " no regnie coord found for lat/lon: ", lat, "/", lon, " y/x: ", y, "/", x, " skipping"
                continue

            path_to_outdir = path_to_output + "row-" + str(y) + "/"
            if not os.path.isdir(path_to_outdir):
                os.makedirs(path_to_outdir)

            path_to_outfile = path_to_outdir + "col-" + str(x)
            if not os.path.isfile(path_to_outfile):
                with open(path_to_outfile, "w") as _:
                    _.write(["iso-date", "tmin", "tavg", "tmax", "precip", "relhumid", "globrad", "windspeed"])
                    _.write(["[]", "[°C]", "[°C]", "[°C]", "[mm]", "[%]", "[MJ m-2]", "[m s-1]"])

            with open(path_to_outdir + "col-" + str(x), "a") as _:
                writer = csv.writer(_, delimiter=",")
                for i in range(no_of_days):
                    row = [
                        date(year, month, i+1).strftime("%Y-%m-%d"),
                        str(data["tmin"].variables["temperature"][i][y][x]),
                        str(data["tavg"].variables["temperature"][i][y][x]),
                        str(data["tmax"].variables["temperature"][i][y][x]),
                        str(regnie[i][reg_coord]) if reg_coord and reg_coord in regnie[i] else "0",
                        str(data["RH"].variables["humidity"][i][y][x]),
                        str(data["SIS"].variables["SIS"][i][y][x]),
                        str(data["FF"].variables["FF"][i][y][x])
                    ]
                    writer.writerow(row)
            
    ref_data.close()

main()


def main_write_nc_to_regnie():

    config = {
        "path_to_data": "m:/data/climate/dwd/grids/germany/daily/",
        "path_to_output": "m:/data/climate/dwd/csvs/germany/",
        "start": 1,
        "end": 938
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = int(vvv)

    path_to_data = config["path_to_data"]
    path_to_output = config["path_to_output"]


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
                nex_dist = nex - lat
                return cur if cur_dist <= nex_dist else nex

        return None


    def find_closest_lat_lon(regdic, lat, lon):
        "find the (row, col) of the closest lat/lon value in dictionary regdic"
        closest_lat = find_closest_value(regdic, lat)
        if closest_lat:
            closest_lon = find_closest_value(regdic[closest_lat], lon)
            if closest_lon:
                return regdic[closest_lat][closest_lon]

        return (None, None)


    ref_data = Dataset(path_to_data + "tavg_199501_daymean.nc")
    #no_of_days = len(ref_data.variables["time"])

    regnie_lat_lon = create_regnie_dicts()


    # first create a mapping of regnie cells to netcdf cells based on lat/lon proximity
    nc_to_regnie = {}
    #len_ys = len(ref_data.dimensions["y"])
    len_xs = len(ref_data.dimensions["x"])

    yc = 1
    for y in range(config["start"]-1, config["end"]):
        for x in range(len_xs):

            lat = ref_data.variables["lat"][y, x]
            lon = ref_data.variables["lon"][y, x]
            reg_row, reg_col = find_closest_lat_lon(regnie_lat_lon, lat, lon)
            reg_coord = (reg_row, reg_col) if reg_row and reg_col else None

            nc_to_regnie[(y,x)] = reg_coord

        yc = yc + 1
        print yc, " of ", (config["end"] - config["start"] + 1), " done"


    with open("out/nc_to_regnie_" + str(config["start"]) + "-" + str(config["end"]) + ".pickle", "w") as _:
        pickle.dump(nc_to_regnie, _)

    ref_data.close()
    return

#main_write_nc_to_regnie()