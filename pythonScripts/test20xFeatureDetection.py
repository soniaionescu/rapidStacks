import MMCorePy
import numpy as np
import cv2 
import matplotlib.pyplot as plt
from PIL import Image
import scipy.misc
from scipy import ndimage
from skimage import io, filters, morphology, measure
import pyqtgraph as pg
from matplotlib import cm
import os
import sys
from scipy.misc import imsave
import time
import tifffile
import glob

#################### different filtering and feature detection algorithms #############################

""" purpose: to detect neurons using frangi filtering
    inputs: the name of a tiff (including the file extension)
    returns: 'true' if a neuron is detected, 'false' if not
    saves: nothing
    credit: based off of Mike Taormina's frangiFilter.py
"""

def frangiFilter(imageName):
    ## read image
    im = cv2.cv2.imread(imageName, 0)
    ## create the different 3D arrays that will be used
    importStack = np.empty([im.shape[i] for i in [0,1]])
    imgStackProcesses = np.empty([im.shape[i] for i in [0,1]])
    imgStackSoma = np.empty([im.shape[i] for i in [0,1]])
    threshStack = np.empty([im.shape[i] for i in [0,1]])
    somaStack = np.empty([im.shape[i] for i in [0,1]])
    ## fill each array
    importStack = im
    imgStackProcesses = filters.frangi(importStack, scale_range = (1, 6), beta1=1, beta2=25 )
    imgStackSoma = filters.frangi(importStack, scale_range = (5, 20), beta1=1, beta2=15)
    threshStack = ((imgStackProcesses > 4e-6) + (imgStackSoma > 4e-6)) > 0
    showThreshStack = threshStack
    showThreshStack[showThreshStack > 0] = 1
    ## save arrays to binary .npy files
    np.save('importStack', importStack)    
    np.save('imgStackProcesses', imgStackProcesses)
    #np.save('imgStackSoma', imgStackSoma)
    np.save('threshStack', threshStack)
    ## set threshold
    pixThresh = 1e3
    ## remove small objects
    bigOnly = morphology.remove_small_objects(showThreshStack, pixThresh)
    bigOnlyShow = np.multiply(bigOnly, 255)
    ## label objects in bigOnly
    lab, n = ndimage.label(bigOnly)
    ## display
    """fig, ax = plt.subplots(ncols=3)
    ax[0].imshow(im)
    ax[0].set_title('Original image')
    ax[1].imshow(imgStackProcesses)
    ax[1].set_title('Frangi filter processes')
    ax[2].imshow(imgStackSoma)
    ax[2].set_title('Frangi filter soma')
    fig2, ax2 = plt.subplots(ncols = 3)
    ax2[0].imshow(showThreshStack)
    ax2[0].set_title('ThreshStack')
    ax2[1].imshow(bigOnlyShow)
    ax2[1].set_title('No small')
    ax2[2].imshow(lab)
    ax2[2].set_title("labeled image")
    plt.show()"""

    """## get list of unique labels
    label = np.unique(lab)
    labelUnique = np.copy(label)
    ## put labels in random order
    np.random.shuffle(label)
    ## reshuffle if there are any consecutive elements with a a difference of 1
    if any(np.abs(np.ediff1d(label)) == 1):
        np.random.shuffle(label)
    ## not sure what this does??
    if np.where(label == 0)[0][0] <> 0:
        label[[0, np.where(label == 0)[0][0]]] = label[[np.where(label == 0)[0][0], 0]]
    print label"""



""" purpose: invert a 16 bit image
    inputs: the name of a tiff (including the file extension)
    returns: an inverted image
    saves: nothing
"""
def invertImage(imageArray):
    invertedImage = np.subtract(255, imageArray)
    return invertedImage


