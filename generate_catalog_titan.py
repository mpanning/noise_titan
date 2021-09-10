"""
Calculate a synthetic catalog of events matching a desired Gutenberg-Richter 
relationship
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
import sys

python3 = sys.version_info > (3,0)
if python3:
    import pickle
else:
    import cPickle as pickle

# Determine if the output filename is specified on command line
if len(sys.argv) > 1:
    fileout = sys.argv[1]
else:
    fileout = 'catalog.pkl'

# Basic characteristics of seismicity catalog
# Updated with numbers from Hurford et al. (2020)
m0totalpercycle = 2.7e15
TCycleHrs = 382.7
HrsYr = 24.0*365.0
TCycleYrs = TCycleHrs/HrsYr
m0total = m0totalpercycle/TCycleYrs
max_m0 = 1.9e16
minM = 0.0
min_m0 = gr.calc_m0(minM)
slope = 1.0
secday = 60.0*60.0*24.0
secyear = secday*365.0
secmonth = secday*30.0
catlength = 10.0*TCycleYrs*secyear

# Define upper and lower bounds with an order of magnitude uncertainty on both
# m0total and max_m0
m0total_upper = m0total*10.0
m0total_lower = m0total*0.1
max_m0_upper = max_m0*10.0
max_m0_lower = max_m0*0.1

# Define the Gutenberg-Richter relationship values
gr_obj = gr.GutenbergRichter(b=slope, m0total=m0total, max_m0=max_m0,
                             min_m0=min_m0)
gr_obj.calc_a()

gr_obj_upper = gr.GutenbergRichter(b=slope, m0total=m0total_upper,
                                   max_m0=max_m0_lower, min_m0=min_m0)
gr_obj_upper.calc_a()
gr_obj_lower = gr.GutenbergRichter(b=slope, m0total=m0total_lower,
                                   max_m0=max_m0_upper, min_m0=min_m0)
gr_obj_lower.calc_a()

# Make a plot of the chosen G-R relationship
maxM = gr.calc_Mw(max_m0)
Msamp = 0.25
Mws = np.arange(minM, maxM + Msamp, Msamp)
Ns = gr_obj.get_N(Mws)
Ns_upper = gr_obj_upper.get_N(Mws)
Ns_lower = gr_obj_lower.get_N(Mws)
max_dep = 2.0 #max depth in km, events will be uniform between 0 and max_dep

# Convert Ns to be for one tidal cycle on Titan
Ns = Ns * TCycleYrs
Ns_upper = Ns_upper * TCycleYrs
Ns_lower = Ns_lower * TCycleYrs

# Calculate probability of a given event per second
Nsec = Ns/secyear

# Generate the catalog
# catlength = 10.0*TCycleYrs*secyear
#(catalog, Nsc, Mwsc) = gr_obj.generate_catalog(catlength)
#(catalog2, Nsc2, Mwsc2) = gr_obj.generate_catalog(secmonth)
gr_obj.generate_catalog(catlength, max_dep=max_dep)

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
plt.semilogy(Mws, Ns_upper, color="blue", linestyle="dashed")
plt.semilogy(Mws, Ns_lower, color="blue", linestyle="dashed")
plt.semilogy(gr_obj.catalog.Mws, gr_obj.catalog.Ns, color="darkgreen",
             linestyle="solid")
plt.title("Gutenberg-Richter relationship")
plt.xlabel("Mw")
plt.ylabel("N")

ndays = int(catlength/secday)
plt.subplot(2, 1, 2)
plt.scatter(gr_obj.catalog.data[:,time_id]/secday,
            gr_obj.catalog.data[:,mag_id], facecolor='darkgreen')
plt.title("%d day catalog" % ndays)
plt.xlabel("Day")
plt.ylabel("Magnitude")
plt.xlim([0, ndays])
plt.ylim([0, 6])

# Plt.subplot(3, 1, 3)
# numBins = 30
# plt.hist(gr_obj.catalog.data[:,delta_id],numBins,color='green')
# plt.title("Distances")
# plt.xlabel("Distance (degrees)")
# plt.ylabel("Frequency")

#plt.show()
figname = 'catalog_titan.png'
P.savefig(figname)

# Write out catalog to pickle file
filename = fileout
with open(filename, 'wb') as f:
    pickle.dump(gr_obj, f, -1)

# Make a lower limit catalog
gr_obj_lower.generate_catalog(catlength, max_dep=max_dep)

# Plot it all up
try:
    time_id = gr_obj_lower.catalog.id_dict['time']
    mag_id = gr_obj_lower.catalog.id_dict['magnitude']
    delta_id = gr_obj_lower.catalog.id_dict['delta']
except AttributeError:
    time_id = 0
    mag_id = 1
    delta_id = 2

plt.clf()
plt.figure(figsize=(10,15))
plt.subplot(2, 1, 1)
plt.semilogy(Mws, Ns, color="blue", linestyle="solid")
plt.semilogy(Mws, Ns_upper, color="blue", linestyle="dashed")
plt.semilogy(Mws, Ns_lower, color="blue", linestyle="dashed")
plt.semilogy(gr_obj_lower.catalog.Mws, gr_obj_lower.catalog.Ns,
             color="darkgreen", linestyle="solid")
plt.title("Gutenberg-Richter relationship")
plt.xlabel("Mw")
plt.ylabel("N")

ndays = int(catlength/secday)
plt.subplot(2, 1, 2)
plt.scatter(gr_obj_lower.catalog.data[:,time_id]/secday,
            gr_obj_lower.catalog.data[:,mag_id], facecolor='darkgreen')
plt.title("%d day catalog" % ndays)
plt.xlabel("Day")
plt.ylabel("Magnitude")
plt.xlim([0, ndays])
plt.ylim([0, 6])

figname = 'catalog_lower.png'
P.savefig(figname)

# Write out catalog to pickle file
filename = 'catalog_lower.pkl'
with open(filename, 'wb') as f:
    pickle.dump(gr_obj, f, -1)
