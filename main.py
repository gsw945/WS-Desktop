#!/usr/bin/env python3

# import argparse
import os
import io

import tornado.ioloop
import tornado.web
import tornado.websocket

from PIL import Image
import mss
import base64
from io import BytesIO
import pymouse

# import pygame.camera
# import pygame.image

'''
parser = argparse.ArgumentParser(description='Start the PyImageStream server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--camera', default=0, type=int, help='Camera index, first camera is 0 (default: 0)')
parser.add_argument('--width', default=640, type=int, help='Width (default: 640)')
parser.add_argument('--height', default=480, type=int, help='Height (default: 480)')
parser.add_argument('--quality', default=70, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 70)')
parser.add_argument('--stopdelay', default=7, type=int, help='Delay in seconds before the camera will be stopped after '
                                                             'all clients have disconnected (default: 7)')
args = parser.parse_args()

class Camera:

    def __init__(self, index, width, height, quality, stopdelay):
        print("Initializing camera...")
        pygame.camera.init()
        camera_name = pygame.camera.list_cameras()[index]
        self._cam = pygame.camera.Camera(camera_name, (width, height))
        print("Camera initialized")
        self.is_started = False
        self.stop_requested = False
        self.quality = quality
        self.stopdelay = stopdelay

    def request_start(self):
        if self.stop_requested:
            print("Camera continues to be in use")
            self.stop_requested = False
        if not self.is_started:
            self._start()

    def request_stop(self):
        if self.is_started and not self.stop_requested:
            self.stop_requested = True
            print("Stopping camera in " + str(self.stopdelay) + " seconds...")
            tornado.ioloop.IOLoop.current().call_later(self.stopdelay, self._stop)

    def _start(self):
        print("Starting camera...")
        self._cam.start()
        print("Camera started")
        self.is_started = True

    def _stop(self):
        if self.stop_requested:
            print("Stopping camera now...")
            self._cam.stop()
            print("Camera stopped")
            self.is_started = False
            self.stop_requested = False

    def get_jpeg_image_bytes(self):
        img = self._cam.get_image()
        imgstr = pygame.image.tostring(img, "RGB", False)
        pimg = Image.fromstring("RGB", img.get_size(), imgstr)
        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()


camera = Camera(args.camera, args.width, args.height, args.quality, args.stopdelay)
'''

sct = mss.mss()
mouse = pymouse.PyMouse()

class ImageWebSocket(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ImageWebSocket.clients.add(self)
        print("WebSocket opened from: " + self.request.remote_ip)
        # camera.request_start()
        global sct
        if not bool(sct):
            sct = mss.mss()
        global mouse
        if not bool(mouse):
            mouse = pymouse.PyMouse()

    def on_message(self, message):
        # jpeg_bytes = camera.get_jpeg_image_bytes()
        # self.write_message(jpeg_bytes, binary=True)
        png_image_buffer = BytesIO()
        global sct
        sct_img = sct.grab(sct.monitors[1])
        offset = mouse.position()
        image = Image.new('RGB', sct_img.size)
        pixels = zip(
            sct_img.raw[2::4],
            sct_img.raw[1::4],
            sct_img.raw[0::4]
        )
        image.putdata(list(pixels))
        image = image.convert('RGBA')
        del sct_img
        folder = os.path.abspath(os.path.dirname(__file__))
        cursor_file = os.path.join(folder, 'cursor.png')
        cursor = Image.open(cursor_file, 'r')
        cursor = cursor.convert('RGBA')
        image.paste(cursor, offset, cursor)
        cursor.close()
        del cursor
        image.save(png_image_buffer, format="PNG")
        image.close()
        del image
        imgStr = base64.b64encode(png_image_buffer.getvalue())
        png_image_buffer.close()
        del png_image_buffer
        imgStr = str(imgStr)[2:-1]
        base64img = 'data:image/png;base64,{0}'.format(imgStr)
        del imgStr
        self.write_message(base64img)

    def on_close(self):
        ImageWebSocket.clients.remove(self)
        print("WebSocket closed from: " + self.request.remote_ip)
        if len(ImageWebSocket.clients) == 0:
            # camera.request_stop()
            global sct
            del sct
            sct = None
            global mouse
            del mouse
            mouse = None


script_path = os.path.dirname(os.path.realpath(__file__))
static_path = script_path + '/static/'

app = tornado.web.Application([
        (r"/websocket", ImageWebSocket),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ])
port = 12323
# app.listen(args.port)
app.listen(port, address='0.0.0.0')
print('visit by [http://127.0.0.1:{0}]'.format(port))

# print("Starting server: http://localhost:" + str(args.port) + "/")

tornado.ioloop.IOLoop.current().start()