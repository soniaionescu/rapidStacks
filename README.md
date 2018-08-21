# Rapid Stacks
As an intern at the Allen Institute for Brain Science, I worked on image acquisition automation and image processing. These are some of the results of this effort.
## Micro-Manager
Added trajectory velocity and acceleration capabilities for the Focus Axis, in the Zeiss device adapter for Micro-Manager
## Python scripts
### 20x acquisition
Goal: find a sample on a slide (using thresholding and an automated routine), acquire z stacks of each x,y coordinate at an appropriate depth (determined using Sobel gradient), create a minimum intensity projection (MIP), and put these in an appropriate format to then be passed into Tera Stitcher. 
### Multi-slide acquisition
Goal: Integrate 20x automation into a routine which can image multiple slides without human intervention
### 63x acquisition
Goal: Get user input and acquire a z-stack, both stitching images within the boundaries given as input, and putting them in an appropriate format for tera stitcher
