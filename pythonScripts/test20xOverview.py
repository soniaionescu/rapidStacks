import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import math
import matplotlib.pyplot as plt
from skimage import data
from skimage.feature import canny
from scipy import ndimage as ndi
from test20xStackToTiff import zStackTiffs
import os
from tifffile import imsave

#Load devices
#mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

#Goal: get a 20x overview of an area with z stacks

## Get x and y files at one layer
def getOverviewAndSaveXY(RightX, LeftX, BottomY, TopY, mmc):
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
        iteration = iteration + 1

## get x y and z pictures
def getOverviewAndSaveZ(RightX, LeftX, BottomY, TopY, upperZ, lowerZ, mmc):
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
                zStackTiffs(subfolder, upperZ, lowerZ)
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                ## make folder for this X coordinate
                subfolder = folder + "/" + str(x)
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)
                zStackTiffs(subfolder, upperZ, lowerZ)
        iteration = iteration + 1

## Get x and y files at one layer
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
        iteration = iteration + 1

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
    displayStitched.show()

def getOverviewAndStitch(RightX, LeftX, BottomY, TopY):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
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
                mmc.sleep(500)
                mmc.snapImage() 
                array = mmc.getImage()
                row = np.concatenate((row, array), axis=1)
                # Image.fromarray(row).show()
            image = np.concatenate((row, image), axis = 0)
            #Image.fromarray(image).show()
        else:
            ## initialize the row
            row = np.empty([imageHeight, 0])
            ## go from left to right
            for x in np.arange((LeftX+ imageWidthUM/2), (RightX - imageWidthUM/2), - imageWidthUM): ##go from Left to Right
                mmc.setXYPosition(x, y)
                mmc.sleep(500)
                mmc.snapImage() 
                array = mmc.getImage()
                row = np.concatenate((array, row), axis = 1)
            # Image.fromarray(row).show()
            image = np.concatenate((row, image), axis = 0)
            # Image.fromarray(image).show() 
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

