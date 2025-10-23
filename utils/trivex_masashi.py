#!/bin/python/
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  1 11:05:15 2023

@author: Josiah, Masashi
Adaptation of Masashi's convex hull code so it's not a Jupyter notebook

##### CONVEX HULL PLOT INPUT FILE FORMAT #####
    First three columns are number of atoms, fourth is hull distance, and fifth is matplotlib marker type
    Atom1, Atom2, and Atom3 must be renamed to their elemental symbols
    Format must be in the order below starting at the first line
        Atom1    Atom2    Atom3    Hf-hull    MarkerType
          1        1        1        10.5         o
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
sys.path.append('/projects/academmic/ezurek/masashik/software/conda/cache/')
import mpltern
args = sys.argv
#Arguments: 1 = input, 2 = output file extension (png, svg, etc.) without period
import numpy as np
import pandas as pd
#from mpl_toolkits.axes_grid1 import make_axes_locatable
#from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import matplotlib.ticker as plticker
import math
from matplotlib import font_manager
from scipy.spatial import Delaunay

# To add Microsoft fonts:
# conda install -c conda-forge mscorefonts
# Delete cache folder: rm ~/.cache/matplotlib -rf
# Find matplotlibrc file: print(matplotlib.matplotlib_fname())
# Uncomment and edit the following lines
    # font.family: sans-serif
    # font.sans-serif: Arial
# Restart python kernel

plt.rcParams["font.size"] = 16
plt.rcParams['figure.dpi'] = 300
plt.rcParams["font.weight"] = 'normal'
plt.rcParams["axes.labelweight"] = 'bold'
#plt.rcParams["font.family"] = 'arial'

# Apply custom fonts if ttf file is available\n",
#font_path = "arial.ttf"
#prop = font_manager.FontProperties(fname=font_path)
#font_manager.fontManager.addfont(font_path.rsplit('\\\\', 1)[-1])
#plt.rcParams["font.family"] = prop.get_name()

def roundup(x):
    "roundup: function to round number up by tens place"
    return math.ceil(x / 10.0) * 10

# Read input file
raw_data = pd.read_csv(args[1])
#print(raw_data)
#print(raw_data.columns)
raw_data['atom_sum'] = raw_data[raw_data.columns[[0, 1, 2]]].sum(axis=1)
percent_atoms = raw_data[raw_data.columns[[0, 1, 2]]].div(raw_data["atom_sum"], axis=0)
percent_atoms.rename(columns = {percent_atoms.columns[0] : percent_atoms.columns[0] + "_per"}, inplace = True)
percent_atoms.rename(columns = {percent_atoms.columns[1] : percent_atoms.columns[1] + "_per"}, inplace = True)
percent_atoms.rename(columns = {percent_atoms.columns[2] : percent_atoms.columns[2] + "_per"}, inplace = True)
all_data = pd.concat([raw_data,percent_atoms], axis=1)

# Get total number of columns and get column index for last three, which are percent atomic compositions
column_name_list = all_data.columns.values.tolist()
all_data_num_columns = len(column_name_list)
percent_atom1_column = all_data_num_columns - 3
percent_atom2_column = all_data_num_columns - 2
percent_atom3_column = all_data_num_columns - 1

# Convert values in each column to lists
extracted_atom1 = all_data[all_data.columns[percent_atom1_column]].tolist()
extracted_atom2 = all_data[all_data.columns[percent_atom2_column]].tolist()
extracted_atom3 = all_data[all_data.columns[percent_atom3_column]].tolist()
hf_hull_list = all_data[all_data.columns[3]].tolist()
marker_list = all_data[all_data.columns[4]].tolist()

zero_hull_atom1 = []
zero_hull_atom2 = []
zero_hull_atom3 = []
zero_hull_marker_list = []

nonzero_hull_atom1 = []
nonzero_hull_atom2 = []
nonzero_hull_atom3 = []
nonzero_hull_marker_list = []
map_hf_hull_list = []

