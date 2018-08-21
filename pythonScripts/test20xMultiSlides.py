import MMCorePy
from test20xOneSlide import oneSlide
from test20xConfiguration import Configuration

""" purpose: ##Goal: take an overview of multiple slides, using the oneSlide acquisition method and moving on to the next slide
    inputs: the name of the slide, the resolution desired of the stitched image
    returns: nothing
    saves: a y/x/mip.tiff folder, a stitched overview image, a fluorescence image
"""
def multiSlides(slideName1, mmc, slideName2=None, slideName3=None, slideName4=None, slideName5=None, slideName6=None, slideName7=None, slideName8=None):
    ## get configuration
    configuration = Configuration()
    ## get list of slide names
    listOfSlideNames = [slideName1, slideName2, slideName3, slideName4, slideName5, slideName6, slideName7, slideName8]
    ## get list without nones
    listOfSlideNamesNoNones = filter(None, listOfSlideNames)
    numberOfSlides = len(listOfSlideNamesNoNones)
    ## assumes that the first slide is in an okay position
    originalX = mmc.getXPosition()
    originalY = mmc.getYPosition()
    ## go through each slide
    for i in range(0, numberOfSlides):
        ## run acquisition routine
        oneSlide(listOfSlideNamesNoNones[i], mmc)
        ## move to next slide 
        mmc.setXYPosition(originalX + configuration.SpaceBetweenSlides, originalY)
    ## maybe handoff script here?

if __name__ == '__main__':
    configuration = Configuration()
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)