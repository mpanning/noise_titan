"""
Calculate a synthetic catalog of events matching a desired Gutenberg-Richter
relationship, and then generate a noise record from this catalog

Usage: python generate_long_noise.py pklfile minMw dt

All arguments are optional.  

The first argument, if present, is assumed to be a catalog pickle file
consistent with catalogs generated by gutenbergrichter.py

The second argument, if present, is assumed to be a minimum moment magnitude
for calculation of waveforms.
"""

import gutenbergrichter as gr
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pylab as P
from tqdm import tqdm
import obspy
import instaseis
import sys
import argparse
python3 = sys.version_info > (3,0)

if python3:
    import pickle
else:
    import cPickle as pickle
    from requests.exceptions import ConnectionError

def wtcoef(t,t1,t2,t3,t4):
    """
    Function to calculate cosine taper

    returns weight coefficient between 0 and 1

    cosine taper from 0 to 1 t1 < t < t2
    1 for t2 < t < t3
    cosine taper from 1 to 0 t3 < t < t4
    0 for t < t1 or t > t2
    """

    if t3 > t4:
        raise ValueError('wtcoef: t3>t4')
    if t1 > t2:
        raise ValueError('wtcoef: t1>t2')

    if (t >= t2) and (t <= t3):
        wt = 1.0
    elif (t >= t4) or (t <= t1):
        wt = 0.0
    elif (t > t3) and (t < t4):
        wt = 0.5 * (1.0 + math.cos(math.pi * (t - t3)/(t4 - t3)))
    elif (t > t1) and (t < t2):
        wt = 0.5 * (1.0 + math.cos(math.pi * (t - t2)/(t2 - t1)))
    else:
        print(t, t1, t2, t3, t4)
        raise ValueError('wtcoef: this should be impossible')
    return wt

# Parse arguments
parser = argparse.ArgumentParser(description=('Generates a long noise record '
                                              + 'from a modeled quake '
                                              + 'catalog.'))
parser.add_argument('-m', '--minMw', type=float,
                    help='Minimum magnitude event for waveform calculation')
parser.add_argument('-d', '--decimation', type=int,
                    help='Decimation factor for seismogram output')
parser.add_argument('pklfile', nargs='?',
                    help='Input catalog pickle file')
args = parser.parse_args()
                                 

# Details for noise record calculation
instaseisDB= "http://instaseis.ethz.ch/icy_ocean_worlds/Tit046km-33pNH-hQ_noiceVI_2s"
db_short = 'Titan46'
taperFrac = 0.05 #end taper length as fraction of db record length
endCutFrac = 0.0 #Allows cutting of end of records to remove numerical probs
maxRetry = 100 

# Basic useful values
secday = 60.0*60.0*24.0
secyear = secday*365.0
secmonth = secday*30.0


# Determine if a catalog pickle file is included on command line
if (args.pklfile is not None): #Assumes argv[1] is pickle file
    filename = args.pklfile
    root = '.'.join(filename.split('.')[:-1])
    with open(filename, 'rb') as f:
        if python3:
            gr_obj = pickle.load(f, encoding='latin1')
        else:
            gr_obj = pickle.load(f)
    minM = gr.calc_Mw(gr_obj.min_m0)
    maxM = gr.calc_Mw(gr_obj.max_m0)
    Msamp = 0.25
    Mws = np.arange(minM, maxM + Msamp, Msamp)
    Ns = gr_obj.get_N(Mws)
    setmin = True
    if (args.minMw is not None):
        min_Mw = args.minMw
    else: # If no min_Mw argument is given
        setmin = False
        min_Mw = -999.0
    

else:
    # Basic characteristics of seismicity catalog
    m0total = 1.0e17
    max_m0 = math.pow(10.0,19.5)
    minM = -1.0
    min_m0 = gr.calc_m0(minM)
    slope = 1.0

    root = 'random'

    # Define the Gutenberg-Richter relationship values
    gr_obj = gr.GutenbergRichter(b=slope, m0total=m0total, max_m0=max_m0,
                                 min_m0=min_m0)
    gr_obj.calc_a()

    # Make a plot of the chosen G-R relationship
    maxM = gr.calc_Mw(max_m0)
    Msamp = 0.25
    Mws = np.arange(minM, maxM + Msamp, Msamp)
    Ns = gr_obj.get_N(Mws)


    # Calculate probability of a given event per second
    Nsec = Ns/secyear

    # Generate catalog
    catlength = 2.0*secday
    gr_obj.generate_catalog(catlength)

def limit_depth(db, depth):
    # Hack: If source depth is larger than maximum depth of
    #       database, scale it to range (0, max_depth)
    #       Assumes that catalog maximum depth is 10 km, which
    #       is the hardcoded value right now.
    radius = db.info.planet_radius
    db_maxdepth = db.info.planet_radius - db.info.min_radius
    if (depth > db_maxdepth): 
        depth *= db_maxdepth / 10e3
    return depth

#(catalog2, Nsc2, Mwsc2) = gr_obj.generate_catalog(secmonth)

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
plt.subplot(3, 1, 1)
plt.semilogy(Mws, Ns, gr_obj.catalog.Mws, gr_obj.catalog.Ns)
plt.title("Gutenberg-Richter relationship")
plt.xlabel("Mw")
plt.ylabel("N")

plt.subplot(3, 1, 2)
secday = 60.0*60.0*24.0
secyear = secday*365.0
catlength = gr_obj.catalog.length
ndays = int(catlength/secday)
plt.scatter(gr_obj.catalog.data[:,time_id]/secday,
            gr_obj.catalog.data[:,mag_id])
