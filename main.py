import io
import os
import shutil
import requests
from fastapi import FastAPI
from google.cloud import vision
from pydantic import BaseModel

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'token.json'

def detect_text(path):
    response_json = {}
    address_variants = ['Ayre', 'Ayrie', 'Aire', 'Aoore', 'Aure']
    response_json['address'] = 'Not found'
    response_json['user_code'] = 'Not found'
    response_json['status'] = 'Not Ok'
    response_json['country_code'] = 'Not found'
    response = requests.get(path,  stream=True)
    with open('image.jpg', 'wb') as file:
        shutil.copyfileobj(response.raw, file)

    client = vision.ImageAnnotatorClient()
    with io.open('image.jpg', 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    with open('description.txt', 'w') as f:
        for text in texts:
            text_ = text.description
            for address in address_variants:
                if address.upper() in text_.upper() and response_json['address'] == 'Not found':
                    response_json['address'] = 'Ok'
            if response_json['address'] == 'Not found' and ("401 JUSTISON ST" in text_.upper() or "APT 253" in text_.upper() or "Lilya Tadevosyan" in text_):
                response_json['address'] = 'Ok'
            alt = text_.replace(' ', '')
            f.write(text_ + "Split" + alt +'\n')
            if (('ARM' in text_ or 'ARM' in alt) and len(text_) == 9 and text_.replace('ARM', '').isnumeric()) or (
                    'ARM' in text_ and 'c' in text_ and len(text_) == 10 and text_.replace('ARMc', '').isnumeric()) :
                response_json['user_code'] = text_
                response_json['country_code'] = 'ARM'
            elif ('RU' in text_ or 'RU' in alt) and len(text_) == 8 and text_.replace('RU', '').isnumeric():
                response_json['user_code'] = text_
                response_json['country_code'] = 'RU'
            elif ('GE' in text_ or 'GE' in alt) and len(text_) == 7 and 'POSTAGE' not in text_ and text_.replace('GE', '').isnumeric():
                response_json['user_code'] = text_
                response_json['country_code'] = 'GE'
            elif 'TBS' in text_ or 'TBS' in alt and (text_.replace('TBS', '').isnumeric() or text_.replace('TBS-', '').isnumeric()):
                if '_' in text_ and len(text_) == 11:
                    response_json['user_code'] = text_.replace('-', '')
                    response_json['country_code'] = 'TBS'
                elif len(text_) == 10:
                    response_json['user_code'] = text_
                    response_json['country'] = 'TBS'

    if response_json['address'] == 'Ok' and response_json['user_code'] != 'Not found':
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
