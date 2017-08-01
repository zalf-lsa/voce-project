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

LOCAL_RUN = True

def main():

    config = {
        "path_to_data": "m:/data/climate/dwd/grids/germany/daily/" if LOCAL_RUN else "/archiv-daten/md/data/climate/dwd/grids/germany/daily/",
        #"path_to_output": "m:/data/climate/dwd/csvs/germany/" if LOCAL_RUN else "/archiv-daten/md/data/climate/dwd/csvs/germany/",
        "path_to_output": "g:/csvs/germany/" if LOCAL_RUN else "/archiv-daten/md/data/climate/dwd/csvs/germany/",
        "start-y": "1",
        "end-y": "-1",
        "start-year": "1995",
        "start-month": "1",
        "end-year": "2012",
        "end-month": "12"
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = vvv

    files = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for f in os.listdir(config["path_to_data"]):
        elem, year_month, _ = str(f).split("_")
        year = int(year_month[:4])
        month = int(year_month[4:])
        files[year][month][elem] = config["path_to_data"] + f

    elem_to_varname = {
        "tmin": "temperature",
        "tavg": "temperature",
        "tmax": "temperature",
        "precip": "precipitation",
        "RH": "humidity",
        "SIS": "SIS",
        "FF": "FF"
    }


    def write_files(cache):
        no_of_files = len(cache)
        count = 0
        for (y, x), rows in cache.iteritems():
            path_to_outdir = config["path_to_output"] + "row-" + str(y) + "/"
            if not os.path.isdir(path_to_outdir):
                os.makedirs(path_to_outdir)

            path_to_outfile = path_to_outdir + "col-" + str(x) + ".csv"
            if not os.path.isfile(path_to_outfile):
                with open(path_to_outfile, "wb") as _:
                    writer = csv.writer(_, delimiter=",")
                    writer.writerow(["iso-date", "tmin", "tavg", "tmax", "precip", "relhumid", "globrad", "windspeed"])
                    writer.writerow(["[]", "[°C]", "[°C]", "[°C]", "[mm]", "[%]", "[MJ m-2]", "[m s-1]"])

            with open(path_to_outfile, "ab") as _:
                writer = csv.writer(_, delimiter=",")
                for row in rows:
                    writer.writerow(row)

            count = count + 1
            if count % 1000 == 0:
                print count, "/", no_of_files, "written"


    write_files_threshold = 50 #ys
    for year, months in files.iteritems():
        if year < int(config["start-year"]):
            continue
        if year > int(config["end-year"]):
            break

        #print "year: ", year, "months: ",
        for month, elems in months.iteritems():
            if year == int(config["start-year"]) and month < int(config["start-month"]):
                continue
            if year == int(config["end-year"]) and month > int(config["end-month"]):
                break

            print "year:", year, "month:", month, "ys ->",
            data = {}
            for elem, filepath in elems.iteritems():
                ds = Dataset(filepath)
                data[elem] = np.copy(ds.variables[elem_to_varname[elem]])
                ds.close()

            ref_data = data["tavg"]
            #no_of_days = len(ref_data.variables["time"])
            no_of_days = ref_data.shape[0]

            start_month = time.clock()
            cache = defaultdict(list)

            for y in range(int(config["start-y"]) - 1, ref_data.shape[1] if int(config["end-y"]) < 0 else int(config["end-y"])):
                #print "y: ", y, "->"
                start_y = time.clock()
                #print y,
                for x in range(ref_data.shape[2]):
                    #print x,

                    if int(ref_data[0, y, x]) == 9999:
                        continue

                    #lat = ref_data.variables["lat"][y, x]
                    #lon = ref_data.variables["lon"][y, x]

                    for i in range(no_of_days):
                        row = [
                            date(year, month, i+1).strftime("%Y-%m-%d"),
                            str(data["tmin"][i, y, x]),
                            str(data["tavg"][i, y, x]),
                            str(data["tmax"][i, y, x]),
                            str(data["precip"][i, y, x]),
                            str(data["RH"][i, y, x]),
                            str(round(data["SIS"][i, y, x] * 3600 / 1000000, 4)),
                            str(data["FF"][i, y, x])

                            #str(data["tmin"].variables["temperature"][i][y][x]),
                            #str(data["tavg"].variables["temperature"][i][y][x]),
                            #str(data["tmax"].variables["temperature"][i][y][x]),
                            #str(data["precip"].variables["precipitation"][i][y][x]),
                            #str(data["RH"].variables["humidity"][i][y][x]),
                            #str(round(data["SIS"].variables["SIS"][i][y][x] * 3600 / 1000000, 4)),
                            #str(data["FF"].variables["FF"][i][y][x])
                        ]
                        cache[(y,x)].append(row)
                
                end_y = time.clock()
                print y, #str(y) + "|" + str(int(end_y - start_y)) + "s ",
               
                if y > int(config["start-y"]) and y % write_files_threshold == 0:
                    print ""
                    s = time.clock()
                    write_files(cache)
                    cache = defaultdict(list)
                    e = time.clock()
                    print "wrote", write_files_threshold, "ys in", (e-s), "seconds"

            #for dataset in data.values():
            #    dataset.close()
            print ""

            #write remaining cache items
            write_files(cache)

            end_month = time.clock()
            print "running month", month, "took", (end_month - start_month), "seconds"

main()