import MMCorePy
import numpy as np
from PIL import Image
from scipy import ndimage
from imread import imsave
import math
import os
import time
import csv
## import the necessary functions
from test20xOverview import getOverviewAndSaveMIP
from test20xStackToTiff import makeMIP
from test20xEdgeDetection import edgeDetectedOverview, findSample
from test20xZEdgeDetection import zLimits
from testRenameForTeraStitcher import renameTiffFolders
from test20xFluorescenceAcquisition import fluorescenceAcquisition
from testImageProcessing import moveForFlatField
from test20xConfiguration import Configuration



""" purpose: ##Goal: take an overview of one brain, finding the edges and outputting folders of y coordinates which each countain folders of x 
            coordinates which contain z stacks as well as a focus spline
    inputs: the name of the slide, the resolution desired of the stitched image
    returns: nothing
    saves: a y/x/mip.tiff folder, a stitched overview image, a y/x/dapi.tiff folder, a fluorescence image, and if configuration.saveImages == True, a subfolder in folderNameMIP of every plane of every z stack of an acquisition.
"""

def oneSlide(slideName, mmc):
    ## get configuration
    configuration = Configuration()
    ## set properties to get 16 bit images and avoid tunneling
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    ## go to some z limit in the middle in the hopes that things won't be horribly out of focus
    middleZ = extremeUpperZ - (extremeUpperZ - extremeLowerZ)/2
    mmc.setPosition(middleZ)
    ## get 16 points to try to find sample
    sampleFound = findSample(mmc)
    ## if sample was found, find focus (not worth doing if no sample was found because there's nothing to focus on)
    if sampleFound == 'true':
        lowerZ, upperZ = zLimits(mmc)
    ## get flatfield and darkfield
    flatField = moveForFlatField(mmc)
    ## get coordinates needed to take an overview (should find sample if sample was not found before)
    coordinates = edgeDetectedOverview(mmc)
    LeftX = coordinates[0]
    RightX = coordinates[1] 
    TopY = coordinates[2] 
    BottomY = coordinates[3]
    ## can now get focus because the sample has definitely been found
    if sampleFound == 'false':
        ## go to somewhere within the sample
        mmc.setXYPosition((LeftX - RightX), (TopY - BottomY))
        lowerZ, upperZ = zLimits(mmc)
    ## create z stack spline
    folderNameMIP = slideName + "MIPS"
    coordinateList = getOverviewAndSaveMIP(folderNameMIP, RightX, LeftX, BottomY, TopY, upperZ, lowerZ, flatField, mmc)
    ## rename all the folders to be in the FFFFFF -> FFFFFF_SSSSSS -> ZZZZZZ.tiff file required by TeraStitcher
    renameTiffFolders(folderNameMIP)
    ## get the fluorescence image
    folderNameFluorescence = slideName + "Fluorescence"
    ## get DAPI flatfield
    flatFieldfileName = "DAPIFlatfield.csv"
    DAPIflatField = np.genfromtxt(flatFieldfileName, delimiter=",")
    fluorescenceAcquisition(coordinateList, folderNameFluorescence, DAPIflatField, mmc) 
    ## rename all the folders to be in the FFFFFF -> FFFFFF_SSSSSS -> ZZZZZZ.tiff file required by TeraStitcher
    renameTiffFolders(folderNameFluorescence)
    ## stitch in tera stitcher
    pixelSize = mmc.getPixelSizeUm()
    if configuration.saveImages == False:
        os.system('terastitcher --import -volin="{}" --ref1=-Y --ref2=X --ref3=Z --vxl1={} --vxl2={} --vxl3={} --projout=xml_import'.format(os.path.abspath(folderNameMIP), pixelSize, pixelSize, configuration.zStep))
        os.system('terastitcher --displcompute --projin="{}"'.format(os.path.abspath(folderNameMIP + r"\xml_import.xml")))
        os.system('terastitcher --displproj --projin="{}"'.format(os.path.abspath(folderNameMIP + r"\xml_displcomp.xml")))
        os.system('terastitcher --displthres --threshold={} --projin="{}"'.format(configuration.threshhold, os.path.abspath( folderNameMIP + r"\xml_displproj.xml")))
        os.system('terastitcher --placetiles --projin="{}"'.format(os.path.abspath(folderNameMIP + r"\xml_displthres.xml")))
        stitchedFolder = folderNameMIP + r"\stitched"
        if not os.path.exists(stitchedFolder):
            os.makedirs(stitchedFolder)
        os.system('terastitcher --merge -projin="{}" -volout="{}" -volout_plugin="TiledXY|2Dseries"'.format(os.path.abspath(folderNameMIP + r"\xml_merging.xml"), os.path.abspath(stitchedFolder)))
    ## stitch in tera stitcher if all the images of MIPS were saved
    if configuration.saveImages == True:
        folderNameMIPSaved = folderNameMIP + "/savedImages"
        os.system('terastitcher --import --volin="{}" --ref1=-Y --ref2=X --ref3=Z --vxl1={} --vxl2={} --vxl3={} --projout=xml_import'.format(os.path.abspath(folderNameMIPSaved), pixelSize, pixelSize, configuration.zStep))
        os.system('terastitcher --displcompute --projin="{}"'.format(os.path.abspath(folderNameMIPSaved  + r"\xml_import.xml")))
        os.system('terastitcher --displproj --projin="{}"'.format(os.path.abspath(folderNameMIPSaved  + r"\xml_displcomp.xml")))
        os.system('terastitcher --displthres --threshold={} --projin="{}"'.format(configuration.threshhold, os.path.abspath( folderNameMIPSaved  + r"\xml_displproj.xml")))
        os.system('terastitcher --placetiles --projin="{}"'.format(os.path.abspath(folderNameMIPSaved  + r"\xml_displthres.xml")))
        stitchedFolder = folderNameMIPSaved  + r"\stitched"
        if not os.path.exists(stitchedFolder):
            os.makedirs(stitchedFolder)
        os.system('terastitcher --merge --projin="{}" --volout="{}" --volout_plugin="TiledXY|2Dseries"'.format(os.path.abspath(folderNameMIPSaved + r"\xml_merging.xml"), os.path.abspath(stitchedFolder)))
    ## stitch DAPI in tera stitcher
    os.system('terastitcher --import --volin="{}" --ref1=-Y --ref2=X --ref3=Z --vxl1={} --vxl2={} --vxl3={} --projout=xml_import'.format(os.path.abspath(folderNameFluorescence), pixelSize, pixelSize, configuration.zStep))
    os.system('terastitcher --displcompute --projin="{}"'.format(os.path.abspath(folderNameFluorescence + r"\xml_import.xml")))
    os.system('terastitcher --displproj --projin="{}"'.format(os.path.abspath(folderNameFluorescence + r"\xml_displcomp.xml")))
    os.system('terastitcher --displthres --threshold={} --projin="{}"'.format(configuration.threshhold, os.path.abspath(folderNameFluorescence + r"\xml_displproj.xml")))
    os.system('terastitcher --placetiles --projin="{}"'.format(os.path.abspath(folderNameMIP + r"\xml_displthres.xml")))
    stitchedFolder = folderNameFluorescence + r"\stitched"
    if not os.path.exists(stitchedFolder):
        os.makedirs(stitchedFolder)
    os.system('terastitcher --merge --projin="{}" --volout="{}" --volout_plugin="TiledXY|2Dseries"'.format(os.path.abspath(folderNameFluorescence + r"\xml_merging.xml"), os.path.abspath(stitchedFolder)))
