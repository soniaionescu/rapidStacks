import MMCorePy
from test20xFeatureDetection import loadFiles, downsampleImage
import matplotlib.pyplot as plt
from skimage import filters, morphology
import numpy as np
from scipy.signal import argrelextrema
import cv2
from test20xStackToTiff import acquireZStack
from test20xConfiguration import Configuration


if __name__ == "__main__":
    # load microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")
    mmc.setProperty('IDS uEye', 'Exposure', .5197)
    mmc.setROI(350, 0, 3454, 2174)
    ## set z focus limits that are generally the extremes of focus
    extremeUpperZ = 200
    extremeLowerZ = -150
    downSampleRate = 6 # Amount to downsample incoming image
    filterBlur = 3 # Blur to apply to Sobel sum vector (units of frames)
    ## return lower and upperZ
    lowerZ, upperZ = zLimits(mmc) 
    print lowerZ, upperZ

######################## Rusty's code adapted to use a zstack instead of images #####################

""" purpose: find the upper and lower bounds of the sample by using sobel gradient to calculate focus (mean didn't work)
    inputs: a mmc object, an extreme upperZ, extreme lower Z
    returns: upper and lower z coordinate and the highestFocusCoordinate as a 3-tuple
    saves: nothing
"""

def zLimits(mmc):
    ## get relevant values
    configuration = Configuration()
    extremeUpperZ = configuration.extremeUpperZ
    extremeLowerZ = configuration.extremeLowerZ
    downSampleRate = configuration.downSampleRate
    filterBlur = configuration.filterBlur
    ## make a from the very high z value to the very low z faluye
    zStack, zList = acquireZStack(extremeUpperZ, extremeLowerZ, mmc)
    ## downsample images
    binImg = downsampleImage(zStack, downSampleRate)

    varVect = varFilterStack(binImg)
    
    startEnd, conservativeStartEnd = processVarianceVector(varVect, filterBlur)
    
    showSelectedPlanes(varVect, startEnd, conservativeStartEnd)

    return startEnd[0], startEnd[1]

########################## Rusty's code ###############################################

"""
Identify start and end of specimen in a Z stack of images.
Downsample images in stack, then calculate sum intensity of edges in each image.
Smooth this vector over z (frames) axis, scale to 0->1 and threshold at 0.5.
Start and end frames of stack are first local min to left and right of thresholded region.

Requires findSomaInStack methods, skimate, nunpy, scipy, and matplotlib.

Created on Sun Jul 29 13:10:44 2018

@author: rustyn

"""


def varFilterStack(binImg):
    varVect = np.zeros((binImg.shape[2], 1))
    for k in range(binImg.shape[2]):
        
        imgHere = (binImg[:,:,k] - np.amin(binImg[:,:,k]))/(np.amax(binImg[:,:,k]) - np.amin(binImg[:,:,k]))
        
    #    varVect[k] = np.sum(filters.rank.entropy(imgHere, morphology.disk(entropyFilterSize)))
        varVect[k] = np.sum(filters.sobel(imgHere))
    #    varVect[k] = np.sum(filters.rank.equalize(imgHere, morphology.disk(entropyFilterSize)))
    
    return varVect

def processVarianceVector(varVect, filterBlur):

    filtVect = filters.gaussian(varVect, sigma=filterBlur)
    scaleVect = (filtVect - np.amin(filtVect)) / (np.amax(filtVect) - np.amin(filtVect))
    
    # Choose start and end for slice
    # Defined as first and last point that are above threshold of 0.5 in scaled blurred edge-transformed image
    
    varThresh = scaleVect > 0.5
    varClose = morphology.binary_closing(varThresh, morphology.rectangle(3, 1))
    
    # May be a good idea to confirm that there is a single large contiguous 'true' block here
    # If this is split or there are multiple blocks above threshold the next steps may return spurious values
    
    startEnd = [np.amin(np.where(varClose)[0]), np.amax(np.where(varClose)[0])]
    # Find first minimum to left of start, first to right of end
    localMin = argrelextrema(scaleVect, np.less)
    
    conservativeStartEnd = [localMin[0][(np.amax(np.where(((localMin[0] - startEnd[0]) < 0))))],
                            localMin[0][(np.amin(np.where(((localMin[0] - startEnd[1]) > 0))))]]

    return startEnd, conservativeStartEnd

