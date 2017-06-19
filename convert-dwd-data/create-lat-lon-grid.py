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

def main():

    config = {
        "path_to_data": "m:/data/climate/dwd/grids/germany/daily/"
    }
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            kkk, vvv = arg.split("=")
            if kkk in config:
                config[kkk] = int(vvv)

    ds = Dataset(config["path_to_data"] + "tavg_199501_daymean.nc")
    lats = np.copy(ds.variables["lat"])
    lons = np.copy(ds.variables["lon"])
    temps = np.copy(ds.variables["temperature"][0])

    if False:
        with open("lat-lon.grid", "w") as _:
            _.write("NCOLS 720\n")
            _.write("NROWS 938\n")
            for y in range(0, 938):
                line = []
                for x in range(0, 720):
                    line.append(str(round(lats[y, x], 4)) + "|" + str(round(lons[y, x], 4)))
                _.write(" ".join(line))
                if y < 937:
                    _.write("\n")
                print "wrote line", y

    if True:
        with open("data-no-data.grid", "w") as _:
            _.write("NCOLS 720\n")
            _.write("NROWS 938\n")
            _.write("NODATA_VALUE -\n")
            for y in range(0, 938):
                line = []
                for x in range(0, 720):
                    line.append("-" if temps[y, x] == 9999 else "x")
                _.write(" ".join(line))
                if y < 937:
                    _.write("\n")
                print "wrote line", y

    ds.close()

main()