# Sort structures that are or not on the convex hull
for idx, value in enumerate(hf_hull_list):
    if value == 0.0:
        zero_hull_atom1.append(extracted_atom1[idx])
        zero_hull_atom2.append(extracted_atom2[idx])
        zero_hull_atom3.append(extracted_atom3[idx])
        zero_hull_marker_list.append(marker_list[idx])
    else:
        nonzero_hull_atom1.append(extracted_atom1[idx])
        nonzero_hull_atom2.append(extracted_atom2[idx])
        nonzero_hull_atom3.append(extracted_atom3[idx])
        nonzero_hull_marker_list.append(marker_list[idx])
        map_hf_hull_list.append(hf_hull_list[idx])

# Set colorbar color gradient
cmap = plt.get_cmap('rainbow')
plt.set_cmap(cmap)
label_table_zeroes = all_data[all_data[all_data.columns[3]] == 0]
label_table_zeroes

fig, ax_single = plt.subplots(1, 1, figsize = (10, 5),subplot_kw=dict(projection='ternary'))
marker_size = 100
marker_linewidth = 0.5

##### SINGLE PLOT #####

# Plots points on the convex hull, but keep them invisible
invisible_hull_points = ax_single.scatter(zero_hull_atom1, zero_hull_atom2, zero_hull_atom3, zorder = 4, 
                                          clip_on=False, c = 'black', linewidth = 0.0, s = 0)

# Plots points that are on the convex hull
for each_atom1, each_atom2, each_atom3, each_mark in zip(zero_hull_atom1, 
                                                         zero_hull_atom2, 
                                                         zero_hull_atom3, 
                                                         zero_hull_marker_list):

    ax_single.scatter(each_atom1, each_atom2, each_atom3, zorder = 5, 
                clip_on=False, c = 'black', marker = each_mark, s = marker_size, 
                edgecolor = 'black', linewidth = marker_linewidth)

# Get max hull distance and round up to tens place
if len(map_hf_hull_list) > 0:
    max_distance = max(map_hf_hull_list)
    min_distance = min(map_hf_hull_list)
    max_distance_tens = roundup(max_distance)
    min_distance_tens = math.floor(min_distance/10)*10
else:
    max_distance_tens = 60
    min_distance_tens = 0
if max_distance_tens < 60:
    max_distance_tens = 60
if min_distance_tens > 0:
    min_distance_tens = 0

# Plots points not on the convex hull, but keep them invisible
invisible_points = ax_single.scatter(nonzero_hull_atom1, nonzero_hull_atom2, nonzero_hull_atom3, zorder = 1, 
                               clip_on=False, c = map_hf_hull_list, linewidth = 0.0, s = 0, vmin = min_distance_tens, vmax = max_distance_tens)

# Plots points not on the convex hull; apply correct color and marker type
for idx, value in enumerate(nonzero_hull_atom1):
    # Get hexcode for color of each invisible point
    rgba_tuple = invisible_points.to_rgba(map_hf_hull_list[idx])
    hex_code = mpl.colors.rgb2hex(rgba_tuple, keep_alpha = True)
    ax_single.scatter(nonzero_hull_atom1[idx],nonzero_hull_atom2[idx],nonzero_hull_atom3[idx], zorder = 5,
                clip_on = False, c = hex_code,
                marker = nonzero_hull_marker_list[idx], s = marker_size, 
                edgecolor = 'black', linewidth = marker_linewidth)
ax_single.grid(linestyle='--')
#add_label = " Mole Fraction"
#ax_single.set_tlabel(column_name_list[0] + add_label, fontweight = 'bold')
#ax_single.set_llabel(column_name_list[1] + add_label, fontweight = 'bold')
#ax_single.set_rlabel(column_name_list[2] + add_label, fontweight = 'bold')
#ax_single.taxis.set_label_position('tick1')
#ax_single.laxis.set_label_position('tick1')
#ax_single.raxis.set_label_position('tick1')
ax_single.text(-0.05, 1, -0.023, column_name_list[1], fontweight='bold', ha="center", va="bottom", size=16)
ax_single.text(-0.0005, -0.00023, 0.01, column_name_list[2], fontweight='bold', ha="center", va="bottom", size=16)
ax_single.text(1, -0.01, -0.01, column_name_list[0], fontweight='bold', ha="center", va="bottom", size=16)