def showSelectedPlanes(varVect, startEnd, conservativeStartEnd):
    
    f = plt.figure()
    ax = f.add_subplot(111)
    ax.plot(varVect)
    ax.plot(startEnd[0], varVect[startEnd[0]], 'kx')
    ax.plot(startEnd[1], varVect[startEnd[1]], 'kx')
    ax.plot([conservativeStartEnd[0], conservativeStartEnd[0]], 
                 [np.amin(varVect), np.amax(varVect)], 'k--')
    ax.plot([conservativeStartEnd[1], conservativeStartEnd[1]], 
                 [np.amin(varVect), np.amax(varVect)], 'k--')
    
    plt.xlabel('Frame')
    plt.ylabel('Sum Sobel response')
    plt.annotate('Start frame = ' + str(conservativeStartEnd[0]), 
                xy = (conservativeStartEnd[0]+5, 0.95*np.amax(varVect)))
    plt.annotate('End frame = ' + str(conservativeStartEnd[1]), 
                xy = (conservativeStartEnd[1]+5,  0.95*np.amax(varVect)))
    
    plt.show()


def mainFindZLimits(baseFolder, downSampleRate, filterBlur):
    
    img = loadFiles(baseFolder)
    binImg = downsampleImage(img, downSampleRate)
    
    varVect = varFilterStack(binImg)
    
    startEnd, conservativeStartEnd = processVarianceVector(varVect, filterBlur)
    
    showSelectedPlanes(varVect, startEnd, conservativeStartEnd)
    

############################## useless code ############################################


""" purpose: find the upper and lower bounds of the sample by using sobel gradient to calculate focus (mean didn't work)
    inputs: a mmc object, an extreme upperZ, extreme lower Z
    returns: upper and lower z coordinate and the highestFocusCoordinate as a 3-tuple
    saves: nothing
"""
"""def zLimits(extremeUpperZ, extremeLowerZ, mmc):
    ## initialize the list of sobel gradients
    intensityList = []
    ## make a from the very high z value to the very low z faluye
    zStack, zList = makeZStack(extremeUpperZ, extremeLowerZ, mmc)
    ## find how many z layers there are in zStack
    numberLayers = len(zStack)
    ## iterate through each layer finding the variance of the laplacian
    for layer in range(0, numberLayers):
        ## look at layer and compute intensity
        thisLayer = zStack[layer,:,:]
        sobelx = cv2.cv2.Sobel(thisLayer,cv2.cv2.CV_64F,1,0,ksize=5)
        sobely = cv2.cv2.Sobel(thisLayer,cv2.cv2.CV_64F,0,1,ksize=5)
        abs_sobel_x = cv2.cv2.convertScaleAbs(sobelx) # converting back to uint8
        abs_sobel_y = cv2.cv2.convertScaleAbs(sobely)
        dst = cv2.cv2.addWeighted(abs_sobel_x,0.5,abs_sobel_y,0.5,0)
        thisVariance = dst.mean()
        ## add the intensity to a list
        intensityList.append(thisVariance)
    print zList
    print intensityList
    highestFocusZ = zList[np.amax(intensityList)]
    belowHighestFocus = zList[0:np.amax(intensityList):1]
    aboveHighestFocus = zList[np.amax(intensityList):len(zList):1]
    lowestZ = zList[np.amin(belowHighestFocus)]
    highestZ = zList[np.amin(aboveHighestFocus) + len(belowHighestFocus)]
    return lowestZ, highestZ """