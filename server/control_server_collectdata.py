import _thread
import datetime
import sys
import cv2
import numpy as np
import socket
import pygame
import struct
import pandas as pd
from PIL import Image
import threading
from multiprocessing import Process as worker

PATH = "dataset"
class Image_Server:
    def __init__(self):
        server_address = ('', 8123)
        self.server_socket = socket.socket()
        self.server_socket.bind(server_address)
        self.angle = 0 # 0 = middle, 1 = left, 2 = right
        self.dataset_filepath = []
        self.dataset_angle = []

    def run(self):
        self.server_socket.listen(0)
        print("image server:start")
        # accept one client's connection
        self.connection, self.address = self.server_socket.accept()
        self.connection = self.connection.makefile('rb')
        print("image server:receiving")
        # get the video stream from our raspberry pi
        try:
            stream_bytes = b' '
            while True:
                stream_bytes += self.connection.read(1024)
                first = stream_bytes.find(b'\xff\xd8')
                last = stream_bytes.find(b'\xff\xd9')
                first_angle = stream_bytes.find(struct.pack('i',520520520))
                last_angle = stream_bytes.find(struct.pack('i',521521521))
                if first != -1 and last != -1 and first_angle != -1 and last_angle!=-1:
                    jpg = stream_bytes[first:last + 2]
                    angle = stream_bytes[first_angle+4:last_angle-4]
                    speed = stream_bytes[first_angle+8:last_angle]
                    angle = struct.unpack('f',angle)[0]
                    speed = struct.unpack('f',speed)[0]
                    # print("angle:{},speed:{}".format(angle,speed))
                    if last > last_angle:
                        stream_bytes = stream_bytes[last+2:]
                    else:
                        stream_bytes = stream_bytes[last_angle + 4:]
                    stream_bytes = stream_bytes[4:]

                    image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8),  cv2.COLOR_BGR2RGB)
                    # show current frame (show video in big picture)
                    cv2.imshow('view', image)
                    #new thread for saving image
                    if speed>0: #only store data when speed > 0
                        _thread.start_new_thread(self.save_image, (image,angle))
                    key = cv2.waitKey(1)
                    if key == 27:
                        break
        except Exception as e:
            print(e)
        finally:
            # self.server_socket.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            self.server_socket.close()

            dataframe = pd.DataFrame({'filepath': self.dataset_filepath, 'steering': self.dataset_angle})
            dataframe.to_csv("data.csv", index=False, sep=',')
            print('connection closed')
            sys.exit()
    def image_predict(self,image):
        with self.graph.as_default():
            self.prediction.predict(image)
    def save_image(self,image,angle):
        # save file
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        now = datetime.datetime.now()
        im = Image.fromarray(image)
        filename = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-" + str(now.hour) + "-" + str(
            now.minute) + "-" + str(now.second) + " " + str(now.microsecond)
        filePath = PATH + "\\" + filename + ".jpeg"
        im.save(filePath)
        self.dataset_filepath.append(filePath)
        self.dataset_angle.append(angle)

class Action_Server:
    def __init__(self):

        self.running = False # if the car is running-> True, else False

        server_address = ('', 8124)
        self.server_socket = socket.socket()
        self.server_socket.bind(server_address)

        self.angle = -1
        self.MID = 0
        self.LEFT = 1
        self.RIGHT = 2
        self.UP = 3
        self.DOWN = 4


    def run(self):
        self.server_socket.listen(0)
        print("action server:start")
        # accept one client's connection
        self.connection, self.address = self.server_socket.accept()
        self.connection = self.connection.makefile('wb')
        print("action server:sending")
        # initialize pygame for keybord control
        pygame.init()
        display_width = 400
        display_height = 300
        pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('Super Manless Car')
        # sending action to raspberry pi
        fps = 120
        clock = pygame.time.Clock()
        clock.tick(fps)

        try:
            while True:
                clock.tick(fps)

                # pygame.time.wait(0)
                self.key_event()
        except Exception as e:
            print(e)
        finally:
            self.connection.close()
            self.server_socket.close()
    def key_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and not self.running:
                    self.running = True
                    self.send_action(self.UP)
                    print("UP")
                if event.key == pygame.K_LEFT and not self.angle == self.LEFT:
                    self.angle = self.LEFT
                    self.send_action(self.LEFT)
                    print("LEFT")
                if event.key == pygame.K_RIGHT and not self.angle == self.RIGHT:
                    self.angle = self.RIGHT
                    self.send_action(self.RIGHT)
                    print("RIGHT")
                if event.key == pygame.K_DOWN:
                    self.running = False
                    self.send_action(self.DOWN)
                    print("DOWN")
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.running = False
                    self.send_action(self.DOWN)
                    print("UP_release")
                if event.key == pygame.K_LEFT:
                    self.angle = self.MID
                    self.send_action(self.MID)
                    print("LEFT_release")
                if event.key == pygame.K_RIGHT:
                    self.angle = self.MID
                    self.send_action(self.MID)
                    print("RIGHT_release")

    def send_action(self,action):
        self.connection.write(struct.pack('i',520520520)) #start lable
        self.connection.write(struct.pack('f',action))
        self.connection.write(struct.pack('i',521521521)) #start lable
        self.connection.flush()

def main():
    image_server = Image_Server()
    action_server = Action_Server()

    t_img_server = worker(target=image_server.run)
    t_act_server = worker(target=action_server.run)

    t_img_server.start()
    t_act_server.start()

    t_img_server.join()
    t_act_server.join()

if __name__ == '__main__':
    main()