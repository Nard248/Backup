import io
import os
import shutil

import cv2
import requests
from fastapi import FastAPI
from google.cloud import vision
from pydantic import BaseModel
from pyzbar.pyzbar import decode

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'token.json'


def resize_image(path):
    image = cv2.imread(path)
    height = image.shape[0]
    width = image.shape[1]
    size = (1500, int((1500 / width) * height))
    image_resized = cv2.resize(image, dsize=size)
    return image_resized


def detect_text(path):
    response_json = {}
    address_variants = ['Ayre', 'Ayrie', 'Aire', 'Aoore', 'Aure']
    response_json['address'] = 'Not found'
    response_json['user_code'] = 'Not found'
    response_json['tracking_code'] = 'Not found'
    response_json['status'] = 'Not Ok'
    response_json['country_code'] = 'Not found'
    # image = imread('https://media.geeksforgeeks.org/wp-content/uploads/20210318103632/gfg-300x300.png')
    response = requests.get(path,  stream=True)
    with open('image.jpg', 'wb') as file:
        shutil.copyfileobj(response.raw, file)

    client = vision.ImageAnnotatorClient()
    with io.open('image.jpg', 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    for text in texts:
        text_ = text.description
        for address in address_variants:
            if address.upper() in text_.upper() and response_json['address'] == 'Not found':
                response_json['address'] = 'Ok'
        if response_json['address'] == 'Not found' and ("401 JUSTISON ST" in text_.upper() or "APT 253" in text_.upper() or "Lilya Tadevosyan" in text_):
            response_json['address'] = 'Ok'
        if 'RU' in text_ and len(text_) == 8:
            response_json['user_code'] = text_
            response_json['country_code'] = 'RU'
        elif ('ARM' in text_ and len(text_) == 9) or ('ARM' in text_ and 'c' in text_ and len(text_) == 10):
            response_json['user_code'] = text_
            response_json['country_code'] = 'ARM'
        elif 'GE' in text_ and len(text_) == 7 and 'POSTAGE' not in text_:
            response_json['user_code'] = text_
            response_json['country_code'] = 'GE'
        elif 'TBS' in text_:
            if '_' in text_ and len(text_) == 11:
                response_json['user_code'] = text_.replace('-', '')
                response_json['country_code'] = 'TBS'
            elif len(text_) == 10:
                response_json['user_code'] = text_
                response_json['country_pip install python-barcodecode'] = 'TBS'

    # image_ = Image.open('image.jpg')
    image_ = resize_image('image.jpg')
    decoded = decode(image_)
    tracks = []
    for i in range(len(decoded)):
        tracks.append(str(decoded[i].data.decode('utf-8')))
    response_json['tracking_code_check'] = tracks
    if len(tracks) == 0:
        response_json['tracking_code'] = 'Not found'
    else:
        for track in tracks:
            if '1Z' in track and response_json['tracking_code'] == 'Not found':
                response_json['tracking_code'] = track
            elif '420' in track and len(track) >= 8 and response_json['tracking_code'] == 'Not found':
                response_json['tracking_code'] = track
            elif len(track) >= 8 and response_json['tracking_code'] == 'Not found':
                response_json['tracking_code'] = track
        # if len(decoded) == 3 and response_json['tracking_code'] == 'Not found':
        #     response_json['tracking_code'] = tracks[1]
        # elif len(decoded) == 2 and response_json['tracking_code'] == 'Not found':
        #     response_json['tracking_code'] = tracks[1]
        # elif len(decoded) == 1 and response_json['tracking_code'] == 'Not found':
        #     response_json['tracking_code'] = tracks[0]
    if response_json['address'] == 'Ok' and response_json['tracking_code'] != 'Not found' and response_json['user_code'] != 'Not found':
        response_json['status'] = 'Ok'

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return response_json



class Item(BaseModel):
    path: str


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item):
    return detect_text(item.path)
#print(detect_text("https://media.geeksforgeeks.org/wp-content/uploads/20210318103632/gfg-300x300.png"))