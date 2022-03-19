from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import mysql.connector
import sys
import os

db = mysql.connector.connect(host="localhost",
                             username="root",
                             password=os.getenv('db_password'),
                             database="crypto_db")


def acct(args, keys: dict) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT * from users where apikey='" + keys['apikey'] +
                   "' and secretkey='" + keys['secretkey'] + "'")
    profile = cursor.fetchall()
    if len(profile) > 0:
        return {
            "userid": profile[0][0],
            "username": profile[0][1],
            "apikey": profile[0][3],
            "secretkey": profile[0][4]
        }
    else:
        return {}


def getprice(args) -> dict:
    res = requests.get("http://localhost:3500/tickers/" + args[2])
    data = json.loads(res.text)
    price = data["last"]
    return {args[2]: price}


def getpositions(args, data) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT * from positions where userid='" +
                   str(data['userid']) + "'")
    pos = cursor.fetchall()[0]
    return {
        "BTC": pos[1],
        "ETH": pos[2],
        "BNB": pos[3],
        "ADA": pos[4],
        "DOGE": pos[5],
        "XRP": pos[6],
        "DOT": pos[7]
    }


def getcash(args, data) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT cash from users where userid=" +
                   str(data["userid"]))
    return {"cash": float(cursor.fetchall()[0][0])}


def maketrade(args, data) -> dict:
    ticker = getdata(["", "", data["coin"]])
    currentcash = getcash(args, data)
    cash = currentcash["cash"]
    pos = getpositions(args, data)
    coin = data["coin"]
    if data["side"]:
        price = float(ticker["ask"])
        if cash >= (price * data["amt"]):
            cursor = db.cursor()
            cursor.execute("UPDATE positions SET " + coin + "= " +
                           str(pos[coin] + data["amt"]) + " where userid= " +
                           str(int(data["userid"])))
            db.commit()
            # subtract cash from account table
            cursor = db.cursor()
            cursor.execute("UPDATE users SET cash= " +
                           str(float(cash - (price * data["amt"]))) +
                           " where userid= " + str(int(data["userid"])))
            db.commit()
            return {
                "result": "success",
                "coin": data["coin"],
                'trade_info': {
                    "side": "buy",
                    "amt": data["amt"],
                    "price": price,
                    'time': ticker["timestamp"]
                }
            }
        else:
            return {"result": "failure", "reason": "Insufficient funds"}
    else:
        price = float(ticker["bid"])
        if pos[coin] >= data["amt"]:
            cursor = db.cursor()
            cursor.execute("UPDATE positions SET " + coin + "= " +
                           str(pos[coin] - data["amt"]) + " where userid= " +
                           str(int(data["userid"])))
            db.commit()
            cursor = db.cursor()
            cursor.execute("UPDATE users SET cash= " +
                           str(float(cash + (price * data["amt"]))) +
                           " where userid= " + str(int(data["userid"])))
            db.commit()
            return {
                "result": "success",
                "coin": data["coin"],
                'trade_info': {
                    "side": "sell",
                    "amt": data["amt"],
                    "price": price,
                    "time": ticker["timestamp"]
                }
            }
        else:
            return {"result": "failure", "reason": "Insufficient assets"}


def getdata(args) -> dict:
    if len(args) > 2:
        res = requests.get('http://localhost:3500/tickers/' + args[2])
        return res.json()


def getall(args, data) -> dict:
    res = requests.get('http://localhost:3500/')
    return json.loads(res.json())


def hello(args):
    print("hello")


getpaths = {
    '': hello,
    "data": getdata,
    "price": getprice,
}

postpaths = {
    "trade": maketrade,
    "acct": acct,
    "positions": getpositions,
    "cash": getcash,
    "all": getall
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("request received")
        self.send_response(200)
        args = self.path.split("/")

        func = getpaths.get(args[1])
        result = func(args)
        self.send_header('Content Type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(result), 'utf-8'))
        self.send_response(4)

    def do_POST(self):
        print(" post request recieved")
        self.send_response(200)
        args = self.path.split("/")
        content_len = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(content_len))
        func = postpaths.get(args[1])
        result = func(args, data)
        self.send_header("Content Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(result), 'utf-8'))
        self.send_response(4)


def main():
    server = HTTPServer(('', 3000), Handler)
    print('serving in port ' + str(3000))
    server.serve_forever()
    db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        db.close()
        sys.exit(0)
