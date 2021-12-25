from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf

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
    if ('symbol' not in ticker.info):
        return jsonify({
            'error': "Ticker symbol not found"
        })
    else:
        return jsonify(ticker.info)