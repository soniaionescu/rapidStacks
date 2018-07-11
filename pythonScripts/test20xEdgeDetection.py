import MMCorePy
import numpy as np
from PIL import Image
import math
import matplotlib.pyplot as plt
from skimage import data
from skimage.feature import canny
from scipy import ndimage as ndi
from test20xStackToTiff import zStackTiffs
import os
from tifffile import imsave
import time

mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

def edgeDetectedOverview():
    ## get values we need
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ## get initial image
    mmc.snapImage()
    initialImage = mmc.getImage()
    initialImage = threshholding(initialImage)
    ## if it contains an edge
    if whichCase(initialImage) is not 'a' and whichCase(initialImage) is not 'j': 
        initialX = mmc.getXPosition()
        initialY = mmc.getYPosition()
        ## arbitrary initialization
        movementList = np.array(['up'])
    ## handle the corner case of it being all white (not at all on the brain)
    elif whichCase(initialImage) is 'j':
    ### go in squares basically until not all corners are white
        movementDirection = moveIfWhite(initialImage)
        ## reinitialize initialImage so that it has an edge
        mmc.snapImage()
        initialImage = threshholding(mmc.getImage())
        initialX = mmc.getXPosition()
        initialY = mmc.getYPosition()
        movementList = np.array([movementDirection])
    ## handle the corner case of it being all black (all on the brain, not on an edge)
    elif whichCase(initialImage) is 'a':
    ### arbitrarily go up until you find an edge
        moveIfBlack(initialImage)
        ## reinitialize initialImage so that it has an edge
        mmc.snapImage()
        initialImage = threshholding(mmc.getImage())
        initialX = mmc.getXPosition()
        initialY = mmc.getYPosition()
        movementList = np.array(['up'])
    ### initialize list of movements and list of coordinates and list of states
    coordinatesList = np.array([[initialX, initialY]])
    statesList = np.array([whichCase(initialImage)])
    shouldWeEnd = 'false'
    ## iterate around the brain
    while shouldWeEnd == 'false':
        mmc.snapImage()
        image = mmc.getImage()
        tImage = threshholding(image)
        Image.fromarray(tImage.astype('uint8')).show()
        ## based on first image, know what case we belong to, add to list
        case = whichCase(tImage)
        statesList = np.append(statesList, case)
        print "states List", statesList
        ## move based on which case
        movement = howToMove(movementList, case)
        print "movement", movement
        ## add to a list of movements
        movementList = np.append(movementList, movement)
        print "movement list", movementList
        ## add to a list of coordinates
        currentX = mmc.getXPosition()
        currentY = mmc.getYPosition()
        coordinatesList = np.concatenate((coordinatesList, np.array([[currentX, currentY]])), axis=0)
        print "coordinates list", coordinatesList
        #mmc.sleep(5000)
        ## see if we should stop
        shouldWeEnd = decideIfEnd(initialImage, tImage, coordinatesList, movementList, statesList)
    ## find the leftmost, topmost, bottommost, and rightmost coordinates of edges
    maxX = coordinatesList[:,0].max()
    maxY = coordinatesList[:,1].max()
    minX = coordinatesList[:,0].min()
    minY = coordinatesList[:,1].min()
    ##return array with [RightX, LeftX, BottomY, TopY] as defined in test20xOverview (as the micrscope moves)
    coordArray = [maxX, minX, minY, maxY]
    print "coord array", coordArray
    return coordArray


## create an image that has only value 0 or 255
def threshholding(imageArray):
    imageArray[imageArray <215] = 0
    imageArray[imageArray >= 215 ] = 255
    ## Image.fromarray(imageArray.astype('uint8')).show()
    return imageArray

##return a list with the values of each of the four courner pixels
def getCornerValues(imageArray):
    ## get values we need
    arrayHeight = imageArray.shape[0]
    arrayWidth = imageArray.shape[1]
    ## get value of pixel of each corner, arificially cropped by 200 px from each side
    upperRight = imageArray[0,arrayWidth-200]
    upperLeft = imageArray[0,200]
    bottomRight = imageArray[arrayHeight-1, arrayWidth-200]
    bottomLeft = imageArray[arrayHeight-1,200]
    pixelValues = [upperRight, upperLeft, bottomRight, bottomLeft]
    return pixelValues

