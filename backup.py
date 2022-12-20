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
    address_variants = ['Ayre', 'Ayrie', 'Aire', 'Aoore', 'Aure', 'Avre']
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
        i = 0
        while i <= len(texts) - 1:
            text_ = texts[i].description
            alt = text_.replace(' ', '')
            for address in address_variants:
                if address.upper() in alt.upper() and response_json['address'] == 'Not found':
                    response_json['address'] = 'Ok'
            if response_json['address'] == 'Not found' and ("401 JUSTISON ST" in text_.upper() or "APT 253" in alt.upper() or "Lilya" in alt):
                response_json['address'] = 'Ok'
            f.write(text_ + "  Split  " + alt +'\n')
            if 'RU' in alt and response_json['user_code'] == 'Not found':
                if len(alt) == 8 and alt.replace('RU', '').isnumeric():
                    response_json['user_code'] = alt
                    response_json['country_code'] = 'RU'
                    break
                elif len(alt) == 2:
                    next = texts[i+1].description.replace(' ', '')
                    if ('c' in next or 'C' in next) and len(next) == 7 and next.upper().replace('C', '').isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'RU'
                        break
                    elif len(next) == 6 and next.isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'RU'
                        break
            elif 'ARM' in alt and response_json['user_code'] == 'Not found':
                if len(alt) == 9 and alt.replace('ARM', '').isnumeric():
                    response_json['user_code'] = alt
                    response_json['country_code'] = 'ARM'
                    break
                elif len(alt) == 3:
                    next = texts[i + 1].description.replace(' ', '')
                    if ('c' in next or 'C' in next) and len(next) == 7 and next.upper().replace('C','').isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'ARM'
                        break
                    elif len(next) == 6 and next.isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'ARM'
                        break
            elif 'GE' in alt and response_json['user_code'] == 'Not found':
                if len(alt) == 7 and alt.replace('GE', '').isnumeric():
                    response_json['user_code'] = alt
                    response_json['country_code'] = 'GE'
                    break
                elif len(alt) == 3:
                    next = texts[i + 1].description.replace(' ', '')
                    if ('c' in next or 'C' in next) and len(next) == 7 and next.upper().replace('C','').isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'ARM'
                        break
                    elif len(next) == 6 and next.isnumeric():
                        response_json['user_code'] = alt + next
                        response_json['country_code'] = 'ARM'
                        break
            elif 'TBS' in text_ or 'TBS' in alt and (text_.replace('TBS', '').isnumeric() or text_.replace('TBS-', '').isnumeric()):
                if '_' in text_ and len(text_) == 11:
                    response_json['user_code'] = text_.replace('-', '')
                    response_json['country_code'] = 'TBS'
                elif len(text_) == 10:
                    response_json['user_code'] = text_
                    response_json['country'] = 'TBS'
            i += 1

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
