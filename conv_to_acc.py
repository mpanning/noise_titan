"""
read in csv file with freq velocity ASD data and convert to acceleration ASD
"""
import csv
import math
import numpy as np

file = "JAXA_vel_detection.csv" # Data lifted from Yamada et al. (2015)

freqs = []
vel_asd = []
with open(file, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        freqs.append(float(row[0]))
        vel_asd.append(float(row[1]))

freqs = np.array(freqs)
vel_asd = np.array(vel_asd)

acc_asd = np.zeros_like(vel_asd)
for i, freq in enumerate(freqs):
    omega = 2.*math.pi*freq
    acc_asd[i] = vel_asd[i]*omega

file = 'noise_PSS.txt'
with open(file, 'w') as f:
    writer = csv.writer(f, delimiter=' ')
    # writer.writerow(['Frequency (Hz)', 'Velocity ASD (m/s/rtHz)',
    #                  'Acceleration ASD (m/s2/rtHz)'])
    for i, freq in enumerate(freqs):
        writer.writerow([freq, acc_asd[i]])
