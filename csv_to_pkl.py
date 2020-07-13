"""
Convert a csv file with events to a gutenbergrichter object and output as 
binary pickle file.  Randomize missing elements
"""

import gutenbergrichter as gr
import math
import random
import numpy as np
from tqdm import tqdm
import csv
import sys

python3 = sys.version_info > (3,0)

if python3:
    import pickle
else:
    import cPickle as pickle
    from requests.exceptions import ConnectionError

infile = 'Titan_159daycatalog_10cycles_MoT5e15_Mm4e16_Mw0to5_time_Mw_latlon_depth_LPSC.csv'
outfile = 'catalogs/Titan_159daycatalog_vary.pkl'
m0totalpercycle = 5.e15
TCycleHrs = 382.7
HrsYr = 24.0*365.0
TCycleYrs = TCycleHrs/HrsYr
m0total = m0totalpercycle/TCycleYrs
max_m0 = 4.e16
maxM = gr.calc_Mw(max_m0)
minM = -1.0
min_m0 = gr.calc_m0(minM)
slope = 1.0
secday = 60.0*60.0*24.0
secyear = secday*365.0
secmonth = secday*30.0


gr_obj = gr.GutenbergRichter(b=slope, m0total=m0total, max_m0=max_m0,
                             min_m0=min_m0)
gr_obj.calc_a()
Msamp = 0.25
Mws = np.arange(minM, maxM + Msamp, Msamp)
Nsec = gr_obj.get_N(Mws)/secyear
Ns = np.zeros_like(Nsec)

catalog = []
evttime_max = -999.0
evtdepth_max = 0.0
with open(infile, 'r') as csvfile:
    evtreader = csv.reader(csvfile)
    evtreader.next() #skip header row
    for row in evtreader:
        evttime_days = float(row[0])
        evttime = evttime_days * secday
        if (evttime > evttime_max):
            evttime_max = evttime
        evtMw = float(row[1])
        mask = (Mws < evtMw).astype(int)
        Ns = Ns + mask
        evtlon = float(row[2])
        evtlat = 90.0 - float(row[3]) #convert to colatitude
        evtdepth = float(row[4])*1.0e-3
        if (evtdepth > evtdepth_max):
            evtdepth_max = evtdepth
        # For other values, use random values
        strike = random.uniform(0,360)
        rake = random.uniform(0,360)
        dip = random.uniform(0,90)
        catalog.append(np.array([evttime, evtMw, evtlat, evtlon, evtdepth,
                                 strike, rake, dip]))

id_dict = {'time' : 0, 'magnitude' : 1, 'delta' : 2, 'backaz' : 3,
           'depth' : 4, 'strike' : 5, 'rake' : 6, 'dip' : 7}
catalog=np.array(catalog)
length = evttime_max
max_dep = evtdepth_max
gr_obj.catalog = gr.Catalog(data=catalog, length=length, max_dep=max_dep,
                            id_dict=id_dict, Mws=Mws, Ns=Ns)
# This does not set Ns and Mws...  This should be fixed in gutenbergrichter.py
    
with open(outfile, 'wb') as f:
    pickle.dump(gr_obj, f, -1)
