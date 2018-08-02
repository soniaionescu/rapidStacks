import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import math
import matplotlib.pyplot as plt
from skimage import data
from skimage.feature import canny
from scipy import ndimage as ndi
from test20xStackToTiff import zStackTiffs, makeMIP
from test20xZEdgeDetection import zLimits
from testImageProcessing import flatFieldCorrection
#from test20xEdgeDetection import zLimits
import os
from scipy.misc import imsave
from scipy.misc import imresize

#Load devices
if __name__ == '__main__':
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

########################### MIP generation ############################################

""" purpose: get Y/X/000000.tiffs of MIPS, as well as a stitched overview
    inputs: The rightmost, leftmost, bottom, and top coordinates (right = minX, left=maxX, bottom = minY, top = maxY), the most positive and most
            negative z coordinates, an mmc object, the desired resolution of the overview image in form 'high', 'medium', or 'low'
    returns: nothing
    saves: Y/X/000000.tiffs of MIPS and one overview image
"""
def getOverviewAndSaveMIP(folder, resolution, RightX, LeftX, BottomY, TopY, upperZ, lowerZ, flatField,  mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    ## go to correct folder
    initialDir = os.getcwd()
    if not os.path.exists(folder):
        os.makedirs(folder)
    os.chdir(folder)
    ## get necessary information
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## initialze the list of (x,y,z) 3-tuples which will be returned for use in the DAPI method
    XYZCoordList = []
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/.9) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## initialize the size of one row 
    rowWidth = (numberImagesArrayRow[len(numberImagesArrayRow)-1] + 1)*int(imageWidth*.9)  ## need to add 1 because we need the total size of the array, if we don't add 1 it's the size of the array up to the last picture
    image = np.empty([0, int(rowWidth)])
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    ### Start in upper left corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, -1, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        if(iteration%2==0): ## it is an even iteration
            ## initialize the row
            row = np.empty([int(imageHeight*.9), 0])
            ## go from Right to left
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY) 
                ## go make MIP at current XY location and find most in focus Z
                array, hvLayer = makeMIP(upperZ, lowerZ, flatField, mmc)
                ## save the MIP
                foldername = str(currentY) + "/" + str(currentX) #make the folder name the y index
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                filename = foldername + "/000000.tiff"
                imsave(filename, array)
                # stitched the cropped mip
                croppedArray = array[0:int(imageHeight*.9):1, 0:int(imageWidth*.9):1]
                row = np.concatenate((row, croppedArray), axis = 1)
                #Add xyz 3-tuple to list
                XYZCoordList = XYZCoordList + [(currentX, currentY, hvLayer)]
            # concatenate rows together
            image = np.concatenate((image, row), axis = 0)
        else:
            ## initialize the row
            row = np.empty([int(imageHeight*.9), 0])
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY) 
                ## go make MIP at current XY location and find most in focus Z
                array, hvLayer = makeMIP(upperZ, lowerZ, flatField, mmc)
                ## Save the MIP
                foldername = str(currentY) + "/" + str(currentX) #make the folder name the y index
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                filename = foldername + "/000000.tiff"
                imsave(filename, array)
                # stitch the cropped mip
                croppedArray = array[0:int(imageHeight*.9):1, 0:int(imageWidth*.9):1]
                row = np.concatenate((croppedArray, row), axis = 1)
                #Add xyz 3-tuple to list
                XYZCoordList = XYZCoordList + [(currentX, currentY, hvLayer)]
            # concatenate rows together
            image = np.concatenate((image, row), axis = 0)
        iteration = iteration+1
    ## go back to initial folder
    os.chdir(initialDir)
    MIPName = folder + ".tiff"
    ## make sure to test medium and low resolution!
    if resolution == 'high':
        imsave(MIPName, image)
    if resolution == 'medium':
        imMedium = imresize(image, (image.shape[0]/2, image.shape[1]/2))
        imsave(MIPName, imMedium)
    if resolution == 'low':
        imLow = imresize(image, (image.shape[0]/4, image.shape[1]/4))
        imsave(MIPName, imLow)
    ## return XYZCoordList
    return XYZCoordList

