import json
import _thread
import hashlib
import jwt
import pytz
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from config import gmail_login, gmail_password, waves_private_key, host, port, jwt_key
from resources.database import *
from resources.diploma import *
from resources.transaction import *


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/auth', methods=['GET'])
@cross_origin()
def authorize():
    login, password = request.args.get('login'), request.args.get('password')
    try:
        user_password, user_role = get_user_data(login)
        if (password != user_password):
            raise Exception("Неверный пароль")

        minutes = 15
        jwt_token = jwt.encode({"sub": "auth", "user": login, "role": user_role, "exp": int(time.time()) + 60 * minutes},
             f"{login}.{password}.{jwt_key}", algorithm="HS256")
        print("Авторизация прошла успешно")
        return jwt_token
    except Exception as ex:
        print("Ошибка авторизации:")
        print(ex)
        return f"Ошибка авторизации:\n{ex}", 404



@app.route('/user', methods=['GET'])
@cross_origin()
def get_user_diplomas():
    try:
        login, token = request.args.get('login'), request.args.get('token')
        password, role = get_user_data(login)
        try:
            decoded_token = jwt.decode(token, f"{login}.{password}.{jwt_key}", algorithms=["HS256"])
            if (decoded_token["exp"] < int(time.time())):
                raise Exception("Время действия токена истекло")

        except Exception as ex:
            raise Exception("Некорректный токен")

        return get_diplomas(case = "user", email = login)
    except Exception as ex:
        print("Не удалось получить информацию о дипломах пользователя:")
        print(ex)
        return f"Не удалось получить информацию о дипломах пользователя:\n{ex}", 400


@app.route('/diplomas', methods=['GET'])
@cross_origin()
def get_all_diplomas():
    try:
        login, token = request.args.get('login'), request.args.get('token')
        password, role = get_user_data(login)
        try:
            decoded_token = jwt.decode(token, f"{login}.{password}.{jwt_key}", algorithms=["HS256"])
            if (decoded_token["exp"] < int(time.time())):
                raise Exception("Время действия токена истекло")

            if (decoded_token["role"] != "admin"):
                raise Exception("Недостаточный уровень доступа")

        except Exception as ex:
            raise Exception("Некорректный токен")

        return get_diplomas(case = "all")
    except Exception as ex:
        print("Не удалось получить информацию о дипломах:")
        print(ex)
        return f"Не удалось получить информацию о дипломах:\n{ex}", 400


@app.route('/request', methods=['GET', 'POST'])
@cross_origin()
def get_request():
    try:
        login, token = request.args.get('login'), request.args.get('token')
        password, role = get_user_data(login)
        try:
            decoded_token = jwt.decode(token, f"{login}.{password}.{jwt_key}", algorithms=["HS256"])
            if (decoded_token["role"] != "admin"):
                raise Exception("Недостаточный уровень доступа")

            if (decoded_token["exp"] < int(time.time())):
                raise Exception("Время действия токена истекло")

        except Exception as ex:
            raise Exception(f"Некорректный токен")

        data = dict(request.get_json())
        date = datetime.now(pytz.timezone('Europe/Moscow')).date()
        print(data)
        print("Получен новый запрос")
        string_to_hash = f'{data["name"]}_{data["surname"]}_{data["course_id"]}'
        hashcode = hashlib.sha256(string_to_hash.encode()).hexdigest()
        link = create_transaction(data["name"], data["surname"], data["course_id"], date.strftime("%d/%m/%Y"), hashcode, waves_private_key)
        create_diploma(name = data["name"], surname = data["surname"], course = data["course"], date = date.strftime("%d.%m.%Y"), link = link)
        add_to_db((*data.values(), hashcode), "diploma")
        send_file(filename = "diploma.pdf", login = gmail_login, password = gmail_password, email = data["email"])
        print("Запрос успешно обработан")
        return "Запрос успешно обработан"
    except Exception as ex:
        print("Не удалось обработать запрос:")
        print(ex)
        return f"Не удалось обработать запрос:\n{ex}", 400


if __name__ == '__main__':
    app.run(host = host, port = port)