plt.title("%d day catalog" % ndays)
plt.xlabel("Day")
plt.ylabel("Magnitude")
plt.xlim([0, ndays])

plt.subplot(3, 1, 3)
numBins = 30
plt.hist(gr_obj.catalog.data[:,delta_id],numBins,color='green')
plt.title("Distances")
plt.xlabel("Distance (degrees)")
plt.ylabel("Frequency")

#plt.show()
figname = 'catalog.png'
P.savefig(figname)

# Now we use instaseis to make a noise record
# db = instaseis.open_db("Instaseis_test/prem_a_20s")
# db = instaseis.open_db("/Volumes/Samsung/EuropaZbLowVUpper30kmMantle20km0WtPctMgSO4")
db = instaseis.open_db(instaseisDB)

# Initialize noise record
dbdt = db.info['dt']
if (args.decimation is not None):
    dt_out = dbdt * args.decimation
else:
    dt_out = dbdt
dbnpts = db.info['npts']
dblen = dbnpts * dbdt
nsamples = int(gr_obj.catalog.length/dt_out) + int(dblen/dt_out)
noise = np.zeros((3,nsamples))

# Create taper windowing function. Can be done once, since all
# seismograms should have the same length
# Taper the end of the data to avoid abrupt endings
t1 = 0
t2 = 0
t4 = int(dbnpts * (1 - endCutFrac)) - 1
t3 = int(t4 - taperFrac * db.info.npts)

wt = np.zeros(dbnpts)
for s in range(dbnpts):
    wt[s] = wtcoef(s, t1, t2, t3, t4)


# Reciever is placed at pole to make it quick to calculate source location
# from delta and backazimuth from catalog
receiver = instaseis.Receiver(latitude=90.0, longitude=0.0, network="XX",
                              station="EURP")

# Loop on sources and make seismograms with InstaSeis
nevents = gr_obj.catalog.data.shape[0]
try:
    time_id = gr_obj.catalog.id_dict['time']
    mag_id = gr_obj.catalog.id_dict['magnitude']
    delta_id = gr_obj.catalog.id_dict['delta']
    baz_id = gr_obj.catalog.id_dict['backaz']
    depth_id = gr_obj.catalog.id_dict['depth']
    strike_id = gr_obj.catalog.id_dict['strike']
    rake_id = gr_obj.catalog.id_dict['rake']
    dip_id = gr_obj.catalog.id_dict['dip']
except AttributeError:
    time_id = 0
    mag_id = 1
    delta_id = 2
    baz_id = 3
    depth_id = 4
    strike_id = 5
    rake_id = 6
    dip_id = 7

for evt in tqdm(range(0, nevents)):
    if (setmin and gr_obj.catalog.data[evt, mag_id] < min_Mw):
        continue
    latitude = 90.0 - gr_obj.catalog.data[evt, delta_id]
    longitude = gr_obj.catalog.data[evt, baz_id]
    if longitude > 180.0:
        longitude -= 360.0
    depth = limit_depth(db, 
                        gr_obj.catalog.data[evt, depth_id] * 1000.)
    strike = gr_obj.catalog.data[evt, strike_id]
    rake = gr_obj.catalog.data[evt, rake_id]
    dip = gr_obj.catalog.data[evt, dip_id]
    M0 = gr.calc_m0(gr_obj.catalog.data[evt, mag_id])
    source = instaseis.Source.from_strike_dip_rake(latitude=latitude,
                                                   longitude=longitude,
                                                   depth_in_m=depth,
                                                   strike=strike, rake=rake,
                                                   dip=dip, M0=M0)
    try:
        st = db.get_seismograms(source=source, receiver=receiver,
                                remove_source_shift=False)
        for tr in st: #Apply taper before decimation
            tr.data = np.multiply(wt, tr.data)
        if (args.decimation is not None): #decimate if requested
            st.decimate(factor=args.decimation)
    except (ConnectionError, TypeError): # Catch http-related errors and retry 
        for i in range(maxRetry):
            try:
                st = db.get_seismograms(source=source, receiver=receiver,
                                        remove_source_shift=False)
            except (ConnectionError, TypeError):
                continue
            break
        else:
            print("Could not connect after max retries")
                

    s1 = int(gr_obj.catalog.data[evt, time_id]/dt_out)
    s2 = s1 + len(st[0].data) 

    noise[0, s1:s2] += st[0].data
    noise[1, s1:s2] += st[1].data
    noise[2, s1:s2] += st[2].data


# Hijack the last stream object to dump the long trace in
for ist in range(3):
    st[ist].data = noise[ist,:]
    st[ist].stats['npts'] = nsamples

st.plot(outfile='noise.png')
print(st)
st[0].stats

for tr in st:
    tr.write('%s.%s' % (db_short, tr.stats.channel), format='SAC')

# Break stream into individual traces for writing to sac files
#st0 = st[0:1]
#st1 = st[1:2]
#st2 = st[2:3]

#print st0
#print st1
#print st2

# Need to work on outputting sac files directly, but for now, just create
# ASCII files

# for i in range(len(st)):
#    filename = root + '.' + db_short + '.noise.' + st[i].stats['channel'] + '.asc'
#    with open(filename, 'w') as f:
#        for j in range(nsamples):
#            t = j * dt
#            f.write(str(t) + ' ' + str(st[i].data[j]) + '\n')


