import MMCorePy
import os
import math
import numpy as np
import itertools
from scipy.misc import imsave
from testImageProcessing import moveForFlatField, flatFieldCorrection


############## take a DAPI image ######################

""" purpose: take a DAPI image at 1 plane
    inputs: the folder into which to save the images, the list of x,y,z coordinates which is the output of getOverviewAndSaveZ and is modified by the focus methods
    returns: nothing
    saves: A folder of DAPI images in X_Y_Z format
"""
def fluorescenceAcquisition(coordinatesList, folder, mmc):
    ## get initialFolder
    initialDir = os.getcwd()
    ## make folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    ## change folder
    os.chdir(folder)
    ## change the reflector turret to DAPI
    mmc.setProperty('ZeissReflectorTurret', 'Label', '4-49 DAPI')
    mmc.setProperty('ZeissTransmittedLightShutter', 'State', 0)
    mmc.setProperty('ZeissReflectedLightShutter', 'State', 1)
    ## get information to construct the stitched image
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ## get the number of images that will be taken and make an array with that many
    # number of images
    numberImagesRow = math.ceil(abs((min(x[0] for x in coordinatesList)) - (max(x[0] for x in coordinatesList)))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((max(y[1] for y in coordinatesList)) - (min(y[1] for y in coordinatesList)))/imageHeightUM/.9) + 2
    # number of images as an array
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    # convert the number of images to an XY coordinate
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    ## initialize the size of one row 
    rowWidth = (numberImagesArrayRow[len(numberImagesArrayRow)-1] + 1)*int(imageWidth*.9)  ## need to add 1 because we need the total size of the array, if we don't add 1 it's the size of the array up to the last picture
    columnHeight = (numberImagesArrayColumn[len(numberImagesArrayColumn) -1] +1)*int(imageHeight*.9)
    ## make the matrix
    imageSoFar = np.empty([columnHeight, rowWidth])
    ## traverse the coordinate list
    for i in range(0, len(coordinatesList)-1):
        ## get the x y z coordinates
        x = coordinatesList[i][0]
        y = coordinatesList[i][1]
        z = coordinatesList[i][2]
        ## travel to that x y z coordinate
        mmc.setXYPosition(x, y)
        mmc.setPosition(z)
        ## take the image
        mmc.snapImage()
        img = mmc.getImage()
        ## save the image in Y/X/Z.tiff folders
        path = str(y) + "/" + str(x)
        if not os.path.exists(path):
            os.makedirs(path)
        filePath = path + "/" + str(z) + ".tiff"
        imsave(filePath, img)
        imageSoFar = stitchDAPI(imageSoFar, x, y, imageHeightArray, imageWidthArray, img, mmc)
    ## change the reflector turret back to BF
    mmc.setProperty('ZeissReflectorTurret', 'Label', '1-Empty Module')
    mmc.setProperty('ZeissReflectedLightShutter', 'State', 0)
    mmc.setProperty('ZeissTransmittedLightShutter', 'State', 1)
    ## change folder back
    os.chdir(initialDir)
    ## save the image
    imsave(folder + "DAPI.tiff", imageSoFar)

    
""" purpose: insert one DAPI image into the larger array which will be a stitched image
    inputs: The stitched DAPI image so far, with the pictures that have been previously taken inserted the x coordinate, the y coordinate, an array of x coordinates and an array of z coordinates
    returns: nothing
    saves: Nothing, but changes the values in imageSoFar
"""

############################ stitch the DAPI #######################################

def stitchDAPI(imageSoFar, x, y, imageHeightArray, imageWidthArray, img, mmc):
    ## get width and height of an image
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    ## get the x and y pixel value of the array
    indexX = [i for i in range(len(imageWidthArray)) if int(imageWidthArray[i]) == int(x)]
    xInArray = indexX[0]*int((3.45/(20*.63)))
    indexY = [i for i in range(len(imageHeightArray)) if imageHeightArray[i] == y]
    yInArray = indexY[0]*int((3.45/(20*.63)))
    ## crop the image
    croppedImg = img[0:int(imageHeight*.9):1, 0:int(imageWidth*.9):1]
    ## put into the larger image
    imageSoFar[yInArray:(yInArray+imageHeight*.9), xInArray:(xInArray+imageWidth*.9)] = croppedImg
    return imageSoFar

########################## main #############################

if __name__ == '__main__':   
    #load microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")
    # set settings
    mmc.setROI(300, 0, 3504, 2174)
    mmc.setProperty('IDS uEye', 'Exposure', 1)
    # set left right top bottom
    LeftX = 8102
    RightX = -3919
    TopY = 1250
    BottomY = -6536
    ## get xy array
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/.9) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    xylist = []
    for y in imageHeightArray:
        xylist = xylist + list(zip(imageWidthArray, itertools.repeat(y), [(mmc.getPosition())]*len(imageWidthArray)))
    fluorescenceAcquisition(xylist, "82FluorescenceAcquisition", mmc)