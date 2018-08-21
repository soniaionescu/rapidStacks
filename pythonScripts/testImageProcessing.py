import MMCorePy
import numpy as np
import scipy
from imread import imsave
from test20xEdgeDetection import whichCase, threshholding
from multiprocessing import Pool
import pyvips


if __name__ == '__main__':
    ##load the microscope
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration("ZeissTestMMConfig.cfg")
    mmc.setProperty('IDS uEye', 'Exposure', .5197)
    mmc.setROI(300, 0, 3504, 2174)
    mmc.snapImage()
    img = mmc.getImage()
    flatField  = moveForFlatField(mmc)
    imgCorrected = flatFieldCorrection(flatField, img, mmc)
    imsave("sampleFlatField.tiff", flatField)
    imsave("sampleNotCorrected16Bit.tiff", img)
    imsave("sampleFlatFieldCorrection16Bit.tiff", imgCorrected.astype('uint16'))

"""purpose: find the minimum across the z axis at a single x,y coordinate
    inputs: the flatField image array,  raw image, mmc object
    returns: the mip
    saves: nothing
"""


################################## MIP creation ############################################


"""purpose: get a minimum intensity projection from one z stack using pyvips.bandrank
    inputs: the z stack
    returns: the minimum intensity array at that location
    saves: nothing
"""
def minimumIntensityProjection(inputArray, mmc):
        # numpy data type to vips image format
    dtype_to_format = {
        'uint8': 'uchar',
        'int8': 'char',
        'uint16': 'ushort',
        'int16': 'short',
        'uint32': 'uint',
        'int32': 'int',
        'float32': 'float',
        'float64': 'double',
        'complex64': 'complex',
        'complex128': 'dpcomplex',
    }
    # vips image format to numpy data type
    format_to_dtype = {
        'uchar': np.uint8,
        'char': np.int8,
        'ushort': np.uint16,
        'short': np.int16,
        'uint': np.uint32,
        'int': np.int32,
        'float': np.float32,
        'double': np.float64,
        'complex': np.complex64,
        'dpcomplex': np.complex128,
    }
    # numpy to vip    
    def numpy2vips(a):
        height, width = a.shape
        linear = a.reshape(width * height)
        vi = pyvips.Image.new_from_memory(linear.data, width, height, 1,
                                        dtype_to_format[str(a.dtype)])
        return vi

    # vips image to numpy array
    def vips2numpy(vi):
        return np.ndarray(buffer=vi.write_to_memory(),
                        dtype=format_to_dtype[vi.format],
                        shape=[vi.height, vi.width, vi.bands])
    # get list of 2d arrays
    arrays = [inputArray[x,:,:] for x in range(0, inputArray.shape[0])]
    # get list of vips images
    images = [numpy2vips(x) for x in arrays]
    # run bandrank the images
    mn = images[0].bandrank(images[1:], index = 0)
    # get back to a numpy array
    mip = vips2numpy(mn)
    # return the mip numpy array
    # save the mip
    mip = mip[:,:,0]
    return mip


##################################### flat field creation ####################################


"""purpose: flat field correct an individual image array with only a flatfield image
    inputs: the flatField image array,  raw image, mmc object
    returns: the corrected image array
    saves: nothing
"""
def flatFieldCorrection(flatField, img,  mmc):
    ## get correctedImage
    #correctedImage = np.divide(np.multiply(img, np.divide(flatField, 2)), flatField)
    correctedImage = np.divide(np.multiply(img, np.mean(flatField)), flatField)
    ## display the corrected image
    return correctedImage.astype('uint16')

"""purpose: moves the camera off the sample to get flatfield, turns light off to get darkfield, ends up in same place w light on
    inputs: mmc object
    returns: flatfield and darkfield image arrays
    saves: nothing
"""
def moveForFlatField(mmc):
    ## get initial coordinates
    initialX = mmc.getXPosition()
    initialY = mmc.getYPosition()
    ## get image height
    imageHeight = mmc.getImageHeight()
    pixelSize = mmc.getPixelSizeUm() ## for ids uEye at 20x magnification
    imageHeightUM = pixelSize*imageHeight 
    ## get off the sample
    mmc.snapImage()
    initialImg = mmc.getImage()
    initialImg = threshholding(initialImg)
    while whichCase(initialImg) is not 'j':
        print whichCase(initialImg)
        mmc.setRelativeXYPosition(0, imageHeightUM)
        mmc.snapImage()
        initialImg = mmc.getImage()
        initialImg = threshholding(initialImg)
    ## move one extra time just in case
    mmc.setRelativeXYPosition(0, imageHeightUM)
    ## take the flatField
    mmc.snapImage()
    flatField = mmc.getImage()
    ## return to initialXY
    mmc.setXYPosition(initialX, initialY)
    ## return flatField
    return flatField

"""purpose: take a 16 bit image and convert it to 8 bit by dividing each value by 256
    inputs: an array
    returns: the array with each value divided by 256
    saves: nothing
"""
def simple16to8conversion(sixteenBitArray):
    eightBit = np.divide(sixteenBitArray, 256)
    return eightBit.astype('uint8')


###################### useless stuff ################################################


"""def minimumIntensityProjection(inputArray, mmc):
    #imageHeight = mmc.getImageHeight()
    #imageWidth = mmc.getImageWidth()
    ## initialize an empty array
    #mip = np.empty([imageHeight, imageWidth])
    ## make list of X, Y coordinates
    #coordinateList = []
    #total_index = np.arange(1, imageHeight*imageWidth)
    #x_coords = [math.floor(ind/imageWidth) for ind in total_index]
    #y_coords = [ind % imageWidth for ind in total_index]
    #coordinateList = list(zip(x_coords, y_coords))
    #print "coordList made"
    #p = Pool(processes = 8)
    #p.map(coord(inputArray, mip), coordinateList, 100)
    #for i in range(0, len(coordinateList)):
    mip = useBandrank(inputArray)
    return mip
"""

"""## coord object, only necessary for multiprocessing
class coord(object):
    def __init__(self, inputArray, mip):
        self.inputArray = inputArray
        self.mip = mip
    def __call__(self, xy):
        findMinimum(xy, self.inputArray, self.mip)"""

"""## find minimum of each pixel in the 3D array
def findMinimum(xy, inputArray, mip):
    x =  xy[0]
    y = xy[1]
    minimumElement = np.amin(inputArray[:,x,y])
    mip[x, y] = int(minimumElement)"""