""" purpose: to produce a version of the tiff which has been Gaussian blurred for better feature recognition
    inputs: the name of a tiff (including the file extension)
    returns: nothing
    saves: a blurred version of the tiff with the name imageNameBlurred.tiff
"""
def blurImage(imageName):
    print imageName
    image = cv2.cv2.imread(imageName, 0)
    ## add blur
    blurredImage = ndimage.gaussian_filter(image, sigma=3)
    ## make an image object
    blurredImage = Image.fromarray(blurredImage.astype("uint8"))
    ## save image
    imageName = imageName.replace(".tiff", "Blurred.tiff") ## to remove the original extension and add Blurred.tiff
    blurredImage.save(imageName) ## save the image

""" purpose: Does SURF on an image after blurring it
    inputs: the image name of the unblurred image (including extension)
    returns: the sum of the size of all the keypoints in the image
    saves: Because it calls blurImage, it saves imageNameBlurred.tiff
"""
def TCISURFwBlur(imageName):
    ## take two images
    blurImage(imageName)
    ## load the image
    filename = imageName.replace(".tiff", "Blurred.tiff") ## so that we run it on the blurred image
    img = cv2.cv2.imread(filename, 0)
    ## create a surf instance
    surf = cv2.cv2.xfeatures2d.SURF_create(1000)
    ## detect and compute
    kp, des = surf.detectAndCompute(img, None)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
    ### go through and find max size of kp in the image -- turned out not to be that effective
    #maxSize = 0
    #for i in range(0, len(kp)):
        #if kp[i].size > maxSize:
            #maxSize = kp[i].size
    ## return the size of the largest keypoint
    #return maxSize
    ### go through and find sum of sizes of all kp in one image
    sumKP = 0
    for i in range(0, len(kp)):
        sumKP = kp[i].size + sumKP
    return sumKP

""" purpose: to return the image which is "most likely" to have a neuron in it
    inputs: folder to look in
    returns: the filename of the file that has been detected to most likely have the neuron in it
    saves: Because it calls blurImage, it saves imageNameBlurred.tiff for each file in the folder
"""

def NeuronDetection(folder):
    ## initialize file that contains max KP
    overallMaxKP = 0
    fileWMaxKP = "randomInit"
    ## go into each folder and run SURF with blur
    for path, subdirs, files in os.walk(folder):
        print files
        for name in files:
            print name
            fullPath = os.path.join(path, name)
            print fullPath
            currentMaxKP = TCISURFwBlur(fullPath)
            if currentMaxKP > overallMaxKP:
                overallMaxKP = currentMaxKP
                fileWMaxKP = fullPath
    print("The file with the maximum KP is {} with KP size {}".format(fileWMaxKP, overallMaxKP))
    return fileWMaxKP 


#################################### Rusty's code ##########################################
"""
Created on Fri Jul 27 13:07:53 2018

@author: rustyn
"""



def loadFiles(baseFolder):
    
    fileList = sorted(glob.glob(baseFolder + os.sep + "*.tif"))
    
    for m,k in enumerate(fileList):
        with tifffile.TiffFile(k, multifile=False) as tif:
            
            if m == 0:
                # Initialize numpy array
                # Include padding from start
                width, length = tif.pages[0].shape
                datatype = tif.pages[0].dtype
            
            
                img = np.zeros([len(fileList), width, length], dtype = datatype)
            
            img[m,:,:] = tif.asarray()
            
    return img

def bandpassFilterImg(img, bigBand, smallBand):
    
        if ((bigBand % 2) == 0):
            bigBand = bigBand + 1
        
        if ((smallBand % 2) == 0):
            smallBand = smallBand + 1

        # Blur with big Gaussian
        bigBlur = cv2.cv2.GaussianBlur(img,(bigBand,bigBand),0)
        
        # Blur with small Gaussian
        smallBlur = cv2.cv2.GaussianBlur(img,(smallBand,smallBand),0)
        
        # Subtract to make bandpass filtered image
        return smallBlur - bigBlur
    
