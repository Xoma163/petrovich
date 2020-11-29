import datetime
import os
import threading
import time
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


class CameraHandler(threading.Thread):
    def _init_my_lists(self):
        self.images = MaxSizeList(self.MAX_FRAMES)
        self.images.init_frames()
        self.time_on_frame = MaxSizeList(self.MAX_FRAMES)
        self.time_on_frame.init_0()

    def __init__(self, max_frames=200):
        super().__init__()
        self.MAX_FRAMES = max_frames
        self._MAX_WIDTH = 1600
        self._running = True
        self.gif = None
        self.SCALED_WIDTH = 720

        self.url = "http://192.168.1.12/mjpg/video.mjpg"

    def run(self):
        self._init_my_lists()
        capture = cv2.VideoCapture(self.url)

        time1 = time.time()
        # ToDo: возможно если я отрублю камеру, всё сломается
        while capture.isOpened():
            while self._running:
                try:
                    delta_time = time.time() - time1
                    self.time_on_frame.push(delta_time * 1000)  # мс
                    fps = round(1 / delta_time, 1)
                    time1 = time.time()

                    ret, frame = capture.read()
                    if ret:
                        frame = cv2.resize(frame, (0, 0), fx=self.SCALED_WIDTH / self._MAX_WIDTH,
                                           fy=self.SCALED_WIDTH / self._MAX_WIDTH)

                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                        frame = self.draw_text_on_image(frame, datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                                                        (10, 20))
                        frame = self.draw_text_on_image(frame, str(fps) + " FPS", (frame.shape[1] - 80, 20))
                        self.images.push(frame)

                    else:
                        print('ret=False')
                        time.sleep(10)
                        capture = cv2.VideoCapture(self.url)
                except Exception as e:
                    print("EXCEPTION IN CAMERAHANDLER" + str(e))
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
        pil_images[0].save(gif,
                           format="GIF",
                           save_all=True,
                           append_images=pil_images[1:],
                           loop=0,
                           )
        return gif

    def get_img(self):
        if not self._running:
            self.images.init_frames()
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

    def init_frames(self):
        frame = np.zeros((100, 100, 3), np.uint8)
        self.ls = [frame for _ in range(self.max_length)]

    def init_0(self):
        self.ls = [0 for _ in range(self.max_length)]

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
