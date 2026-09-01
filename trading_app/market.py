from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from .config import PH_TZ


def ema(series: pd.Series, length: int = 9) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi_values = 100 - (100 / (1 + rs))
    return rsi_values.fillna(50)


@st.cache_data(ttl=10)
def get_current_price(symbol: str) -> float:
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return float(response.json()["price"])
    except Exception:
        pass
    return 0.0


@st.cache_data(ttl=10)
def fetch_live_data(symbol: str, interval: str) -> pd.DataFrame:
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=100"
    response = requests.get(url, timeout=3)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(
        data,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "num_trades",
            "taker_base_vol",
            "taker_quote_vol",
            "ignore",
        ],
    )

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    return df


def analyze_market(df):
    if df is None or len(df) < 30:
        return {
            "signal": "CONSOLIDATING",
            "candle_time": None,
            "buy_score": 0,
            "sell_score": 0,
            "ready_buy": False,
            "ready_sell": False,
            "confirmed_buy": False,
            "confirmed_sell": False,
            "extended_buy": False,
            "extended_sell": False,
            "ready_exit_buy": False,
            "ready_exit_sell": False,
            "confirmed_exit_buy": False,
            "confirmed_exit_sell": False,
        }

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    ema9 = ema(close, length=9)
    ema21 = ema(close, length=21)
    ema50 = ema(close, length=50)
    rsi_values = rsi(close, length=14)

    idx = -2
    candle_time = df["time"].iloc[idx]
    price = float(close.iloc[idx])
    prev_price = float(close.iloc[idx - 1])
    current_ema9 = float(ema9.iloc[idx])
    current_ema21 = float(ema21.iloc[idx])
    current_ema50 = float(ema50.iloc[idx])
    current_rsi = float(rsi_values.iloc[idx])
    previous_rsi = float(rsi_values.iloc[idx - 1])

    avg_volume = volume.rolling(20).mean().iloc[idx]
    if pd.isna(avg_volume):
        avg_volume = 0
    current_volume = float(volume.iloc[idx])
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

    candle_body = abs(float(close.iloc[idx]) - float(df["open"].iloc[idx]))
    candle_range = float(high.iloc[idx]) - float(low.iloc[idx])
    body_ratio = candle_body / candle_range if candle_range > 0 else 0

    bullish_candle = price > float(df["open"].iloc[idx]) and body_ratio >= 0.50
    bearish_candle = price < float(df["open"].iloc[idx]) and body_ratio >= 0.50
    price_rising = price > prev_price
    price_falling = price < prev_price

    strong_bull_structure = current_ema9 > current_ema21 > current_ema50
    strong_bear_structure = current_ema9 < current_ema21 < current_ema50
    bull_structure = current_ema9 > current_ema21
    bear_structure = current_ema9 < current_ema21

    strong_volume = volume_ratio >= 1.25
    normal_volume = volume_ratio >= 1.05

    buy_score = 0
    if bull_structure:
        buy_score += 1
    if strong_bull_structure:
        buy_score += 1
    if current_rsi > 50:
        buy_score += 1
    if current_rsi > previous_rsi:
        buy_score += 1
    if price_rising:
        buy_score += 1
    if bullish_candle:
        buy_score += 1
    if strong_volume:
        buy_score += 2
    elif normal_volume:
        buy_score += 1

    sell_score = 0
    if bear_structure:
        sell_score += 1
    if strong_bear_structure:
        sell_score += 1
    if current_rsi < 50:
        sell_score += 1
    if current_rsi < previous_rsi:
        sell_score += 1
    if price_falling:
        sell_score += 1
    if bearish_candle:
        sell_score += 1
    if strong_volume:
        sell_score += 2
    elif normal_volume:
        sell_score += 1

    recent_high = float(high.tail(8).max())
    recent_low = float(low.tail(8).min())
    recent_range = (recent_high - recent_low) / price
    is_consolidating = recent_range < 0.0030

    ready_buy = (
        not is_consolidating
        and bull_structure
        and current_rsi >= 48
        and buy_score >= 4
    )
    ready_sell = (
        not is_consolidating
        and bear_structure
        and current_rsi <= 52
        and sell_score >= 4
    )

    confirmed_buy = (
        not is_consolidating
        and strong_bull_structure
        and current_rsi >= 52
        and current_rsi <= 67
        and price_rising
        and bullish_candle
        and strong_volume
        and buy_score >= 8
    )
    confirmed_sell = (
        not is_consolidating
        and strong_bear_structure
        and current_rsi <= 48
        and current_rsi >= 33
        and price_falling
        and bearish_candle
        and strong_volume
        and sell_score >= 8
    )

    extension_up = (
        recent_range >= 0.0060
        and current_rsi >= 65
        and bull_structure
    )
    extension_down = (
        recent_range >= 0.0060
        and current_rsi <= 35
        and bear_structure
    )

    ready_exit_buy = (
        current_rsi >= 68
        or (current_rsi >= 63 and previous_rsi > current_rsi)
    )
    ready_exit_sell = (
        current_rsi <= 32
        or (current_rsi <= 37 and previous_rsi < current_rsi)
    )

    confirmed_exit_buy = (
        current_ema9 < current_ema21
        and current_rsi < previous_rsi
        and price_falling
        and bearish_candle
        and (strong_volume or current_rsi < 45)
    )
    confirmed_exit_sell = (
        current_ema9 > current_ema21
        and current_rsi > previous_rsi
        and price_rising
        and bullish_candle
        and (strong_volume or current_rsi > 55)
    )

    return {
        "signal": "CONSOLIDATING",
        "candle_time": candle_time,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "ready_buy": ready_buy,
        "ready_sell": ready_sell,
        "confirmed_buy": confirmed_buy,
        "confirmed_sell": confirmed_sell,
        "extended_buy": extension_up,
        "extended_sell": extension_down,
        "ready_exit_buy": ready_exit_buy,
        "ready_exit_sell": ready_exit_sell,
        "confirmed_exit_buy": confirmed_exit_buy,
        "confirmed_exit_sell": confirmed_exit_sell,
    }


def to_ph_time(timestamp):
    if timestamp is None:
        return None

    try:
        if isinstance(timestamp, pd.Timestamp):
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize("UTC")
            return timestamp.tz_convert(PH_TZ).to_pydatetime()

        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return timestamp.astimezone(PH_TZ)
    except Exception:
        return None

    return None


def get_elapsed_text(signal_timestamp):
    if signal_timestamp is None:
        return ""

    try:
        signal_ph = to_ph_time(signal_timestamp)
        if signal_ph is None:
            return ""

        now_ph = datetime.now(PH_TZ)
        elapsed_seconds = int((now_ph - signal_ph).total_seconds())
        if elapsed_seconds < 0:
            elapsed_seconds = 0

        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s ago"
        if minutes > 0:
            return f"{minutes}m {seconds}s ago"
        return f"{seconds}s ago"
    except Exception:
        return ""


def is_market_neutral(analysis):
    return (
        not analysis["ready_buy"]
        and not analysis["ready_sell"]
        and not analysis["extended_buy"]
        and not analysis["extended_sell"]
    )