if __name__ == '__main__':
    ## load configuration
    configuration = Configuration()
    ## load microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    ## get information for setting configuration
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    # set settings
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)
    LeftX = 798
    RightX = -10280
    TopY = 106
    BottomY = -7028
    upperZ = 70
    lowerZ = -19
    extremeUpperZ = 135
    extremeLowerZ = -123
    highestFocusZ = -50
    start_time = time.time()
    flatField = moveForFlatField(mmc)
    start_time = time.time()
    #makeMIP(70, -19, flatField, mmc)
    resolution = configuration.resolution
    configuration = Configuration()
    notOverlap = configuration.notOverlap
    xyzTuple = getOverviewAndSaveMIP("810MIPOverview", RightX, LeftX, BottomY, TopY, upperZ, lowerZ, flatField,  mmc)
    print "%s seconds to create overall MIP overview" % (time.time() - start_time)
    csvfile = "XYZCoord.csv"
    #save xyzTuple to csv so I can use it for DAPI image 
    with open(csvfile, "w") as output:
        writer = csv.writer(output)
        for val in xyzTuple:
            writer.writerow([val])


################################################ useless stuff ################################################################################



"""def oneSlide(slideName):
    ## set a reasonable focus
    ## get 16 points to try to find sample
    ## get coordinates needed to take an overview
    coordinates = edgeDetectedOverview(mmc)
    LeftX = coordinates[0]
    RightX = coordinates[1] 
    TopY = coordinates[2] 
    BottomY = coordinates[3]
    ## take overview, output is x images which are in y folders
    folderNameXY = slideName + "XYOverview"
    getOverviewAndSaveXY(folderNameXY, RightX, LeftX, BottomY, TopY, mmc)
    ## detect which picture is most likely to have a neuron in it
    mostLikelyPath = repr(NeuronDetection(folderNameXY)) ##(pass in a string literal since there are slashes)
    mostLikelyPathFolder = mostLikelyPath.replace(".tiff", "")
    ## find x and y position where there was most likely to be a neuron
    xy = mostLikelyPath.split("\\")
    print xy
    ## strip the x "coordinate" to just the number
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
    folderNameZ = slideName + "zStacks"
    getOverviewAndSaveZ(folderNameZ, RightX, LeftX, BottomY, TopY, upperZ, lowerZ, mmc)
    ## rename all the folders to be in the FFFFFF -> FFFFFF_SSSSSS -> ZZZZZZ.tiff file required by TeraStitcher
    renameFiles(folderNameZ)
    ## make the focus spline
    folderNameSpline = slideName + "FocusSpline"
    createFocusSpline(folderNameSpline)"""
    
## possible improvements
# SURF doesn't work that well because it also detects corners which are numerous where there's a tear or segmentation in the brain
## maybe it would be better to use simple blob detection
# not renaming the files
## but then going to xy position based off of file name doesn't work b/c there's fewer sigfigs
## also renaming the files is pretty fast
# only looking within a certain range of the most focused z stack for the focus spline
## how do we know this range

