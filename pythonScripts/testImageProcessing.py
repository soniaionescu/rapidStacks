import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import scipy
from scipy.misc import imsave
from test20xEdgeDetection import whichCase, threshholding
from multiprocessing import Pool
#get one level of acquisition
##load the microscope
#mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")
## testing how pictures are acquired and stored

"""purpose: find the minimum across the z axis at a single x,y coordinate
    inputs: the flatField image array,  raw image, mmc object
    returns: the corrected image array
    saves: nothing
"""
## find minimum of each pixel in the 3D array
def findMinimum(xy, inputArray, mip):
    x = xy[0]
    y = xy[1]
    minimumElement = np.amin(inputArray[:,y,x])
    mip[y,x] = minimumElement

class coord(object):
    def __init__(self, xy, inputArray, mip):
        self.x = xy[0]
        self.y = xy[1]
    def __call__(self, xy, inputArray, mip):
        findMinimum(xy, inputArray, mip)

"""purpose: get a minimum intensity projection from one z stack
    inputs: the z stack
    returns: the minimum intensity array at that location
    saves: nothing
"""
def minimumIntensityProjection(inputArray, mmc):
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    ## initialize an empty array
    mip = np.empty([imageHeight, imageWidth])
    ## make list of X, Y coordinates
    coordinateList = []
    yList = list(range(imageHeight-1))
    xList = list(range(imageWidth-1))
    coordinateList = list(zip(xList, yList))
    print "coordList made"
    p = Pool(8)
    p.map(coord(coordinateList, inputArray, mip), coordinateList, 1)
    return mip



"""purpose: flat field correct an individual image array with only a flatfield image
    inputs: the flatField image array,  raw image, mmc object
    returns: the corrected image array
    saves: nothing
"""
def flatFieldCorrection(flatField, img,  mmc):
    ## get correctedImage
    #correctedImage = np.divide(np.multiply(img, np.divide(flatField, 2)), flatField)
    correctedImage = np.divide(np.multiply(img, np.mean(flatField)), flatField)
    ## display the corrected image
    return correctedImage.astype('uint16')

"""purpose: moves the camera off the sample to get flatfield, turns light off to get darkfield, ends up in same place w light on
    inputs: mmc object
    returns: flatfield and darkfield image arrays
    saves: nothing
"""
def moveForFlatField(mmc):
    ## get initial coordinates
    initialX = mmc.getXPosition()
    initialY = mmc.getYPosition()
    ## get image height
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageHeightUM = pixelSize*imageHeight 
    ## get off the sample
    mmc.snapImage()
    initialImg = mmc.getImage()
    initialImg = threshholding(initialImg)
    while whichCase(initialImg) is not 'j':
        print whichCase(initialImg)
        mmc.setRelativeXYPosition(0, imageHeightUM)
        mmc.snapImage()
        initialImg = mmc.getImage()
        initialImg = threshholding(initialImg)
    ## move one extra time just in case
    mmc.setRelativeXYPosition(0, imageHeightUM)
    ## take the flatField
    mmc.snapImage()
    flatField = mmc.getImage()
    ## return to initialXY
    mmc.setXYPosition(initialX, initialY)
    ## return flatField
    return flatField







