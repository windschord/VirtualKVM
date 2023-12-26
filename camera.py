from threading import Thread

import cv2


def get_connected_camera():
    """
    Check the connection between the camera numbers and the computer.
    """
    true_camera_is = []

    # check the camera number from 0 to 9
    for camera_number in range(0, 10):
        cap = cv2.VideoCapture(camera_number)

        ret, _ = cap.read()

        if ret is True:
            true_camera_is.append(camera_number)
            print("port number", camera_number, "Find!")

        else:
            print("port number", camera_number, "None")

    return true_camera_is


class ConnectCamera(Thread):
    def __init__(self, window, camera_number=0, width=1920, height=1080, fps=30):
        Thread.__init__(self)
        self.window = window
        self.camera_number = camera_number
        self.width = width
        self.height = height
        self.fps = fps
        self.capture = None

    def run(self):
        """
        Connect the camera.
        """
        self.capture = cv2.VideoCapture(self.camera_number)

        self.capture.set(3, self.width)
        self.capture.set(4, self.height)
        self.capture.set(5, self.fps)
        # self.window.write_event_value(Event.CONNECT_CAMERA, 'Done!')
