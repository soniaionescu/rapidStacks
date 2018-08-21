import MMCorePy
import os
import math
import numpy as np
import itertools
#from imread import imsave
from scipy.misc import imsave
from imread import imsave as imsave16
from test20xEdgeDetection import whichCase, threshholding
from test20xConfiguration import Configuration 
import math
import csv


############## take a DAPI image ######################

""" purpose: take a DAPI image at 1 plane
    inputs: the folder into which to save the images, the list of x,y,z coordinates which is the output of getOverviewAndSaveZ and is modified by the focus methods
    returns: nothing
    saves: A folder of DAPI images in X_Y_Z format
"""
def fluorescenceAcquisition(coordinatesList, folder, flatField, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    ## get initialFolder
    initialDir = os.getcwd()
    ## make folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    ## change folder
    os.chdir(folder)
    ## change the reflector turret to DAPI
    DAPIOn(mmc)
    ## get information to construct the stitched image
    pixelSize = mmc.getPixelSizeUm()
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    configuration = Configuration()
    notOverlap = configuration.notOverlap
    ## initialize the size of one row 
    ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ## get the number of images that will be taken and make an array with that many
    # number of images
    numberImagesRow = math.ceil(abs((min(x[0] for x in coordinatesList)) - (max(x[0] for x in coordinatesList)))/imageWidthUM/notOverlap) + 1
    numberImagesColumn = math.ceil(abs((max(y[1] for y in coordinatesList)) - (min(y[1] for y in coordinatesList)))/imageHeightUM/notOverlap) + 1
    # number of images as an array
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## initialize the size of one row 
    rowWidth = (numberImagesArrayRow[len(numberImagesArrayRow)-1] + 1)*(imageWidth*notOverlap)  ## need to add 1 because we need the total size of the array, if we don't add 1 it's the size of the array up to the last picture
    columnHeight = (numberImagesArrayColumn[len(numberImagesArrayColumn)-1] + 1)*(imageHeight*notOverlap) ## add 2 for same reason as above
    ## make the matrix
    imageSoFar = np.zeros([int(rowWidth), int(columnHeight)])
    # Convert coordinates into pixels
    pixCoord = np.array(coordinatesList)
    pixCoord = pixCoord/pixelSize
    pixCoord[:,0] = pixCoord[:,0] - np.amin(pixCoord[:,0])
    pixCoord[:,1] = np.amax(pixCoord[:,1]) - pixCoord[:,1]
    ## traverse the coordinate list
    for i in range(0, len(coordinatesList)):
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
        img = flatFieldCorrection(flatField, img, mmc)
        ## save the image in Y/X/Z.tiff folders
        path = str(y) + "/" + str(x)
        if not os.path.exists(path):
            os.makedirs(path)
        filePath = path + "/" + str(z) + ".tiff"
        print img.dtype
        imsave16(filePath, img)
        imageSoFar = stitchDAPI(imageSoFar, pixCoord[i,0], pixCoord[i,1], img.T, mmc)
    ## change the reflector turret back to BF
    DAPIOff(mmc)
    ## change folder back
    os.chdir(initialDir)
    ## save the image
    imageSoFar = stitchToEnd(imageSoFar.T, mmc)
    imageSoFar = imageSoFar.astype('uint16')
    print imageSoFar.dtype
    imsave(folder + "DAPI.tiff", imageSoFar)

    
""" purpose: turn DAPI things on"""
def DAPIOn(mmc):
    mmc.sleep(100)
    mmc.setProperty('ZeissTransmittedLightShutter', 'State', 0)
    mmc.sleep(100)
    mmc.setProperty('ZeissReflectorTurret', 'State', 3)
    mmc.sleep(100)
    mmc.setProperty('ZeissReflectedLightShutter', 'State', 1)

def DAPIOff(mmc):
    mmc.sleep(100)
    mmc.setProperty('ZeissReflectedLightShutter', 'State', 0)
    mmc.sleep(100)
    mmc.setProperty('ZeissReflectorTurret', 'State', 0)
    mmc.sleep(100)
    mmc.setProperty('ZeissTransmittedLightShutter', 'State', 1)


""" purpose: insert one DAPI image into the larger array which will be a stitched image
    inputs: The stitched DAPI image so far, with the pictures that have been previously taken inserted the x coordinate, the y coordinate, an array of x coordinates and an array of z coordinates
    returns: nothing
    saves: Nothing, but changes the values in imageSoFar
"""

############################ stitch the DAPI #######################################

def stitchDAPI(imageSoFar, x, y, img, mmc):
    configuration = Configuration()
    notOverlap = configuration.notOverlap
    ## crop the image
    croppedImg = img[0:int(math.floor(img.shape[0]*notOverlap)), 0:int(math.floor(img.shape[1]*notOverlap))]
    
    ## put into the larger image
    imageSoFar[int(math.floor(x)):(int(math.floor(x))+croppedImg.shape[0]), 
               int(math.floor(y)):(int(math.floor(y))+croppedImg.shape[1])] = croppedImg
    return imageSoFar

###################### because I can't figure out why first and last columns are stitched, take the final image and move first column to the end

def stitchToEnd(imageSoFar, mmc):
    configuration = Configuration()
    notOverlap = configuration.notOverlap
    imageWidthNotOverlap = int(mmc.getImageWidth()*notOverlap)
    ## get the first column
    columnToStitch = imageSoFar[0:imageSoFar.shape[0], 0:imageWidthNotOverlap]
    ## move the image without the first column over by one column
    imageSoFar[0:imageSoFar.shape[0],  0:(imageSoFar.shape[1] - imageWidthNotOverlap)] = imageSoFar[0:imageSoFar.shape[0], imageWidthNotOverlap:imageSoFar.shape[1]]

    ## make columnToStitch the last column
    imageSoFar[0:imageSoFar.shape[0], (imageSoFar.shape[1]-imageWidthNotOverlap):imageSoFar.shape[1]] = columnToStitch
    imageSoFarCropped = imageSoFar[0:imageSoFar.shape[0], 0:imageSoFar.shape[1]-imageWidthNotOverlap+1]
    return imageSoFarCropped

####################### DAPI flatfield methods #######################################

"""purpose: flat field correct an individual image array with only a flatfield image
    inputs: the flatField image array,  raw image, mmc object
    returns: the corrected image array
    saves: nothing
"""
def flatFieldCorrection(flatField, img,  mmc):
    ## get correctedImage
    correctedImage = np.divide(np.multiply(img, np.mean(flatField)), flatField)
    ## display the corrected image
    return correctedImage.astype('uint16')


########################## main #############################

if __name__ == '__main__':  
    # create configuration object
    configuration = Configuration() 
    #load microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    ## get info for setting ROI
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    # set settings
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureDAPI)
    ## nned to get height and width here again because otherwise it's different b/c we changed the ROI
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    # set left right top bottom
    ## (right = minX, left=maxX, bottom = minY, top = maxY)
    LeftX = 8266
    RightX = -4773
    TopY = -2489
    BottomY = -11605
    pixelSize = mmc.getPixelSizeUm()
    notOverlap = configuration.notOverlap
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM, BottomY-imageHeightUM)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM, RightX)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*notOverlap , BottomY-imageHeightUM*notOverlap )
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*notOverlap , RightX)
    xylist = []
    for y in imageHeightArray:
        xylist = xylist + list(zip(imageWidthArray, itertools.repeat(y), [(mmc.getPosition())]*len(imageWidthArray)))
    csvfile = "XYZCoord.csv"
    #save xyzTuple to csv so I can use it for DAPI image 
    with open(csvfile, "w") as output:
        writer = csv.writer(output)
        for val in xylist:
            writer.writerow([val])
    flatField = np.genfromtxt(configuration.DAPIflatField, delimiter=",")
    fluorescenceAcquisition(xylist, "816FluorescenceAcquisition", flatField,  mmc) 