""" purpose: get 1 stitched TIFF of MIPS
    inputs: The rightmost, leftmost, bottom, and top coordinates (right = minX, left=maxX, bottom = minY, top = maxY), the most positive and most
            negative z coordinates, an mmc object
    returns: nothing
    saves: a tiff of MIPS with the name specified in the function
"""
def getOverviewAndStitchMIP(RightX, LeftX, BottomY, TopY, upperZ, lowerZ, flatField,  mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## initialze the list of (x,y,z) 3-tuples which will be returned for use in the DAPI method
    XYZCoordList = []
    ## initialize the size of one row 
    rowWidth = math.ceil(abs((RightX -imageWidthUM/2) - (LeftX + imageWidthUM/2))/imageWidthUM)*imageWidth  ## to get an integer number of imageWidths in a row
    image = np.empty([0, int(rowWidth)])
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM, BottomY-imageHeightUM)
    print "imageHeightArray", imageHeightArray
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM, RightX)
    ### Start in upper left corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, 0, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        if(iteration%2==0): ## it is an even iteration
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from Right to left
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                print "moving to", currentX, currentY
                mmc.setXYPosition(currentX, currentY) 
                array, hvLayer = makeMIP(upperZ, lowerZ, flatField, mmc)
                row = np.concatenate((row, array), axis = 1)
                # add 3-tuple of coordinates to list
                XYZCoordList = XYZCoordList + [(currentX, currentY, hvLayer)]
            image = np.concatenate((image, row), axis = 0)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                print "moving to", currentX, currentY
                mmc.setXYPosition(currentX, currentY) 
                array, hvLayer = makeMIP(upperZ, lowerZ, flatField, mmc)
                row = np.concatenate((array, row), axis = 1)
                # add 3-tuple of coordinates to list
                XYZCoordList = XYZCoordList + [(currentX, currentY, hvLayer)]
            image = np.concatenate((image, row), axis = 0)
        iteration = iteration+1
    ## display
    imsave("730StitchedStitchedMIPOvernight.tiff", image)
    print XYZCoordList



############################### one layer overview generation ####################################


""" purpose: save tiffs corresponding to X coordinates in the following structure: Y/X.tiff
    inputs: the folder to save into, the rightmost, leftmost, bottom, top, coordinates, and an mmc object. right = minX, left=maxX, bottom = minY, top = maxY. 
    returns: nothing
    saves: Saves an XY overview in the format Y/X/Z.tiff into FolderToSaveTo
"""

def getOverviewAndSaveXY(FolderToSaveTo, RightX, LeftX, BottomY, TopY, flatField, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/.9) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    print imageHeightArray
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    print imageWidthArray
    ### intialize iteration
    iteration = 0
    ## go into correct directory
    initialDir = os.getcwd()
    if not os.path.exists(FolderToSaveTo):
            os.makedirs(FolderToSaveTo)
    os.chdir(FolderToSaveTo)
    ### Start in upper riught corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, -1, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        ## go through x on an even iteration 
        if(iteration%2==0): 
            ## go from Right to left
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY)     
                ## make folder for this X coordinate
                foldername = str(currentY) + "/" + str(currentX) #make the folder name the y index
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                filename = foldername + "/000000.tiff"
                ## move and take photo
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
                ## save tiff at the filename
                imsave(filename, singleLayer)
        ## go through x on an odd iteration
        else:
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY)      
                ## make folder for this X coordinate
                foldername = str(currentY) + "/" + str(currentX) #make the folder name the y index
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                filename = foldername + "/000000.tiff"
                ## move and take photo
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer = flatFieldCorrection(flatField, singleLayer, mmc)
                ## save tiff at the filename
                imsave(filename, singleLayer)
        iteration = iteration + 1
    ## go back to initial working directory for the next step
    os.chdir(initialDir)

""" purpose: get 1 stitched TIFF
    inputs: The rightmost, leftmost, bottom, and top coordinates (right = minX, left=maxX, bottom = minY, top = maxY), the most positive and most
            negative z coordinates, an mmc object
    returns: nothing
    saves: a tiff with the name specified in the function
"""
def getOverviewAndStitch(fileName, RightX, LeftX, BottomY, TopY, flatField,  mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## initialize the size of one row 
    rowWidth = math.ceil(abs((RightX -imageWidthUM/2) - (LeftX + imageWidthUM/2))/imageWidthUM)*imageWidth  ## to get an integer number of imageWidths in a row
    image = np.empty([0, int(rowWidth)])
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM, BottomY-imageHeightUM)
    print "imageHeightArray", imageHeightArray
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM, RightX)
    ### Start in upper left corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, 0, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        if(iteration%2==0): ## it is an even iteration
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from Right to left
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY) 
                mmc.snapImage() 
                array = mmc.getImage()
                array = flatFieldCorrection(flatField, array, mmc)
                row = np.concatenate((row, array), axis= 1)
                #Image.fromarray(row).show()
            image = np.concatenate((image, row), axis = 0)
            #Image.fromarray(image).show()
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY) 
                mmc.snapImage() 
                array = mmc.getImage()
                array = flatFieldCorrection(flatField, array, mmc)
                row = np.concatenate((array, row), axis = 1)
                #Image.fromarray(row).show()
            image = np.concatenate((image, row), axis = 0)
            #Image.fromarray(image).show() 
        iteration = iteration+1
    ## display
    name = fileName + "tiff"
    imsave(name, image)


