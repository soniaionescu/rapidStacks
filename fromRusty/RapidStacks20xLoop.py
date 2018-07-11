######################################
### RapidStacks 20x feedback 

# Overview image
	# Could be stitched 20x tiles
	# or 20x try-to-draw-outline
	# or center of mass marked by user

# Pick a few (3-10) places around each tissue sample and take a z stack

	# Stack maybe 500 microns deep
	# Image maybe every 5 microns
	# Write intermediates all to disk
	takeStackAtXYPosition(xyPosition, zRange, stepSize, instrumentParameters)


# Pick reasonable focus in stack positions
	
	# Load position stack from disk
	# Find good focus within first ~50 microns of tissue
	# From points generate focus spline
	# From focus spline and tissue outline, generate tile positions
	focusCoorinates = generateFocusSpline(xyPoints, zPoints, smoothParameters)
	

# Take tile brightfield image at given plane only
	
	# Send output to NAS
	# Include coordinates table
	
# Take DAPI image at given plane + offset only
	
	# Send output to NAS
	# Include coordinates table
	
# At NAS, stitch files and send to LIMS