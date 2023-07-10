
# from py5paisa import FivePaisaClient
# import json
# from fastapi import FastAPI, Request, Response
from flask import Flask, render_template, request
# import datetime
# from datetime import datetime, timedelta
# import http
# import logging
# import sys
# import pandas as pd
from order_manager import OrderManager

app = Flask(__name__)
order_manager = OrderManager()
logger = order_manager.logger

@app.route('/')
def index():
    return render_template('token.html')


@app.route('/process', methods=['POST'])
def process():
    token = request.form['token']
    # Perform any necessary background process with the token
    # Replace the example background process with your own logic
    
    # Example: Print the token to the console
    print(f'Token submitted: {token}')
    
    # You can perform any other action with the token here
    
    return "Token submitted successfully"


@app.route("/webhookcallback", methods=['POST'])
# @app.route("/webhookcallback", methods=['GET'])
def hook():
    try:
        data = request.get_json()
        action = data['action']
        remote_id = None
        
        if action != 'exit':
            price = int(data['price'])
            strike_price = (price // 100) * 100
            scrip_code = order_manager.get_scrip_code(strike_price, action)
            print(scrip_code)
            logger.info(f"following order identified: {action} at {strike_price} ")
            
            order_status, remote_id = order_manager.set_order(scrip_code)
            logger.info(f"{action} at {strike_price} with remote_id: {remote_id} with scripcode: {scrip_code}")
            logger.info(f"{order_status}")
        else:
            order_manager.square_off(remote_id)
            logger.info("Square off all orders.")
            # remote_id = None
            
        return "{'message':'OK'}"
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return str(e), 500
    

if __name__ == '__main__':
    try:
        app.run()
    except Exception as e:
        logger.exception(f"Error starting the application: {e}")
