
import upstox_client

from upstox_client.rest import ApiException


ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1R0FNVlkiLCJqdGkiOiI2YTBmZTAwMDQxMjg2ZjI0MTk3MzhmOWQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc3OTQyNTI4MCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzc5NDg3MjAwfQ.TID9GkWHBG5BwjNbhWYRibkxvvcmqOSLBFBt5y0-m_o"

configuration = upstox_client.Configuration()

configuration.access_token = ACCESS_TOKEN

api_client = upstox_client.ApiClient(
    configuration
)

# MARKET QUOTES
market_api = upstox_client.MarketQuoteApi(
    api_client
)

# OPTION CONTRACTS
options_api = upstox_client.OptionsApi(
    api_client
)