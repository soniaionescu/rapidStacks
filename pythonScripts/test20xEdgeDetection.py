import MMCorePy
import numpy as np
import math
from test20xConfiguration import Configuration
import os
from imread import imsave
import time
import logging

############################## initial location of the function #############################

""" purpose: sample points over a broad region of the sample where there is generally tissue and attempt to find a location with tissue
        goes to xy location where there either is a sample or the central region
    inputs: a mmc object
    returns: true if there is a sample detected and true otherwise
    saves: nothing
"""

def findSample(mmc):
    ## go to each position
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    ## relevant info
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm() ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    configuration = Configuration() 
    numberOfPictures = configuration.numberOfPictures
    distanceBetweenPictures = configuration.distanceBetweenPictures
    ## take 4 images in row and 4 in column for a total of 16
    numberImagesArrayRow = np.arange(0, numberOfPictures)
    numberImagesArrayColumn = np.arange(0, numberOfPictures)
    ## make an array with all the X and Y coordinates (need to start at RightX and TopY)
    # assume it starts at a relatively centered position, so set rightX and TopY to be right and up
    RightX = mmc.getXPosition() - distanceBetweenPictures*2 - imageWidth*2
    TopY = mmc.getYPosition() + distanceBetweenPictures*2 + imageWidth*2
    # create an array of the indeces the images will be taken at
    distanceBetweenPicturesArray = np.arange(0, distanceBetweenPictures*numberOfPictures, distanceBetweenPictures)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM, TopY)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM, RightX)
    imageHeightArrayWithOffset = np.add(imageHeightArray, distanceBetweenPicturesArray)
    imageWidthArrayWithOffset = np.add(imageWidthArray, distanceBetweenPicturesArray)
    ### intialize iteration
    iteration = 0
    ### Start in upper right corner and go to the bottom left
    for y in range(len(imageHeightArrayWithOffset)-1, 0, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArrayWithOffset[y]
        ## go through x on an even iteration 
        if(iteration%2==0): 
            ## go from Right to left
            for x in range(0, len(imageWidthArrayWithOffset)): 
                ## go to correct x,y location
                currentX = imageWidthArrayWithOffset[x]
                mmc.setXYPosition(currentX, currentY) 
                ## move and take photo
                mmc.snapImage()
                singleLayer = mmc.getImage()
                #singleLayer[singleLayer >= 255] = 255
                ## threshold and see which case
                singleLayer = threshholding(singleLayer)
                if whichCase(singleLayer) is not 'j':
                    return 'true'
        ## go through x on an odd iteration
        else:
            ## go from left to right
            for x in range(len(imageWidthArrayWithOffset)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArrayWithOffset[x]
                mmc.setXYPosition(currentX, currentY) 
                ## move and take photo
                mmc.snapImage()
                singleLayer = mmc.getImage()
                #singleLayer[singleLayer >= 255] = 255
                ## threshold and see which case
                singleLayer = threshholding(singleLayer)
                if whichCase(singleLayer) is not 'j':
                    return 'true'
        iteration = iteration + 1

    return 'false'


######################### main methods to find outline of a sample ########################


""" purpose: To detect the most extreme x and y coordinates of a sample
    inputs: an mmc object
    returns: an array with the values [maxX, minX, minY, maxY]
    saves: nothing
"""
def edgeDetectedOverview(mmc):
    ## get values we need
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm() ## for ids uEye at 20x magnification
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
        logging.info('Not on the sample yet')
        movementDirection = moveIfWhite(initialImage, mmc)
        ## reinitialize initialImage so that it has an edge
        mmc.snapImage()
        initialImage = threshholding(mmc.getImage())
        initialX = mmc.getXPosition()
        initialY = mmc.getYPosition()
        movementList = np.array([movementDirection])
    ## handle the corner case of it being all black (all on the brain, not on an edge)
    elif whichCase(initialImage) is 'a':
    ### arbitrarily go up until you find an edge
        logging.info('Completely on the sample')
        moveIfBlack(initialImage, mmc)
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
        ## based on first image, know what case we belong to, add to list
        case = whichCase(tImage)
        statesList = np.append(statesList, case)
        logging.info("states List, {}".format(statesList))
        ## move based on which case
        movement = howToMove(movementList, case, mmc)
        logging.info("movement, {}".format(movement))
        ## add to a list of movements
        movementList = np.append(movementList, movement)
        logging.info("movement list, {}".format(movementList))
        ## add to a list of coordinates
        currentX = mmc.getXPosition()
        currentY = mmc.getYPosition()
        coordinatesList = np.concatenate((coordinatesList, np.array([[currentX, currentY]])), axis=0)
        logging.info("coordinates list, {}".format(coordinatesList))
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


############################## thresholding ###################################################  


""" purpose: takes an image and makes each pixel either black (0) or white (255)
    inputs: a numpy array representing an image
    returns: the image array with each pixel either black or white
    saves: nothing
"""
## create an image that has only value 0 or 255
def threshholding(imageArray):
    maxPixelValue = np.amax(imageArray)
    threshhold = .5*maxPixelValue
    imageToThreshhold = imageArray
    imageToThreshhold[imageToThreshhold < threshhold] = 0
    if imageArray.dtype == 'uint16':
        maxValue = 65535
    else:
        maxValue = 255
    imageToThreshhold[imageToThreshhold >= threshhold] = maxValue
    ## Image.fromarray(imageArray.astype('uint8')).show()
    return imageArray


#################################### defines cases #########################################
    

""" purpose: get the values at each corner (actually 200px horizontally in from the corners because of the tunnelling that happens)
    inputs: a numpy array representing an image (should already be threshholded)
    returns: a list representing [upperRight, upperLeft, bottomRight, bottomLeft]
    saves: nothing
"""
##return a list with the values of each of the four courner pixels
def getCornerValues(imageArray):
    ## get values we need
    arrayHeight = imageArray.shape[0]
    arrayWidth = imageArray.shape[1]
    ## get value of pixel of each corner, arificially cropped by 200 px from each side
    upperRight = imageArray[0,arrayWidth-1]
    upperLeft = imageArray[0,0]
    bottomRight = imageArray[arrayHeight-1, arrayWidth-1]
    bottomLeft = imageArray[arrayHeight-1,0]
    pixelValues = [upperRight, upperLeft, bottomRight, bottomLeft]
    return pixelValues

""" purpose: translate the pixelValues into a case which describes where on the sample we are
    inputs: a numpy array representing an image (should already be threshholded)
    returns: a char a through j, corresponding to a specific location on the sample
    saves: nothing
"""
##return a character which corresponds to which case, which can be used for a case switch statement
def whichCase(imageArray):
    pixelValues = getCornerValues(imageArray)
    if imageArray.dtype == 'uint16':
        maxValue = 65535
    else:
        maxValue = 255
    ## all corners are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'a'
    ## all but upper right corner are black
    if pixelValues[0] == maxValue and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'b'
    ## all but upper left corner are black
    if pixelValues[0] == 0 and pixelValues[1] == maxValue and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'c'
    ## all but bottom right corner are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == maxValue and pixelValues[3] == 0:
        return 'd'
    ## all but bottom left corner are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == maxValue:
        return 'e'
    ## top two are black
    if pixelValues[0] == 0 and pixelValues[1] == 0 and pixelValues[2] == maxValue and pixelValues[3] == maxValue:
        return 'f'
    ## bottom two are black
    if pixelValues[0] == maxValue and pixelValues[1] == maxValue and pixelValues[2] == 0 and pixelValues[3] == 0:
        return 'g'
    ## left two are black
    if pixelValues[0] == maxValue and pixelValues[1] == 0 and pixelValues[2] == maxValue and pixelValues[3] == 0:
        return 'h'
    ## right two are black
    if pixelValues[0] == 0 and pixelValues[1] == maxValue and pixelValues[2] == 0 and pixelValues[3] == maxValue:
        return 'i'
    ## all but upper right corner are white
    if pixelValues[0] == 0 and pixelValues[1] == maxValue and pixelValues[2] == maxValue and pixelValues[3] == maxValue:
        return 'e'
    ## all but upper left corner are white
    if pixelValues[0] == maxValue and pixelValues[1] == 0 and pixelValues[2] == maxValue and pixelValues[3] == maxValue:
        return 'd'
    ## all but bottom right corner are white
    if pixelValues[0] == maxValue and pixelValues[1] == maxValue and pixelValues[2] == 0 and pixelValues[3] == maxValue:
        return 'c'
    ## all but bottom left corner are white
    if pixelValues[0] == maxValue and pixelValues[1] == maxValue and pixelValues[2] == maxValue and pixelValues[3] == 0:
        return 'b'
    ## all are white
    if pixelValues[0] == maxValue and pixelValues[1] == maxValue and pixelValues[2] == maxValue and pixelValues[3] == maxValue:
        return 'j'
    ## test whether None is being returned 
    if pixelValues[0] == 0 and pixelValues[1] == maxValue and pixelValues[2] == maxValue and pixelValues[3] == 0:
        return 'diagonal'
    if pixelValues[0] == maxValue and pixelValues[1] == 0 and pixelValues[2] == 0 and pixelValues[3] == maxValue:
        return 'diagonal'

""" purpose: to see if we have already gone around the entire sample once
    inputs: the initial image as a numpy array, the current image as a numpy array, the list of coordinates, the list of movements, the list of states (cases)
    returns: true or false
    saves: nothing
"""
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


###################################### defines how to move ################################


""" purpose: based on the current case and the previous movements, how should the microscope move
    inputs: the list of previous movements, the current case, an mmc object
    returns: the direction that the microscope should move in 
    saves: nothing
"""
def howToMove(movementList, case, mmc):
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
            while whichCase(image) == 'a':
                mmc.setRelativeXYPosition(-imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still black moving left")
            return 'left'
        ## if it previously moved down, then move right
        if movementList[previousIndex] == 'down':
            while whichCase(image) == 'a':
                mmc.setRelativeXYPosition(imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still black moving right")
            return 'right'
        ## if it previously moved right, then move up
        if movementList[previousIndex] == 'right':
            while whichCase(image) == 'a':
                mmc.setRelativeXYPosition(0, imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still black moving up")
            return 'up'
        ## if it previously moved left, then move down
        if movementList[previousIndex] == 'left':
            while whichCase(image) == 'a':
                mmc.setRelativeXYPosition(0, -imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still black moving down")
            return 'down'
        ## if there is an error (means it was a diagonal case), move based off of two movements ago
        if movementList[previousIndex] == 'error' or 'None':
            if movementList[previousIndex-1] == 'up':
                while whichCase(image) == 'a':
                    mmc.setRelativeXYPosition(-imageWidthUM, 0)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still black moving left")
                return 'left'
            ## if it previously moved down, then move right
            if movementList[previousIndex-1] == 'down':
                while whichCase(image) == 'a':
                    mmc.setRelativeXYPosition(imageWidthUM, 0)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still black moving right")
                return 'right'
            ## if it previously moved right, then move up
            if movementList[previousIndex-1] == 'right':
                while whichCase(image) == 'a':
                    mmc.setRelativeXYPosition(0, imageHeightUM)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still black moving up")
                return 'up'
            ## if it previously moved left, then move down
            if movementList[previousIndex-1] == 'left':
                while whichCase(image) == 'a':
                    mmc.setRelativeXYPosition(0, -imageHeightUM)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still black moving down")
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
                logging.warning("still white moving right")
            return 'right'
        ## if it previously moved down, then move left
        elif movementList[previousIndex] == 'down':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(-imageWidthUM, 0)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still white moving left")
            return 'left'
        ## if it previously moved right, then move down
        elif movementList[previousIndex] == 'right':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(0, -imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still white moving down")
            return 'down'
        ## if it previously moved left, then move up
        elif movementList[previousIndex] == 'left':
            while whichCase(image) == 'j':
                mmc.setRelativeXYPosition(0, imageHeightUM)
                mmc.snapImage()
                image = mmc.getImage()
                image = threshholding(image)
                logging.warning("still white moving up")
            return 'up'
        ## if the case is diagonal (which doesn't really give is information about where it is), move based off movement before that
        elif movementList[previousIndex] == 'error' or 'None':
            if movementList[previousIndex-1] == 'up':
                while whichCase(image) == 'j':
                    mmc.setRelativeXYPosition(imageWidthUM, 0)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still white moving right")
                return 'right'
            ## if it previously moved down, then move left
            elif movementList[previousIndex-1] == 'down':
                while whichCase(image) == 'j':
                    mmc.setRelativeXYPosition(-imageWidthUM, 0)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still white moving left")
                return 'left'
            ## if it previously moved right, then move down
            elif movementList[previousIndex-1] == 'right':
                while whichCase(image) == 'j':
                    mmc.setRelativeXYPosition(0, -imageHeightUM)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still white moving down")
                return 'down'
            ## if it previously moved left, then move up
            elif movementList[previousIndex-1] == 'left':
                while whichCase(image) == 'j':
                    mmc.setRelativeXYPosition(0, imageHeightUM)
                    mmc.snapImage()
                    image = mmc.getImage()
                    image = threshholding(image)
                    logging.warning("still white moving up")
                return 'up'
    elif case == 'diagonal':
        return 'error'

""" purpose: to move the microscope/camera to an edge if the initial image is entirely black
    inputs: the initial image as a numpy array, an mmc object
    returns: nothing
    saves: nothing
"""
def moveIfBlack(initialImage, mmc):
    ## values we need
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm ## for ids uEye at 20x magnification
    imageHeightUM = pixelSize*imageHeight 
    image = initialImage
    ## arbitrarily move up in terms of y coordinates, up in terms of how it looks
    while whichCase(image) == 'a':
        mmc.setRelativeXYPosition(0, imageHeightUM)
        mmc.snapImage()
        array = mmc.getImage()
        image = threshholding(array)

""" purpose: to move the microscope/camera to an edge if the initial image is entirely white
    inputs: the initial image as a numpy array, an mmc object
    returns: nothing
    saves: nothing
"""
def moveIfWhite(initialImage, mmc):
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm() 
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    image = initialImage
    ## get initial measurements

    ## move in an increasingly large square until an edge is found
    currentSideLength = 2 ## not possible to move in a square of less than size 2
    #have 26000/imageWidthUM because 26000 is the width of a slide 
    while whichCase(image) == 'j' and currentSideLength < 26000/imageWidthUM:
        ## move down
        for xy in range (1, currentSideLength): ## how many pictures we want to take
            mmc.setRelativeXYPosition(0, -imageHeightUM)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            if whichCase(image) is not 'j':
                logging.warning("Still white moving down")
                return 'down'
        ## then move right
        for xRight in range (1, currentSideLength):
            mmc.setRelativeXYPosition(-imageWidthUM, 0)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            if whichCase(image) is not 'j':
                logging.warning("Still white moving right")
                return 'right'
        ## then move up
        for yUp in range (1, currentSideLength):
            mmc.setRelativeXYPosition(0, imageHeightUM)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            if whichCase(image) is not 'j':
                logging.warning("Still white moving up")
                return 'up'
        ## then move left but go one further to make a larger square next time
        for xLeft in range (1, currentSideLength+1):
            mmc.setRelativeXYPosition(imageWidthUM, 0)
            mmc.snapImage()
            array = mmc.getImage()
            image = threshholding(array)
            if whichCase(image) is not 'j':
                logging.warning("Still white moving left")
                return 'left'
        ## increase currentSideLength
        currentSideLength = currentSideLength+1

if __name__ == '__main__':
    ## load microscope
    configuration = Configuration() 
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    ## get info for setting ROI
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    # set settings
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)
    #edgeDetectedOverview(mmc)
    mmc.snapImage()
    image = mmc.getImage()
    imsave("unthreshholdedImage.tiff", image)
    imageT = threshholding(image)
    imsave("threshholdedImage.tiff", imageT)
    print whichCase(image)