##return a character which corresponds to which case, which can be used for a case switch statement
def whichCase(imageArray):
    pixelValues = getCornerValues(imageArray)
    ## all corners are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'a'
    ## all but upper right corner are black
    if pixelValues[0] == 255 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'b'
    ## all but upper left corner are black
    if pixelValues[0] == 0 and pixelValues[1] == 255 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'c'
    ## all but bottom right corner are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 255 and pixelValues[3] == 0:
        return 'd'
    ## all but bottom left corner are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 255:
        return 'e'
    ## top two are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 255 and pixelValues[3] == 255:
        return 'f'
    ## bottom two are black
    if pixelValues[0] == 255 and pixelValues[1] == 255 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'g'
    ## left two are black
    if pixelValues[0] == 255 and pixelValues[1] == 0 and pixelValues[2] == 255 and pixelValues[3] == 0:
        return 'h'
    ## right two are black
    if pixelValues[0] == 0 and pixelValues[1] == 255 and pixelValues[2] == 0 and pixelValues[3] == 255:
        return 'i'
    ## all but upper right corner are white
    if pixelValues[0] == 0 and pixelValues[1] == 255 and pixelValues[2] == 255 and pixelValues[3] == 255:
        return 'e'
    ## all but upper left corner are white
    if pixelValues[0] == 255 and pixelValues[1] == 0 and pixelValues[2] == 255 and pixelValues[3] == 255:
        return 'd'
    ## all but bottom right corner are white
    if pixelValues[0] == 255 and pixelValues[1] == 255 and pixelValues[2] == 0 and pixelValues[3] == 255:
        return 'c'
    ## all but bottom left corner are white
    if pixelValues[0] == 255 and pixelValues[1] == 255 and pixelValues[2] == 255 and pixelValues[3] == 0:
        return 'b'
    ## all are white
    if pixelValues[0] == 255 and pixelValues[1] == 255 and pixelValues[2] == 255 and pixelValues[3] == 255:
        return 'j'
    ## test whether None is being returned 
    if pixelValues[0] == 0 and pixelValues[1] == 255 and pixelValues[2] == 225 and pixelValues[3] == 0:
        return 'diagonal'
    if pixelValues[0] == 255 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 255:
        return 'diagonal'

def decideIfEnd(initialArray, currentArray, coordinatesList, movementList, statesList):
    initialCase = whichCase(initialArray)
    currentCase = whichCase(currentArray)
    initialXY = coordinatesList[0,:]
    currentXY = coordinatesList[coordinatesList.shape[0]-1,:]
    if initialCase == currentCase: ## note, initialCase will never be all white or all black because of how corner cases were handled in the main method
    ## these only make sense because movement is defined to be clockwise (as seen visually through the camera)
        print "should we end?", "initial case and current case are", initialCase, "initialXY are", initialXY, "currentXY are", currentXY
        if initialCase == 'b': ## all but upper right corner are black
            if initialXY[0] > currentXY[0] and initialXY[1] > currentXY[1] and 'left' in movementList: ## more right than initially AND lower AND we've moved left before
                if 'd' in statesList and 'e' in statesList and 'c' in statesList: ## we've seen all three other types of corners
                    return 'true'
        elif initialCase == 'c': ## all but upper left corner are black
            if initialXY[0] > currentXY[0] and initialXY[1] < currentXY[1] and 'left' in movementList: ## more right than initially AND higher AND we've moved left before
                if 'd' in statesList and 'e' in statesList and 'b' in statesList: ## we've seen all three other types of corners
                    return 'true'
        elif initialCase == 'd': ## all but bottom right corner are black
            if initialXY[0] < currentXY[0] and initialXY[1] < currentXY[1] and 'right' in movementList: ## more left and higher, and we've already gone right
                if 'b' in statesList and 'e' in statesList and 'c' in statesList: ## we've seen all three other types of corners
                    return 'true'
        elif initialCase == 'e': ## all but bottom left corner are black
            if initialXY[0] < currentXY[0] and initialXY[1] < currentXY[1] and 'right' in movementList: ## more left and higher, and we've already gone right
                if 'd' in statesList and 'b' in statesList and 'c' in statesList: ## we've seen all three other types of corners
                    return 'true'
        elif initialCase == 'f': ## top two are black
            if initialXY[0] < currentXY[0] and initialXY[1] < currentXY[1] and 'right' in movementList: ## more left and higher, and we've already gone right
                if 'i' in statesList and 'g' in statesList and 'h' in statesList: ## we've seen all three other types of edges
                    return 'true'
        elif initialCase == 'g': ## bottom two are black
            if initialXY[0] > currentXY[0] and initialXY[1] > currentXY[1] and 'left' in movementList: ## more right than initially AND lower AND we've moved left before
                if 'i' in statesList and 'f' in statesList and 'h' in statesList: ## we've seen all three other types of edges
                    return 'true'
        elif initialCase == 'h': ## left two are black
            if initialXY[0] > currentXY[0] and initialXY[1] > currentXY[1] and 'up' in movementList: ## more right than initially AND lower AND we've moved up before
                if 'i' in statesList and 'g' in statesList and 'f' in statesList: ## we've seen all three other types of edges
                    return 'true'
        elif initialCase == 'i': ## right two are black
            if initialXY[0] < currentXY[0] and initialXY[1] > currentXY[1] and 'down' in movementList: ## more left than initially AND lower AND we've moved down before
                if 'f' in statesList and 'g' in statesList and 'h' in statesList: ## we've seen all three other types of edges
                    return 'true'
    return 'false'
