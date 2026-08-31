from zoneinfo import ZoneInfo

PAIRS = [
    {"symbol": "BTCUSDT", "tv_symbol": "BINANCE:BTCUSDT", "display": "BTCUSDT", "icon": "₿"},
    {"symbol": "ETHUSDT", "tv_symbol": "BINANCE:ETHUSDT", "display": "ETHUSDT", "icon": "Ξ"},
    ## {"symbol": "SOLUSDT", "tv_symbol": "BINANCE:SOLUSDT", "display": "SOLUSDT", "icon": "◎"},
    ## {"symbol": "BNBUSDT", "tv_symbol": "BINANCE:BNBUSDT", "display": "BNBUSDT", "icon": "🔶"},
    ## {"symbol": "XRPUSDT", "tv_symbol": "BINANCE:XRPUSDT", "display": "XRPUSDT", "icon": "✕"},
    ## {"symbol": "ADAUSDT", "tv_symbol": "BINANCE:ADAUSDT", "display": "ADAUSDT", "icon": "₳"},
    ## {"symbol": "DOGEUSDT", "tv_symbol": "BINANCE:DOGEUSDT", "display": "DOGEUSDT", "icon": "Ð"},
    ## {"symbol": "AVAXUSDT", "tv_symbol": "BINANCE:AVAXUSDT", "display": "AVAXUSDT", "icon": "🔺"},
    ## {"symbol": "LINKUSDT", "tv_symbol": "BINANCE:LINKUSDT", "display": "LINKUSDT", "icon": "⬡"},
    ## {"symbol": "DOTUSDT", "tv_symbol": "BINANCE:DOTUSDT", "display": "DOTUSDT", "icon": "●"},
]

PAIR_SYMBOLS = [pair["symbol"] for pair in PAIRS]
TIMEFRAMES = ["1m", "3m", "5m", "1h", "4h"]
PH_TZ = ZoneInfo("Asia/Manila")

STATE_CONSOLIDATING = "CONSOLIDATING"
STATE_READY_BUY = "READY TO BUY"
STATE_READY_SELL = "READY TO SELL"
STATE_BUY = "BUY NOW"
STATE_SELL = "SELL NOW"
STATE_NO_CHASE_BUY = "NO CHASE BUY"
STATE_NO_CHASE_SELL = "NO CHASE SELL"
STATE_READY_EXIT_BUY = "READY TO EXIT TP"
STATE_READY_EXIT_SELL = "READY TO EXIT TP"
STATE_EXIT_BUY = "EXIT BUY NOW"
STATE_EXIT_SELL = "EXIT SELL NOW"

BUY_CONFIRMATION_REQUIRED = 2
SELL_CONFIRMATION_REQUIRED = 2
EXIT_BUY_CONFIRMATION_REQUIRED = 1
EXIT_SELL_CONFIRMATION_REQUIRED = 1

TIMED_SIGNALS = {"BUY NOW", "SELL NOW", "EXIT BUY NOW", "EXIT SELL NOW"}
