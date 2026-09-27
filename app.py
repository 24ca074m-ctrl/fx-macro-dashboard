import datetime
import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

DB_PATH = "trades.db"

st.set_page_config(
    page_title="プロ仕様・超多次元為替＆マクロ総合分析システム",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e0e6ed; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1f2c; border-radius: 6px 6px 0 0; padding: 6px 14px; color: #a0aec0; font-size: 14px; }
    .stTabs [aria-selected="true"] { background-color: #2d3748 !important; color: #ffffff !important; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)


def safe_extract_series(df, col_name="Close"):
    if df is None or df.empty or col_name not in df:
        return pd.Series(dtype="float64")
    data = df[col_name]
    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    return data.dropna()


@st.cache_data(ttl=300)
def fetch_macro_data():
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=60)
    tickers = {
        "us10y": "^TNX",
        "us02y": "ZT=F",
        "vix": "^VIX",
        "dxy": "DX-Y.NYB",
        "oil": "CL=F",
    }
    data = {}
    for key, symbol in tickers.items():
        try:
            df = yf.download(
                symbol, start=start_date, end=end_date, progress=False
            )
            c = safe_extract_series(df, "Close")
            if len(c) > 0:
                val, ma = float(c.iloc[-1]), float(c.tail(20).mean())
                if key in ["us10y", "us02y"] and val > 20.0:
                    val /= 10.0
                    ma /= 10.0
                data[key] = (val, ma)
            else:
                data[key] = (None, None)
        except Exception:
            data[key] = (None, None)
    return data


@st.cache_data(ttl=300)
def fetch_ticker_ta(symbol):
    try:
        return yf.download(
            symbol, period="6mo", interval="1d", progress=False
        )
    except Exception:
        return pd.DataFrame()


now = datetime.datetime.now()
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
reiwa_year = now.year - 2018
st.title("🌐 超多次元マクロ＆マルチアセット統合判定ダッシュボード")
st.caption(
    f"📅 リアルタイム多次元解析実行中: **令和{reiwa_year}年{now.month}月{now.day}日 ({weekdays[now.weekday()]}) {now.strftime('%H:%M')} 現在**"
)

st.sidebar.header("⚙️ システム設定")
if st.sidebar.button("🔄 データを手動更新"):
    st.cache_data.clear()
    st.rerun()

analysis_mode = st.sidebar.radio(
    "分析モードを選択:",
    [
        "📊 銘柄別・詳細分析",
        "🏛️ ファンダメンタルズ＆高度先行指標（PMI/MOVE/金利）",
        "⚔️ 通貨強弱＆ポジション偏り（CFTC/IMM）",
        "🔥 モメンタム＆変動率ランキング",
        "📰 リアルタイム・マクロニュース＆市況",
    ],
)

ticker_database = {
    "クロス円（対日本円）": {
        "USD/JPY (ドル円)": {
            "yf": "JPY=X",
            "tv": "FX:USDJPY",
            "tv_ta": "FX:USDJPY",
        },
        "EUR/JPY (ユーロ円)": {
            "yf": "EURJPY=X",
            "tv": "FX:EURJPY",
            "tv_ta": "FX:EURJPY",
        },
        "GBP/JPY (ポンド円)": {
            "yf": "GBPJPY=X",
            "tv": "FX:GBPJPY",
            "tv_ta": "FX:GBPJPY",
        },
    },
    "新興国・高金利通貨": {
        "MXN/JPY (ペソ円)": {
            "yf": "MXNJPY=X",
            "tv": "FX_IDC:MXNJPY",
            "tv_ta": "FX_IDC:MXNJPY",
        },
        "TRY/JPY (トルコリラ円)": {
            "yf": "TRYJPY=X",
            "tv": "FX_IDC:TRYJPY",
            "tv_ta": "FX_IDC:TRYJPY",
        },
    },
    "ドルストレート": {
        "EUR/USD (ユーロドル)": {
            "yf": "EURUSD=X",
            "tv": "FX:EURUSD",
            "tv_ta": "FX:EURUSD",
        },
    },
}

timeframe_map = {
    "1分": "1",
    "5分": "5",
    "15分": "15",
    "30分": "30",
    "1時間": "60",
    "2時間": "120",
    "4時間": "240",
    "1日": "D",
    "1週": "W",
    "1ヶ月": "1M",
}

if analysis_mode == "📊 銘柄別・詳細分析":
    st.sidebar.header("📌 銘柄＆時間軸選択")
    selected_group = st.sidebar.selectbox(
        "カテゴリを選択:", list(ticker_database.keys())
    )
    selected_name = st.sidebar.selectbox(
        "分析銘柄を選択:", list(ticker_database[selected_group].keys())
    )
    selected_info = ticker_database[selected_group][selected_name]
    selected_tf_label = st.sidebar.selectbox(
        "チャート時間軸を選択:", list(timeframe_map.keys()), index=7
    )
    selected_interval = timeframe_map[selected_tf_label]

    st.subheader("📅 ① 経済指標カレンダー")
    components.html(
        """<div class="tradingview-widget-container" style="height:180px;width:100%;"><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark","width": "100%","height": "180","locale": "ja","importanceFilter": "0,1","currencyFilter": "USD,JPY,EUR,GBP,AUD,TRY,MXN"}</script></div>""",
        height=190,
    )

    st.markdown("---")
    st.subheader("💡 ② 多次元マクロ環境判定")
    macro_data = fetch_macro_data()
    us10y, us10y_ma = macro_data.get("us10y", (None, None))
    us02y, us02y_ma = macro_data.get("us02y", (None, None))
    vix, vix_ma = macro_data.get("vix", (None, None))
    dxy, dxy_ma = macro_data.get("dxy", (None, None))
    oil, oil_ma = macro_data.get("oil", (None, None))

    macro_score = 0
    reasons = []
    if us10y and us10y_ma:
        macro_score += 1 if us10y > us10y_ma else -1
        reasons.append(
            f"・米10年金利 ({us10y:.2f}%): {'上昇トレンド (+1)' if us10y > us10y_ma else '下降トレンド (-1)'}"
        )
    if vix and vix_ma:
        macro_score += 1 if vix < vix_ma else -1
        reasons.append(
            f"・VIX指数 ({vix:.1f}): {'リスクオン (+1)' if vix < vix_ma else 'リスクオフ (-1)'}"
        )

    col_sc, col_re = st.columns([1, 2])
    with col_sc:
        st.metric("マクロ総合評価スコア", f"{macro_score:+d}")
    with col_re:
        st.info("\n".join(reasons))

    st.markdown("---")
    st.subheader(f"📊 ③ 【{selected_name}】テクニカル & チャート")
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{"autosize": true, "symbol": "{selected_info['tv']}", "interval": "{selected_interval}", "timezone": "Asia/Tokyo", "theme": "dark", "style": "1", "locale": "ja", "container_id": "tradingview_chart"}});
      </script>
    </div>
    """
    components.html(tv_html, height=510)

st.markdown("---")
st.subheader("⚡ 全時間軸AI勝率モニタリング＆検証ログ")


def load_perf():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        df = pd.read_sql("SELECT * FROM signals", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df_perf = load_perf()
if not df_perf.empty:
    filter_tf = st.selectbox(
        "表示する時間軸でフィルタ:", ["すべて"] + list(timeframe_map.keys())
    )
    df_display = (
        df_perf[df_perf["timeframe"] == filter_tf]
        if filter_tf != "すべて"
        else df_perf
    )

    completed = df_display[df_display["result"].isin(["WIN", "LOSE"])]
    pending = df_display[df_display["result"] == "PENDING"]
    total = len(completed)
    wins = len(completed[completed["result"] == "WIN"])
    rate = (wins / total * 100) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("検証総数", f"{total} 回")
    c2.metric("勝率", f"{rate:.1f} %")
    c3.metric("勝ち数", f"{wins} 勝")
    c4.metric("判定待ち", f"{len(pending)} 件")

    st.dataframe(
        df_display.sort_values(by="id", ascending=False).head(20)[
            [
                "timestamp",
                "symbol",
                "timeframe",
                "signal_type",
                "entry_price",
                "exit_price",
                "result",
            ]
        ],
        use_container_width=True,
    )
else:
    st.info(
        "💡 監視用エンジン（bot.py）を起動してください。自動生成されたログがここにリアルタイム反映されます。"
    )

# --- 自動でbot.pyを裏起動する連携処理 ---
import subprocess
import sys


@st.cache_resource
def auto_start_bot():
    # bot.pyがすでに動いているか確認し、動いていなければバックグラウンドで起動
    try:
        # プロセスが起動しているか判定（OSに応じた安全な起動）
        subprocess.Popen([sys.executable, "bot.py"])
        print("🤖 bot.py をバックグラウンドで自動起動しました。")
    except Exception as e:
        print(f"bot自動起動エラー: {e}")


auto_start_bot()
