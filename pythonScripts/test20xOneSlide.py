import MMCorePy
import numpy as np
from PIL import Image
from scipy import ndimage
import math
import os


## import the necessary functions
from test20xOverview import getOverviewAndSaveXY, getOverviewAndSaveZ
from test20xStackToTiff import zStackTiffs
#from test20xEdgeDetection import edgeDetectedOverview
from test20xFocusFinder import findFocusLayerVLPictureCreation, createFocusSpline
from test20xFeatureDetection import blurImage, TCISURFwBlur, NeuronDetection

##Goal: take an overview of one brain, finding the edges and outputting folders of y coordinates which each countain folders of x coordinates which contain z stacks
## as well as a focus spline

## load microscope -- should ONLY be done here
mmc = MMCorePy.CMMCore()
mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

def oneSlide(slideName):
    ## get coordinates needed to take an overview
    coordinates = edgeDetectedOverview()
    LeftX = coordinates[0]
    RightX = coordinates[1] 
    TopY = coordinates[2] 
    BottomY = coordinates[3]
    ## take overview, output is x images which are in y folders
    getOverviewAndSaveXY(RightX, LeftX, BottomY, TopY, mmc)
    ## detect which picture is most likely to have a neuron in it
    mostLikelyPath = repr(NeuronDetection()) ##(pass in a string literal since there are slashes)
    mostLikelyPathFolder = mostLikelyPath.replace(".tiff", "")
    ## find x and y position where there was most likely to be a neuron
    xy = mostLikelyPath.split("\\")
    print xy
    xy[3] = xy[3].replace("layer", "")
    xy[3] = xy[3]. replace(".tiff", "")
    ## 3 and 2 because the x is at the end and the y is in the middle and they are two folders deep
    x = float(xy[3])
    print x
    y = float(xy[2])
    print y
    ## make a folder for that x position
    if not os.path.exists(mostLikelyPathFolder):
        os.makedirs(mostLikelyPathFolder)
    ## move to that xy position
    mmc.setXYPosition(x, y)
    ## take a Z stack and see where there is the best focus
    focusedZ = findFocusLayerVLPictureCreation(mostLikelyPathFolder, 30, -30, mmc) ## arbitrary range, can be changed
    ## set a range with this focused area
    upperZ = focusedZ + 15
    lowerZ = focusedZ - 15
    ## get overview with z stacks at appropriate position
    getOverviewAndSaveZ(RightX, LeftX, BottomY, TopY, upperZ, lowerZ, mmc)
    ## rename all the folders to be in the FFFFFF -> FFFFFF_SSSSSS -> ZZZZZZ.tiff file required by TeraStitcher
    renameFiles("OverviewTest")
    ## make the focus spline
    createFocusSpline(slideName)
    
oneSlide("exampleSlide")

