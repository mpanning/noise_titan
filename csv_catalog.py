"""
Output a pre-calculated synthetic event catalog as a csv file
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

# Get catalog file from command line
if len(sys.argv) > 1:
    filein = sys.argv[1]
else:
    sys.exit("Please specify the catalog pickle file as an argument")

# Get the catalog from the pickle file
with open(filein, 'rb') as f:
    gr_obj = pickle.load(f)

# Write out a csv file
csv_out = filein + '.csv'
gr_obj.write_csv(csv_out)






