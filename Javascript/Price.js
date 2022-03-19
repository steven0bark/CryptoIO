const ccxws = require('ccxws');
const express = require('express');
const app = express();
const time = new Date()

const port = 3500;
const binance = new ccxws.Binance();

const coins = ["BTC","ETH","BNB","ADA","DOGE","XRP", "DOT"];
const data = {
	BTC:{},
	ETH:{},
	BNB:{},
	ADA:{},
	DOGE:{},
	XRP:{},
	DOT:{}
};

binance.on("ticker", ticker => {
	console.log(ticker);
	data[ticker.base] = ticker
	console.log()
	console.log(data[ticker.base])
});

//open websockets
coins.forEach(i => { binance.subscribeTicker(({id: i+"USDT", base: i, quote: "USDT"})) });

app.all('*', function(req, res, next) {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

app.get('/tickers/:base', (req,res) => {
	res.json(data[req.params.base]);
});

app.get('/tickers', (req, res) => {
	res.json(JSON.stringify(coins));
})

app.get('/', (req, res) => {
	res.json(JSON.stringify(data))
});

app.listen(port, () => console.log('listening on ${port}'));


