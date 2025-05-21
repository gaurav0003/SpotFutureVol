import streamlit as st
import requests
import time


def get_klines(symbol, interval, limit=1, futures=False):
    base_url = "https://fapi.binance.com" if futures else "https://api.binance.com"
    endpoint = "/fapi/v1/klines" if futures else "/api/v3/klines"
    url = base_url + endpoint
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except:
        return None


def get_funding_rate(symbol):
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        res = requests.get(url, params={"symbol": symbol}, timeout=10)
        res.raise_for_status()
        return float(res.json().get("lastFundingRate", 0)) * 100
    except:
        return None


def get_all_symbols():
    try:
        spot_info = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()
        future_info = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()

        spot_symbols = {s['symbol'] for s in spot_info['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'}
        future_symbols = {s['symbol'] for s in future_info['symbols'] if s['quoteAsset'] == 'USDT' and s['contractType'] == 'PERPETUAL'}

        return sorted(list(spot_symbols & future_symbols))
    except:
        return []


def compare_volumes(symbol, interval):
    spot = get_klines(symbol, interval, futures=False)
    futures = get_klines(symbol, interval, futures=True)
    funding_rate = get_funding_rate(symbol)

    spot_vol = float(spot[-1][5]) if spot else None
    futures_vol = float(futures[-1][7]) if futures else None

    st.subheader(f"{symbol} Volume Comparison ({interval})")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Spot Volume", f"{spot_vol:,.2f} USDT" if spot_vol else "❌ Not listed")
    with col2:
        st.metric("Futures Volume", f"{futures_vol:,.2f} USDT" if futures_vol else "❌ Not listed")

    if spot_vol and futures_vol:
        diff = abs(futures_vol - spot_vol)
        if futures_vol > spot_vol:
            st.success(f"🚀 More activity in **Futures** by {diff:,.2f} USDT")
        else:
            st.info(f"💧 More activity in **Spot** by {diff:,.2f} USDT")
    elif futures_vol:
        st.warning("Only listed in **Futures** market.")
    elif spot_vol:
        st.warning("Only listed in **Spot** market.")
    else:
        st.error("Symbol not listed in either Spot or Futures.")

    if funding_rate is not None:
        st.write(f"📈 Funding Rate: `{funding_rate:.4f}%`")
    else:
        st.write("📉 Funding Rate: ❌ Not available")


def compare_overall_volume(interval):
    symbols = get_all_symbols()
    total_spot_volume = 0.0
    total_futures_volume = 0.0

    progress = st.progress(0)
    for i, sym in enumerate(symbols):
        spot_klines = get_klines(sym, interval, futures=False)
        futures_klines = get_klines(sym, interval, futures=True)

        if spot_klines:
            try:
                total_spot_volume += float(spot_klines[-1][5])
            except:
                pass

        if futures_klines:
            try:
                total_futures_volume += float(futures_klines[-1][7])
            except:
                pass

        progress.progress((i + 1) / len(symbols))

        time.sleep(0.2)

    st.subheader(f"📊 Overall Volume Comparison ({interval})")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Spot Volume", f"{total_spot_volume:,.2f} USDT")
    with col2:
        st.metric("Total Futures Volume", f"{total_futures_volume:,.2f} USDT")

    diff = abs(total_futures_volume - total_spot_volume)
    if total_futures_volume > total_spot_volume:
        st.success(f"🔥 More activity in **Futures** by {diff:,.2f} USDT")
    else:
        st.info(f"💧 More activity in **Spot** by {diff:,.2f} USDT")


# === Streamlit App ===
st.set_page_config(page_title="Spot vs Futures Volume", layout="centered")
st.title("📈 Spot vs Futures Volume Comparison")

menu = st.sidebar.selectbox("Choose Option", ["Compare Volume for a Symbol", "Compare Overall Market Volume"])
timeframe = st.sidebar.selectbox("Timeframe", ['2h', '4h', '8h', '12h'])

if menu == "Compare Volume for a Symbol":
    all_symbols = get_all_symbols()
    selected_symbol = st.selectbox("Select Symbol", all_symbols)
    if st.button("Compare Volumes"):
        compare_volumes(selected_symbol, timeframe)

elif menu == "Compare Overall Market Volume":
    if st.button("Compare Overall Volumes"):
        compare_overall_volume(timeframe)
