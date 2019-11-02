# import the necessary packages
from detect_motion.singlemotiondetector import SingleMotionDetector
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
import sys
import os
from multiprocessing import Process


class VideoStreamServer(object):
    # flask route decorators require app to be static
    app = Flask(__name__)
    output_frame = None
    output_frame_lock = threading.Lock()

    def __init__(self):
        try:
            self.ip = os.getenv('IP', '0.0.0.0')
            self.port = int(os.getenv('PORT', 8080))
            self.frame_count = int(os.getenv('FRAME_COUNT', 32))
            self.resize_width = int(os.getenv('RESIZE_WIDTH', 400))
            self.frame_weight = float(os.getenv('FRAME_WEIGHT', 0.1))
            self.frame_count_required = int(os.getenv('FRAME_COUNT_REQUIRED', 32))


        except ValueError as error:
            print (error)
            sys.exit(1)

        self.event_stop_process_frames = threading.Event()
        self.thread_process_frames = threading.Thread(
            target=self.process_frames,
            args=(self.frame_count, self.resize_width),
            #daemon=True
        )

        #start Flask in another process so it can be terminated in stop()
        #self.server = Process(target=VideoStreamServer.app.run, kwargs={'host':self.ip, 'port': self.port, 'debug': True, 'threaded': True, 'use_reloader': False,})
        self.server = threading.Thread(
            target=VideoStreamServer.app.run,
            kwargs={'host':self.ip, 'port': self.port, 'debug': True, 'threaded': True, 'use_reloader': False,},
            daemon=True
        )

    def start(self):
        # initialize the video stream
        #uncomment next and comment next-next if RPi camera, else USB camera
        #vs = VideoStream(usePiCamera=1).start()
        print('Starting video stream...', end='')
        self.vs = VideoStream(src=0).start()
        time.sleep(3.0)
        print('done.')

        print('Starting process frames thread...', end='')
        self.thread_process_frames.start()
        print('done.')

        print('Starting server at address {} and port {}...'.format(self.ip, self.port), end='')
        self.server.start()
        print('done.')
        #VideoStreamServer.app.run(self.ip, self.port, debug=True, threaded=True, use_reloader=False)
        #print('Server at address {} and port {} stopped'.format(self.ip, self.port))

        #self.stop()

    def stop(self):
        print('Stopping server at address {} and port {}...'.format(self.ip, self.port), end='')
        #self.server.terminate()
        #self.server.join()
        #print('done.')
        print('daemon thread will terminate automatically.')

        print('Stopping process frames thread...', end='')
        self.event_stop_process_frames.set()
        self.thread_process_frames.join()
        print('done.')
        #print('daemon thread will terminate automatically.')

        # release the video stream
        print('Stopping video stream...', end='')
        self.vs.stop()
        print('done.')

    @staticmethod
    @app.route("/")
    def index():
        # return the rendered template
        return render_template("index.html")

    @staticmethod
    @app.route("/video_feed")
    def video_feed():
        return Response(VideoStreamServer.generate_response(), mimetype = "multipart/x-mixed-replace; boundary=frame")

    @classmethod
    def generate_response(cls):
        while True:
            with cls.output_frame_lock:
                if cls.output_frame is None:
                    continue

                # encode the frame in JPEG format
                (flag, encodedImage) = cv2.imencode(".jpg", cls.output_frame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

    def process_frames(self, frameCount, resize_width):
        md = SingleMotionDetector(frame_weight=self.frame_weight, frame_count_required=self.frame_count_required)

        #while True:
        while not self.event_stop_process_frames.is_set():
            frame = self.vs.read()

            if frame is not None:

                frame = imutils.resize(frame, width=resize_width)

                # apply single area detection to frame
                motion_area = md.detect(frame, 25)
                if motion_area is not None:
                    (thresh, (minX, minY, maxX, maxY)) = motion_area
                    cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)

                # apply watermark to frame
                timestamp = datetime.datetime.now()
                cv2.putText(frame, timestamp.strftime(
                    "%A %d %B %Y %I:%M:%S%p (c) Compass Point, Inc."), (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                        
                #copy to output
                with VideoStreamServer.output_frame_lock:
                    VideoStreamServer.output_frame = frame.copy()
