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
#import copy
from StringIO import StringIO
from datetime import date, datetime, timedelta
from collections import defaultdict
#import types
import sys
#print sys.path
import zmq
print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

import sqlite3
import numpy as np

import monica_io
#print "path to monica_io: ", monica_io.__file__
import soil_io
import ascii_io

#print "sys.path: ", sys.path
#print "sys.version: ", sys.version

USER = "xps15"
LOCAL_RUN = True #False

PATHS = {
    "xps15": {
        "INCLUDE_FILE_BASE_PATH": "C:/Users/berg.ZALF-AD/GitHub",
        "ARCHIVE_PATH_TO_CLIMATE_CSVS_DIR": "/archiv-daten/md/data/climate/dwd/csvs/",
        "PATH_TO_SOIL_DIR": "D:/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": "D:/climate/dwd/csvs/"
    }
}

def main():
    "main"

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    #port = 6666 if len(sys.argv) == 1 else sys.argv[1]
    config = {
        "port": 6666,
        "start": 1,
        "end": 8157
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            k,v = arg.split("=")
            if k in config:
                config[k] = int(v) 

    soil_db_con = sqlite3.connect(PATHS[USER]["PATH_TO_SOIL_DIR"] + "soil.sqlite")

    if LOCAL_RUN:
        socket.connect("tcp://localhost:" + str(config["port"]))
    else:
        socket.connect("tcp://cluster2:" + str(config["port"]))

    with open("sim.json") as _:
        sim = json.load(_)

    with open("site.json") as _:
        site = json.load(_)

    with open("crop.json") as _:
        crop = json.load(_)

    #sim["include-file-base-path"] = PATHS[USER]["INCLUDE_FILE_BASE_PATH"]

    def read_ascii_grid_into_numpy_array(path_to_file, no_of_headerlines=6, extract_fn=lambda s: int(s), np_dtype=np.int32, nodata_value=-9999):
        "read an ascii grid into a map, without the no-data values"
        with open(path_to_file) as file_:
            nrows = 0
            ncols = 0
            row = -1
            arr = None
            skip_count = 0
            for line in file_:
                if skip_count < no_of_headerlines:
                    skip_count += 1
                    sline = line.split(sep=" ")
                    if len(sline) > 1:
                        key = sline[0].strip().upper()
                        if key == "NCOLS":
                            ncols = int(sline[1].strip())
                        elif key == "NROWS":
                            nrows = int(sline[1].strip())

                if skip_count == no_of_headerlines:
                    arr = np.full((nrows, ncols), nodata_value, dtype=np_dtype)

                row += 1
                col = -1
                for col_str in line.strip().split(" "):
                    col += 1
                    if int(col_str) == -9999:
                        continue
                    arr[row, col] = extract_fn(col_str)

            return arr

    soil_ids = read_ascii_grid_into_numpy_array(PATHS[USER]["PATH_TO_SOIL_DIR"] + "buek1000_100_gk5.asc")

    germany_dwd_lats = read_ascii_grid_into_numpy_array(PATHS[USER]["PATH_TO_CLIMATE_CSVS_DIR"] + "germany-lat-lon-coordinates.grid", 2, \
        lambda s: float(s.split("|")[0]), np_dtype=np.float)

    germany_dwd_nodata = read_ascii_grid_into_numpy_array(PATHS[USER]["PATH_TO_CLIMATE_CSVS_DIR"] + "germany-data-no-data.grid", 2, \
        lambda s: 0 if s == "-" else 1)


    def load_mapping():
        ""
        to_climate_row_col = {}

        with(open("out/working_resolution_to_climate_row_col.json")) as _:
            l = json.load(_)
            for i in xrange(0, len(l), 2):
                to_climate_row_col[tuple(l[i])] = tuple(l[i+1])    
        
        return to_climate_row_col
        
    soil_to_climate = load_mapping()


    def update_soil(soil_res, row, col, crop_id):
        "update function"

        crop["cropRotation"][2] = crop_id

        site["SiteParameters"]["SoilProfileParameters"] = soil_io.soil_parameters(soil_db_con, soil_ids[row, col])

        #print site["SiteParameters"]["SoilProfileParameters"]


    soil_profiles = {}
    envs = {}

    start = time.clock()
    i = 1
    srows, scols = soil_ids.shape()
    for srow in xrange(0, srows):

        for scol in xrange(0, scols):

            soil_id = soil_ids[srow, scol]

            if soil_id not in soil_profiles:
                soil_profiles[soil_id] = soil_io.soil_parameters(soil_db_con, soil_id)
                envs[soil_id] = monica_io.create_env_json_from_json_config({
                    "crop": crop,
                    "site": site,
                    "sim": sim,
                    "climate": ""
                })
                envs[soil_id]["params"]["SiteParameters"]["SoilProfileParameters"] = soil_profiles[soil_id]
                envs[soil_id]["csvViaHeaderOptions"] = sim["climate.csv-options"]
            
            env = envs[soil_id]

            crow, ccol = soil_to_climate[(srow, scol)]

            if LOCAL_RUN:
                env["pathToClimateCSV"] = PATHS[USER]["PATH_TO_CLIMATE_CSVS_DIR"] + "germany/row-" + str(crow) + "/col-" + str(ccol) + ".csv"
            else:
                env["pathToClimateCSV"] = PATHS[USER]["ARCHIVE_PATH_TO_CLIMATE_CSVS_DIR"] + "germany/row-" + str(crow) + "/col-" + str(ccol) + ".csv"


            env["customId"] = "(" + str(crow) + "/" + str(ccol) + ")" \
                            + "|(" + str(srow) + "/" + str(scol) + ")"

            #with open("envs/env-"+str(i)+".json", "w") as _:
            #    _.write(json.dumps(env))

            socket.send_json(env)
            print "sent env ", i, " customId: ", env["customId"]
            #exit()
            i += 1

    stop = time.clock()
    print "sending ", (i-1), " envs took ", (stop - start), " seconds"
    #print "ran from ", start, "/", row_cols[start], " to ", end, "/", row_cols[end]
    return


main()