#################################### save whole z stack generation ##############################


""" purpose: saves z tiffs to FolderToSaveTo in the format y/x/z.tiff (with flatfield correction applied)
    inputs: The folderToSaveTo, the rightmost, leftmost, bottom, and top coordinates (right = minX, left=maxX, bottom = minY, top = maxY), the most positive and most
            negative z coordinates, an mmc object
    returns: nothing
    saves: z tiffs to FolderToSaveTo in the format y/x/z.tiff
"""
def getOverviewAndSaveZ(FolderToSaveTo, RightX, LeftX, BottomY, TopY, upperZ, lowerZ, highestFocusZ, flatField, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/.9) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    print imageHeightArray
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    print imageWidthArray
    ### intialize iteration and list of coordinates
    iteration = 0
    ### initialize list of coordinates
    middleZ = upperZ - (upperZ - lowerZ)/2
    ### go into correct folder
    initialDir = os.getcwd()
    if not os.path.exists(FolderToSaveTo):
            os.makedirs(FolderToSaveTo)
    os.chdir(FolderToSaveTo)
    ### Start in upper left corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, -1, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        folder = str(currentY) #make the folder name the y index
        if not os.path.exists(folder):
            os.makedirs(folder)
        ## go through x for even iteration
        if(iteration%2==0): 
            ## go from Right to left 
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY)  
                ## add this xy coordinate to the list of xy coordinates and put z in the middle
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(currentX)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder, upperZ, lowerZ, flatField,  mmc)
        ## go through x for odd iteration
        else:
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): ##go from Left to Right
                 ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY)
                ## add this xy coordinate to the list of xy coordinates and put z in the middle
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(currentX)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder, upperZ, lowerZ, flatField,  mmc)
        iteration = iteration + 1
    os.chdir(initialDir)
    return imageHeightArray, imageWidthArray


########################### useless things #################################################


"""def getOverviewAndStitchOverlap(RightX, LeftX, BottomY, TopY, flatField,  mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/(20*.63) ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## initialize the size of one row 
    rowWidth = math.ceil(abs((RightX -imageWidthUM/2) - (LeftX + imageWidthUM/2))/imageWidthUM/.9)*imageWidth  ## to get an integer number of imageWidths in a row
    image = np.empty([0, int(rowWidth)])
    ## get the number of images that will be taken and make an array with that many
    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/.9) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/.9) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*.9, BottomY-imageHeightUM*.9)
    print imageHeightArray
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*.9, RightX)
    print imageWidthArray
    ### Start in upper left corner and go to the bottom left
    for y in range(len(imageHeightArray)-1, -1, -1): ## go from top down, 0 indexed
        ## make folder for this Y coordinate
        currentY = imageHeightArray[y]
        if(iteration%2==0): ## it is an even iteration
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from Right to left
            for x in range(0, len(imageWidthArray)): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                print "moving to", currentX, currentY
                mmc.setXYPosition(currentX, currentY) 
                mmc.snapImage() 
                array = mmc.getImage()
                array = flatFieldCorrection(flatField, array, mmc)
                row = np.concatenate((row, array), axis= 1)
                #Image.fromarray(row).show()
            image = np.concatenate((image, row), axis = 0)
            #Image.fromarray(image).show()
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in range(len(imageWidthArray)-1, -1, -1): 
                ## go to correct x,y location
                currentX = imageWidthArray[x]
                mmc.setXYPosition(currentX, currentY) 
                mmc.snapImage() 
                array = mmc.getImage()
                array = flatFieldCorrection(flatField, array, mmc)
                row = np.concatenate((array, row), axis = 1)
                #Image.fromarray(row).show()
            image = np.concatenate((image, row), axis = 0)
            #Image.fromarray(image).show() 
        iteration = iteration+1
    ## save
    imsave("StitchedOverviewCorrectedOverlap.tiff", image)"""

