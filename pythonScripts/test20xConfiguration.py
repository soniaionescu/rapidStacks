import os
class Configuration():
    def __init__(self):
        ## for micromanager settings
        self.exposureBrightField = .5197
        self.exposureDAPI = 5
        self.cropX = 350
        self.cropY = 0
        self.pixelSize = 3.45
        self.magnification = (20*.63)

        ## for getting overlap in saved pictures and not in the stitched image
        self.notOverlap = .9

        ## for finding the z limit and taking a z stack
        self.zStep = .5
        self.downSampleRate = 6
        self.filterBlur = 3
        self.extremeUpperZ = 200
        self.extremeLowerZ = -200
        self.saveImages = False

        ## resolution, can be 'high', 'medium', or 'low'
        self.resolution = 'high'

        ## for findSample
        self.distanceBetweenPictures = 500
        self.numberOfPictures = 4

        ## for Tera Stitcher
        self.threshhold = .7

        ## DAPI flatfield, would be good to give an absolute path so it doesn't matter what folder you're in
        self.DAPIflatField = os.path.relpath("NecessaryFiles\DAPIflatfield.csv")

        ## Configuration file, would be good to give an absolute path so it doesn't matter what folder you're in
        self.cfg = os.path.relpath("NecessaryFiles\ZeissTestMMConfig.cfg")

        ## for multiple slides
        self.SpaceBetweenSlides = 28000