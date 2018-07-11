import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from tifffile import imsave
import math
import os
##Goal: get a folder full of TIFFs which each represent one layer of a z stack
##Goal: Get a TIFF file which is a z stack at 20x magnification

#load microscope
#mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

##a function that creates a folder of tiffs
def zStackTiffs(folder, topZ, bottomZ, mmc):
    ## initialize 3d array
    nSlices = int(math.ceil((topZ-bottomZ)/.5)) ## if we want to slice every 50 microns
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    finalStack = np.zeros((nSlices,imageHeight,imageWidth)) 
    index = nSlices - 1 ## so that we are in the correct index
    ## make list of z values
    zList = np.empty([0])
    ## make the file folder, if it doesn't already exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    ## go from top to bottom, incrementing by 50 microns
    for z in np.arange(topZ, bottomZ, -.5): 
        ## create file name
        filename = folder + "/" + str(z) + ".tiff"
        ## move and take photo
        mmc.setPosition(z)
        mmc.snapImage()
        singleLayer = mmc.getImage()
        ## add to the z stack
        finalStack[index,:,:] = singleLayer
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
        ## save tiff at the filename
        singleLayer[singleLayer >= 255] = 255
        singleLayer = Image.fromarray(singleLayer.astype('uint8'))
        singleLayer.save(filename)

    return finalStack, zList

##a function that returns a 3d array
def makeZStack(topZ, bottomZ, mmc):
    nSlices = int(math.ceil((topZ-bottomZ)/.5)) ## if we want to slice every 50 microns
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    finalStack = np.zeros((nSlices,imageHeight,imageWidth)) 
    index = nSlices - 1 ## so that we are in the correct index
    ## go from top to bottom, incrementing by 50 microns
    for z in np.arange(topZ, bottomZ, -.5): 
        mmc.setPosition(z)
        mmc.snapImage()
        singleLayer = mmc.getImage()
        finalStack[index,:,:] = singleLayer
        index = index-1
    return finalStack 
