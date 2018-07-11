import MMCorePy
import numpy as np
from pylab import *
from PIL import Image
import scipy
#get one level of acquisition
##load the microscope
mmc = MMCorePy.CMMCore()
mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")
## testing how pictures are acquired and stored

## Test displaying images
### mmc.snapImage()
###img = mmc.getImage()

## display = Image.fromarray(img) ## converts the numpy array into an image object
## display.show() ## can show us a preview of the first image
 
#  Test stitching 2 images
## get height and width of image
pixelSize = 3.45 ## microns
width = mmc.getImageWidth()
height = mmc.getImageHeight()
## getxy position of first image
initialX = mmc.getXPosition()
initialY = mmc.getYPosition
## take first image
mmc.snapImage()
img1 = mmc.getImage()
## set xy position of second image
mmc.setRelativeXYPosition(width*pixelSize/20, 0) ## this is just a guess because of the magnification of the objective?? seems to be correct based off image vs what's im microscope
mmc.sleep(1000)
## take second image
mmc.snapImage()
img2 = mmc.getImage()
## stitch images together
totalImage = np.concatenate((img1,img2), axis=1)
## make image object
displayStitched = Image.fromarray(totalImage)
## display concatenated image
displayStitched.show()

# flat field correct an individual image array: equation is C = [(R-D)*m]/(F-D) where R is Raw, C is correct, F is flat field, D is dark field, and m is image averaged valued of F-D
## take a flat field
###raw_input("Move off the sample and press enter")
###mmc.snapImage()
###flatField = mmc.getImage()
## take a dark field 
###raw_input("Turn the lamp off and press enter")
###mmc.snapImage()
###darkField = mmc.getImage()
## calculate m
###m = np.average(np.subtract(flatField, darkField))
## create the corrected image
###n = np.subtract(img1, darkField)
###numerator = np.multiply(n, m)
###denominator = np.subtract(flatField, darkField)
###correctedImage = np.divide(numerator, denominator)
## display the corrected image
###displayCorrected = Image.fromarray(correctedImage)
###displayCorrected.show()
###displayCStitched = Image.fromarray(np.concatenate((correctedImage, correctedImage), axis = 1))
###displayCStitched.show()







