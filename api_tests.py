from api.oanda_api import OandaApi
from infrastructure.instrument_collection import instrumentCollection


if __name__ == '__main__':
    api = OandaApi()
    instrumentCollection.LoadInstruments("./data")
    api.place_trade("EUR_USD", 100, 1, take_profit=1.14400, stop_loss=1.14230)