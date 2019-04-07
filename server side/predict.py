import numpy as np
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2


class Prediction:
    def __init__(self):
        self.model = load_model('model.h5')

    def img_preprocess(self,img):
        # img = img[:, :, :]
        img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
        img = cv2.GaussianBlur(img, (3, 3), 0)
        img = cv2.resize(img, (160, 120))
        img = img / 255
        return img

    def predict(self,image):
        image = np.asarray(image)
        # print(image)
        image = self.img_preprocess(image)
        image = np.array([image])
        steering_angle = float(self.model.predict(image))
        print("steering angle:{}".format(steering_angle))