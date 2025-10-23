#!/bin/python

import sys
args = sys.argv

#Arguments: 1 = ALS_conv. 2+ = whatever numbers we need.
#returns a "True" or "False" to tell bash to break ALS or not.

a = int(args[1])
br = "False"
if a == 1:
    #If N_diff/N_train < 0.01, aka if N_diff < 1% of N_train
    r = int(args[2])/int(args[3])
    if r < 0.01:
        br = "True"
elif a == 2:
    #If RMSE < chull_var. Note that both are in eV and RMSE arrives doubled, hence the x/2.
    if float(args[2])/2 < float(args[3]):
        br = "True"
elif a == 3:
    #If |new_rmse - prev_rmse| < 0.1 meV/atom. Note that both are in eV and arrive doubled, hence the 0.0002.
    if abs(float(args[2]) - float(args[3])) < 0.0002:
        br = "True"
elif a == 4:
    #If N_Iterations = 50
    if int(args[2]) == 50:
        br = "True"
else:
    print("ALS_conv is 0 or unknown. PRAPs will proceed with default convergence criteria.")

print(br)
