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
    
    # transform time format to milliseconds to fit highcharts format
    # an array of int64 epoch time in milliseconds
    epoch_time_arr = close_price_history_obj.index.astype(np.int64)
    epoch_time_arr = (epoch_time_arr/1000000).astype(np.int64)

    # array to store price history in the shape of [[<time>, <price>], ...]
    close_price_history_arr = []    
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

@app.route('/get_list', methods=["POST"])
def getList():
    input_json = request.get_json(force=True)
    ticker_list = input_json['ticker_list']
    
    # STAGE 1: fetch price history on monthly basis
    # ticker names ticker_list should be all caps, separated by space
    # if name do not exist, yfinance will eliminate it  
    download = yf.download(
        tickers = ticker_list,
        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "1y",
        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval = "1mo",
        # group by ticker (to access via data['SPY'])
        # (optional, default is 'column')
        group_by = 'column',
        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust = True,
    )
    
    # use only Close price column
    close_column = download["Close"]
    # drop a row if  it contains only NaN and fill
    close_column = close_column.dropna(axis='index', how='all')
    close_column = close_column.fillna(axis='index', value=0)
    
    # convert timestamps from nanosec to millisec
    epoch_time_list = (close_column.index.astype(np.int64)/1000000).astype(np.int64).tolist()

    # get a list of columns, aka ticker names from the Close column
    ticker_name_arr = close_column.columns
    
    # create a dict with this format: 
    # {
    #   <ticker_name>: [price_history],...
    # }
    close_price_history = {}
    for ticker in (ticker_name_arr):
        close_price_history[ticker] = close_column[ticker].tolist()
    
    # TODO: concurrency, fetch these two in parallel
    # STAGE 2: fetch tickers info
    info = {}
    tickers = yf.Tickers(ticker_list);
    for ticker in tickers.tickers:
      info[ticker] = tickers.tickers[ticker].info
    
    
    return jsonify({
        "status": "ok",
            "data": {
                "timestamps":  epoch_time_list,
                "tickers_price_history": close_price_history,
                "info": info,
            },
            'error': {}
    })
    
    # error handling for unknown symbols
    
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