# Rapid Stacks
As an intern at the Allen Institute for Brain Science, I worked on image acquisition automation and image processing. These are some of the results of this effort.
## Micro-Manager
Added trajectory velocity and acceleration capabilities for the Focus Axis, in the Zeiss device adapter for Micro-Manager
## Python scripts
### 20x acquisition
Goal: find a sample on a slide (using thresholding and an automated routine), acquire z stacks of each x,y coordinate at an appropriate depth (determined using Sobel gradient), create a minimum intensity projection (MIP), and put these in an appropriate format to then be passed into Tera Stitcher. 
[an example 20x MIP image](https://drive.google.com/open?id=1ummEJlB67zS1suWxVzDhUPzMmc_T0wQx)
[an example 20x DAPI image](https://drive.google.com/open?id=1mQ76_P02AlVrXt2KmPumIQhifzuhGdut)
[a close-up of a MIP of neurons](https://drive.google.com/open?id=1mZNTy_lRZCxKMDq4bMLMgSTl47Ax3VcK)
[a close-up of neurons imaged at only one plane](https://drive.google.com/open?id=1SCIP99QJ6eLdtDMyyL5BCGCRvGOTdDHz)
### Multi-slide acquisition
Goal: Integrate 20x automation into a routine which can image multiple slides without human intervention
### 63x acquisition
Goal: Get user input and acquire a z-stack, both stitching images within the boundaries given as input, and putting them in an appropriate format for tera stitcher
