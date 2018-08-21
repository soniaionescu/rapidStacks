import MMCorePy
import numpy as np
from imread import imsave
from skimage import filters
import math
import os
from testImageProcessing import flatFieldCorrection, moveForFlatField, minimumIntensityProjection
from test20xConfiguration import Configuration 
import cv2
import time




###################### MIP and stack making #############################################

""" purpose: go down a z stack acquiring images
    inputs: topZ, bottomZ, mmc object, folder for if confuration.saveImages is true, flatField which should always be there except for the getting of z boundaries in test20xZEdgeDetection
    returns: the z stack as a 3d array, a list of z coordinates
    saves: z Stack if configuration.saveImages is true
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
        if flatField != None:
            singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
        finalStack[index,:,:] = singleLayer
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
        if configuration.saveImages == True:
            filename = folder + "/" + str(z) + ".tiff"
            singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
            imsave(filename, singleLayer)
    return finalStack, zList

""" purpose: go down a z stack acquiring images continuously
    inputs:  topZ, bottomZ, mmc object, folder for if confuration.saveImages is true, flatField which should always be there except for the getting of z boundaries in test20xZEdgeDetection
    returns: the z stack as a 3d array, a list of Z coordinates
    saves: nothing
"""
def acquireZStackContinuous(topZ, bottomZ, mmc, folder=None, flatField = None):
    ## get information we need
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    configuration = Configuration()
    zStep = configuration.zStep
    nSlices = int(math.ceil((topZ-bottomZ)/zStep))
    ## intialize
    finalStack = np.zeros((nSlices,imageHeight,imageWidth)).astype("uint16")
    ## make list of z values
    zList = np.empty([0])
    ## so that we are in the correct index
    index = nSlices - 1
    ## go from top to bottom, incrementing by amount specified in 
    velocity = mmc.getProperty("ZeissFocusAxis", "Velocity (micron/s)")
    mmc.startSequenceAcquisition(nSlices, 0, True)
    frame = 0
    exposureMs = configuration.exposureBrightField
    
    while (mmc.getRemainingImageCount() > 0 or mmc.isSequenceRunning()):
        mmc.setPosition(mmc.getPosition()-zStep)
        if (mmc.getRemainingImageCount() > 0):
            singleLayer = mmc.popNextImage()
            finalStack[index,:,:] = singleLayer
            frame = frame + 1
            index = index - 1
        else:
            mmc.sleep(min(0.5 * exposureMs, 20))
    mmc.stopSequenceAcquisition()
    mmc.stopSequenceAcquisition(mmc.getCameraDevice())
    print finalStack[:,:,0]
    imsave("oneLayer.tiff", finalStack[:,:,0])
    return finalStack, zList


""" purpose: make a MIP by taking the minimum value at each pixel through a whole Z stack
    inputs: the most positive z coordinate, the most negative z coordinate, a mmc object, a flatField array
    returns: the minimum intensity array of the z Stack
    saves: nothing
"""
def makeMIP(topZ, bottomZ, flatField, mmc, folder=None):
    ## load configuration
    configuration = Configuration()
    if configuration.saveImages == True:
        finalStack, zList = acquireZStack(topZ, bottomZ, mmc, folder, flatField)
    if configuration.saveImages == False:
        finalStack, zList = acquireZStack(topZ, bottomZ, mmc, None, flatField)
    mip = minimumIntensityProjection(finalStack, mmc)
    hvLayer = findFocusLayerVL(finalStack, zList, mmc)
    return mip, hvLayer

""" purpose: make a z stack and save each layer as a tiff with the file name as the z coordinate
    inputs: the folder to save the z stack into, the most positive z coordinate, the most negative z coordinate, a mmc object
    returns: a tuple: 3d numpy array where each layer is an image acquired with mmc.getImage(), a list of the z coordinates in the same order
    saves: z tiffs
"""
def zStackTiffs(folder, topZ, bottomZ, flatField,  mmc):
    ## make the file folder, if it doesn't already exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    ## go from top to bottom, incrementing by the z step specified in the configuration file and saving images
    finalStack, zList = acquireZStack(topZ, bottomZ, flatField, mmc, folder)
    return finalStack, zList

if __name__ == '__main__':
    #load microscope
    configuration = Configuration()
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    mmc.setExposure(configuration.exposureBrightField)
    acquireZStackContinuous(0, -100, mmc)


########################## focus finding ##############################################


""" purpose: uses sobel gradient to return z coordinate of the most focused layer of a Z stack
    input: a 3d numpy array of images, a list of the z coordinates
    returns: the z coordinate of the image with the highest sobel gradient
    saves: nothing
