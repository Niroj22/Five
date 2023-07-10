from py5paisa import FivePaisaClient
import json
from datetime import datetime, timedelta
# import http
import logging
import sys
import pandas as pd
# import contextlib

class OrderManager:
    def __init__(self):
        self.logger = self.setup_logger()
        self.expiry = self.get_next_thursday()
        self.codes = self.get_codes_ready()     
        self.client = self.login_from_file()

    def setup_logger(self):
        logger = logging.getLogger()

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

        stdout_handler = logging.StreamHandler(stream = sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)

        stdout_handler.setFormatter(formatter)

        file_handler = logging.FileHandler('logs.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
        return logger
    
    def get_codes_ready(self):
        try:
            scripcodes = pd.read_csv('https://images.5paisa.com/website/scripmaster-csv-format.csv', usecols=['Scripcode', 'FullName'])
            codes = scripcodes[scripcodes['FullName'].str.contains('.*BANKNIFTY.*')]
            codes = codes[codes['FullName'].str.contains(str(self.expiry))]
            return codes
        except Exception as e:
            self.logger.exception(f"Error initializing OrderManager (filtering scrip codes): {e}")
            raise
        
    def login_from_file(self):
        try:
            with open('login_details.json') as f:
                login_args = json.load(f)
            with open('cred_details.json') as f:
                cred = json.load(f)
            
            client = FivePaisaClient(cred=cred)
            response_token = str(input('enter your totka : '))
            client.get_access_token(response_token)          
          
            original_stdout = sys.stdout # Save a reference to the original standard output

            with open('logs.log', 'a') as f:
                sys.stdout = f # Change the standard output to the file we created.
                print(client.login())
                
                sys.stdout = original_stdout
            # self.logger.info(f"login status is: {status}")
            
            return  client #status, client 
        
        except Exception as e:
            self.logger.exception(f"Error logging in to 5paisa: {e}")
            raise
    
    def get_scrip_code(self, strikeprice, action):
        try:
            #action can be 'CE' or 'PE' which we get from trading view
            search_string = 'BANKNIFTY '+ self.expiry+ ' '+ action + ' ' + str(strikeprice) + '.00'
            print(search_string)
            self.logger.info(f"search for {search_string}")
            scripcode = self.codes[self.codes['FullName'] == search_string]['Scripcode']
            return scripcode.values
        except Exception as e:
            self.logger.exception(f"Error getting scrip code for option : {e}")
            raise
        
    def get_next_thursday(self):
        current_date = datetime.now()
        self.logger.info(f"\n\n------------{current_date}----------")
        while current_date.weekday() != 3:  # 3 represents Thursday (Monday is 0)
            current_date += timedelta(days=1)
        thursday_formatted = current_date.strftime("%d %b %Y")
        expiry = thursday_formatted
        self.logger.info(f"next expiry is on {expiry}")
        return expiry

    def set_order(self, scrip_code):
        try:
            remote_id = 'rid_'+str(datetime.now())
            # Place the order
            ## order_status = self.client.place_order(OrderType='B',Exchange='N',ExchangeType='C', ScripCode = scrip_code, Qty=1, Price=350, IsIntraday=False, StopLossPrice=345, RemoteOrderID =remote_id) #exchange type D for derivatives
            order_status = self.client.place_order(OrderType='B',Exchange='N',ExchangeType='D', ScripCode = scrip_code, Qty=1, Price=0, IsIntraday=True, RemoteOrderID =remote_id)
            # D for derivative excange type
            # price 0 for market order
            # OrderType = 'B' or 'S' for Buy or Sell #we are not using sell because the scrip code will be different
            
            # order_status = 'success'
            self.logger.info(f"{datetime.now()} Placed order. Order status: {order_status}, Remote ID: {remote_id}")
            return order_status, remote_id
        except Exception as e:
            self.logger.exception(f"Error placing order: {e}")
            raise

    def square_off(self, remote_id):
        try:
            # Square off all orders
            exitstatus = self.client.squareoff_all()
            self.logger.info(f"Square off all orders, status is: {exitstatus}")
            #fetch order status
            req_list_= [
            {
                "Exch": "N",
                "RemoteOrderID": remote_id
            }]
            order_status = self.client.fetch_order_status(req_list_)
            # order_status = 'success'
            self.logger.info(f"order status for remote_id: {remote_id} is {order_status}")
            return order_status
        except Exception as e:
            self.logger.exception(f"Error during square off: {e}")
            raise
