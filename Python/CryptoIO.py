import requests
import os
import json


class CryptoIO:
    def __init__(self, apikey: str = None, secretkey: str = None):
        self.coins = ["BTC", "ETH", "BNB", "ADA", "DOGE", "XRP", "DOT"]
        if apikey is None:
            apikey = os.getenv('CryptoIO_APIKEY')
        if secretkey is None:
            secretkey = os.getenv('CyptoIO_SECRETKEY')
        self.keys = {"apikey": apikey, "secretkey": secretkey}
        if self.keys["apikey"] is None or self.keys[
                "secretkey"] is None or not self.verify_user():
            raise InvalidCredentials()

    def verify_user(self):
        res = requests.post("http://localhost:3000/acct", json=self.keys)
        data = json.loads(res.text)
        try:
            if data["userid"] is not None:
                self.keys = data
                return True
        except KeyError:
            return False

    def get_account(self):
        return self.keys

    def get_total(self) -> float:
        positions = self.get_positions()
        data = self.get_all_data()
        toreturn = 0.0
        for sym in self.coins:
            toreturn = toreturn + (float(data[sym]["last"]) * positions[sym])
        return toreturn

    def get_cash(self) -> float:
        res = requests.post("http://localhost:3000/cash", json=self.keys)
        return json.loads(res.text)["cash"]

    def check_if_tradable(self, ticker: str) -> bool:
        return ticker in self.coins

    def get_all_data(self) -> dict:
        res = requests.post("http://localhost:3000/all", json=self.keys)
        return res.json()

    def get_assets(self) -> list:
        return self.coins

    def get_positions(self) -> dict:
        res = requests.post("http://localhost:3000/positions", json=self.keys)
        return res.json()

    def get_price(self, sym: str) -> float:
        res = requests.get("http://localhost:3000/price/" + sym)
        return res.json()[sym]

    def trade(self, coin: str, amt: int, buy: bool) -> dict:
        assert self.check_if_tradable(coin)
        res = requests.post(
            "http://localhost:3000/trade",
            json.dumps({
                "coin": coin,
                "amt": amt,
                "side": buy,
                "userid": self.keys["userid"]
            }))
        result = json.loads(res.text)
        if result["result"] == "failure":
            raise InvalidTradeException(result["reason"])
        else:
            return result


class InvalidCredentials(Exception):
    def __init__(self):
        self.message = "InvalidCredentials"


class InvalidTradeException(Exception):
    def __init__(self, mes):
        self.message = mes
