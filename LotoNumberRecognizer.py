from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i","--image",required = True , help = "Path to the image")
args = vars(ap.parse_args())



image = cv2.imread(args["image"],1)




# initialize a rectangular (wider than it is tall) and square
# structuring kernel
rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(1,5))




#Pre-process orginal image 
image = imutils.resize(image, height=500)
#Gray-scale
gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
#Blurr
blurred = cv2.GaussianBlur(gray.copy(),(5,5),0)
#EDGES
edge = cv2.Canny(blurred,45,200,255)

#Verified
# show the original edges
# cv2.imshow('edge',edge)
#verified


#Getting out the noise 
#Closing: Erosion + Dilation 
thresh = cv2.morphologyEx(edge.copy(), cv2.MORPH_CLOSE, sqKernel)


#Verified 
# cv2.imshow("Morphed",thresh)
#Fijnis



#--------------------------------------------
# Getting outermost shape to zoom in the ticket 
#--------------------------------------------

# find countours in the edge map , then sort them by their size 
cnts = cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#get outside parent contour only
cnts = cnts[0] if imutils.is_cv2() else cnts[1] 

#sort highest to smallest
cnts = sorted(cnts,key=cv2.contourArea,reverse=True)

displayCNt= None

c = max(cnts, key=cv2.contourArea)

#Verified
#Added piece
#Number of Countours in image 
#print len(cnts)


cv2.drawContours(image, c , -1 ,(255,0,0),2)
#verified
#cv2.imshow("BIG",image)



#------------------------------------
# Finding the four corners of the paper 
#------------------------------------


#  loop over th econtours 
for c in cnts:
    #aproximate the countors
   peri = cv2.arcLength (c,True)
   approx = cv2.approxPolyDP(c,0.02*peri,True)
    #if the counter has four vertices , then we found the receit
   if len(approx) == 4:
        displayCnt = approx
        break


 #Extract receipt only, apply perspective 

 #grayscale 
warped = four_point_transform(gray.copy(), displayCnt.reshape(4,2))   

crop = warped.copy()

#original image 
output = four_point_transform(image.copy(), displayCnt.reshape(4,2))    
#Show final outout of the the reciept 

color_crop= output.copy()

#verified 
#cv2.imshow("wARPED",warped)
#cv2.imshow("output",output)


#checking the width and height of the new picture 
w,h = warped.shape[::-1]

#------------------------------------
# Finish Finding Four corners of ticket 
# Finding the four corners of the paper 
#------------------------------------



#Blurr
blurred = cv2.GaussianBlur(warped,(5,5),0)

edges = cv2.Canny(blurred,50,200,255)



# show the original edges
#Verified
#cv2.imshow('*edges',edges)


#------------------------------------------
# Apply special filters 
#-------------------------------------------


# apply a tophat (whitehat) morphological operator to find light
# regions against a dark background (i.e., the credit card numbers)
tophat = cv2.morphologyEx(edges.copy() , cv2.MORPH_TOPHAT, rectKernel)

#Verify 
#cv2.imshow("TOPHAT",tophat)


#-----------------------------
# get vertical components with gradient 
#----------------------------


# compute the Scharr gradient of the tophat image, then scale
# the rest back into the range [0, 255]
gradX = cv2.Sobel(tophat, ddepth=cv2.CV_32F, dx=1, dy=0,
	ksize=-1)

gradX = np.absolute(gradX)
(minVal, maxVal) = (np.min(gradX), np.max(gradX))
gradX = (255 * ((gradX - minVal) / (maxVal - minVal)))
gradX = gradX.astype("uint8")

#Verify 
#cv2.imshow("Gradient",gradX)



# apply a closing operation using the rectangular kernel to help
# cloes gaps in between credit card number digits, then apply
# Otsu's thresholding method to binarize the image
gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel)
thresh = cv2.threshold(gradX, 0, 255,
	cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
 

# apply a second closing operation to the binary image, again
# to help close gaps between credit card number regions
thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, sqKernel)



#Verified 
#cv2.imshow("Closing",thresh)


#-------------------------------
# Experiment wih different filters to get best output 
#-----------------------------------------

thresh2 = cv2.morphologyEx(thresh.copy(), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13 )))



#Verified 
#cv2.imshow("Thresh2",thresh2 )



erosion = cv2.erode(thresh2,rectKernel,iterations = 1)

#cv2.imshow("Erode",erosion )

#Verified
#Matplot 
#plt.imshow(erosion)
#plt.show()   


#more processing ==================++++++++++++


#======================
#Experiment with different values to get 5 numbers in ticket 
#using length , width  , height of rectangle 
#=======================



# find contours in the thresholded image, then initialize the
# list of digit locations
cnts = cv2.findContours(erosion.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]
locs = []

for (i,c)in enumerate(cnts):
     (x,y,w,h) = cv2.boundingRect(c)
     aspectRatio = w /float(h)

     #print cv2.boundingRect(c)
     if  14 < h < 25  and  151 < y < 195:
         
         #Verified
        #create rectangle around contour 
         #print cv2.boundingRect(c)
         
         if 6 < aspectRatio < 9:
            #if 19 <= h <= 30:
            cv2.drawContours(warped, [c] ,-1,(255,0,0),2) 
            #append numbers
            locs.append((x, y, w, h))
            #Verified 
            #print "number location  appended"

#Verified 
#How many locations  
#print len(locs)
cv2.imshow('***sPECIFIC',warped)




# sort the digit locations from left-to-right, then initialize the
# list of classified digits
locs = sorted(locs, key=lambda x:x[0])
output = []

#loops
 

#------------------------------------------------------
# Specfying rectangle of the location where it found the numbers 
# padding on the left and  the right 
#-----------------------------------------------------


# loop over the 4 groupings of 4 digits
for (i, (gX, gY, gW, gH)) in enumerate(locs):
	# initialize the list of group digits
	groupOutput = []
   
	# extract the group ROI of 4 digits from the grayscale image,
	# then apply thresholding to segment the digits from the
	# background of the credit card

    

	group = crop[gY - 5:gY + gH + 5, abs(gX -2)  :gX + gW + 3]  
	group = cv2.threshold(group.copy(), 10, 255,
		cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
 


#Verified 
#cv2.imshow('Group',group)

#Contour later
#cv2.drawContours(color_crop, digitCnts ,-1,(255,0,0),2)


#Verified 
#cv2.imshow('Numbers',color_crop)



#-----------------------------
# tesseract recognition of detected numbers 
#----------------------------

cv2.imshow('**Numbers',group)

print "Printing numbers identified within image:"
cv2.imwrite('number.jpg',group)
img = Image.open("number.jpg")
print(pytesseract.image_to_string(img ,config='outputbase digits'))


cv2.waitKey(0)
cv2.destroyAllWindows()

