from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    path: str


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item):
    return item