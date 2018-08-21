import os
class Configuration():
    def __init__(self):
        ## for micromanager settings
        self.exposureBrightField = .5197
        self.cropX = 350
        self.cropY = 0
        self.cfg = os.path.relpath("NecessaryFiles\ZeissTestMMConfig.cfg")
        self.zStep = .28
        self.notOverlap = .9
        self.threshhold = .7
        self.pixelSize = 3.45
        self.magnification = (20*.63)