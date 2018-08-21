import MMCorePy
from testImageProcessing import moveForFlatField
from test63xConfiguration import Configuration
from test63xzStackAcquisition import acquireZStack
from testRenameForTeraStitcher import renameTiffFolders
import numpy as np
import os
import math

def getZStackAndStitch(FolderToSaveTo,  LeftX, RightX, TopY, BottomY, lowerZ, upperZ, flatField, mmc):
    mmc.assignImageSynchro('ZeissXYStage')
    mmc.assignImageSynchro('IDS uEye')
    configuration = Configuration()
    ## get important values
    notOverlap = configuration.notOverlap
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm() ## for ids uEye at 20x magnification
    imageWidthUM = pixelSize*imageWidth 
    imageHeightUM = pixelSize*imageHeight 
     ##get region of interest

    numberImagesRow = math.ceil(abs((RightX) - (LeftX))/imageWidthUM/notOverlap) + 1
    numberImagesColumn = math.ceil(abs((TopY) - (BottomY))/imageHeightUM/notOverlap) + 2
    numberImagesArrayRow = np.arange(0, numberImagesRow)
    numberImagesArrayColumn = np.arange(0, numberImagesColumn)
    ## make an array with all the X and Y coordinates (need to start at RightX and BottomY)
    imageHeightArray = np.add(numberImagesArrayColumn*imageHeightUM*notOverlap, BottomY-imageHeightUM*notOverlap)
    imageWidthArray = np.add(numberImagesArrayRow*imageWidthUM*notOverlap, RightX)
    ### intialize iteration
    iteration = 0
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
                acquireZStack(upperZ, lowerZ, mmc, folder, flatField)
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
                acquireZStack(upperZ, lowerZ, mmc, folder, flatField)
        iteration = iteration + 1
    os.chdir(initialDir)

def getInput():
    raw_input("Go to the leftmost area of the region of interest and press enter to continue")
    LeftX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the rightmost area of the region of interest and press enter to continue")
    RightX = mmc.getXPosition("ZeissXYStage")
    raw_input("Go to the top (Y) most area of the region of interest and press enter to continue")
    TopY = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the bottom (Y) most area of the region of interest and press enter to continue")
    BottomY = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the lower most (Z) area of the region of interest and press enter to continue")
    lowerZ = mmc.getYPosition("ZeissXYStage")
    raw_input("Go to the upper most (Y) area of the region of interest and press enter to continue")
    upperZ = mmc.getYPosition("ZeissXYStage")
    return LeftX, RightX, TopY, BottomY, lowerZ, upperZ

if __name__ == '__main__':

    configuration = Configuration()
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    pixelSize = mmc.getPixelSizeUm()
    ## set properties to get 16 bit images and avoid tunneling
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    ## get flatfield
    flatfield = moveForFlatField(mmc)
    ## get images of z stack
    Slidename = "slideName"
    LeftX, RightX, TopY, BottomY, lowerZ, upperZ = getInput()
    getZStackAndStitch(Slidename, LeftX, RightX, TopY, BottomY, lowerZ, upperZ, flatfield, mmc)
    ## rename for Tera Stitcher
    renameTiffFolders(Slidename)
    ## stitch in tera stitcher
    os.system('terastitcher --import -volin="{}" -ref1=-Y -ref2=X -ref3=Z -vxl1={} -vxl2={} -vxl3={} -projout=xml_import'.format(os.path.abspath(Slidename), pixelSize, pixelSize, configuration.zStep))
    os.system('terastitcher --displcompute -projin="{}"'.format(os.path.abspath(Slidename + r"\xml_import.xml")))
    os.system('terastitcher --displproj -projin="{}"'.format(os.path.abspath(Slidename + r"\xml_displcomp.xml")))
    os.system('terastitcher --displthres -threshold={} -projin="{}"'.format(configuration.threshhold, os.path.abspath(Slidename + r"\xml_displproj.xml")))
    os.system('terastitcher --placetiles -projin="{}"'.format(os.path.abspath(Slidename + r"\xml_displthres.xml")))
    stitchedFolder = Slidename + r"\stitched"
    if not os.path.exists(stitchedFolder):
         os.makedirs(stitchedFolder)
    os.system('terastitcher --merge -projin="{}" -volout="{}" -volout_plugin="TiledXY|2Dseries"'.format(os.path.abspath(Slidename + r"\xml_merging.xml"), os.path.abspath(stitchedFolder)))
