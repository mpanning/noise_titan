#!/bin/bash

source activate obspy
COUNTER=0
while [ $COUNTER -lt 10 ]; do
    filename=catalogs/Titan_cycle_${COUNTER}.pkl
    echo Working on $filename
    python generate_catalog_titan.py $filename
    let COUNTER=COUNTER+1
done
