import MMCorePy
import numpy as np
from PIL import Image
from scipy import ndimage
import math
import cv2
import os
from test20xStackToTiff import makeZStack, zStackTiffs
import shutil

## Goal: with a z stack, be able to find the most focused plane; return z index.

## load microscope
#mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

##uses variance of the laplacian to return index of the most focused layer of a Z stack
def findFocusLayerVL(topZ, bottomZ, mmc):
    
    ## initialize variance to be 0 which is as out of focus as possible
    highestVariance = 0
    ## initialize layer with highest variance
    hvLayer = 0
    ## make a z stack
    zStack = makeZStack(topZ, bottomZ, mmc)
    ## find how many z layers there are in zStack
    numberLayers = len(zStack)
    ## iterate through each layer finding the variance of the laplacian
    for layer in range(0, numberLayers):
        thisLayer = zStack[layer,:,:]
        thisVariance = cv2.cv2.Laplacian(thisLayer, cv2.cv2.CV_64F).var()
        ## store the layer with the highest variance so far
        if thisVariance > highestVariance:
            highestVariance = thisVariance
            hvLayer = layer
    return hvLayer  

## call zStackTiffs to get pictures and return the z coordinate of the picture with the highest focus
def findFocusLayerVLPictureCreation(folder, topZ, bottomZ, mmc):
    
    ## initialize variance to be 0 which is as out of focus as possible
    highestVariance = 0
    ## initialize layer with highest variance
    hvLayer = 0
    ## get a folder of z stack photos, assign the return values to a zstack and a list of the z coordinates associated with each layer
    zStack, zList = zStackTiffs(folder, topZ, bottomZ, mmc)
    ## find how many pictures there are in the folder
    numberLayers = len(zStack)
    ## iterate through each layer finding the variance of the laplacian
    for layer in range(0, numberLayers):
        thisLayer = zStack[layer,:,:]
        thisVariance = cv2.cv2.Laplacian(thisLayer, cv2.cv2.CV_64F).var()
        ## store the layer with the highest variance so far
        if thisVariance > highestVariance:
            highestVariance = thisVariance
            hvLayer = layer
    ## find the photo that is associated with hvLayer, that is the photo that is most in focus. return the name of that photo, which is the z position
    fileWHighestFocus = zList[hvLayer-1]
    return fileWHighestFocus


    
## go through each folder of z stacks and find the most focused of each folder, and create a separate folder with only these in the same x/y/z.tiff format
def createFocusSpline(slideName):
    ## create a separate folder
    if not os.path.exists(slideName):
        os.makedirs(slideName)
    ## go through each x y and find the highest focus and then copy the highest focus one in the same file into the slideName file
    for path, subdirs, files in os.walk("OverviewTest"):
        ## go through each subdirectory
        for subdir in subdirs:
            ## only go through subdirectories with three layers
            if len(os.path.relpath(subdir)) is not 8:
            ## reinitialize each time
                hvLayer = 0
                highestVariance = 0
                ## create full path name so that we can pass it in correctly
                subdirPath = os.path.join(path, subdir)
                ## go through each file
                for path2, subdirs2, files2, in os.walk(subdirPath):
                    ## read the image and compute the variance
                    for fileName in files2:
                        filePath = subdirPath + "/" + fileName
                        img = cv2.cv2.imread(filePath, 0)
                        Image.fromarray(img).show()
                        thisVariance = cv2.cv2.Laplacian(img, cv2.cv2.CV_64F).var()
                        ## update highest variance and file
                        if thisVariance > highestVariance:
                            highestVariance = thisVariance
                            hvLayer = filePath
                    ## copy everything in the file path of the highest variance to the slideName folder
                    makePath = slideName + "/" + subdirPath
                    os.makedirs(makePath)
                    shutil.copy(hvLayer, makePath)
                
                
                
            

#findFocusLayerVLWithPictures(r"OverviewTest\-659.0925\28505.63", 10.22, -30)

## function to get normalized variance
"""def normalizedVariance(twoDArray):
    mean = np.mean(twoDArray)
    totalVar = 0
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    for j in range(0, imageHeight):
        for i in range(0, imageWidth):
            pixelValue = twoDArray[i,j]
            t = (pixelValue-mean)*(pixelValue-mean)
            totalVar = totalVar + t
    return totalVar
    
def findFocusNV():
    ## initialize normalized variance to be 0 which is as out of focus as possible
    highestVariance = 0

    ## intialize layer with highest variance
    hvLayer = 0

    ## get z stack as array
    zStack = makeZStack()

    ## find how many z layers there are in zStack
    numberLayers = len(zStack)

    ## iterate through each layer applying edge filtering and then finding the normalized variance
    for layer in range(0, numberLayers):
        thisLayer = zStack[layer,:,:]
        thisVariance = normalizedVariance(thisLayer)
        if thisVariance > highestVariance:
            highestVariance = thisVariance
            hvLayer = layer ## store the layer with the highest variance so far
    return hvLayer ## return which layer has the highest variance


    
def findFocusRangeVL(threshold):
    ## range seems to be between 12400-12700, with most falling around 12600

    ## initialize list of layers with acceptable variances
    rangeOfFocus = np.empty([0]) 
    ## make a z stack
    zStack = makeZStack()
    ## find how many z layers there are in zStack
    numberLayers = len(zStack)
    print numberLayers
    ## iterate through each layer finding the variance of the laplacian
    for layer in range(0, numberLayers):
        thisLayer = zStack[layer,:,:]
        thisVariance = cv2.cv2.Laplacian(thisLayer, cv2.cv2.CV_64F).var()
        ## store the layer with the highest variance so far
        if thisVariance > threshold:
            rangeOfFocus = np.concatenate((rangeOfFocus, np.array([layer])), axis = 0)
            print layer
            print thisVariance
    ## get minimum and maximum indeces of in focus layers
    minLayer = np.amin(rangeOfFocus)
    maxLayer = np.amax(rangeOfFocus)
    rangeMinMax = np.array([minLayer, maxLayer])
    print rangeMinMax
    return rangeMinMax """


#def findFocusSpline():