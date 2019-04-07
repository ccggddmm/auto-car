import io
import socket
import struct
import time
import picamera
import threading

from controlTest import control

SERVER_IP = "10.0.3.154"


class Image_Client:
    def __init__(self):
        self.server_address = (SERVER_IP,8123)
        self.clinet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        print("image client:start")
        self.clinet_socket.connect(self.server_address)
        self.connection = self.clinet_socket.makefile("wb")
        print("image client:connected")
        try:
            with picamera.PiCamera() as camera:
                camera.resolution = (160,120)
                camera.framerate = 15
                time.sleep(2)
                stream = io.BytesIO()
                for foo in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
                    self.connection.write(struct.pack('<L', stream.tell()))
                    self.connection.flush()
                    stream.seek(0)
                    self.connection.write(stream.read())
                    angle = control.get_angle()
                    self.connection.write(struct.pack('i',520520520)) #start lable
                    self.connection.write(struct.pack('f',angle))
                    self.connection.write(struct.pack('i',521521521)) #end lable
                    stream.seek(0)
                    stream.truncate()

            self.connection.write(struct.pack('<L', 0))
        except socket.error as e:
            print("image client ERROR")
            print(e)
        finally:
            self.connection.close()
            self.clinet_socket.close()
            print ('image client:connection closed')
            
class Action_Client:
    #this client used to recive action from the srever 
    def __init__(self):
        self.server_address = (SERVER_IP,8124)
        self.clinet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.MID = 0
        self.LEFT = 1
        self.RIGHT = 2
        self.UP = 3
        self.DOWN = 4
    def run(self):
        print("action client:start")
        self.clinet_socket.connect(self.server_address)
        self.connection = self.clinet_socket.makefile("rb")
        print("action client:connected")
        try:
            stream_bytes = b''
            while True:
                stream_bytes += self.connection.read(12)
                first = stream_bytes.find(struct.pack('i',520520520))
                last = stream_bytes.find(struct.pack('i',521521521)) 
                print("first:{} \n last:{}\n".format(first,last))
                if first != -1 and last != -1:
                    action = struct.unpack('i',stream_bytes[first+4:last])[0]
                    stream_bytes = stream_bytes[last+4:]
                    print(action)
                    self.do_action(action)
        except socket.error as e:
            print("action client ERROR")
            print(e)
        finally:
            self.connection.close()
            self.clinet_socket.close()
            print ('action client:connection closed')
    def do_action(self,action):
        if action == self.UP:
            control.speed_up()
        elif action == self.LEFT:
            control.turn_left()
        elif action == self.RIGHT:
            control.turn_right()
        elif action == self.MID:
            control.turn_back()
        elif action == self.DOWN:
            control.speed_down()
   


if __name__ == '__main__':
    image_client = Image_Client()
    action_client = Action_Client()
    t_img_client = threading.Thread(target=image_client.run)
    t_act_client = threading.Thread(target=action_client.run)
    
    t_img_client.start()
    t_act_client.start()