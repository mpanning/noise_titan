# noise_titan

This is a repository for developing icequake catalogs and noise records for Titan analogous to those made for Europa in Panning et al. (JGR, 2018).

`generate_titan_catalog.py`

Uses `gutenbergrichter.py` to create a catalog according to desired cumulative seismic moment and maximum event size.

`generate_noise.py`

Uses Instaseis to create a long noise record based on catalogs created by `generate_titan_catalog.py`.  Incorporates command line arguments to specify the input catalog, and whether to limit the minimum event size or decimate the data to speed up the calculation or reduce the size of output files

`make_cat_fig.py`

Makes a plot of a catalog, and adds in possible range of uncertainties by shifting cumulative moment and maximum event size by an order of magnitude.
