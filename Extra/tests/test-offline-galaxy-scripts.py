from pyPhysio.galaxy.GalaxyHRVAnalysis import *
from pyPhysio.galaxy.GalaxyLoadRR import *
from pyPhysio.galaxy.GalaxyFilter import *
from pyPhysio.galaxy.GalaxyNormalizeRR import *
from pyPhysio.galaxy.GalaxyLinearTimeWindows import *
from pyPhysio.features import get_available_indexes

hrv_list = get_available_indexes()
in_file = "../z_data/A05.txt"
rr_file = "rr.ibi"
out_file = "features.csv"
win_file = "wins.win"
GalaxyLoadRR(input=in_file, output=rr_file, data_type='rr').execute()
GalaxyFilter(input=rr_file, output=rr_file).execute()
GalaxyLinearTimeWindows(input=rr_file, output=win_file, step=20, width=40).execute()
GalaxyNormalizeRR(input=rr_file, output=rr_file, norm_mode="mean_sd").execute()
print GalaxyHRVAnalysis(input=rr_file, output=out_file, input_w=win_file, indexes=hrv_list).execute()