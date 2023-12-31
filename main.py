import logging
import os
import threading
import tkinter as tk
from logging.handlers import TimedRotatingFileHandler
from tkinter import ttk

import cv2
import serial.tools.list_ports
from PIL import Image, ImageOps, ImageTk

from ch9329 import CH9329

os.makedirs('log', exist_ok=True)
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
file_handler = TimedRotatingFileHandler(os.path.join('log', 'app.log'), when='D', interval=1, backupCount=7)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class Gui(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.disp_img = None
        self.capture = None
        self.serial_keyboard = None
        self.master = master
        self.master.geometry("1465x920")
        self.master.title("Virtual KVM")
        self.master.bind('<KeyPress>', self.keyPress)
        self.master.bind('<KeyRelease>', self.keyRelease)

        # ----- Setting frame -----
        self.setting_frame = ttk.Labelframe(self.master,
                                            relief="ridge",
                                            text="Settings",
                                            labelanchor=tk.NW,
                                            width=200,
                                            height=50,
                                            padding=5,
                                            )
        self.setting_frame.grid(row=0, padx=10, sticky=tk.NW)

        # Setting camera frame
        self.cam_frame = ttk.Labelframe(self.setting_frame,
                                        relief="ridge",
                                        text="Camera selector",
                                        labelanchor=tk.NW,
                                        padding=5,
                                        )
        self.cam_frame.grid(row=0, column=0, padx=5)

        self.cam_selector = ttk.Combobox(self.cam_frame,
                                         width=20,
                                         height=45,
                                         state="readonly",
                                         )
        self.cam_selector.bind('<<ComboboxSelected>>', self.selected_cam)
        self.cam_selector.grid(row=0, column=1)

        self.reload_cam = tk.Button(self.cam_frame,
                                    text="Reload",
                                    width=10,
                                    command=self.reload_cam_list
                                    )
        self.reload_cam.grid(row=0, column=2, padx=5)

        # Setting serial frame
        self.serial_frame = ttk.Labelframe(self.setting_frame,
                                           relief="ridge",
                                           text="Serial selector",
                                           labelanchor=tk.NW,
                                           padding=5,
                                           )
        self.serial_frame.grid(row=0, column=1, padx=5)

        self.serial_selector = ttk.Combobox(self.serial_frame,
                                            width=20,
                                            height=50,
                                            state="readonly",
                                            )
        self.serial_selector.bind('<<ComboboxSelected>>', self.selected_serial)
        self.serial_selector.grid(row=0, column=1)

        self.reload_serial = tk.Button(self.serial_frame,
                                       text="Reload",
                                       width=10,
                                       command=self.reload_serial_list)
        self.reload_serial.grid(row=0, column=2, padx=5)

        # ----- Image frame -----
        self.image_frame = tk.Frame(self.master, width=200, height=400, bg='grey')
        self.image_frame.grid(row=1, padx=10, pady=5, sticky=tk.NSEW)
        self.canvas_cam = tk.Canvas(self.image_frame, width=1440, height=810, bg='black')
        self.canvas_cam.pack(side="top", fill="both")
        self.canvas_img = self.canvas_cam.create_image(0, 0, anchor=tk.NW)

        # ----- Init Camera -----
        self.master.after_idle(self.startup_task)

    def startup_task(self):
        self.reload_serial_list()
        threading.Thread(target=self.reload_cam_list, args=(True,)).start()

    def selected_cam(self, event):
        self.master.focus()
        select_num = self.cam_selector.get()
        if self.capture:
            logger.debug('Capture release')
            self.capture.release()
        self.capture = self.connect_camera(int(select_num))
        self.start_video()

    def selected_serial(self, event):
        self.master.focus()
        if self.serial_keyboard:
            logger.debug('Serial release')
            self.serial_keyboard.close()
            self.serial_keyboard = None

        try:
            self.serial_keyboard = CH9329(self.serial_selector.get())
        except:
            logger.exception('Failed to connect to serial device', stack_info=True)

    def reload_cam_list(self, default_select=False):
        self.master.focus()
        self.reload_cam['state'] = tk.DISABLED
        self.cam_selector['state'] = tk.DISABLED
        threading.Thread(target=self._get_connected_camera, args=(default_select,)).start()

    def reload_serial_list(self):
        self.master.focus()
        self.serial_selector['values'] = sorted([p.device for p in list(serial.tools.list_ports.comports())])
        if len(self.serial_selector['values']):
            self.serial_selector.current(0)

    def connect_camera(self, camera_number, width=1920, height=1080, fps=30):
        capture = cv2.VideoCapture(camera_number)
        capture.set(3, width)
        capture.set(4, height)
        capture.set(5, fps)
        logger.debug(f'Connected to camera {camera_number}')
        return capture

    def start_video(self):
        canvas_width = self.canvas_cam.winfo_width()
        canvas_height = self.canvas_cam.winfo_height()

        if not self.capture or not self.capture.isOpened():
            logger.debug('Capture is not ready...')
            self.master.after(300, self.start_video)
        else:
            _, img = self.capture.read()

            try:
                img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img2 = Image.fromarray(img2)
                img2 = ImageOps.pad(img2, (canvas_width, canvas_height))
                self.disp_img = ImageTk.PhotoImage(image=img2)

                self.canvas_cam.itemconfig(self.canvas_img, image=self.disp_img)
                # self.canvas_cam.update()
            except Exception as e:
                logging.exception(e)

        self.master.after(20, self.start_video)

    def _get_connected_camera(self, default_select=False):
        """
        Check the connection between the camera numbers and the computer.
        """
        true_camera_is = []

        # check the camera number from 0 to 9
        for camera_number in range(0, 10):
            cap = cv2.VideoCapture(camera_number)

            ret, _ = cap.read()

            if ret:
                true_camera_is.append(camera_number)
                logger.debug("Camera number %s Find!", camera_number)
            else:
                logger.debug("Camera number %s None..", camera_number)
            cap.release()

        # update UI
        self.cam_selector['values'] = true_camera_is
        if len(true_camera_is) and default_select:
            self.cam_selector.current(0)
            self.capture = self.connect_camera(true_camera_is[0])
            self.start_video()
        self.reload_cam['state'] = tk.NORMAL
        self.cam_selector['state'] = tk.READABLE

    def keyPress(self, event):
        """ 何かキーが押された時に実行したい処理 """
        self.master.focus()
        logger.debug(f'PRESS keycode: {event.keycode} keysym: {event.keysym} keysym_num: {event.keysym_num}')
        if self.serial_keyboard:
            self.serial_keyboard.key_press(event.keycode)

    def keyRelease(self, event):
        """ 何かキーが押された時に実行したい処理 """
        self.master.focus()
        logger.debug(f'RELEASE keycode: {event.keycode} keysym: {event.keysym} keysym_num: {event.keysym_num}')
        if self.serial_keyboard:
            self.serial_keyboard.key_release(event.keycode)


def main():
    root = tk.Tk()
    app = Gui(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