def showImgOverlay(baseImg, overlayImg):
    
    imv = pg.ImageView()
    imv.setImage(baseImg.T)
    imv.show()
    
    regImg = pg.ImageItem()
    imv.addItem(regImg)
    regImg.setZValue(10)
    
    colormap = cm.get_cmap("CMRmap")  # cm.get_cmap("CMRmap")
    colormap._init()
    lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
    regImg.setLookupTable(lut)
    
    regImg.setAutoDownsample(True)
    
    #lut = np.array([[0,0,0], [255,0,0]])
    #threshImg.setLookupTable(lut)
    regImg.setCompositionMode(pg.QtGui.QPainter.CompositionMode_Plus)
    

    def updateThresholdImg():
        regImg.setImage(overlayImg[..., imv.currentIndex].T)
        regImg.setLevels([0, np.amax(overlayImg)+1])
    
    imv.sigTimeChanged.connect(updateThresholdImg)
    
def downsampleImage(img, downsampleRate):
    binImg = np.zeros([img.shape[1]/downsampleRate, img.shape[2]/downsampleRate, img.shape[0]])
    for k in range(img.shape[0]):
        binImg[:,:,k] = cv2.cv2.resize(img[k,:,:], dsize=(img.shape[2]/downsampleRate, img.shape[1]/downsampleRate), interpolation=cv2.cv2.INTER_LINEAR)
    
    return binImg

def bandpassFilterStack(binImg, bigRad, smallRad):
    
    bPassImg = np.zeros(binImg.shape, dtype=float)

    for k in range(binImg.shape[2]):
        
        bPassImg[:,:,k] = bandpassFilterImg(binImg[:,:,k], bigRad, smallRad)
        
    bPassImg = bPassImg + np.amin(bPassImg)
    bPassImg = np.amax(bPassImg) - bPassImg
    bPassImg = 255*((bPassImg - np.amin(bPassImg)) / (np.amax(bPassImg) - np.amin(bPassImg)))
    
    return bPassImg
    
def localizeBlobs(labImg, binImg):
    # Regionprops to find centroid of blobs
    regsOut = measure.regionprops(labImg)
    regArray = np.zeros([len(regsOut), 6])
    k = 0
    for regs in regsOut:
        regArray[k,:] = [regs.label] + list(regs.centroid) +[ regs.area, np.sum(binImg[labImg == (regs.label)])/(regs.area)]
        k = k+1
        
    return regArray

def mainFindSoma(baseFolder, downsampleRate = 4, bigGauss = 150, smallGauss = 40, intThresh = 127, pixThresh = 1e4):
    
    # Load TIFFs from baseFolder
    img = loadFiles(baseFolder)
    
    # Downsample image to save on processing time
    binImg = downsampleImage(img, downsampleRate)
    
    # Bandpass filter the image to enhance soma-sized objects
    bPassImg = bandpassFilterStack(binImg, bigGauss/downsampleRate, smallGauss/downsampleRate)
        
    # Threshold bandpass-enhanced image
    threshStack = bPassImg > intThresh 
    
    # Filter blobs to soma-sized objects remain
    bigOnly = morphology.remove_small_objects(threshStack, pixThresh/downsampleRate)
    
    ################################
    
    # Label blobs
    labImg = morphology.label(bigOnly, neighbors = 8)
    
    # Localize each blob and pull out some stats
    somaLocations = localizeBlobs(labImg, binImg)
    
    for k in range(somaLocations.shape[0]):
        # Return soma locations to pre-downsampled image space
        somaLocations[k, 1:2] = somaLocations[k,1:2]*downsampleRate
        print 'Soma found on plane ' + str(int(somaLocations[k,3])) + ' at X : ' + str(int(somaLocations[k,1])) + '; Y : ' + str(int(somaLocations[k,2]))
    
    # Show overlay image of data + blobs
    showImgOverlay(binImg, labImg)
    
    # Returned array is N x 6, with [ID, X location (pixels), Y location (pixels), Z location (planes), area (voxels), meanIntensity]
    return somaLocations
    
    