"""def getOverviewAndSaveZ(FolderToSaveTo, RightX, LeftX, BottomY, TopY, upperZ, lowerZ, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration
    iteration = 0
    ### go into correct folder
    initialDir = os.getcwd()
    if not os.path.exists(FolderToSaveTo):
            os.makedirs(FolderToSaveTo)
    os.chdir(FolderToSaveTo)
    ### Start in upper left corner and go to the bottom left
    for y in np.arange((TopY - imageHeightUM/2), (BottomY + imageHeightUM/2), imageHeightUM): ## go from top down, should add + imageHeightUM to bottomY so that there's no error when adding 
        ## make folder for this Y coordinate
        folder = str(y)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if(iteration%2==0): ## it is an even iteration
            ## go from Right to left
            for x in np.arange((RightX - imageWidthUM/2), (LeftX + imageWidthUM/2), imageWidthUM): 
                mmc.setXYPosition(x, y)
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(x)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder, upperZ, lowerZ, mmc)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(x)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder, upperZ, lowerZ, mmc)
        iteration = iteration + 1
    os.chdir(initialDir)"""

"""def getOverviewAndSaveXY(FolderToSaveTo, RightX, LeftX, BottomY, TopY, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    ## relevant info
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration
    iteration = 0
    ## go into correct directory
    initialDir = os.getcwd()
    if not os.path.exists(FolderToSaveTo):
            os.makedirs(FolderToSaveTo)
    os.chdir(FolderToSaveTo)
    ### Start in upper left corner and go to the bottom left
    for y in np.arange((TopY - imageHeightUM/2), (BottomY + imageHeightUM/2), imageHeightUM): ## go from top down, should add + imageHeightUM to bottomY so that there's no error when adding 
        ## make folder for this Y coordinate
        folder = str(y)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if(iteration%2==0): ## it is an even iteration
            ## go from Right to left
            for x in np.arange((RightX - imageWidthUM/2), (LeftX + imageWidthUM/2), imageWidthUM): 
                mmc.setXYPosition(x, y)              ## make folder for this X coordinate
                filename = folder + "/" + "layer" + str(x) + ".tiff"
                ## move and take photo
                mmc.setXYPosition(x, y)
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer[singleLayer >= 255] = 255
                ## save tiff at the filename
                singleLayer = Image.fromarray(singleLayer.astype('uint8'))
                singleLayer.save(filename)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                ## make folder for this X coordinate
                filename = folder + "/" + "layer" + str(x) + ".tiff"
                ## move and take photo
                mmc.setXYPosition(x, y)
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer[singleLayer >= 255] = 255
                ## save tiff at the filename
                singleLayer = Image.fromarray(singleLayer.astype('uint8'))
                singleLayer.save(filename)
        iteration = iteration + 1
    ## go back to initial working directory for the next step
    os.chdir(initialDir)"""

"""## Get x and y files at one layer
def getUserInputOverviewandSave():
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
     ##get region of interest
    raw_input("Go to the leftmost area of the region of interest and press enter to continue")
    LeftX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the rightmost area of the region of interest and press enter to continue")
    RightX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the upper most area of the region of interest and press enter to continue")
    TopY = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the lower most area of the region of interest and press enter to continue")
    BottomY = mmc.getYPosition("ZeissXYStage")
    ## relevant info
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration
    iteration = 0
    ## go into correct directory
    os.chdir("OverviewTest")
    ### Start in upper left corner and go to the bottom left
    for y in np.arange((TopY - imageHeightUM/2), (BottomY + imageHeightUM/2), imageHeightUM): ## go from top down, should add + imageHeightUM to bottomY so that there's no error when adding 
        ## make folder for this Y coordinate
        folder = str(y)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if(iteration%2==0): ## it is an even iteration
            ## go from Right to left
            for x in np.arange((RightX - imageWidthUM/2), (LeftX + imageWidthUM/2), imageWidthUM): 
                mmc.setXYPosition(x, y)              ## make folder for this X coordinate
                filename = folder + "/" + "layer" + str(x) + ".tiff"
                ## move and take photo
                mmc.setXYPosition(x, y)
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer[singleLayer >= 255] = 255
                ## save tiff at the filename
                singleLayer = Image.fromarray(singleLayer.astype('uint8'))
                singleLayer.save(filename)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                ## make folder for this X coordinate
                filename = folder + "/" + "layer" + str(x) + ".tiff"
                ## move and take photo
                mmc.setXYPosition(x, y)
                mmc.snapImage()
                singleLayer = mmc.getImage()
                singleLayer[singleLayer >= 255] = 255
                ## save tiff at the filename
                singleLayer = Image.fromarray(singleLayer.astype('uint8'))
                singleLayer.save(filename)
        iteration = iteration + 1 """