""" 
def findFocusFromSobelGradient(inputArray, zList, mmc):
    highestVariance = 0
    numberLayers = len(inputArray) 
    for layer in range(0, numberLayers):
        thisLayer = inputArray[layer,:,:]
        thisVariance = np.sum(filters.sobel(thisLayer))
        ## store the layer with the highest variance so far
        if thisVariance > highestVariance:
            highestVariance = thisVariance
            hvLayer = layer
    return zList[hvLayer]

""" purpose: uses variance of the laplacian to return z coordinate of the most focused layer of a Z stack
    input: a 3d numpy array of images, a list of the z coordinates
    returns: the z coordinate of the image with the highest variance of the laplacian
    saves: nothing
"""
def findFocusLayerVL(inputArray, zList, mmc):
    highestVariance = 0
    numberLayers = len(inputArray) 
    ## iterate through each layer finding the variance of the laplacian
    for layer in range(0, numberLayers):
        thisLayer = inputArray[layer,:,:]
        thisVariance = cv2.cv2.Laplacian(thisLayer, cv2.cv2.CV_64F).var()
        ## store the layer with the highest variance so far
        if thisVariance > highestVariance:
            highestVariance = thisVariance
            hvLayer = layer
    return zList[hvLayer]  

################################ useless things ###########################################  

""" purpose: make a MIP by keeping a running minimum array and comparing that to the currentSlice
    inputs: the most positive z coordinate, the most negative z coordinate, a mmc object, a flatField array
    returns: the minimum intensity array of the z Stack
    saves: nothing
"""
"""
def runningMIP(topZ, bottomZ, flatField, mmc):
    nSlices = int(math.ceil((topZ-bottomZ))) ## if we want to slice every 50 microns
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    finalStack = np.zeros((nSlices,imageHeight,imageWidth))
    print finalStack
    ## make list of z values
    zList = np.empty([0])
    ## so that we are in the correct index
    index = nSlices - 1 
    print "index", index
    ## initialize MIP things
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    ## make list of X, Y coordinates
    coordinateList = []
    totalNumberPixels = np.arange(1, imageHeight*imageWidth)
    x_coords = [math.floor(pixel/imageWidth) for pixel in totalNumberPixels]
    y_coords = [pixel % imageWidth for pixel in totalNumberPixels]
    coordinateList = list(zip(x_coords, y_coords))
    print "coordList made"
    #p = Pool(processes = 8)
    #p.map(coord(inputArray, mip), coordinateList, 100)
    ## go from top to bottom, incrementing by 50 microns
    print "acquiring stack and finding runningMIP"
    start_time = time.time()
    for z in np.arange(topZ, bottomZ, -1): 
        mmc.setPosition(z)
        mmc.snapImage()            
        singleLayer = mmc.getImage()
        singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
        print singleLayer
        print singleLayer.dtype
        if z == topZ:
            runningMIP = singleLayer
        else:
            twoLayerMIP(runningMIP, singleLayer, coordinateList)
        print index
        finalStack[index,:,:] = singleLayer
        print finalStack
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
    print " %s seconds to find acquire and make MIP" % (time.time() - start_time)
    print "calculating MIP"
    start_time = time.time()
    hvLayer = findFocusFromSobelGradient(finalStack, zList, mmc)
    print " %s seconds to find focus" % (time.time() - start_time)
    imsave("731RunningMIP1.tiff", runningMIP)
    return runningMIP, hvLayer
    

def twoLayerMIP(runningMIP, nextSlice, coordinateList):
    for i in range(0, len(coordinateList)):
        findMinimum(coordinateList[i], runningMIP, nextSlice)
    
def findMinimum(xy, runningMIP, nextSlice):
    x =  xy[0]
    y = xy[1]
    minimumElement = np.minimum(runningMIP[x,y], nextSlice[x,y])
    runningMIP[x, y] = int(minimumElement) """
