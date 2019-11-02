# import the necessary packages
import numpy as np
import imutils
import cv2

class SingleMotionDetector:
    def __init__(self, frame_weight, frame_count_required):
        #the weight applied to each new frame added to accumulated_weighted_frames
        self.frame_weight = frame_weight

        #the number of frames required in accumulated_weighted_frames before detection attempted
        self.frame_count_required = frame_count_required

        #the number of frames in accumulated_weighted_frames
        self.frame_count = 0

        self.accumulated_weighted_frames = None

    def detect(self, frame, threshold):
        frame_gray_blurred = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_gray_blurred = cv2.GaussianBlur(frame_gray_blurred, (7, 7), 0)

        # update the background model and increment the total number
        # of frames read thus far
        if self.accumulated_weighted_frames is None:
            self.accumulated_weighted_frames = frame_gray_blurred.copy().astype("float")
        else:
            # update the weighted average of accumulated frames with this new frame
            cv2.accumulateWeighted(frame_gray_blurred, self.accumulated_weighted_frames, self.frame_weight)
        self.frame_count += 1

        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if self.frame_count > self.frame_count_required:
            # compute the absolute difference between the background model
            # and the image passed in, then threshold the delta image
            delta = cv2.absdiff(self.accumulated_weighted_frames.astype("uint8"), frame_gray_blurred)
            thresh = cv2.threshold(delta, threshold, 255, cv2.THRESH_BINARY)[1]

            # perform a series of erosions and dilations to remove small
            # blobs
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # find contours in the thresholded image and initialize the
            # minimum and maximum bounding box regions for motion
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            (minX, minY) = (np.inf, np.inf)
            (maxX, maxY) = (-np.inf, -np.inf)

            # if no contours were found, return None
            if len(cnts) == 0:
                return None

            # otherwise, loop over the contours
            for c in cnts:
                # compute the bounding box of the contour and use it to
                # update the minimum and maximum bounding box regions
                (x, y, w, h) = cv2.boundingRect(c)
                (minX, minY) = (min(minX, x), min(minY, y))
                (maxX, maxY) = (max(maxX, x + w), max(maxY, y + h))

            # otherwise, return a tuple of the thresholded image along
            # with bounding box
            return (thresh, (minX, minY, maxX, maxY))
        else:
            return None
