# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 17:52:52 2018

@author: rustyn
"""

import numpy as np
import matplotlib.pyplot as plt

stepSize = 3.115 # Step size in microns
nPlanes = 50 # n planes to sample
A = 550 # Calibrated amplitude of path A
B = 652 # Calibrated amplitude of path B
angleOffset = 2*np.pi/2.5

angleStep = 2*np.pi/(2./stepSize)

angleStops = np.arange(angleOffset, (angleStep*nPlanes)+angleOffset, angleStep) 

aStops = np.round(A*np.cos(angleStops))
bStops = np.round(B*np.sin(angleStops))

plt.cla()
plt.plot(aStops, bStops, 'b.-')
plt.show()

