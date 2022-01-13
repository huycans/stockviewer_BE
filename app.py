from flask import Flask, json, request, jsonify, Response
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET', 'POST'])
def welcome():
    return "Welcome to stockviewer app."


@app.route('/get_info', methods=["POST"])
def getInfo():
    input_json = request.get_json(force=True)
    ticker_name = input_json['ticker_symbol']
    ticker = yf.Ticker(ticker_name)
    # get ticker's price history
    # .to_json(orient="split", date_format="epoch", date_unit="ms")
    close_price_history_obj = ticker.history(
        period="max", interval="1d")["Close"]
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
            "status": "error",
            "data": {},
            'error': {
                "code": "404",
                "name": "Ticker symbol not found",
                "description": "Ticker symbol not found"
            }
        })
    else:
        return jsonify({
            "status": "ok",
            "data": {
                "info": ticker.info,
                "price_history": close_price_history_arr
            },
            'error': {}
        })

    '''
        response object shape: 
        {
            "status": "ok" or "error",
            "data": can be [...] or {...}, default is {}
            "error": {
                "code": "",
                "name": "",
                "description": ""
            }
        }
        '''

# this error handler will handle both HTTPException and normal Python's exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        response = e.get_response()
        # replace the body with JSON
        response.data = json.dumps({
            "status": "error",
            "data": {},
            'error': {
                "code": e.code,
                "name": e.name,
                "description": e.description,
            }
        })
        response.content_type = "application/json"
        return response

    # now you're handling non-HTTP exceptions only
    else: 
        return Response(json.dumps({
            "status": "error",
            "data": {},
            'error': {
                "code": 500,
                "name": "Server error",
                "description": "Server has encountered an error. Please try again.",
            }
        }), status=500, mimetype='application/json')