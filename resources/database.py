import json
import sqlite3 as sq
from threading import Lock

db = Lock()

def create_db():
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()

            cur.execute("""CREATE TABLE IF NOT EXISTS diplomas (
                name text not null,
                surname text not null,
                email text not null,
                course text not null,
                course_id integer not null,
                direction text not null,
                portfolio text not null,
                hashcode text not null
                )""")

            print("Таблица requests успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
                hashcode text not null,
                transaction_id text not null,
                date text not null
                )""")

            print("Таблица transactions успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                login text not null,
                password text not null,
                role text not null
                )""")

            print("Таблица users успешно создана")

            cur.close()
    except Exception as ex:
        print("Не удалось создать таблицу:")
        print(ex)


def add_to_db(data, case):
    db.acquire()
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            if case == "diploma":
                cur.execute("""INSERT INTO diplomas (name, surname, email, course, course_id, direction, portfolio, hashcode) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", data)
                print("Данные о запросе успешно сохранены")
            elif case == "transaction":
                cur.execute("""INSERT INTO transactions (hashcode, transaction_id, date) VALUES (?, ?, ?)""", data)
                print("Данные о транзакции успешно сохранены")
            elif case == "user":
                cur.execute("""INSERT INTO users (login, password, role) VALUES (?, ?, ?)""", data)
                print("Данные о пользователе успешно сохранены")
            cur.close()
    except Exception as ex:
        if case == "diploma":
            print("Не удалось сохранить данные о запросе:")
        elif case == "transaction":
            print("Не удалось сохранить данные о транзакции:")
        elif case == "user":
            print("Не удалось сохранить данные о пользователе:")
        if db.locked():
            db.release()
        print(ex)
        raise ex

    if db.locked():
        db.release()


def get_user_data(login):
    db.acquire()
    client = None
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            users = cur.execute("""SELECT * FROM users WHERE login = ?""", (login, ))
            for user in users:
                client = user
            cur.close()
    except Exception as ex:
        print("Не удалось получить данные о пользователе:")
        print(ex)
        if db.locked():
            db.release()
        raise ex   

    if db.locked():
        db.release()

    if (client == None):
        raise Exception("Пользователь с таким логином не найден")

    return client[1], client[2]


def get_diplomas(case = "all", email = ""):
    db.acquire()
    try:
        data = []
        with sq.connect("data.db") as con:
                cur = con.cursor()
                if (case == "all"):
                    diplomas = cur.execute("""SELECT surname, name, direction, course, email, portfolio, date, transaction_id
                         FROM diplomas JOIN transactions ON diplomas.hashcode = transactions.hashcode""")
                elif (case == "user"):
                     diplomas = cur.execute("""SELECT surname, name, direction, course, email, portfolio, date, transaction_id, course_id
                         FROM diplomas JOIN transactions ON diplomas.hashcode = transactions.hashcode
                         WHERE email = ?""", (email, ))
                for diploma in diplomas:
                    dict_data = {}
                    dict_data["surname"] = diploma[0]
                    dict_data["name"] = diploma[1]
                    dict_data["direction"] = diploma[2]
                    dict_data["course"] = diploma[3]
                    dict_data["email"] = diploma[4]
                    dict_data["portfolio"] = diploma[5]
                    dict_data["date"] = diploma[6]
                    dict_data["transaction"] = f'https://wavesexplorer.com/tx/{diploma[7]}'
                    if (case == "user"):
                        dict_data["course_id"] = diploma[8]
                    data.append(dict_data)
                cur.close()
        if db.locked():
            db.release()
        return str(json.dumps(data))
    except Exception as ex:
        print("Не удалось получить данные о дипломах:")
        print(ex)
        if db.locked():
            db.release()
        raise ex