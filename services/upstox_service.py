import os
import upstox_client

from dotenv import load_dotenv
from upstox_client.rest import ApiException

load_dotenv()

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
print("TOKEN:", ACCESS_TOKEN[:20])

if not ACCESS_TOKEN:
    raise Exception("UPSTOX_ACCESS_TOKEN not found in .env")

configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

api_client = upstox_client.ApiClient(configuration)

market_api = upstox_client.MarketQuoteApi(api_client)
options_api = upstox_client.OptionsApi(api_client)