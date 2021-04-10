import datetime
import logging
import os
import threading
import time
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

cv2_logger = logging.getLogger('cv2')
cv2_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
cv2_logger.addHandler(handler)


class CameraHandler(threading.Thread):
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1080
    SCALED_WIDTH = 510
    SCALED_COEFF = SCALED_WIDTH / MAX_WIDTH
    SCALED_HEIGHT = int(MAX_HEIGHT * SCALED_COEFF)

    def _init_my_lists(self):
        self.images = MaxSizeList(self.MAX_FRAMES)
        self.images.init_frames(self.SCALED_WIDTH, self.SCALED_HEIGHT)
        self.time_on_frame = MaxSizeList(self.MAX_FRAMES)
        self.time_on_frame.init_values(0)

    def __init__(self, max_frames=500):
        super().__init__()
        self.MAX_FRAMES = max_frames

        self._running = True
        self.gif = None

        # self.url = "http://192.168.1.12/mjpg/video.mjpg"
        self.url = "rtsp://192.168.1.15:554/user=admin&password=&channel=1&stream=0.sdp"

    def run(self):
        self._init_my_lists()
        capture = cv2.VideoCapture(self.url)

        time1 = time.time()
        fps_queue = MaxSizeList(40)
        fps_queue.init_values(25)
        while capture.isOpened():
            while self._running:
                try:
                    delta_time = time.time() - time1
                    self.time_on_frame.push(delta_time * 1000)  # мс
                    fps = 1 / delta_time
                    fps_queue.push(fps)
                    fps = round(sum(fps_queue.ls) / len(fps_queue.ls))
                    time1 = time.time()

                    ret, frame = capture.read()
                    if ret:
                        frame = cv2.resize(frame, (0, 0), fx=self.SCALED_COEFF, fy=self.SCALED_COEFF,
                                           interpolation=cv2.INTER_AREA)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        frame = self.draw_text_on_image(
                            frame, datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), (10, 20))
                        frame = self.draw_text_on_image(frame, str(fps) + " FPS", (frame.shape[1] - 80, 20))
                        self.images.push(frame)
                    else:
                        time.sleep(10)
                        capture = cv2.VideoCapture(self.url)
                except Exception as e:
                    print("EXCEPTION IN CAMERA HANDLER" + str(e))
                    self.wait()
            else:
                self.wait()

    def terminate(self):
        self._running = False

    def resume(self):
        self._running = True

    def is_active(self):
        return self._running

    @staticmethod
    def wait():
        time.sleep(1)

    def get_gif(self, frames=20):
        if not self._running:
            self.resume()
            while self.time_on_frame.get_list_size(frames)[0] == 0:
                self.wait()
            self.terminate()

        images = self.images.get_list_size(frames)

        # Высокое качество
        duration = sum(self.time_on_frame.get_list_size(frames)) / frames

        pil_images = []
        for i, _ in enumerate(images):
            pil_image = Image.fromarray(images[i])
            pil_image.info['duration'] = duration
            pil_images.append(pil_image)

        gif = BytesIO()
        pil_images[0].save(
            gif,
            format="GIF",
            save_all=True,
            append_images=pil_images[1:],
            loop=0,
        )
        return gif

    def get_img(self):
        if not self._running:
            self.images.init_frames(self.SCALED_WIDTH, self.SCALED_HEIGHT)
            self.time_on_frame.init_0()
            self.resume()
            while self.time_on_frame.get_last() == 0:
                self.wait()
            self.terminate()
        frame = self.images.get_last()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        _bytes = cv2.imencode('.jpg', frame)[1].tostring()
        return _bytes

    @staticmethod
    def clear_file(path):
        os.remove(path)

    @staticmethod
    def draw_text_on_image(image, text, pos):
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 4)
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return image


class MaxSizeList(object):

    def __init__(self, max_length):
        self.max_length = max_length
        self.ls = []

    def init_frames(self, w, h):
        frame = np.zeros((h, w, 3), np.uint8)
        self.ls = [frame for _ in range(self.max_length)]

    def init_values(self, value):
        self.ls = [value for _ in range(self.max_length)]

    def push(self, st):
        if len(self.ls) == self.max_length:
            self.ls.pop(0)
        self.ls.append(st)

    def get_list(self):
        return self.ls

    def get_list_size(self, size):
        return self.ls[self.max_length - size:self.max_length]

    def get_last(self):
        return self.ls[self.max_length - 1]

    def get_size(self):
        return self.max_length

    def del_list(self):
        self.ls = []
