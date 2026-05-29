
import upstox_client

from upstox_client.rest import ApiException


ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1R0FNVlkiLCJqdGkiOiI2OWZlZmI0ODA0MGZlMTc1ZmYzMGViN2MiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlzRXh0ZW5kZWQiOnRydWUsImlhdCI6MTc3ODMxODE1MiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxODA5OTAwMDAwfQ._6jndzKjFXA3p77YWr0uZC0js_WshzNVDm5gCwwHU9g"

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
