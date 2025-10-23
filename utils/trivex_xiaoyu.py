#!/usr/bin/env python
#
# Plot My Tenary Convex Hull
# version 2.3 
# Feb-19th-2020 
#
# Copyright (C) 2018 Xiaoyu Wang <xwang224@buffalo.edu>
#
# Everyone is permitted to copy and distribute or modified
# copies of this file, and changing it is allowed as long
# as the name is changed.
#
# XIAOYU'S YOU HAPPY JIU OK TO PUBLIC LICENSE
# TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
# 0. You just HAPPILY DO WHATEVER YOU WANT TO.
#

# Change log
# version 2 is a complete change to this script: it accepts the components of the elements as the imput
# ver 2.2 add a new function to visualize the 3d hull
# ver 2.3 calculate vertical distance to the hull

""" 
===============================================================
example of new version input files with default parameters
===============================================================
pressure 0                  # pressure is the keyword, unit of pressure is in GPa
color spring                # color theme of the diagram. 
                            # more colors can be found at https://matplotlib.org/examples/color/colormaps_reference.html
file output.eps             # saving fig to this format. png, pdf, ps, eps and svg are commonly supported. if this line is missing, the default is DON'T save fig and the fig will be shown on the screen
contour 15                  # number of contour lines
animate                     # generate animation (not implemented)
3d                          # enable 3d plot
silent                      # no verbal output
                            # components must be at the end of the input file
component                   # component/fractional(not implemented)
Ca1 S1  H2   meV/atom       # element top, element bottom left, element bottom right, unit of formation enthalpy
3   3   5    -72.631        # X(A), X(B), X(C), Enthalpy
4   4   1    -88.923        # three vertices of 0 are NOT necessary
7   7   4    -15.376

===============================================================

"""
import sys, os, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import tri
from scipy.spatial import ConvexHull
from matplotlib import cm
from mpl_toolkits import mplot3d

