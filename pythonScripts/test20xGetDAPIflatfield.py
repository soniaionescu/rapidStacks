import numpy as np
import MMCorePy
from test20xConfiguration import Configuration
from test20xFluorescenceAcquisition import DAPIOff, DAPIOn
from PIL import Image

""" purpose: Get a DAPI flatfield, should be done any hardware is changed or if someone changes ROI
    inputs: nothing
    returns: nothing
    saves: a .csv with the DAPI flatfield 
"""
def getDAPIFlatField(mmc):
    raw_input("Put blue chroma slide on, then press enter")
    ## load configuration
    configuration = Configuration()
    ## get information to set ROI 
    imageWidth = mmc.getImageWidth()
    imageHeight = mmc.getImageHeight()
    ## set ROI
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    ## turn on correct settings
    DAPIOn(mmc)
    ## need to sleep otherwise it's all grey
    mmc.sleep(100)
    ## snap image
    mmc.snapImage()
    ## save as CSV
    flatField = mmc.getImage()
    np.savetxt("DAPIFlatfield.csv", flatField, delimiter=",")
    DAPIOff(mmc)

if __name__ == '__main__':
    configuration = Configuration()
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    getDAPIFlatField(mmc)