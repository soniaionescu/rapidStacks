# User Inputs:
startPosition 	# microns
stopPosition 	# microns

frameSpacing	# microns/frame

xyStagePositionList # microns

saveFileName

# Fixed parameters:

maxFrameRate	# 1/sec

maxZslewRate	# microns/sec

exposureTime = 250 # microseconds

arduinoCOMPort
zeissCOMPort
stageCOMPort

###################################################33
# Internal functions

def	checkReply(reply, equipment):

	def getGood(x):
		return {
			'arduino' : ardGood, 
			'zeiss' : zeissGood,
			'stage' : stageGood
			}.get(x, defaultGood)
			
	GoodReply = getGood(equipment)

	if reply == GoodReply:
		return 1
	else:
		return 0
		
def setXYPosition(COMPort, position):
	
	flushSerial()
	serial(COMPort, 'xy', position)
	reply = readSerial(COMPort)
	
	checkReply(reply, 'stage');

def setZPosition(COMPort, position): 
	
	flushSerial()
	serial(COMPort, 'SetPost', position);
	reply = readSerial(COMPort)
	
	checkReply(reply, 'zeiss')

def setTravelRate(COMPort, rate):

	flushSerial()
	serial(COMPort, 'SetRate', rate);
	reply = readSerial(COMPort)
	
	checkReply(reply, 'zeiss')
		
def zeroStepCounter(COMPort, startStop):

	flushSerial()
	serial(COMPort, 'zeroCounter')
	
	if startStop == START:
		serial(COMPort, 'expLatchToOn')
	else if startStop == STOP:
		serial(COMPort, 'expLatchToOff')
	
	reply = readSerial(COMPort)
	
	checkReply(reply, 'arduino')
	

def writeToDisk(data, writeName):

	writeDataToDisk(data, writeName)
	

########################
# Calc experimental settings

nFrames = ceil((startPosition - stopPosition)/frameSpacing)

zTravelRate = min([maxZslewRate, nFrames*frameSpacing*maxFrameRate])

#########################
# Pre-acquisition

setxyPosition(stageCOMPort, xyStagePositionList[0])

# Loop over available positions
for xypost in setxyPosition:

	setxyPosition(stageCOMPort, xypost)

	setZPosition(zeissCOMPort, startPosition)

	setTravelRate(zeissCOMPort, zTravelRate)
	zeroStepCounter(arduinoCOMPort, 'START')

	mmc.setProperty('Camera', 'TriggerType', 'External')

	store = mm.data().createRAMDatastore()
	mmc.startSequenceAcquisition(nFrames, 0, true)

	builder = mm.data().getCoordsBuilder().z(0).channel(0).stagePosition(0)

	#########################
	# Acquisition

	int curFrame = 0
	while (mmc.getRemainingImageCount() > 0 || mmc.isSequenceRunning(mmc.getCameraDevice())) {
	   if (mmc.getRemainingImageCount() > 0) {
		  tagged = mmc.popNextTaggedImage();
		  # Convert to an Image at the desired timepoint.
		  image = mm.data().convertTaggedImage(tagged,
			 builder.z(curFrame).build(), null);
		  store.putImage(image);
		  curFrame++;
	   }
	   else {
		  // Wait for another image to arrive.
		  mmc.sleep(Math.min(.5 * exposureTime, 20));
	   }
	}


	mmc.stopSequenceAcquisition();


	#########################
	# Post-acquisition

	setZPosition(zeissCOMPort, startPosition)
	zeroStepCounter(arduinoCOMPort, 'STOP')
	mmc.setProperty('Camera', 'TriggerType', 'Internal')

	mm.displays().manage(store);

	thread = Thread();
	thread.writeToDisk(store, saveFileName+xypost);

	store.close();
	
setxyPosition(stageCOMPort, xyStagePositionList[0])

# Write coordinates and metadata to .txt file in destination folder




