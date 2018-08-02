import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.misc import imsave
from skimage import filters
import math
import os
from testImageProcessing import flatFieldCorrection, moveForFlatField, minimumIntensityProjection
import cv2
import time


if __name__ == '__main__':
    #load microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

###################### MIP and stack making #############################################

""" purpose: make a MIP by taking the minimum value at each pixel through a whole Z stack
    inputs: the most positive z coordinate, the most negative z coordinate, a mmc object, a flatField array
    returns: the minimum intensity array of the z Stack
    saves: nothing
"""
def makeMIP(topZ, bottomZ, flatField,  mmc):
    nSlices = int(math.ceil((topZ-bottomZ))) ## if we want to slice every 50 microns
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    finalStack = np.zeros((nSlices,imageHeight,imageWidth))
    ## make list of z values
    zList = np.empty([0])
    ## so that we are in the correct index
    index = nSlices - 1 
    ## go from top to bottom, incrementing by 50 microns
    start_time = time.time()
    
    for z in np.arange(topZ, bottomZ, -1): 
        mmc.setPosition(z)
        mmc.snapImage()
        singleLayer = mmc.getImage()
        singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
        finalStack[index,:,:] = singleLayer
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
    print " %s seconds for acquisition" % (time.time() - start_time)
    start_time = time.time()
    mip = minimumIntensityProjection(finalStack, mmc)
    print " %s seconds to calculate MIP" % (time.time() - start_time)
    start_time = time.time()
    hvLayer = findFocusFromSobelGradient(finalStack, zList, mmc)
    print " %s seconds to calculate focus layer" % (time.time() - start_time)
    return mip, hvLayer

""" purpose: make a z stack and save each layer as a tiff with the file name as the z coordinate
    inputs: the folder to save the z stack into, the most positive z coordinate, the most negative z coordinate, a mmc object
    returns: a tuple: 3d numpy array where each layer is an image acquired with mmc.getImage(), a list of the z coordinates in the same order
    saves: z tiffs
"""
def zStackTiffs(folder, topZ, bottomZ, flatField,  mmc):
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
        singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
        imsave(filename, singleLayer)

    return finalStack, zList

""" purpose: make a z stack but don't save the images
    inputs: the most positive z coordinate, the most negative z coordinate, a mmc object
    returns: a 3d numpy array where each layer represents an image acquired using mmc.getImage()
    saves: nothing
"""
def makeZStack(topZ, bottomZ, mmc):
    nSlices = int(math.ceil((topZ-bottomZ))) ## if we want to slice every 50 microns
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    finalStack = np.zeros((nSlices,imageHeight,imageWidth))
    ## make list of z values
    zList = np.empty([0])
    ## so that we are in the correct index
    index = nSlices - 1 
    ## go from top to bottom, incrementing by 50 microns
    for z in np.arange(topZ, bottomZ, -1): 
        mmc.setPosition(z)
        mmc.snapImage()
        singleLayer = mmc.getImage()
        finalStack[index,:,:] = singleLayer
        index = index-1
        ## add the z layer to the list of z coordinates
        zList = np.append(z, zList)
    return finalStack, zList



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
        #sobelx = cv2.cv2.Sobel(thisLayer,cv2.cv2.CV_64F,1,0,ksize=5)
        #sobely = cv2.cv2.Sobel(thisLayer,cv2.cv2.CV_64F,0,1,ksize=5)
        #abs_sobel_x = cv2.cv2.convertScaleAbs(sobelx) # converting back to uint8
        #abs_sobel_y = cv2.cv2.convertScaleAbs(sobely)
        #dst = cv2.cv2.addWeighted(abs_sobel_x,0.5,abs_sobel_y,0.5,0)
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
