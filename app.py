from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def welcome():
    return "Welcome to stockviewer app."

@app.route('/get_info', methods=["POST"])
def testpost():
    input_json = request.get_json(force=True) 
    ticker_name = input_json['ticker_symbol']
    ticker = yf.Ticker(ticker_name)
    # get ticker's price history
    close_price_history_obj = ticker.history(period="max", interval="1d")["Close"]#.to_json(orient="split", date_format="epoch", date_unit="ms")
    # transform price history into array of [<time>, <price>]
    close_price_history_arr = []
    # an array of int64 epoch time in milliseconds
    epoch_time_arr = close_price_history_obj.index.astype(np.int64)
    epoch_time_arr = (epoch_time_arr/1000000).astype(np.int64)
    
    # create an array like this: [<time>, <price>]
    for idx, time in enumerate(epoch_time_arr):
        price = close_price_history_obj.values[idx]
        close_price_history_arr.append([time, price])
    
    # if symbol does not exist in yfinance
    if ('symbol' not in ticker.info):
        return jsonify({
            'error': "Ticker symbol not found"
        })
    else:
        return jsonify({
            "info": ticker.info,
            "price_history": close_price_history_arr
        })