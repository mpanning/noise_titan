"""
Make a figure for a catalog
"""

import gutenbergrichter as gr
import math
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pylab as P
from tqdm import tqdm
import cPickle as pickle
import sys

# Determine if the output filename is specified on command line
if len(sys.argv) > 1:
    filein = sys.argv[1]
else:
    print('Usage: python make_cat_fig.py filein')

# Basic characteristics of seismicity catalog
# m0totalpercycle = 4.8e15
TCycleHrs = 382.7
HrsYr = 24.0*365.0
TCycleYrs = TCycleHrs/HrsYr
# m0total = m0totalpercycle/TCycleYrs
# max_m0 = 4e16
# minM = -1.0
# min_m0 = gr.calc_m0(minM)
# slope = 1.0
secday = 60.0*60.0*24.0
secyear = secday*365.0
secmonth = secday*30.0
seccycle = TCycleHrs*3600.0
# catlength = 10.0*TCycleYrs*secyear

# Read catalog and get basic statistics
with open(filein, 'rb') as f:
    gr_obj = pickle.load(f)

catlength = gr_obj.catalog.length
ndays = int(catlength/secday)
ncycles = int(catlength/seccycle)
max_m0 = gr_obj.max_m0
min_m0 = gr_obj.min_m0
m0total = gr_obj.m0total
slope = gr_obj.b
max_dep = gr_obj.max_dep

# Define upper and lower bounds with an order of magnitude uncertainty on both
# m0total and max_m0
m0total_upper = m0total*10.0
m0total_lower = m0total*0.1
max_m0_upper = max_m0*10.0
max_m0_lower = max_m0*0.1

# Define the Gutenberg-Richter relationship values for uncertainty estimates
# gr_obj = gr.GutenbergRichter(b=slope, m0total=m0total, max_m0=max_m0,
#                              min_m0=min_m0)
# gr_obj.calc_a()

gr_obj_upper1 = gr.GutenbergRichter(b=slope, m0total=m0total_upper,
                                   max_m0=max_m0, min_m0=min_m0)
gr_obj_upper1.calc_a()
gr_obj_upper2 = gr.GutenbergRichter(b=slope, m0total=m0total_upper,
                                   max_m0=max_m0_lower, min_m0=min_m0)
gr_obj_upper2.calc_a()
gr_obj_lower1 = gr.GutenbergRichter(b=slope, m0total=m0total_lower,
                                   max_m0=max_m0, min_m0=min_m0)
gr_obj_lower1.calc_a()
gr_obj_lower2 = gr.GutenbergRichter(b=slope, m0total=m0total_lower,
                                   max_m0=max_m0_upper, min_m0=min_m0)
gr_obj_lower2.calc_a()

# Make a plot of the chosen G-R relationship
maxM = gr.calc_Mw(max_m0)
minM = gr.calc_Mw(min_m0)
Msamp = 0.25
Mws = np.arange(minM, maxM + Msamp, Msamp)
Ns = gr_obj.get_N(Mws)
Ns_upper1 = gr_obj_upper1.get_N(Mws)
Ns_upper2 = gr_obj_upper2.get_N(Mws)
Ns_lower1 = gr_obj_lower1.get_N(Mws)
Ns_lower2 = gr_obj_lower2.get_N(Mws)
# max_dep = 2.0 #max depth in km, events will be uniform between 0 and max_dep

# Convert Ns to be for one tidal cycle on Titan
Ns = Ns * TCycleYrs
Ns_upper1 = Ns_upper1 * TCycleYrs
Ns_upper2 = Ns_upper2 * TCycleYrs
Ns_lower1 = Ns_lower1 * TCycleYrs
Ns_lower2 = Ns_lower2 * TCycleYrs

# Calculate probability of a given event per second
Nsec = Ns/secyear

# Generate the catalog
# catlength = 10.0*TCycleYrs*secyear
#(catalog, Nsc, Mwsc) = gr_obj.generate_catalog(catlength)
#(catalog2, Nsc2, Mwsc2) = gr_obj.generate_catalog(secmonth)
# gr_obj.generate_catalog(catlength, max_dep=max_dep)

# Plot it all up
try:
    time_id = gr_obj.catalog.id_dict['time']
    mag_id = gr_obj.catalog.id_dict['magnitude']
    delta_id = gr_obj.catalog.id_dict['delta']
except AttributeError:
    time_id = 0
    mag_id = 1
    delta_id = 2

plt.figure(figsize=(10,15))
plt.subplot(2, 1, 1)
plt.semilogy(Mws, Ns, color="blue", linestyle="solid")
plt.semilogy(Mws, Ns_upper1, color="blue", linestyle="dashed")
plt.semilogy(Mws, Ns_upper2, color="blue", linestyle="dotted")
plt.semilogy(Mws, Ns_lower1, color="blue", linestyle="dashed")
plt.semilogy(Mws, Ns_lower2, color="blue", linestyle="dotted")

plt.semilogy(gr_obj.catalog.Mws[gr_obj.catalog.Ns != 0],
             gr_obj.catalog.Ns[gr_obj.catalog.Ns != 0], color="darkgreen",
             linestyle="solid")
    
plt.title("Gutenberg-Richter relationship")
plt.xlabel("Mw")
plt.ylabel("N")

ndays = int(catlength/secday)
plt.subplot(2, 1, 2)
plt.scatter(gr_obj.catalog.data[:,time_id]/secday,
            gr_obj.catalog.data[:,mag_id], facecolor='darkgreen')
plt.title("%d day (%d tidal cycles) catalog" % (ndays, ncycles))
plt.xlabel("Day")
plt.ylabel("Magnitude")
plt.xlim([0, ndays])
plt.ylim([0, 6])

# plt.subplot(3, 1, 3)
# numBins = 30
# plt.hist(gr_obj.catalog.data[:,delta_id],numBins,color='green')
# plt.title("Distances")
# plt.xlabel("Distance (degrees)")
# plt.ylabel("Frequency")

#plt.show()
figname = 'catalog_titan.png'
P.savefig(figname)




