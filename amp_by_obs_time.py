"""
Reads in a long file, and chops it into a series of small observation chunks and calculates the PPSD.  Saves the top 1% psd for each chunk, and then calculates the statistics to determine likely observation amplitude as a function of observation time
"""

from obspy.signal import PPSD
from obspy import read, UTCDateTime
import numpy as np
from tqdm import tqdm
import sys

# Hack to suppress stdout from PPSD
class NullWriter(object):
    def write(self, arg):
        pass

noisefile = 'noise_records/Titan46_100cycle_0.MXZ'
outputfile = 'amp_by_obs_time.csv'
ppsd_length = 1800.

# Define a flat response file
paz = {'gain': 1.0,
       'poles': [],
       'zeros': [],
       'sensitivity': 1.0}

secday = 3600. * 24 # seconds per Earth day
secyear = 365 * secday
hrsyear = secyear/3600.
TCycleHrs = 382.7
TCycleSecs = TCycleHrs * 3600.
HrsYr = 24.0*365.0
TCycleYrs = TCycleHrs/HrsYr

# Get stats about noise file
st = read(noisefile)

starttime = st[0].stats.starttime
endtime = st[0].stats.endtime
#temp for test only look at 20 cycles
endtime = starttime + 20.*TCycleHrs*3600.
#end temp for test
length = endtime - starttime



print('The input noise record is %.2f seconds (%.2f tidal cycles) long.' % (length, length/TCycleSecs))

obslengths = np.arange(50., 5.*TCycleHrs, 100.)
# obslengths = [50.]

refperiod = 3.
nullwrite = NullWriter()
amp_by_obs_length = []
for obslength in tqdm(obslengths):
    peak_amp = []
    start = starttime
    end = start + obslength*3600.
    while (end < endtime):
        # print((end-starttime)/length)
        st = read(noisefile, starttime=start, endtime=end)
        oldstdout = sys.stdout
        sys.stdout = nullwrite
        ppsd = PPSD(st[0].stats, paz, db_bins=[-300, -75, 5],
                    period_limits=[1.0, 200], ppsd_length=ppsd_length)
        ppsd.add(st)
        (pd, psd) = ppsd.get_percentile(percentile=95)
        sys.stdout = oldstdout
        peak_amp.append(float(psd.max()))
        start = end
        end = start + obslength*3600.

    peak_amp = np.array(peak_amp)
    amp_by_obs_length.append(peak_amp)

with open(outputfile, 'w') as f:
    f.write('Obs period, mean, std, median, 5th percentile\n')
    for i, obslength in enumerate(obslengths):
        f.write('%.1f, %.2f, %.1f, %.1f, %.1f\n' %
                (obslength, np.mean(amp_by_obs_length[i]),
                 np.std(amp_by_obs_length[i]),
                 np.median(amp_by_obs_length[i]),
                 np.percentile(amp_by_obs_length[i], 5.0)))