#ax_single.set_tlabel(column_name_list[0], fontweight='bold')
#ax_single.set_llabel(column_name_list[1], fontweight='bold')
#ax_single.set_rlabel(column_name_list[2], fontweight='bold')
ticks = [0.2, 0.4, 0.6, 0.8]
ax_single.taxis.set_ticks(ticks)
ax_single.laxis.set_ticks(ticks)
ax_single.raxis.set_ticks(ticks)
ax_single.tick_params(labelrotation='horizontal', width=3, length=6)

# Custom infinite lines (top, left, right) -> (right, left, bottom)
#start_point_list_finite = [[0.000, 0.875, 0.125], [0.10, 0.90, 0.00], [0.20, 0.80, 0.00], [0.33, 0.67, 0.00], [0.00, 0.50, 0.50], [0.67, 0.33, 0.00], [0.67, 0.33, 0.00]]
#end_point_list_finite   = [[0.100, 0.900, 0.000], [0.00, 0.75, 0.25], [0.00, 0.75, 0.25], [0.00, 0.75, 0.25], [0.33, 0.67, 0.00], [0.00, 0.50, 0.50], [0.00, 0.00, 1.00]]

#for each_finite_line_idx, line_coords_finite in enumerate(start_point_list_finite):
#    ax_single.plot([start_point_list_finite[each_finite_line_idx][0], end_point_list_finite[each_finite_line_idx][0]], 
#             [start_point_list_finite[each_finite_line_idx][1], end_point_list_finite[each_finite_line_idx][1]], 
#             [start_point_list_finite[each_finite_line_idx][2], end_point_list_finite[each_finite_line_idx][2]], 
#             color = 'black', zorder = 4, linewidth = 0.75)

# Automatically add tie lines
invisible_hull_list = invisible_hull_points.get_offsets()
invisible_hull_list = np.ma.getdata(invisible_hull_list, subok=True)
tri = Delaunay(invisible_hull_list)

ax_single.triplot(invisible_hull_list[:,0], invisible_hull_list[:,1], tri.simplices, transform = ax_single.transData,
                  color = 'black', zorder = 4, linewidth = 0.75)

# Colorbar
colorbar = plt.colorbar(invisible_points, shrink = 0.70, orientation = 'vertical')
if min_distance_tens < 0:
    colorbar.set_label("Enthalpy (meV/atom)", rotation=270, labelpad=20)
else:
    colorbar.set_label("Hull Distance (meV/atom)", rotation=270, labelpad = 20)

# Place suitable major ticks between five units
colorbar.locator = plticker.MultipleLocator(base=5)
tmax = roundup(raw_data.loc[:,'Hf-hull'].max())
tmin = math.floor(raw_data.loc[:,'Hf-hull'].min()/10)*10
if max_distance_tens == 60:
    ticklist = [0, 10, 20, 30, 40, 50, 60]
else:
    ticklist = list(np.linspace(tmin,tmax,6, dtype=int))
if tmin < 0:
    colorbar.locator = plticker.LinearLocator(6)
    #colorbar.formatter = plticker.LinearFormatter(6)
else:
    colorbar.locator = plticker.FixedLocator(ticklist)
    colorbar.formatter = plticker.FixedFormatter(ticklist)
#colorbar.minorticks_on()
colorbar.update_ticks()

out = args[1][:-3] + args[2]

fig.savefig(out, bbox_inches = 'tight', dpi = 300)
#fig.savefig("CMoW_ALS_AP_RR_dftrx+DFT_22.svg", bbox_inches = 'tight', dpi = 300)

