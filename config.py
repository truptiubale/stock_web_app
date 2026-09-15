# config.py
# Central place for every ticker the app cares about.
# Yahoo Finance symbols for Indian indices start with ^ and use NSE suffixes.

GLOBAL_BENCHMARKS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "GIFT Nifty": "NIFTY_FIN_SERVICE.NS",  # placeholder — confirm exact symbol before relying on it
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
}

MAJOR_INDICES = {
    "Nifty 50": "^NSEI",
    "Nifty Next 50": "^NSMIDCP",  # verify symbol
    "Sensex": "^BSESN",
}

SECTOR_INDICES = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
}

THEMATIC_INDICES = {
    "Nifty Energy": "^CNXENERGY",
    "Nifty Infra": "^CNXINFRA",
    "Nifty PSE": "^CNXPSE",
}

# RSI thresholds used for trend confirmation / mean-reversion triggers
RSI_PERIOD = 14
RSI_UPPER_BAND = 60
RSI_LOWER_BAND = 40

# Bollinger Band settings
BB_PERIOD = 20
BB_STD_DEV = 2

# Volume confirmation lookback
VOLUME_SMA_PERIOD = 20
