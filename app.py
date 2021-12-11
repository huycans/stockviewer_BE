from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def welcome():
    return "Welcome to stockviewer app."

@app.route('/get_info', methods=["POST"])
def testpost():
    input_json = request.get_json(force=True) 
    ticker_name = input_json['ticker_symbol']
    ticker = yf.Ticker(ticker_name)
    return jsonify(ticker.info)