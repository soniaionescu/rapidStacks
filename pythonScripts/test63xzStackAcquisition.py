import numpy as np
from test63xConfiguration import Configuration
from imread import imsave
from testImageProcessing import flatFieldCorrection
import math
""" purpose: go down a z stack acquiring images
    inputs: nothing
    returns: the z stack as a 3d array
    saves: tiffs of z stack with overlap of 10%
    note: have flatField = none because I don't want to use flatfield correction for the initial getting of z boundaries in test20xZEdgeDetection
"""
def acquireZStack(topZ, bottomZ, mmc, folder=None, flatField = None):
    ## get information we need
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    configuration = Configuration()
    zStep = configuration.zStep
    nSlices = int(math.ceil((topZ-bottomZ)/zStep))
    ## intialize
    finalStack = np.zeros((nSlices,imageHeight,imageWidth))
    ## make list of z values
    zList = np.empty([0])
    ## so that we are in the correct index
    index = nSlices - 1 
    ## go from top to bottom, incrementing by amount specified in 
    for z in np.arange(topZ, bottomZ, -zStep): 
        mmc.setPosition(z)
        mmc.snapImage()
        singleLayer = mmc.getImage()
        singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
        finalStack[index,:,:] = singleLayer
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
        filename = folder + "/" + str(z) + ".tiff"
        imsave(filename, singleLayer)
    return finalStack, zList
