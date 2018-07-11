import numpy as np
import MMCorePy

import numpy as np
import cv2 
import matplotlib.pyplot as plt
import os
from PIL import Image
import shutil
import glob

## test for array indexing in doWeEnd
array = np.array([[1,15],[3,12]])
maxX = array[:,0].max()
maxY = array[:,1].max()
minX = array[:,0].min()
minY = array[:,1].min()
initialXY = array[0,:]
currentXY = array[array.shape[1]-1,:]
movementList = np.array(['right', 'left', 'right', 'left'])
movementList = np.append(movementList, 'left')
movement = np.repeat(['up'], 5)
rangeOfFocus = np.empty([0]) 
array = np.array([1])
rangeOfFocus = np.concatenate((rangeOfFocus, array), axis = 0)
arraycv = np.array([[1,2],[3,4]])
cvl1 = np.zeros([2,2])
cvl2 = np.zeros([2,2])
threeLayer = np.empty([3,2,2])
threeLayer[0,:,:] = arraycv
threeLayer[1,:,:] = cvl1
threeLayer[2,:,:] = cvl2
coordinatesList = np.array([[1,2]])
coordinatesList = np.concatenate((coordinatesList, np.array([[3, 4]])), axis=0)
coordinatesList = np.concatenate((coordinatesList, np.array([[5, 6]])), axis=0)
coordinatesList = np.concatenate((coordinatesList, np.array([[7, 8]])), axis=0)
initialXY = coordinatesList[0,:]
currentXY = coordinatesList[coordinatesList.shape[0]-1,:]
