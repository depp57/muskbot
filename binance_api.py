from binance.client import Client
import configparser

# Read 'conf.ini' file to get binance API credentials and other constants
parser = configparser.ConfigParser()
parser.read('conf.ini')

API_KEY = parser.get('binance_credentials', 'api_key')
API_KEY_SECRET = parser.get('binance_credentials', 'api_key_secret')

client = Client(API_KEY, API_KEY_SECRET)

# get market depth
depth = client.get_open_orders()
print(depth)