if __name__ == "__main__":
    
    baseFolder = r'D:\Users\ics\Documents\Dev\rapidstacks\soniaGitRepos\rapidstacks\pythonScripts\727zStackSobelCalc'
    
    dwnRate = 6 # Amount to downsample original images before remaining analysis
    
    bG = 165 # Size of upper radius to bandpass filter
    sG = 45 # Size of lower radius to bandpass filter
                    # Objects of interest should be of radius between bigGauss and smallGauss
                    # Units of pixels in ORIGINAL image
    
    thrsh = 127 # Assume splitting histogram halfway by intensity returns reasonable segmentation of 
                                # soma targeted in filtering
                                # Could be found automatically 
                                
    pthrsh = 2e4 # min size for objects to continue through localization
                    # Units of voxels in ORIGINAL image
                            
    somaLocations = mainFindSoma(baseFolder, downsampleRate = dwnRate, bigGauss = bG, smallGauss = sG, intThresh = thrsh, pixThresh = pthrsh)      


########################### useless stuff ############################################


"""def NeuronDetection(folder):
    ## initialize file that contains max KP
    overallMaxKP = 0
    fileWMaxKP = "randomInit"
    ## go into each folder and run SURF with blur
    for path, subdirs, files in os.walk(folder):
        print files
        for name in files:
            print name
            fullPath = os.path.join(path, name)
            print fullPath
            currentMaxKP = TCISURFwBlur(fullPath)
            if currentMaxKP > overallMaxKP:
                overallMaxKP = currentMaxKP
                fileWMaxKP = fullPath
    print("The file with the maximum KP is {} with KP size {}".format(fileWMaxKP, overallMaxKP))
    return fileWMaxKP """

"""def takeTwoImages():
    ## take two images
    raw_input("Go somewhere with no neuron and press enter")
    mmc.snapImage()
    noNeuron = mmc.getImage()
    ## thresshold to make it maximum of 255
    noNeuron[noNeuron >= 200 ] = 255
    ## make an image object
    noNeuronImage = Image.fromarray(noNeuron.astype("uint8"))
    ## save image
    noNeuronImage.save("noNeuron.tiff")
    ## do the same with a neuron in the image
    raw_input("Go somewhere with a neuron and press enter")
    mmc.snapImage()
    yesNeuron = mmc.getImage()
    ## thresshold to make it maximum of 255 (for some reason there are two pixels that are way above)
    yesNeuron[yesNeuron >= 200 ] = 255
    yesNeuronImage = Image.fromarray(yesNeuron.astype("uint8"))
    yesNeuronImage.save("yesNeuron.tiff")

def takeTwoImagesWBlur():
    ## take two images
    raw_input("Go somewhere with no neuron and press enter")
    mmc.snapImage()
    noNeuron = mmc.getImage()
    ## thresshold to make it maximum of 255
    noNeuron[noNeuron >= 200 ] = 255
    ## add blur
    blurredNN = ndimage.gaussian_filter(noNeuron, sigma=3)
    ## make an image object
    noNeuronImage = Image.fromarray(blurredNN.astype("uint8"))
    ## save image
    noNeuronImage.save("noNeuronBlurred.tiff")
    ## do the same with a neuron in the image
    raw_input("Go somewhere with a neuron and press enter")
    mmc.snapImage()
    yesNeuron = mmc.getImage()
    ## thresshold to make it maximum of 255 (for some reason there are two pixels that are way above)
    yesNeuron[yesNeuron >= 200 ] = 255
    ## add blur
    blurredYN = ndimage.gaussian_filter(yesNeuron, sigma=3)
    ## make an image object
    yesNeuronImage = Image.fromarray(blurredYN.astype("uint8"))
    ## save image
    yesNeuronImage.save("yesNeuronBlurred.tiff") """


