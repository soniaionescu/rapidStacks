import tkinter as tk
from test63xOneAcquisition import getZStackAndStitch
import MMCorePy
from test63xConfiguration import Configuration
from testImageProcessing import moveForFlatField
import os 
from testRenameForTeraStitcher import renameTiffFolders


## set Micro-manager settings
def mainLoading():
    configuration = Configuration()
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configuration.cfg)
    pixelSize = mmc.getPixelSizeUm()
    ## set properties to get 16 bit images and avoid tunneling
    mmc.setProperty('IDS uEye', 'Exposure', configuration.exposureBrightField)
    imageHeight = mmc.getImageHeight()
    imageWidth = mmc.getImageWidth()
    mmc.setROI(configuration.cropX, configuration.cropY, (imageWidth - configuration.cropX*2), (imageHeight - configuration.cropY*2))
    return mmc


def gui_input(prompt, whatKind, mmc):

    root = tk.Toplevel()
    # this will contain the entered string, and will
    # still exist after the window is destroyed
    var = tk.StringVar()

    # create the GUI
    label = tk.Label(root, text=prompt) 
    label.pack(side="left", padx=(20, 0), pady=20)

    ## create position class
    class Position():
        def __init__(self):
            self.position = 0

    ## instantiate Position object
    coordinate = Position()

    ## use mmc to get position and make it an attribute of position object called coordinate
    def getPosition(coordinate):
        ## use mmc to get Relevant position

        if whatKind == 'x':
            coordinate.position = mmc.getXPosition()
        if whatKind == 'y':
            coordinate.position = mmc.getYPosition()
        if whatKind == 'z':
            coordinate.position = mmc.getPosition()


    ## create button to be pushed once they're at the desired position
    b = tk.Button(root, text="I'm at the position", command=getPosition(coordinate))
    b.pack()
    ## destory the popup window once the button has been pushed
    entry.bind("<Button-1>", lambda event: root.destroy())
    # this will block until the window is destroyed
    root.wait_window()

    return coordinate.position

def remindUser(prompt):
    root = tk.Toplevel()
    # this will contain the entered string, and will
    # still exist after the window is destroyed
    var = tk.StringVar()

    # create the GUI
    label = tk.Label(root, text=prompt) 
    label.pack(side="left", padx=(20, 0), pady=20)
    ## use mmc to get position
    # Let the user press the return key to destroy the gui 
    b = tk.Button(root, text="OK")
    entry.bind("<Button>", lambda event: root.destroy())


    # this will block until the window is destroyed
    root.wait_window()

def callTeraStitcher(SlideName):
    configuration = Configuration()
    renameTiffFolders(SlideName)
    pixelSize = configuration.pixelSize/configuration.magnification
    ## stitch in tera stitcher
    os.system('terastitcher --import -volin="{}" -ref1=-Y -ref2=X -ref3=Z -vxl1={} -vxl2={} -vxl3={} -projout=xml_import'.format(os.path.abspath(SlideName), pixelSize, pixelSize, configuration.zStep))
    os.system('terastitcher --displcompute -projin="{}"'.format(os.path.abspath(SlideName + r"\xml_import.xml")))
    os.system('terastitcher --displproj -projin="{}"'.format(os.path.abspath(SlideName + r"\xml_displcomp.xml")))
    os.system('terastitcher --displthres -threshold={} -projin="{}"'.format(configuration.threshhold, os.path.abspath(SlideName + r"\xml_displproj.xml")))
    os.system('terastitcher --placetiles -projin="{}"'.format(os.path.abspath(SlideName + r"\xml_displthres.xml")))
    stitchedFolder = SlideName + r"\stitched"
    if not os.path.exists(stitchedFolder):
         os.makedirs(stitchedFolder)
    os.system('terastitcher --merge -projin="{}" -volout="{}" -volout_plugin="TiledXY|2Dseries"'.format(os.path.abspath(SlideName + r"\xml_merging.xml"), os.path.abspath(stitchedFolder)))

if __name__ == '__main__':
    ## create the tkinter window
    root = tk.Tk()
    root.title("63x Acquisition Window")
    ## load micro-manager settings
    mmc = mainLoading()
    ## ask for slidename
    var = tk.StringVar()
    label = tk.Label(root, text="Enter your Slide Name here")
    entry = tk.Entry(root, textvariable=var)
    label.pack(side="left", padx=(20, 0), pady=20)
    entry.pack(side="right", fill="x", padx=(0, 20), pady=20, expand=True)
    SlideName = var.get()
    print SlideName
    ## create popup windows to instuct user to get positional variables
    LeftX = gui_input("Go to the most positive X position you want imaged and press the button then close the window", 'x', mmc)
    print LeftX
    RightX = gui_input("Go to the most negative X position you want imaged and press the button then close the window", 'x',  mmc)
    TopY = gui_input("Go to the most positive Y position you want imaged and press the button then close the window", 'y', mmc)
    BottomY = gui_input("Go to the most negative Y position you want imaged and press the button then close the window", 'y', mmc)
    lowerZ = gui_input("Go to the most negative Z position you want imaged and press the button then close the window", 'z', mmc)
    upperZ = gui_input("go to the most positive Z position you want imaged and press the button then close the window", 'z', mmc)
    remindUser("Put lever in position so that the camera can view")
    #flatField = moveForFlatField(mmc)
    #getZStackAndStitch(SlideName,  LeftX, RightX, TopY, BottomY, lowerZ, upperZ, flatField, mmc)
    #callTeraStitcher(SlideName)