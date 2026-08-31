from __future__ import annotations

from datetime import datetime

import streamlit as st

from .config import STATE_CONSOLIDATING


def initialize_session_state() -> None:
    defaults = {
        "active_trades": {},
        "trade_history": [],
        "last_spoken_signal": {},
        "signal_timestamps": {},
        "signal_states": {},
        "signal_confirmations": {},
        "confirmation_candles": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state_key(symbol: str, timeframe: str) -> str:
    return f"{symbol}_{timeframe}"


def get_current_state(symbol: str, timeframe: str) -> str:
    key = get_state_key(symbol, timeframe)
    return st.session_state.signal_states.get(key, STATE_CONSOLIDATING)


def save_signal_state(symbol: str, timeframe: str, state: str, candle_time) -> str:
    key = get_state_key(symbol, timeframe)
    previous = st.session_state.signal_states.get(key)
    st.session_state.signal_states[key] = state

    if previous != state:
        st.session_state.signal_timestamps[key] = candle_time

    return state


def reset_signal_state(symbol: str, timeframe: str, candle_time) -> None:
    key = get_state_key(symbol, timeframe)
    st.session_state.signal_states[key] = STATE_CONSOLIDATING
    st.session_state.signal_confirmations[key] = {
        "buy": 0,
        "sell": 0,
        "exit_buy": 0,
        "exit_sell": 0,
    }
    st.session_state.confirmation_candles[key] = {
        "buy": None,
        "sell": None,
        "exit_buy": None,
        "exit_sell": None,
    }
    st.session_state.signal_timestamps[key] = candle_time


def reset_confirmation(key: str, counter_name: str) -> None:
    if key not in st.session_state.signal_confirmations:
        st.session_state.signal_confirmations[key] = {
            "buy": 0,
            "sell": 0,
            "exit_buy": 0,
            "exit_sell": 0,
        }

    if key not in st.session_state.confirmation_candles:
        st.session_state.confirmation_candles[key] = {
            "buy": None,
            "sell": None,
            "exit_buy": None,
            "exit_sell": None,
        }

    st.session_state.signal_confirmations[key][counter_name] = 0


def update_confirmation_counter(key: str, counter_name: str, condition: bool, candle_time) -> int:
    if key not in st.session_state.signal_confirmations:
        st.session_state.signal_confirmations[key] = {
            "buy": 0,
            "sell": 0,
            "exit_buy": 0,
            "exit_sell": 0,
        }

    if key not in st.session_state.confirmation_candles:
        st.session_state.confirmation_candles[key] = {
            "buy": None,
            "sell": None,
            "exit_buy": None,
            "exit_sell": None,
        }

    counters = st.session_state.signal_confirmations[key]
    candles = st.session_state.confirmation_candles[key]

    if candles[counter_name] != candle_time:
        candles[counter_name] = candle_time
        if condition:
            counters[counter_name] += 1
        else:
            counters[counter_name] = 0

    return counters[counter_name]


def ensure_key_state(key: str) -> None:
    if key not in st.session_state.signal_confirmations:
        st.session_state.signal_confirmations[key] = {
            "buy": 0,
            "sell": 0,
            "exit_buy": 0,
            "exit_sell": 0,
        }

    if key not in st.session_state.confirmation_candles:
        st.session_state.confirmation_candles[key] = {
            "buy": None,
            "sell": None,
            "exit_buy": None,
            "exit_sell": None,
        }


def get_spoken_signal_key(symbol: str, timeframe: str, signal: str) -> str:
    return f"{symbol}_{timeframe}_{signal}"


def get_timestamp_for_trade(candle_time) -> datetime:
    return candle_time if candle_time is not None else datetime.now()
