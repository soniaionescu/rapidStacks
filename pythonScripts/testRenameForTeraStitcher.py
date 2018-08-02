import numpy as np
import MMCorePy

import numpy as np
import cv2 
import matplotlib.pyplot as plt
import os
from PIL import Image
import shutil
import glob
from pathlib2 import *
import warnings

############################### functional renaming function ################################

"""
Created on Fri Jul 27 10:01:05 2018

Rename child folders and files to fit TeraStitcher format requirements.
Assume files are arranged in proper two-level hierarchy, 
    but with values as raw coordinates.  
Rename all to comply with Terastitcher format

@author: rustyn
"""

import os
import numpy as np
import warnings

def renameAllTIFFFiles(newChildren):
    
    # This entry is only files, not folders
    # Data is TIFF planes
    # Rename as ZZZZZZ.tif
    fNames = np.array([x.rsplit('.', 1)[0] for x in newChildren[2]]).astype(np.float)
    newNames = np.round(fNames - np.amin(fNames), 1)*10
    
    for k in range(len(newChildren[2])):
        os.rename(os.path.join(newChildren[0], newChildren[2][k]), os.path.join(newChildren[0], format(int(newNames[k]), '06d') + '.tif'))
    

def renameTiffFolders(baseFolder):
    # Rename child folders and files
    # Assume files are arranged in proper two-level hierarchy, but with raw coordinates
    # Reformat to Terastitcher-compatible format
    
    # Need Y names before we can do anything else later
    # Calc but don't rename folder yet
    files = os.walk(baseFolder, topdown=True)
    newChildren = next(files)[1]
    yNames = np.array(newChildren).astype(np.float)
    yModNames = np.round(yNames - np.amin(yNames), 1)*10
    
    # Regen tree from bottom-up direction
    files = os.walk(baseFolder, topdown=False)
    
    # Walk from bottom up through files and folders to do renaming
    for newChildren in files:
    #newChildren = next(files)
    
        if ((len(newChildren[1]) == 0) and (len(newChildren[2]) > 0)):
            renameAllTIFFFiles(newChildren)
        
        elif (len(newChildren[1]) > 0):
            # Is subfolders
            # Rename as appropriate
            
            if (newChildren[0] == baseFolder):
                # Is first level of children
                # Y coordinate; name as YYYYYY
                newNames = np.array(newChildren[1]).astype(np.float)
                newNames = np.round(newNames - np.amin(newNames), 1)*10
                
                for k in range(len(newChildren[1])):
                    os.rename(os.path.join(newChildren[0], newChildren[1][k]), os.path.join(newChildren[0], format(int(newNames[k]), '06d')))
                    
            else:
                # Is second level of children
                # X coordinate; rename as YYYYY_XXXXXX
                
                # Check if already in TeraStitcher format
                if any([(x.find('_')) > 0 for x in newChildren[1]]):
                    warnings.warn('Folder has already been processed. Skipping')
              
                else:
                    # Figure out which Y coordinate is needed
                    base, yFolder = os.path.split(newChildren[0])
                    yFoldHere = yModNames[yNames == float(yFolder)][0]
                    
                    # Gen corresponding X names
                    newNames = np.array(newChildren[1]).astype(np.float)
                    newNames = np.round(newNames - np.amin(newNames), 1)*10
                    
                    for k in range(len(newChildren[1])):
                        os.rename(os.path.join(newChildren[0], newChildren[1][k]), 
                                  os.path.join(newChildren[0], format(int(yFoldHere), '06d') + '_' + format(int(newNames[k]), '06d')))


################################## useless stuff ###########################################

""" purpose: to rename folders in the necessary way for Tera Stitcher
    inputs: the name of the root folder in which the X/Y/Z.tiff's should be renamed
    returns: Nothing
    saves: Doesn't save anything, but renames things which have already been saved
"""

"""def renameFiles(rootFolder):
    ## get initial folder
    initialDir = os.getcwd()
    ## go to rootFolder
    os.chdir(rootFolder)
    ## go through and find all x folders and all y folders
    listOfY = np.empty([0])
    listOfX = np.empty([0])
    listOfZ = np.empty([0])
    ## get y folders
    yFolders = [y for y in os.listdir('.') if os.path.isdir(y)]
    for yFolder in yFolders:
        ## add yFolders to list of yFolders
        listOfY = np.append(listOfY, yFolder)
        ## walk each y folder
        for root, xFolders, zTiffs in os.walk(yFolder):
            for xFolder in xFolders:
                listOfX = np.append(listOfX, xFolder)
            for zTiff in zTiffs:
                listOfZ = np.append(listOfZ, zTiff.rstrip(".tiff"))
  
    ## print statements
    ## find minimum of each list
    # for Y List
    print listOfY
    listOfYFloat = listOfY.astype(np.float)
    minY = np.amin(listOfYFloat)
    print minY
    # for X List
    print listOfX
    listOfXFloat = listOfX.astype(np.float)
    minX = np.amin(listOfXFloat)
    print minX
    # for Z List
    listOfZFloat = listOfZ.astype(np.float)
    minZ = np.amin(listOfZFloat)
    print minZ
    ## walk again, now renaming
    for yFolder in yFolders:
        ## find relative path
        subdirPath = os.path.relpath(yFolder)
        ## set permision
        os.chmod(subdirPath, 644)
        ## find correct name
        yFolderPositive = (float(yFolder) - minY)*10
        yFolderSplit = str(yFolderPositive).split(".")
        yFolderPositiveInt = yFolderSplit[0]
        yFolderPadded = yFolderPositiveInt.zfill(6)
        # rename
        print "renaming ", yFolder, "to", yFolderPadded
        #renameYTo = os.path.join(os.path.relpath(yFolder), yFolderPadded)
        try:
            os.rename(subdirPath, yFolderPadded)
        except IOError:
            print "permission denied"
        ## rename x folders
        for yFolderPath, xFolders, zTiffs in os.walk(yFolderPadded):
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
    os.chdir(initialDir)"""
"""def renameFiles(rootFolder):
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
    print listOfY
    listOfYFloat = listOfY.astype(np.float)
    minY = np.amin(listOfYFloat)
    print minY
    # for X List
    print listOfX
    listOfXFloat = listOfX.astype(np.float)
    minX = np.amin(listOfXFloat)
    print minX
    # for Z List
    listOfZFloat = listOfZ.astype(np.float)
    minZ = np.amin(listOfZFloat)
    print minZ
    ## walk again, now renaming
    for root, yFolders, zTiffs in os.walk(rootFolder):
        for yFolder in yFolders:
            print "folder is", yFolder, "and length is", len(os.path.abspath(yFolder))
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
                                    print "permission denied"""