"""def userInputOverview():
    ##load the microscope
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    ##set z position so it is in focus
    raw_input("Set Z stage to a focused area and press enter to continue")
    ##get region of interest
    raw_input("Go to the leftmost area of the region of interest and press enter to continue")
    LeftX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the rightmost area of the region of interest and press enter to continue")
    RightX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the upper most area of the region of interest and press enter to continue")
    TopY = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the lower most area of the region of interest and press enter to continue")
    BottomY = mmc.getYPosition("ZeissXYStage")
    ##find out how far we should go each picture
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration, intitalize the row which will be concatenated
    iteration = 0
    ## initialize the size of one row 
    rowWidth = math.ceil(abs((RightX -imageWidthUM/2) - (LeftX + imageWidthUM/2))/imageWidthUM)*imageWidth  ## to get an integer number of imageWidths in a row
    image = np.empty([0, int(rowWidth)])
    ### Start in upper left corner and go to the bottom left
    for y in np.arange((TopY - imageHeightUM/2), (BottomY + imageHeightUM/2), imageHeightUM): ## go from top down, should add + imageHeightUM to bottomY so that there's no error when adding 
        if(iteration%2==0): ## it is an even iteration
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from Right to left
            for x in np.arange((RightX - imageWidthUM/2), (LeftX + imageWidthUM/2), imageWidthUM): 
                mmc.setXYPosition(x, y)
                mmc.waitForImageSynchro()
                mmc.snapImage() 
                array = mmc.getImage()
                row = np.concatenate((row, array), axis=1)
                Image.fromarray(row).show()
            image = np.concatenate((row, image), axis = 0)
            Image.fromarray(image).show()
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                mmc.setXYPosition(x, y)
                mmc.waitForImageSynchro()
                mmc.snapImage() 
                array = mmc.getImage()
                row = np.concatenate((array, row), axis = 1)
                Image.fromarray(row).show()
            image = np.concatenate((row, image), axis = 0)
            Image.fromarray(image).show() 
        iteration = iteration+1
    ## display
    displayStitched = Image.fromarray(image)
    displayStitched.show() """



"""def getUserInputOverviewandSave():
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
     ##get region of interest
    raw_input("Go to the leftmost area of the region of interest and press enter to continue")
    LeftX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the rightmost area of the region of interest and press enter to continue")
    RightX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the upper most area of the region of interest and press enter to continue")
    TopY = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the lower most area of the region of interest and press enter to continue")
    BottomY = mmc.getYPosition("ZeissXYStage")
    ## relevant info
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = 3.45/20 ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
    ### intialize iteration
    iteration = 0
    ## go into correct directory
    os.chdir("OverviewTest")
    ### Start in upper left corner and go to the bottom left
    for y in np.arange((TopY - imageHeightUM/2), (BottomY + imageHeightUM/2), imageHeightUM): ## go from top down, should add + imageHeightUM to bottomY so that there's no error when adding 
        ## make folder for this Y coordinate
        folder = str(y)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if(iteration%2==0): ## it is an even iteration
            ## go from Right to left
            for x in np.arange((RightX - imageWidthUM/2), (LeftX + imageWidthUM/2), imageWidthUM): 
                mmc.setXYPosition(x, y)
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(x)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(x)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder)
        iteration = iteration + 1

def folderTest():
    os.chdir("OverviewTest")
    for y in range(0, 2, 1):
        folder = str(y)
        if not os.path.exists(folder):
            os.makedirs(folder)
        for x in range(0, 2, 1):
            subfolder = folder + "/" + str(x)
            if not os.path.exists(subfolder):
                os.makedirs(subfolder)
            for z in range(0,2,1):
                filename = subfolder + "/" + "layer" + str(z) + ".tiff"
                image = np.zeros((2,2))
                imsave(filename, image) """