class coffee(object):
    def __init__(self, path):
        self.silent = False
        self.pressure = ''
        self.color = 'spring'
        self.fig_name = False 
        self.contour = 12
        self.animate = False
        self.dia3d = False
        self.unit = 'eV/atom'
        self.elements = []
        self.data = []
        self.ratio = []
        self.pos = []
        self.read(path)
        self.hull = ConvexHull(self.pos)

    def hulldistance(self):
        v = self.hull.vertices
        s = self.hull.simplices
        p = self.hull.points
        distance = []
        for i in p:
            xp, yp = i[0:2]
            for j in s:
                vec = p[j]
                x1, y1 = vec[0][0:2]
                x2, y2 = vec[1][0:2]
                x3, y3 = vec[2][0:2]
                d1  = ((x2 - x1)**2 + (y2 - y1)**2)**.5
                d2  = ((x3 - x1)**2 + (y3 - y1)**2)**.5
                d3  = ((x3 - x2)**2 + (y3 - y2)**2)**.5
                dp1 = ((xp - x1)**2 + (yp - y1)**2)**.5
                dp2 = ((xp - x2)**2 + (yp - y2)**2)**.5
                dp3 = ((xp - x3)**2 + (yp - y3)**2)**.5
                dd1 = abs(d1 - dp1 - dp2)
                dd2 = abs(d2 - dp1 - dp3)
                dd3 = abs(d3 - dp3 - dp2)
                c1 = (x2 - x1) * (yp - y1) - (y2 - y1) * (xp - x1)
                c2 = (x3 - x2) * (yp - y2) - (y3 - y2) * (xp - x2)
                c3 = (x1 - x3) * (yp - y3) - (y1 - y3) * (xp - x3)
                # calculate the plane
                v1 = vec[2] - vec[0]
                v2 = vec[1] - vec[0]
                cp = np.cross(v1, v2)
                a, b, c = cp
                d = np.dot(cp, vec[2])
                # skip the cover
                if (vec[0][2] >= 0 and vec[1][2] >= 0 and vec[2][2] >= 0):
                    continue
                # check if plane is vertical
                elif c == 0:
                    continue
                # check if point is vertice
                elif d1 == 0 or d2 == 0 or d3 == 0:
                    break
                # check if point on edge
                elif dd1 < 10.**-7 or dd2 < 10.**-7 or dd3 < 10.**-7:
                    break
                # check if point in triangle
                elif (c1 < 0 and c2 < 0 and c3 < 0) or (c1 > 0 and c2 > 0 and c3 > 0):
                    break
            else:
                print("Found point not inside the convex hull!!!")
                sys.exit(-1)

            value = i[2] - (d - a * i[0] - b * i[1]) / c
            if abs(value) < 10**-5:
                distance.append(0.)
            else:
                distance.append(value)
        return distance
                


    def diagram3d(self):
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        cmap = cm.get_cmap(name=self.color, lut=None)

        vertices = self.pos[self.hull.vertices].T
        others = self.pos[[i for i in range(len(self.pos)) if i not in self.hull.vertices]].T

        levels = np.arange(min(vertices[2]), .0, abs(min(vertices[2]))/20.0)
        triang = tri.Triangulation(self.pos.T[0], self.pos.T[1], triangles=self.hull.simplices)
        ax.tricontour(triang, self.data.T[3], levels=levels, cmap=cmap, linewidths=0.5)
        ax.plot(vertices[0], vertices[1], vertices[2], "bo", markersize=1)
        ax.plot(others[0], others[1], others[2], "ro", markersize=1)

        for s in self.hull.simplices:
            s = np.append(s, s[0])  
            ax.plot(self.pos[s, 0], self.pos[s, 1], self.pos[s, 2], "b-", linewidth=0.5)
        ax.axis('off')

        tags = [self.elements[i][0]+('_{'+self.elements[i][1]+'}')*(self.elements[i][1]!='1') for i in range(3)]

        ax.text(0.5, 0.86602540378, 0.05, "$\mathrm{%s}$" % tags[0], fontsize=8, ha="center", va="bottom", size=10)
        ax.text(0.0, 0.0, 0.05, "$\mathrm{%s}$" % tags[1], fontsize=8, ha="center", va="bottom", size=10)
        ax.text(1, 0., 0.05, "$\mathrm{%s}$" % tags[2], fontsize=8, ha="center", va="bottom", size=10)

        for i in self.hull.vertices[:-3]:
            tag = ''.join([int(self.component[i][j]!=0.)*(self.elements[j][0]+int(self.component[i][j]!=1.)*('_{'+str(int(self.component[i][j]))+'}')) for j in range(3)])
            ax.text(self.pos.T[0][i]+0.01, self.pos.T[1][i]+0.01, self.pos.T[2][i], "$\mathrm{%s}$" % tag, fontsize=8, size=10)

        plt.show()

    def diagram(self):
        distance = self.hulldistance()
        metas = [count for count,i in enumerate(distance) if 0 < i < 26]
        metastable = self.pos[metas].T
        vertices = self.pos[self.hull.vertices].T
        
        triang = tri.Triangulation(self.pos.T[0], self.pos.T[1], triangles=self.hull.simplices)

        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.triplot(triang, lw=1.5, color='k')

        levels = np.arange(min(vertices[2]), .0, abs(min(vertices[2]))/100.0)
        cmap = cm.get_cmap(name=self.color, lut=None)
        cs = ax.tricontourf(triang, self.data.T[3], levels=levels, cmap=cmap)
        ax.tricontour(triang, self.data.T[3], self.contour, linewidths=0.5, colors='k')
        ax.scatter(vertices[0], vertices[1], marker='o', c='k', s=50, zorder=10)
        ax.scatter(metastable[0], metastable[1], marker='o', c='w', s=50, zorder=10)
        ax.axis('off')

        tags = [self.elements[i][0]+('_{'+self.elements[i][1]+'}')*(self.elements[i][1]!='1') for i in range(3)]
        ax.text(0.5, 0.88602540378, "$\mathrm{%s}$" % tags[0], fontsize=15, ha="center", va="bottom", size=20)
        ax.text(0.0, -0.02, "$\mathrm{%s}$" % tags[1], fontsize=15, ha="center", va="top", size=20)
        ax.text(1, -0.02, "$\mathrm{%s}$" % tags[2], fontsize=15, ha="center", va="top", size=20)

        for i in self.hull.vertices[:-3]:
            tag = ''.join([int(self.component[i][j]!=0.)*(self.elements[j][0]+int(self.component[i][j]!=1.)*('_{'+str(int(self.component[i][j]))+'}')) for j in range(3)])
            ax.text(self.pos.T[0][i]+0.01, self.pos.T[1][i]+0.01, "$\mathrm{%s}$" % tag, fontsize=12, size=12)
        for i in metas:
            tag = ''.join([int(self.component[i][j]!=0.)*(self.elements[j][0]+int(self.component[i][j]!=1.)*('_{'+str(int(self.component[i][j]))+'}')) for j in range(3)])
            ax.text(self.pos.T[0][i]+0.01, self.pos.T[1][i]+0.01, "$\mathrm{%s}$" % tag, fontsize=12, size=12)

        if self.pressure:
            ax.text(0.80, 0.75, 'P='+self.pressure+' GPa', fontsize=15, ha='center', va='center', size=15)

        label_cb = 'Enthalpy of Formation, $\Delta$H$_F$ %s' % self.unit
        cax = fig.add_axes([0.85, 0.30, 0.03, 0.60])
        cb = plt.colorbar(cs, cax=cax, format='%.1f')
        cb.set_label(label_cb, rotation=270, labelpad=15)

        if self.fig_name:
              plt.savefig(fname=self.fig_name, edgecolor='k', facecolor='white') #quality=95 used to be in there, now deprecated
              print("diagram is saved to %s" % self.fig_name)
        else: plt.show()

    def read(self, path):
        if not os.path.isfile(path):
            print(">>> Error reading file %s: such file doesn't exist <<<" % path)
            sys.exit(-1)
    
        with open(path, 'r') as fid:
            p = fid.readline().split()
            while len(p):
                if p[0].lower() == 'pressure': self.pressure = p[1]
                elif p[0].lower() == 'color': self.color = p[1]
                elif p[0].lower() == 'file': self.fig_name = p[1]
                elif p[0].lower() == 'contour': self.contour = int(p[1])
                elif p[0].lower() == '3d': self.dia3d = True
                elif p[0].lower() == 'animation': self.animate = True 
                elif p[0].lower() == 'silent': self.silent = True
                elif p[0].lower() == 'component': 
                    tags = fid.readline().split()
                    if len(tags) >= 4:
                        self.unit = tags[3]
                    self.elements = [re.split('(\d+)', i)[:2] for i in tags[:3]]
                    self.data = np.array([[float(y) for y in x.split()[:5]] for x in fid.readlines()+["1. 0. 0. 0. 0.", "0. 1. 0. 0. 0.", "0. 0. 1. 0. 0."] if len(x) > 3])
                    self.component = [[i[j]*float(self.elements[j][1]) for j in range(3)] for i in self.data]
                    #self.ratio = [[i[j]*float(self.elements[j][1])/(i[0]*float(self.elements[0][1])+i[1]*float(self.elements[1][1])+i[2]*float(self.elements[2][1])) for j in range(3)] for i in self.data]
                    self.ratio = [np.array(i[:3])/sum(i[:3]) for i in self.data]
                    self.pos = np.array([[self.ratio[i][2]+0.5*self.ratio[i][0], self.ratio[i][0]*0.86602540, self.data[i][3]] for i in range(len(self.ratio))])
                    self.indices = self.data.T[4]
                    break
                p = fid.readline().split()

    def display(self):
        distance = self.hulldistance()
        print("%i data points were generated:" % len(self.data))
        print("%i of them are on the hull:" % len(self.hull.vertices))
        print("%6s %6s %9s %3s %3s %3s %9s %9s" % ('X', 'Y', 'Hf', self.elements[0][0], self.elements[1][0], self.elements[2][0], 'Hf-hull', 'CFG-index'))
        for i in range(len(self.data)):
            print("%6.3f %6.3f %9.3f %3i %3i %3i %9.3f %6i" % (self.pos[i][0], self.pos[i][1], self.pos[i][2], self.component[i][0], self.component[i][1], self.component[i][2], distance[i], self.indices[i]))
        if any([x[2]>0 for x in self.pos]):
            print("Warning: I see at least one positive energy value among your input. This will create simplices above 0 and makes that data cheatingly on the hull. I hope you know what you are doing.")


if __name__ == '__main__':
    for f in sys.argv[1::]:
        a = coffee(f)
        if not a.silent: a.display()
        if a.dia3d: 
            a.diagram3d()
        else:
            a.diagram()
   
