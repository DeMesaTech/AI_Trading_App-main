from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from .config import (
    BUY_CONFIRMATION_REQUIRED,
    EXIT_BUY_CONFIRMATION_REQUIRED,
    EXIT_SELL_CONFIRMATION_REQUIRED,
    PAIRS,
    SELL_CONFIRMATION_REQUIRED,
    STATE_BUY,
    STATE_CONSOLIDATING,
    STATE_EXIT_BUY,
    STATE_EXIT_SELL,
    STATE_NO_CHASE_BUY,
    STATE_NO_CHASE_SELL,
    STATE_READY_BUY,
    STATE_READY_EXIT_BUY,
    STATE_READY_EXIT_SELL,
    STATE_READY_SELL,
    STATE_SELL,
    TIMEFRAMES,
    TIMED_SIGNALS,
)
from .market import (
    analyze_market,
    fetch_live_data,
    get_current_price,
    is_market_neutral,
    to_ph_time,
)
from .state import (
    ensure_key_state,
    get_current_state,
    get_state_key,
    get_timestamp_for_trade,
    initialize_session_state,
    reset_confirmation,
    reset_signal_state,
    save_signal_state,
    update_confirmation_counter,
)
from .voice import trigger_voice_alert


st.set_page_config(
    page_title="FREDOMCRI LIVE PRO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def initialize_ui_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top right, rgba(16,185,129,0.10), transparent 30%),
            linear-gradient(rgba(4,8,15,0.96), rgba(4,8,15,0.98));
            color: #e2e8f0;
        }
        .block-container {
            padding-top: 6rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        .dashboard-title {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: 1px;
        }
        .dashboard-subtitle {
            color: #94a3b8;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 22px;
            font-weight: 750;
            margin-top: 15px;
            margin-bottom: 12px;
        }
        .live-card {
            background: rgba(10,15,26,1.0);
            border: 1px solid rgba(16,185,129,0.20);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .live-status {
            color: #10b981;
            font-size: 12px;
            font-weight: 700;
        }
        .badge {
            display: block;
            text-align: center;
            padding: 6px;
            border-radius: 7px;
            font-size: 11px;
            font-weight: 800;
        }
        .signal-time {
            display: block;
            text-align: center;
            font-size: 10px;
            color: #38bdf8;
            margin-top: 4px;
            font-weight: 600;
        }
        .signal-elapsed {
            display: block;
            text-align: center;
            font-size: 10px;
            color: #facc15;
            margin-top: 2px;
            font-weight: 700;
        }
        .buy { background: #10b981; color: white; box-shadow: 0 0 12px rgba(16,185,129,0.45); }
        .sell { background: #ef4444; color: white; box-shadow: 0 0 12px rgba(239,68,68,0.45); }
        .exit-buy { background: #f97316; color: white; box-shadow: 0 0 12px rgba(249,115,22,0.45); }
        .exit-sell { background: #a855f7; color: white; box-shadow: 0 0 12px rgba(168,85,247,0.40); }
        .ready-buy { background: #2563eb; color: white; box-shadow: 0 0 12px rgba(37,99,235,0.35); }
        .ready-sell { background: #f59e0b; color: white; box-shadow: 0 0 12px rgba(245,158,11,0.35); }
        .no-chase-buy { background: #0ea5e9; color: white; box-shadow: 0 0 12px rgba(14,165,233,0.35); }
        .no-chase-sell { background: #dc2626; color: white; box-shadow: 0 0 12px rgba(220,38,38,0.35); }
        .neutral { background: #1e293b; color: #94a3b8; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_badge_class(signal: str) -> str:
    if signal == STATE_BUY:
        return "buy"
    if signal == STATE_SELL:
        return "sell"
    if signal == STATE_EXIT_BUY:
        return "exit-buy"
    if signal == STATE_EXIT_SELL:
        return "exit-sell"
    if signal == STATE_READY_BUY:
        return "ready-buy"
    if signal == STATE_READY_SELL:
        return "ready-sell"
    if signal == STATE_NO_CHASE_BUY:
        return "no-chase-buy"
    if signal == STATE_NO_CHASE_SELL:
        return "no-chase-sell"
    return "neutral"


def render_signal_timing(symbol: str, timeframe: str, signal: str, candle_time) -> None:
    if signal not in TIMED_SIGNALS or candle_time is None:
        st.markdown('<span class="signal-time" style="color:transparent;">-</span>', unsafe_allow_html=True)
        st.markdown('<span class="signal-elapsed" style="color:transparent;">-</span>', unsafe_allow_html=True)
        return

    ph_time = to_ph_time(candle_time)
    if ph_time is None:
        return

    formatted_time = ph_time.strftime("%m-%d-%Y %I:%M:%S %p")
    elapsed_html = f"""
    <style>
        body {{ margin: 0; background: transparent; }}
        .signal-time, .signal-elapsed {{
            display: block;
            text-align: center;
            font-family: sans-serif;
            font-size: 10px;
            font-weight: 600;
            line-height: 14px;
        }}
        .signal-time {{ color: #38bdf8; }}
        .signal-elapsed {{ color: #facc15; }}
    </style>
    <span class="signal-time">🕒 {formatted_time} PHT</span>
    <span id="signal-elapsed" class="signal-elapsed"></span>
    <script>
        const candleTime = new Date({candle_time.isoformat()!r});
        const elapsedElement = document.getElementById("signal-elapsed");

        function updateElapsed() {{
            let elapsedSeconds = Math.max(0, Math.floor((Date.now() - candleTime.getTime()) / 1000));
            const hours = Math.floor(elapsedSeconds / 3600);
            elapsedSeconds %= 3600;
            const minutes = Math.floor(elapsedSeconds / 60);
            const seconds = elapsedSeconds % 60;
            let elapsed = `${{seconds}}s ago`;

            if (hours > 0) {{
                elapsed = `${{hours}}h ${{minutes}}m ${{seconds}}s ago`;
            }} else if (minutes > 0) {{
                elapsed = `${{minutes}}m ${{seconds}}s ago`;
            }}

            elapsedElement.textContent = `⏱ ${{elapsed}}`;
        }}

        updateElapsed();
        setInterval(updateElapsed, 1000);
    </script>
    """
    st.components.v1.html(elapsed_html, height=36)


def get_signal_and_time(df, symbol: str, timeframe: str):
    analysis = analyze_market(df)
    candle_time = analysis["candle_time"]

    if candle_time is None:
        return STATE_CONSOLIDATING, None

    current_state = get_current_state(symbol, timeframe)
    key = get_state_key(symbol, timeframe)
    ensure_key_state(key)

    buy_confirmations = update_confirmation_counter(
        key,
        "buy",
        analysis["confirmed_buy"],
        candle_time,
    )
    sell_confirmations = update_confirmation_counter(
        key,
        "sell",
        analysis["confirmed_sell"],
        candle_time,
    )
    exit_buy_confirmations = update_confirmation_counter(
        key,
        "exit_buy",
        analysis["confirmed_exit_buy"],
        candle_time,
    )
    exit_sell_confirmations = update_confirmation_counter(
        key,
        "exit_sell",
        analysis["confirmed_exit_sell"],
        candle_time,
    )

    if current_state == STATE_CONSOLIDATING:
        if analysis["extended_buy"]:
            return save_signal_state(symbol, timeframe, STATE_NO_CHASE_BUY, candle_time), candle_time
        if analysis["extended_sell"]:
            return save_signal_state(symbol, timeframe, STATE_NO_CHASE_SELL, candle_time), candle_time
        if analysis["ready_buy"]:
            return save_signal_state(symbol, timeframe, STATE_READY_BUY, candle_time), candle_time
        if analysis["ready_sell"]:
            return save_signal_state(symbol, timeframe, STATE_READY_SELL, candle_time), candle_time
        return STATE_CONSOLIDATING, None

    if current_state == STATE_NO_CHASE_BUY:
        if analysis["extended_buy"]:
            return STATE_NO_CHASE_BUY, candle_time
        if analysis["ready_buy"]:
            return save_signal_state(symbol, timeframe, STATE_READY_BUY, candle_time), candle_time
        if is_market_neutral(analysis):
            return save_signal_state(symbol, timeframe, STATE_CONSOLIDATING, candle_time), None
        return STATE_NO_CHASE_BUY, candle_time

    if current_state == STATE_NO_CHASE_SELL:
        if analysis["extended_sell"]:
            return STATE_NO_CHASE_SELL, candle_time
        if analysis["ready_sell"]:
            return save_signal_state(symbol, timeframe, STATE_READY_SELL, candle_time), candle_time
        if is_market_neutral(analysis):
            return save_signal_state(symbol, timeframe, STATE_CONSOLIDATING, candle_time), None
        return STATE_NO_CHASE_SELL, candle_time

    if current_state == STATE_READY_BUY:
        if analysis["extended_buy"]:
            reset_confirmation(key, "buy")
            return save_signal_state(symbol, timeframe, STATE_NO_CHASE_BUY, candle_time), candle_time
        if buy_confirmations >= BUY_CONFIRMATION_REQUIRED:
            return save_signal_state(symbol, timeframe, STATE_BUY, candle_time), candle_time
        return STATE_READY_BUY, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_READY_SELL:
        if analysis["extended_sell"]:
            reset_confirmation(key, "sell")
            return save_signal_state(symbol, timeframe, STATE_NO_CHASE_SELL, candle_time), candle_time
        if sell_confirmations >= SELL_CONFIRMATION_REQUIRED:
            return save_signal_state(symbol, timeframe, STATE_SELL, candle_time), candle_time
        return STATE_READY_SELL, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_BUY:
        if analysis["ready_exit_buy"]:
            reset_confirmation(key, "exit_buy")
            return save_signal_state(symbol, timeframe, STATE_READY_EXIT_BUY, candle_time), candle_time
        return STATE_BUY, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_SELL:
        if analysis["ready_exit_sell"]:
            reset_confirmation(key, "exit_sell")
            return save_signal_state(symbol, timeframe, STATE_READY_EXIT_SELL, candle_time), candle_time
        return STATE_SELL, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_READY_EXIT_BUY:
        if exit_buy_confirmations >= EXIT_BUY_CONFIRMATION_REQUIRED:
            return save_signal_state(symbol, timeframe, STATE_EXIT_BUY, candle_time), candle_time
        return STATE_READY_EXIT_BUY, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_READY_EXIT_SELL:
        if exit_sell_confirmations >= EXIT_SELL_CONFIRMATION_REQUIRED:
            return save_signal_state(symbol, timeframe, STATE_EXIT_SELL, candle_time), candle_time
        return STATE_READY_EXIT_SELL, st.session_state.signal_timestamps.get(key, candle_time)

    if current_state == STATE_EXIT_BUY:
        reset_signal_state(symbol, timeframe, candle_time)
        return STATE_CONSOLIDATING, None

    if current_state == STATE_EXIT_SELL:
        reset_signal_state(symbol, timeframe, candle_time)
        return STATE_CONSOLIDATING, None

    return STATE_CONSOLIDATING, None


def update_trade_tracker(symbol: str, timeframe: str, signal: str, price: float, candle_time) -> None:
    active = st.session_state.active_trades
    history = st.session_state.trade_history
    timestamp_to_use = get_timestamp_for_trade(candle_time)

    if signal == STATE_BUY and symbol not in active:
        active[symbol] = {
            "side": "BUY",
            "entry_price": price,
            "entry_time": timestamp_to_use.strftime("%Y-%m-%d %H:%M:%S"),
            "tf": timeframe,
        }
    elif signal == STATE_SELL and symbol not in active:
        active[symbol] = {
            "side": "SELL",
            "entry_price": price,
            "entry_time": timestamp_to_use.strftime("%Y-%m-%d %H:%M:%S"),
            "tf": timeframe,
        }
    elif signal == STATE_EXIT_BUY and symbol in active and active[symbol].get("side") == "BUY":
        entry_price = active[symbol]["entry_price"]
        entry_time = active[symbol]["entry_time"]
        saved_tf = active[symbol]["tf"]
        pnl_pct = ((price - entry_price) / entry_price) * 100
        result = "WIN" if pnl_pct > 0 else "LOSS"
        history.append(
            {
                "symbol": symbol,
                "tf": saved_tf,
                "signal": STATE_EXIT_BUY,
                "entry_price": entry_price,
                "exit_price": price,
                "entry_time": entry_time,
                "exit_time": timestamp_to_use.strftime("%Y-%m-%d %H:%M:%S"),
                "pnl": pnl_pct,
                "result": result,
            }
        )
        del active[symbol]
    elif signal == STATE_EXIT_SELL and symbol in active and active[symbol].get("side") == "SELL":
        entry_price = active[symbol]["entry_price"]
        entry_time = active[symbol]["entry_time"]
        saved_tf = active[symbol]["tf"]
        pnl_pct = ((entry_price - price) / entry_price) * 100
        result = "WIN" if pnl_pct > 0 else "LOSS"
        history.append(
            {
                "symbol": symbol,
                "tf": saved_tf,
                "signal": STATE_EXIT_SELL,
                "entry_price": entry_price,
                "exit_price": price,
                "entry_time": entry_time,
                "exit_time": timestamp_to_use.strftime("%Y-%m-%d %H:%M:%S"),
                "pnl": pnl_pct,
                "result": result,
            }
        )
        del active[symbol]


@st.fragment(run_every="15s")
def live_market_terminal() -> None:
    st.markdown("---")
    st.markdown('<div class="section-title">⚡ LIVE MARKET TERMINAL</div>', unsafe_allow_html=True)

    for pair in PAIRS:
        symbol = pair["symbol"]
        tv_symbol = pair["tv_symbol"]

        with st.container():
            try:
                live_signals = {}
                live_times = {}
                price = get_current_price(symbol)

                for timeframe_name in TIMEFRAMES:
                    df = fetch_live_data(symbol, timeframe_name)
                    signal, candle_time = get_signal_and_time(df, symbol, timeframe_name)
                    live_signals[timeframe_name] = signal
                    live_times[timeframe_name] = candle_time

                    if timeframe_name == "1m":
                        update_trade_tracker(symbol, timeframe_name, signal, price, candle_time)
            except Exception:
                price = 0.0
                live_signals = {tf: STATE_CONSOLIDATING for tf in TIMEFRAMES}
                live_times = {tf: None for tf in TIMEFRAMES}

            st.markdown('<div class="live-card">', unsafe_allow_html=True)

            tv_widget_html = f"""
            <div class="tradingview-widget-container" style="height:95px; width:100%; margin-bottom:8px;">
                <div class="tradingview-widget-container__widget" style="height:100%; width:100%;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
                {{
                    "symbol": "{tv_symbol}",
                    "width": "100%",
                    "colorTheme": "dark",
                    "isTransparent": true,
                    "locale": "en"
                }}
                </script>
            </div>
            """
            st.components.v1.html(tv_widget_html, height=105)

            timeframe_columns = st.columns(len(TIMEFRAMES))
            for index, timeframe_name in enumerate(TIMEFRAMES):
                signal = live_signals[timeframe_name]
                candle_time = live_times[timeframe_name]
                with timeframe_columns[index]:
                    st.markdown(f"**{timeframe_name.upper()}**")
                    st.markdown(f'<span class="badge {get_badge_class(signal)}">{signal}</span>', unsafe_allow_html=True)
                    render_signal_timing(symbol, timeframe_name, signal, candle_time)

                    voice_enabled = st.checkbox("🔊 Voice", value=(timeframe_name == "1m"), key=f"voice_{symbol}_{timeframe_name}")
                    if voice_enabled and signal != STATE_CONSOLIDATING:
                        voice_key = f"{symbol}_{timeframe_name}"
                        signal_key = f"{symbol}_{timeframe_name}_{signal}"
                        if st.session_state.last_spoken_signal.get(voice_key) != signal_key:
                            trigger_voice_alert(f"{symbol} {timeframe_name} {signal}")
                            st.session_state["last_spoken_signal"][voice_key] = signal_key

            st.markdown('</div>', unsafe_allow_html=True)


def render_trade_statistics() -> None:
    st.markdown("---")
    st.markdown("### 📋 LIVE TRADE STATISTICS")

    live_history = st.session_state.trade_history
    if not live_history:
        st.info("No closed live trades yet.")
        return

    total_closed = len(live_history)
    wins = sum(1 for t in live_history if t["result"] == "WIN")
    losses = sum(1 for t in live_history if t["result"] == "LOSS")
    total_pnl = sum(t["pnl"] for t in live_history)
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("CLOSED TRADES", total_closed)
    s2.metric("WINS", wins)
    s3.metric("LOSSES", losses)
    s4.metric("WIN RATE", f"{win_rate:.1f}%")
    s5.metric("TOTAL PNL", f"{total_pnl:+.2f}%")

    st.markdown("#### 📜 Closed Trades History")
    st.dataframe(pd.DataFrame(live_history), use_container_width=True, hide_index=True)


def render_active_trades() -> None:
    if not st.session_state.active_trades:
        return

    st.markdown("### 🟢 ACTIVE TRADES")
    active_rows = []

    for symbol, trade in st.session_state.active_trades.items():
        current_price = get_current_price(symbol)
        entry_price = trade["entry_price"]
        side = trade.get("side", "BUY")

        if side == "SELL":
            live_pnl = ((entry_price - current_price) / entry_price * 100) if entry_price else 0
        else:
            live_pnl = ((current_price - entry_price) / entry_price * 100) if entry_price else 0

        active_rows.append(
            {
                "PAIR": symbol,
                "SIDE": side,
                "TIMEFRAME": trade["tf"],
                "ENTRY PRICE": entry_price,
                "LIVE PRICE": current_price,
                "LIVE PNL %": f"{live_pnl:+.3f}%",
                "ENTRY TIME": trade["entry_time"],
            }
        )

    st.dataframe(pd.DataFrame(active_rows), use_container_width=True, hide_index=True)


def render_voice_test() -> None:
    st.markdown("---")
    if st.button("🎙️ TEST FEMALE VOICE", use_container_width=True):
        trigger_voice_alert("Female AI voice test successful. FREDOMCRI Live Pro is ready.")


def render_footer() -> None:
    st.markdown(
        """
        <div style="text-align:center; margin-top:25px; color:#64748b; font-size:11px;">
            ⚡ FREDOMCRI LIVE PRO
            &nbsp;•&nbsp;
            TRADINGVIEW LIVE FEED
            &nbsp;•&nbsp;
            EXACT TIMESTAMP ENGINE
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    initialize_session_state()
    initialize_ui_styles()

    st.markdown('<div class="dashboard-title">⚡ FREDOMCRI LIVE PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Binance Futures Real-Time Scalping</div>', unsafe_allow_html=True)
    st.markdown('<div class="live-status">● TRADINGVIEW LIVE FEED & EXACT TIMESTAMP ENGINE ACTIVE</div>', unsafe_allow_html=True)

    live_market_terminal()
    render_trade_statistics()
    render_active_trades()
    render_voice_test()
    render_footer()


if __name__ == "__main__":
    main()
