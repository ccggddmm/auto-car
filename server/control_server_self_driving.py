import sys
import cv2
import numpy as np
import socket
import pygame
import struct
import pandas as pd
import threading
import server.predict as predict
import tensorflow as tf
PATH = "dataset"
class Image_Server:
    def __init__(self):
        server_address = ('', 8123)
        self.server_socket = socket.socket()
        self.server_socket.bind(server_address)
        self.angle = 0 # 0 = middle, 1 = left, 2 = right
        self.dataset_filepath = []
        self.dataset_angle = []
        self.prediction = predict.Prediction()
        self.graph = tf.get_default_graph()
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
                    angle = stream_bytes[first_angle+4:last_angle]
                    angle = struct.unpack('f',angle)[0]
                    # print(angle)
                    if last > last_angle:
                        stream_bytes = stream_bytes[last+2:]
                    else:
                        stream_bytes = stream_bytes[last_angle + 4:]
                    stream_bytes = stream_bytes[4:]

                    image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8),  cv2.COLOR_BGR2RGB)
                    #new thread for predicting
                    t_predict_image = threading.Thread(target=self.image_predict, args=(image,))
                    t_predict_image.start()

                    # show current frame (show video in big picture)
                    cv2.imshow('view', image)

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
        global action_server
        with self.graph.as_default():
            steering_angle = self.prediction.predict(image)
            action_server.send_action(steering_angle)


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

        self._value_lock = threading.Lock()

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
        try:
            while True:
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
        with self._value_lock:
            self.connection.write(struct.pack('i',520520520)) #start lable
            self.connection.write(struct.pack('f',action))
            self.connection.write(struct.pack('i',521521521)) #end lable
            self.connection.flush()

def main():
    global image_server,action_server
    image_server = Image_Server()
    action_server = Action_Server()

    t_img_server = threading.Thread(target=image_server.run)
    t_act_server = threading.Thread(target=action_server.run)

    t_img_server.start()
    t_act_server.start()
if __name__ == '__main__':
    main()