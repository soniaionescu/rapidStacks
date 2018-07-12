import numpy as np
import MMCorePy

import numpy as np
import cv2 
import matplotlib.pyplot as plt
import os
from PIL import Image
import shutil
import glob

## test for array indexing in doWeEnd
array = np.array([[1,15],[3,12]])
maxX = array[:,0].max()
maxY = array[:,1].max()
minX = array[:,0].min()
minY = array[:,1].min()
initialXY = array[0,:]
currentXY = array[array.shape[1]-1,:]
movementList = np.array(['right', 'left', 'right', 'left'])
movementList = np.append(movementList, 'left')
movement = np.repeat(['up'], 5)
rangeOfFocus = np.empty([0]) 
array = np.array([1])
rangeOfFocus = np.concatenate((rangeOfFocus, array), axis = 0)
arraycv = np.array([[1,2],[3,4]])
cvl1 = np.zeros([2,2])
cvl2 = np.zeros([2,2])
threeLayer = np.empty([3,2,2])
threeLayer[0,:,:] = arraycv
threeLayer[1,:,:] = cvl1
threeLayer[2,:,:] = cvl2
coordinatesList = np.array([[1,2]])
coordinatesList = np.concatenate((coordinatesList, np.array([[3, 4]])), axis=0)
coordinatesList = np.concatenate((coordinatesList, np.array([[5, 6]])), axis=0)
coordinatesList = np.concatenate((coordinatesList, np.array([[7, 8]])), axis=0)
initialXY = coordinatesList[0,:]
currentXY = coordinatesList[coordinatesList.shape[0]-1,:]

def renameFiles(rootFolder):
    ## go through and find all x folders and all y folders
    listOfY = np.empty([0])
    listOfX = np.empty([0])
    listOfZ = np.empty([0])
    for root, yFolders, zTiffs in os.walk(rootFolder):
        for yFolder in yFolders:
            ## only go through subdirectories with two layers (y folders)
            if len(os.path.relpath(yFolder)) is not 9:
                subdirPath = os.path.join(root, yFolder)
                listOfY = np.append(listOfY, yFolder)
                ## go through each file
                for yFolderPath, xFolders, zTiffs, in os.walk(subdirPath):
                    ## read the image and compute the variance
                    for xFolder in xFolders:
                        listOfX = np.append(listOfX, xFolder)
                    for zTiff in zTiffs:
                        listOfZ = np.append(listOfZ, zTiff.rstrip(".tiff"))
    ## print statements
    ## find minimum of each list
    # for Y List
    listOfYFloat = listOfY.astype(np.float)
    minY = np.amin(listOfYFloat)
    # for X List
    listOfXFloat = listOfX.astype(np.float)
    minX = np.amin(listOfXFloat)
    # for Z List
    listOfZFloat = listOfZ.astype(np.float)
    minZ = np.amin(listOfZFloat)
    ## walk again, now renaming
    for root, yFolders, zTiffs in os.walk(rootFolder):
        for yFolder in yFolders:
            ## only go through subdirectories with two layers (y folders)
            if len(os.path.relpath(yFolder)) is not 9:
                ## find relative path
                subdirPath = os.path.join(root, yFolder)
                ## set permision
                os.chmod(subdirPath, 644)
                ## find correct name
                yFolderPositive = (float(yFolder) - minY)*10
                yFolderSplit = str(yFolderPositive).split(".")
                yFolderPositiveInt = yFolderSplit[0]
                yFolderPadded = yFolderPositiveInt.zfill(6)
                # rename
                print "renaming ", yFolder, "to", yFolderPadded
                renameYTo = os.path.join(root, yFolderPadded)
                try:
                    os.rename(subdirPath, renameYTo)
                except IOError:
                    print "permission denied"
                ## go through each x Folder
                for yFolderPath, xFolders, zTiffs, in os.walk(renameYTo):
                    for xFolder in xFolders:
                        ## get the full path of the x folde
                        xFolderPath = os.path.join(yFolderPath, xFolder)
                        ## get the new name of the x folder
                        xFolderPositive = (float(xFolder) - minX)*10
                        xFolderSplit = str(xFolderPositive).split(".")
                        xFolderPositiveInt = xFolderSplit[0]*10
                        if len(str(xFolderPositiveInt)) < 6:
                            xFolderPadded = xFolderPositiveInt.zfill(6)
                        else:
                            xFolderPadded = xFolderPositiveInt[:6]
                        ## append yFolder _ xFolder
                        xFull = yFolderPadded + "_" + xFolderPadded
                        print "renaming ", xFolder, "to", xFull
                        ## rename
                        renameXTo = os.path.join(yFolderPath, xFull)
                        try:
                            os.rename(xFolderPath, renameXTo)
                        except IOError:
                            print "permission denied"
                        ## go through each tiff
                        for xFolderPathRoot, subdirs, zTiffs in os.walk(renameXTo):
                            for zTiff in zTiffs:
                                ## get the full path of the tiff
                                zTiffPath = os.path.join(renameXTo, zTiff)
                                ## find the new name
                                zFolderPositive = (float(zTiff.rstrip(".tiff")) - minZ)*10
                                zFolderSplit = str(zFolderPositive).split(".")
                                zFolderPositiveInt = zFolderSplit[0]
                                zFolderPadded = zFolderPositiveInt.zfill(6)
                                zTiffFull = str(zFolderPadded) + ".tiff"
                                print "renaming ", zTiff, "to", zFolderPadded
                                ## rename
                                renameZTo = os.path.join(renameXTo, zTiffFull)
                                try:
                                    os.rename(zTiffPath, renameZTo)
                                except IOError:
                                    print "permission denied"
