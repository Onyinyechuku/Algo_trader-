import requests
import pandas as pd
import json
import constants.defs as defs
from dateutil import parser
from datetime import datetime as dt
from infrastructure.instrument_collection import instrumentCollection as ic


class OandaApi:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {defs.API_KEY}",
            "Content-Type": "application/json"
        })

    def make_request(self, url, verb='get', code=200, params=None, data=None, headers=None):
        full_url = f"{defs.OANDA_URL}/{url}"

        if data is not None:
            data = json.dumps(data)

        # Merge default session headers with any custom headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            if verb.lower() == "get":
                response = self.session.get(full_url, params=params, headers=request_headers)
            elif verb.lower() == "post":
                response = self.session.post(full_url, params=params, data=data, headers=request_headers)
            else:
                return False, {'error': f'Unsupported HTTP verb: {verb}'}

            if response.status_code == code:
                return True, response.json()
            else:
                return False, response.json()

        except Exception as error:
            return False, {'Exception': str(error)}

    def get_account_ep(self, ep, data_key):
        url = f"accounts/{defs.ACCOUNT_ID}/{ep}"
        ok, data = self.make_request(url)

        if ok and data_key in data:
            return data[data_key]
        else:
            print("ERROR get_account_ep()", data)
            return None

    def get_account_summary(self):
        return self.get_account_ep("summary", "account")

    def get_account_instruments(self):
        return self.get_account_ep("instruments", "instruments")

    def fetch_candles(self, pair_name, count=10, granularity="H1",
                        price="MBA", date_f=None, date_t=None):
        url = f"instruments/{pair_name}/candles"
        params = dict(
            granularity=granularity,
            price=price
        )

        if date_f and date_t:
            date_format = "%Y-%m-%dT%H:%M:%SZ"
            params["from"] = dt.strftime(date_f, date_format)
            params["to"] = dt.strftime(date_t, date_format)
        else:
            params["count"] = count

        ok, data = self.make_request(url, params=params)

        if ok and 'candles' in data:
            return data['candles']
        else:
            print("ERROR fetch_candles()", params, data)
            return None

    def get_candles_df(self, pair_name, **kwargs):
        data = self.fetch_candles(pair_name, **kwargs)

        if not data:
            return pd.DataFrame()

        final_data = []
        for candle in data:
            if not candle['complete']:
                continue
            new_dict = {
                'time': parser.parse(candle['time']),
                'volume': candle['volume']
            }
            for p in ['mid', 'bid', 'ask']:
                if p in candle:
                    for o in ['o', 'h', 'l', 'c']:
                        new_dict[f"{p}_{o}"] = float(candle[p][o])
            final_data.append(new_dict)

        return pd.DataFrame(final_data)

    def place_trade(self, pair_name: str, units: float, direction: int,
                    stop_loss: float = None, take_profit: float = None):
        url = f"accounts/{defs.ACCOUNT_ID}/orders"

        try:
            instruments = ic.instruments_dict[pair_name]
            precision = instruments.tradeUnitsPrecision
        except KeyError:
            print(f"Instrument not found: {pair_name}")
            return False, {'error': 'Invalid instrument'}

        units = round(units * direction, precision)

        order_data = {
            "instrument": pair_name,
            "units": str(units),
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }

        if stop_loss:
            order_data["stopLossOnFill"] = {"price": str(stop_loss)}
        if take_profit:
            order_data["takeProfitOnFill"] = {"price": str(take_profit)}

        data = {"order": order_data}

        print("Placing order:", json.dumps(data, indent=2))
        ok, response = self.make_request(url, verb="post", data=data, code=201)

        if ok and 'orderFillTransaction' in response:
            print("Order placed successfully!")
            return True, response['orderFillTransaction']['id']
        else:
            print("Order failed:", response)
            return False, response

        
    def close_trade(self, trade_id: str):
        if not trade_id or not isinstance(trade_id, str) or not trade_id.strip():
            print("Invalid trade ID provided. Cannot close trade.")
            return False, {"errorMessage": "Missing or invalid tradeID"}

        url = f"accounts/{defs.ACCOUNT_ID}/trades/{trade_id}/close"
        ok, response = self.make_request(url, verb="put", code=200)

        if ok:
            print("Trade closed successfully!")
            return True, response
        else:
            print("Error closing trade:", response)
            return False, response 
        
    def get_open_trades(self, trade_id):
        url = f"accounts/{defs.ACCOUNT_ID}/trades/{trade_id}"
        ok, response = self.make_request(url, code=200)
    
        if ok ==True and'trade' in response:
            return openTrades(response['trade'])
        
        










