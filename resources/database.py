import json
import sqlite3 as sq
from threading import Lock

db = Lock()

def create_db():
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id integer primary key autoincrement,
                login text not null,
                password text not null,
                role text not null
                )""")

            print("Таблица users успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS diplomas (
                id integer primary key autoincrement,
                student_email text not null,
                course_id integer not null,
                portfolio text not null,
                hashcode text not null
                )""")

            print("Таблица diplomas успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS students (
                id integer primary key autoincrement,
                name text not null,
                surname text not null,
                email text not null
                )""")

            print("Таблица students успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS courses (
                id integer primary key,
                name text not null,
                direction text not null
                )""")

            print("Таблица courses успешно создана")

            cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id integer primary key autoincrement,
                hashcode text not null,
                transaction_id text not null,
                date text not null
                )""")

            print("Таблица transactions успешно создана")

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
                cur.execute("""INSERT INTO diplomas (student_email, course_id, portfolio, hashcode) 
                    VALUES (?, ?, ?, ?)""", data)
                print("Данные о запросе успешно сохранены")
            elif case == "transaction":
                cur.execute("""INSERT INTO transactions (hashcode, transaction_id, date) VALUES (?, ?, ?)""", data)
                print("Данные о транзакции успешно сохранены")
            elif case == "user":
                cur.execute("""INSERT INTO users (login, password, role) VALUES (?, ?, ?)""", data)
                print("Данные о пользователе успешно сохранены")
            elif case == "student":
                cur.execute("""INSERT INTO students (name, surname, email) VALUES (?, ?, ?)""", data)
                print("Данные о студенте успешно сохранены")
            elif case == "course":
                cur.execute("""INSERT INTO courses (id, name, direction) VALUES (?, ?, ?)""", data)
                print("Данные о курсе успешно сохранены")
            cur.close()
    except Exception as ex:
        if case == "diploma":
            print("Не удалось сохранить данные о запросе:")
        elif case == "transaction":
            print("Не удалось сохранить данные о транзакции:")
        elif case == "user":
            print("Не удалось сохранить данные о пользователе:")
        elif case == "student":
            print("Не удалось сохранить данные о студенте:")
        elif case == "course":
            print("Не удалось сохранить данные о курсе:")
        if db.locked():
            db.release()
        print(ex)
        raise ex

    if db.locked():
        db.release()


def get_user_data(login):
    db.acquire()
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            res = cur.execute("""SELECT DISTINCT * FROM users WHERE login = ?""", (login, ))
            user = tuple(*res)
            cur.close()
    except Exception as ex:
        print("Не удалось получить данные о пользователе:")
        print(ex)
        if db.locked():
            db.release()
        raise ex   

    if db.locked():
        db.release()

    if (len(user) != 4):
        raise Exception("Пользователь с таким логином не найден")

    return user[2], user[3]


def get_user_stats(email):
    db.acquire()
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            res = cur.execute("""SELECT COUNT(*) FROM diplomas 
                WHERE diplomas.student_email = ?""", (email, ))

            cnt = tuple(*res)
            res = cur.execute("""SELECT DISTINCT name, surname FROM students 
                WHERE students.email = ?""", (email, ))

            user = tuple(*res)
            if (len(user) != 2 or len(cnt) != 1):
                raise Exception("Пользователь с таким логином не найден")

            name, surname = user[0], user[1]
            dict_data = {"name": name, "surname": surname, "diplomas_count": cnt[0]}
            cur.close()
            if db.locked():
                db.release()

        return str(json.dumps(dict_data))
    except Exception as ex:
        if db.locked():
            db.release()

        raise ex


def get_diploma_info(email, id):
    db.acquire()
    try:
        with sq.connect("data.db") as con:
            cur = con.cursor()
            res = cur.execute("""SELECT DISTINCT
                transactions.transaction_id,
                transactions.date,
                courses.name
                FROM diplomas JOIN transactions ON diplomas.hashcode = transactions.hashcode
                JOIN courses ON diplomas.course_id = courses.id
                WHERE diplomas.student_email = ? AND courses.id = ?""", (email, id))

            diploma = tuple(*res)
            if (len(diploma) != 3):
                raise Exception("Данный пользователь не проходил этот курс")

            dict_data = {"transaction": f'https://wavesexplorer.com/tx/{diploma[0]}', "date": diploma[1], "name": diploma[2]}
            cur.close()
            if db.locked():
                db.release()

        return str(json.dumps(dict_data))
    except Exception as ex:
        if db.locked():
            db.release()

        raise(ex)


def get_diplomas(case = "all", email = ""):
    db.acquire()
    try:
        data = []
        with sq.connect("data.db") as con:
                cur = con.cursor()
                if (case == "all"):
                    diplomas = cur.execute("""SELECT
                        students.name,
                        students.surname,
                        courses.direction,
                        courses.name,
                        students.email,
                        diplomas.portfolio,
                        transactions.date,
                        transactions.transaction_id
                        FROM diplomas JOIN transactions ON diplomas.hashcode = transactions.hashcode
                        JOIN students ON diplomas.student_email = students.email
                        JOIN courses ON diplomas.course_id = courses.id""")
                elif (case == "user"):
                     diplomas = cur.execute("""SELECT
                        students.name,
                        students.surname,
                        courses.direction,
                        courses.name,
                        students.email,
                        diplomas.portfolio,
                        transactions.date,
                        transactions.transaction_id,
                        courses.id
                        FROM diplomas JOIN transactions ON diplomas.hashcode = transactions.hashcode
                        JOIN students ON diplomas.student_email = students.email
                        JOIN courses ON diplomas.course_id = courses.id
                        WHERE students.email = ?""", (email, ))

                for diploma in diplomas:
                    dict_data = {}
                    dict_data["name"] = diploma[0]
                    dict_data["surname"] = diploma[1]
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
        if db.locked():
            db.release()

        raise ex
