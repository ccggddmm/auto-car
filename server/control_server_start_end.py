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
    action_server = Action_Server()

    t_act_server = worker(target=action_server.run)

    t_act_server.start()

    t_act_server.join()

if __name__ == '__main__':
    main()