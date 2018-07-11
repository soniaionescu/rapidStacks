import MMCorePy
import numpy as np
import cv2 
import matplotlib.pyplot as plt
from PIL import Image
import scipy.misc
from scipy import ndimage
import os
from tifffile import imsave

## load microscope
mmc = MMCorePy.CMMCore()
#mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")

def blurImage(imageName):
    print imageName
    image = cv2.cv2.imread(imageName, 0)
    ## thresshold to make it maximum of 255
    image[image >= 255 ] = 255
    ## add blur
    blurredImage = ndimage.gaussian_filter(image, sigma=3)
    ## make an image object
    blurredImage = Image.fromarray(blurredImage.astype("uint8"))
    ## save image
    imageName = imageName.replace(".tiff", "Blurred.tiff") ## to remove the original extension and add Blurred.tiff
    blurredImage.save(imageName) ## save the image

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

# go through folders of photos and find which one has the maximum keypoint size in it
def NeuronDetection():
    ## initialize file that contains max KP
    overallMaxKP = 0
    fileWMaxKP = "randomInit"
    ## go into each folder and run SURF with blur
    for path, subdirs, files in os.walk("OverviewTest"):
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

#getUserInputOverviewandSave()
#NeuronDetection()


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


