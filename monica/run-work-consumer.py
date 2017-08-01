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
#sys.path.insert(0, "C:\\Users\\berg.ZALF-AD\\GitHub\\monica\\project-files\\Win32\\Release")
#sys.path.insert(0, "C:\\Users\\berg.ZALF-AD\\GitHub\\monica\\src\\python")
#sys.path.insert(0, "C:\\Program Files (x86)\\MONICA")
print sys.path

import gc
import csv
import types
import os
import json
from datetime import datetime
from collections import defaultdict, OrderedDict
import string

import zmq
print "pyzmq version: ", zmq.pyzmq_version(), " zmq version: ", zmq.zmq_version()

import monica_io
import numpy as np
#print "path to monica_io: ", monica_io.__file__

def create_output(result):
    "create crop output lines"

    out = []
    if len(result.get("data", [])) > 0 and len(result["data"][0].get("results", [])) > 0:

        year_to_vals = defaultdict(dict)

        for data in result.get("data", []):
            results = data.get("results", [])
            oids = data.get("outputIds", [])

            #skip empty results, e.g. when event condition haven't been met
            if len(results) == 0:
                continue

            assert len(oids) == len(results)
            for kkk in range(0, len(results[0])):
                vals = {}

                for iii in range(0, len(oids)):
                    oid = oids[iii]
                    val = results[iii][kkk]

                    name = oid["name"] if len(oid["displayName"]) == 0 else oid["displayName"]

                    if isinstance(val, types.ListType):
                        for val_ in val:
                            vals[name] = val_
                    else:
                        vals[name] = val

                if "Year" not in vals:
                    print "Missing Year in result section. Skipping results section."
                    continue

                year_to_vals[vals.get("Year", 0)].update(vals)

        return year_to_vals

    return out


HEADER = """ncols         3653
nrows         5001
xllcorner     5137800
yllcorner     5562800
cellsize      100
NODATA_value  -9999
"""

def write_row_to_grids(all_data, template_grid, srow, years):
    "write grids row by row"

    srow_template = template_grid[srow]
    srows, scols = template_grid.shape

    output_grids = {
        "sumYield": defaultdict(list),
        "sumGIso": defaultdict(list),
        "sumGMono": defaultdict(list),
        "sumJIso": defaultdict(list),
        "sumJMono": defaultdict(list),
        "sumGlobrad": defaultdict(list),
        "avgGlobrad": defaultdict(list),
        "sumTavg": defaultdict(list),
        "avgTavg": defaultdict(list),
        "maxLAI": defaultdict(list)
    }

    for scol in xrange(0, scols):
        no_data = srow_template[scol] == -9999
        if no_data:
            for year in years:
                for key, val in output_grids.iteritems():
                    val[year].append(-9999)
        else:
            for year, data in all_data[srow][scol].iteritems():
                for key, val in output_grids.iteritems():
                    val[year].append(data[key])


    for key, y2d in output_grids.iteritems():

        for year, row in y2d.iteritems():
            path_to_file = "out/" + key + "_" + str(year) + ".asc"

            if not os.path.isfile(path_to_file):
                with open(path_to_file, "w") as _:
                    _.write(HEADER)

            with open(path_to_file, "a") as _:
                rowstr = " ".join(map(str, row))
                _.write(rowstr +  "\n")

    all_data[srow] = {}



USER = "xps15"
LOCAL_RUN = False

PATHS = {
    "xps15": {
        "INCLUDE_FILE_BASE_PATH": "C:/Users/berg.ZALF-AD/GitHub",
        "ARCHIVE_PATH_TO_CLIMATE_CSVS_DIR": "/archiv-daten/md/data/climate/dwd/csvs/",
        "PATH_TO_SOIL_DIR": "D:/soil/buek1000/ddr/",
        "PATH_TO_CLIMATE_CSVS_DIR": "D:/climate/dwd/csvs/"
    }
}

rtd_col_count = {}
tgf_at_row = -1
template_np_grid = None

def main():
    "collect data from workers"

    data = defaultdict(dict)
    next_row = 0

    with open(PATHS[USER]["PATH_TO_SOIL_DIR"] + "buek1000_100_gk5.asc") as template_grid_file:
        
        def row_to_data_col_count(row, sub=None): 
            global tgf_at_row
            global rtd_col_count
            global template_np_grid
            scols = 3653
            srows = 5001
            if tgf_at_row < 0:
                template_np_grid = np.full((srows, scols), -9999, dtype=np.int32)
                for _ in range(0, 6):
                    template_grid_file.next()
            
            for r in xrange(tgf_at_row, row):
                
                line = template_grid_file.next()
                tgf_at_row += 1

                col = -1
                count = 0
                for col_str in line.strip().split(" "):
                    col += 1
                    if int(col_str) == -9999:
                        continue
                    template_np_grid[tgf_at_row, col] = int(col_str)
                    count += 1

                rtd_col_count[tgf_at_row] = count

            if row in rtd_col_count:
                if sub:
                    rtd_col_count[row] -= sub
                else:
                    return rtd_col_count[row]
            
            return None


        i = 1
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        if LOCAL_RUN:
            socket.connect("tcp://localhost:7777")
        else:
            socket.connect("tcp://cluster2:17777")
        socket.RCVTIMEO = 1000
        leave = False
        write_normal_output_files = False
        #start_writing_lines_threshold = 270
        while not leave:

            try:
                result = socket.recv_json(encoding="latin-1")
            except:
                #for crop_id, production_situation, period, grcp, climate_resolution, soil_resolution in data.keys():
                #    if len(data[(crop_id, production_situation, period, grcp, climate_resolution, soil_resolution)]) > 0:
                #        write_data(crop_id, production_situation, period, grcp, climate_resolution, soil_resolution, data)
                continue

            if result["type"] == "finish":
                print "received finish message"
                leave = True

            elif not write_normal_output_files:
                print "received work result ", i, " customId: ", result.get("customId", "")

                custom_id = result["customId"]
                ci_parts = custom_id.split("|")
                crow, ccol = map(int, ci_parts[0][1:-1].split("/")) 
                srow, scol = map(int, ci_parts[1][1:-1].split("/")) 

                data[srow][scol] = create_output(result)
                row_to_data_col_count(srow, sub=1)
                
                while row_to_data_col_count(next_row) == 0:
                    write_row_to_grids(data, template_np_grid, next_row, data[srow][scol].keys())
                    next_row += 1

                i = i + 1

            elif write_normal_output_files:
                print "received work result ", i, " customId: ", result.get("customId", "")

                custom_id = result["customId"]
                ci_parts = custom_id.split("|")
                crow, ccol = map(int, ci_parts[0][1:-1].split("/")) 
                srow, scol = map(int, ci_parts[1][1:-1].split("/")) 
                file_name = "crow"+ str(crow) + "-ccol" + str(ccol) + "-srow"+ str(srow) + "-scol" + str(scol)

                with open("out/out-" + file_name + ".csv", 'wb') as _:
                    writer = csv.writer(_, delimiter=",")

                    for data_ in result.get("data", []):
                        results = data_.get("results", [])
                        orig_spec = data_.get("origSpec", "")
                        output_ids = data_.get("outputIds", [])

                        if len(results) > 0:
                            writer.writerow([orig_spec.replace("\"", "")])
                            for row in monica_io.write_output_header_rows(output_ids,
                                                                        include_header_row=True,
                                                                        include_units_row=True,
                                                                        include_time_agg=False):
                                writer.writerow(row)

                            for row in monica_io.write_output(output_ids, results):
                                writer.writerow(row)

                        writer.writerow([])

                i = i + 1

        

main()