"""def testCompareTwoImagesORB():

    ## take two images
    takeTwoImages()
    ## create orb instance
    orb = cv2.cv2.ORB_create()
    ## detect and compute for no neuron
    img = cv2.cv2.imread('noNeuron.tiff',0)
    kp = orb.detect(img, None)
    kp, des = orb.compute(img, kp)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
    ## detect and compute for yes neuron
    img2 = cv2.cv2.imread('yesNeuron.tiff',0)
    kp = orb.detect(img2, None)
    kp, des = orb.compute(img2, kp)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsY = cv2.cv2.drawKeypoints(img2, kp, img2, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsY).show()

def testCompareTwoImagesSURF():

    ## take two images
    takeTwoImages()
    ## detect and compute for no neuron
    img = cv2.cv2.imread('noNeuron.tiff',0)
    surf = cv2.cv2.xfeatures2d.SURF_create(1000)
    kp, des = surf.detectAndCompute(img, None)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
    ## detect and compute for yes neuron
    img2 = cv2.cv2.imread('yesNeuron.tiff',0)
    surf = cv2.cv2.xfeatures2d.SURF_create(1000)
    kp, des = surf.detectAndCompute(img2, None)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsY = cv2.cv2.drawKeypoints(img2, kp, img2, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsY).show()

def testCompareTwoImagesBlob():

    ## take two images
    takeTwoImages()
    ##compute for no neuron
    img = cv2.cv2.imread('noNeuron.tiff',0)
    detector = cv2.cv2.SimpleBlobDetector_create()
    kp = detector.detect(img)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
     
    ## detect and compute for yes neuron
    img2 = cv2.cv2.imread('yesNeuron.tiff',0)
    detector = cv2.cv2.SimpleBlobDetector_create()
    kp = detector.detect(img2)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsY = cv2.cv2.drawKeypoints(img2, kp, img2, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsY).show()

def TC2ISURFwBlur():
    ## take two images
    takeTwoImagesWBlur()
    ## detect and compute for no neuron
    img = cv2.cv2.imread('noNeuronBlurred.tiff',0)
    surf = cv2.cv2.xfeatures2d.SURF_create(1000)
    kp1, des = surf.detectAndCompute(img, None)
    print("# kps: {}.".format(len(kp1)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp1, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
    ## detect and compute for yes neuron
    img2 = cv2.cv2.imread('yesNeuronBlurred.tiff',0)
    surf = cv2.cv2.xfeatures2d.SURF_create(1000)
    kp2, des = surf.detectAndCompute(img2, None)
    print("# kps: {}.".format(len(kp2)))
    imgWKeypointsY = cv2.cv2.drawKeypoints(img2, kp2, img2, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsY).show()
    ## do comparison to see which image has a neuron in it
    ### go through and find max size of kp in no neuron
    maxSizeN = 0
    maxSizeY = 0
    for i in range(0, len(kp1)):
        if kp1[i].size > maxSizeN:
            maxSizeN = kp1[i].size
    for j in range(0, len(kp2)):
        if kp2[i].size > maxSizeY:
            maxSizeY = kp2[i].size
    if (maxSizeY > maxSizeN):
        print "there is a neuron where I expected"
    else:
        ###print "did you switch these?"""



"""def TC2IBlobWBlur():
    ## take two images
    takeTwoImagesWBlur()
    ##compute for no neuron
    img = cv2.cv2.imread('noNeuronBlurred.tiff',0)
    detector = cv2.cv2.SimpleBlobDetector_create()
    kp = detector.detect(img)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsN = cv2.cv2.drawKeypoints(img, kp, img, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsN).show()
    ## detect and compute for yes neuron
    img2 = cv2.cv2.imread('yesNeuronBlurred.tiff',0)
    detector = cv2.cv2.SimpleBlobDetector_create()
    kp = detector.detect(img2)
    print("# kps: {}.".format(len(kp)))
    imgWKeypointsY = cv2.cv2.drawKeypoints(img2, kp, img2, color=(0,255,0), flags=4 )
    Image.fromarray(imgWKeypointsY).show()"""

"""start_time = time.time()
frangiFilter("726mPatchInFocus.tiff")
frangiFilter("726mPatchOutOfFocus.tiff")
frangiFilter("726NoNeuron.tiff")
print "--- %s seconds ---" % (time.time() - start_time)"""