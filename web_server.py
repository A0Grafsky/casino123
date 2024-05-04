import json

import fastapi.responses
from fastapi import FastAPI, Request
import requests
from fastapi.responses import JSONResponse, FileResponse
from starlette.templating import Jinja2Templates
from database import database as db

app = FastAPI()
templates = Jinja2Templates(directory='templates')



@app.get('/scan')
async def get_scan(request: Request):
    return FileResponse('templates/index.html')

@app.get('/scanbonus')
async def scan_bonus(request: Request):
    user_id = request.query_params.get('user_id')
    return templates.TemplateResponse('bonus.html', {'request': request, 'user_id': user_id})

@app.get('/bonus')
async def bonus(request: Request):
    user_id = request.query_params.get('user_id')
    count = request.query_params.get('count')
    await db.give_bonus(float(count), int(user_id))
    # Теперь можно обрабатывать данные дальше, например, добавить логику на основе user_id и count
    return FileResponse('templates/succes_bonus.html')

@app.get("/transactions")
async def read_root(request: Request):
    user_id = request.query_params.get('user_id')
    data = []
    with open('exchange_data.json', 'r', encoding='utf-8') as file:
        for i in json.load(file):
            if i['id'] == int(user_id):
                data.append(i)
    return JSONResponse(content=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