def howToMove(movementList, case):
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    if case == 'a':
        previousIndex = len(movementList) - 1
        mmc.snapImage()
        inIm = mmc.getImage()
        initialImage = threshholding(inIm)
        image = initialImage
        ## if it previously moved up, then move left
        if movementList[previousIndex] == 'up':
            while whichCase(image) == 'a' or np.mean(image) < 50:
                mmc.setRelativeXYPosition(-imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still black moving left"
            return 'left'
        ## if it previously moved down, then move right
        if movementList[previousIndex] == 'down':
            while whichCase(image) == 'a' or np.mean(image) < 50:
                mmc.setRelativeXYPosition(imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still black moving right"
            return 'right'
        ## if it previously moved right, then move up
        if movementList[previousIndex] == 'right':
            while whichCase(image) == 'a' or np.mean(image) < 50:
                mmc.setRelativeXYPosition(0, imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still black moving up"
            return 'up'
        ## if it previously moved left, then move down
        if movementList[previousIndex] == 'left':
            while whichCase(image) == 'a' or np.mean(image) < 50:
                mmc.setRelativeXYPosition(0, -imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                print "still black moving down"
            return 'down'
    ## in upper right corner, move down and right
    elif case == 'b':
        mmc.setRelativeXYPosition(imageWidthUM, -imageHeightUM)
        return 'down'
    ## in upper left corner, move right and up
    elif case == 'c':
        mmc.setRelativeXYPosition(imageWidthUM, imageHeightUM)
        return 'right'
    ## in bottom right corner, move left and down
    elif case == 'd':
        mmc.setRelativeXYPosition(-imageWidthUM, -imageHeightUM)
        return 'left'
    ## in bottom left corner, move up and left
    elif case == 'e':
        mmc.setRelativeXYPosition(imageHeightUM, imageHeightUM)
        return 'up'
    ## bottom edge, move left
    elif case == 'f':
        mmc.setRelativeXYPosition(-imageWidthUM, 0)
        return 'left'
    ## top edge, move right
    elif case == 'g':
        mmc.setRelativeXYPosition(imageWidthUM, 0)
        return 'right'
    ##right edge, move down
    elif case == 'h':
        mmc.setRelativeXYPosition(0, -imageHeightUM)
        return 'down'
    ## left edge, move up
    elif case == 'i':
        mmc.setRelativeXYPosition(0, imageHeightUM)
        return 'up'
    ## all white, move to an edge and return a movement
    elif case == 'j':
        previousIndex = len(movementList) - 1
        mmc.snapImage()
        inIm = mmc.getImage()
        initialImage = threshholding(inIm)
        image = initialImage
        ## if it previously moved up, then move right
        if movementList[previousIndex] == 'up':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still white moving rigt"
            return 'right'
        ## if it previously moved down, then move left
        elif movementList[previousIndex] == 'down':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(-imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still white moving left"
            return 'left'
        ## if it previously moved right, then move down
        elif movementList[previousIndex] == 'right':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(0, -imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still white moving down"
            return 'down'
        ## if it previously moved left, then move up
        elif movementList[previousIndex] == 'left':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(0, imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                Image.fromarray(image).show()
                print "still white moving up"
            return 'up'
    elif case == 'diagonal':
        return 'error'
def moveIfBlack(initialImage):
    ## values we need
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageHeightUM = pixelSize*imageHeight 
    image = initialImage
    ## arbitrarily move up in terms of y coordinates, up in terms of how it looks
    while whichCase(image) == 'a':
        mmc.setRelativeXYPosition(0, imageHeightUM)
        mmc.snapImage()
        array = mmc.getImage()
        image = threshholding(array)
    
def moveIfWhite(initialImage):
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    image = initialImage
    ## get initial measurements

    ## move in an increasingly large square until an edge is found
    currentSideLength = 2 ## not possible to move in a square of less than size 2
    while whichCase(image) == 'j' or 'e' and currentSideLength < 10:
        ## move down
        for xy in range (1, currentSideLength): ## how many pictures we want to take
            mmc.setRelativeXYPosition(0, -imageHeightUM)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            Image.fromarray(image.astype('uint8')).show()
            if whichCase(image) is not 'j':
                return 'down'
        ## then move right
        for xRight in range (1, currentSideLength):
            mmc.setRelativeXYPosition(-imageWidthUM, 0)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            Image.fromarray(image.astype('uint8')).show()
            if whichCase(image) is not 'j':
                return 'right'
        ## then move up
        for yUp in range (1, currentSideLength):
            mmc.setRelativeXYPosition(0, imageHeightUM)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            Image.fromarray(image.astype('uint8')).show()
            if whichCase(image) is not 'j':
                return 'up'
        ## then move left but go one further to make a larger square next time
        for xLeft in range (1, currentSideLength+1):
            mmc.setRelativeXYPosition(imageWidthUM, 0)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            Image.fromarray(image.astype('uint8')).show()
            if whichCase(image) is not 'j':
                return 'left'
        ## increase currentSideLength
        currentSideLength = currentSideLength+1

start_time = time.time()
edgeDetectedOverview()
print "My program took", time.time() - start_time, "to run"

