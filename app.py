import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# ---------------------------------------------------------
# 1. ページ基本設定 & レスポンシブCSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="プロ仕様・超多次元為替＆マクロ総合分析システム",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f2c;
        border-radius: 6px 6px 0 0;
        padding: 6px 14px;
        color: #a0aec0;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d3748 !important;
        color: #ffffff !important;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. キャッシュ付きデータ取得関数（安全強化版）
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_macro_data():
    """マクロ指標（米金利・VIX・DXY・原油）を安全に取得"""
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
            if not df.empty and "Close" in df:
                close_series = (
                    df["Close"].iloc[:, 0]
                    if isinstance(df["Close"], pd.DataFrame)
                    else df["Close"]
                )
                close_series = close_series.dropna()
                if len(close_series) > 0:
                    val = float(close_series.iloc[-1])
                    ma = float(close_series.tail(20).mean())

                    # 金利データのスケール調整 (^TNXは10倍で取得される場合がある)
                    if key in ["us10y", "us02y"] and val > 20.0:
                        val /= 10.0
                        ma /= 10.0

                    data[key] = (val, ma)
                else:
                    data[key] = (None, None)
            else:
                data[key] = (None, None)
        except Exception:
            data[key] = (None, None)

    return data


@st.cache_data(ttl=300)
def fetch_ticker_ta(symbol):
    """個別銘柄データ取得（合成レート自動計算フォールバック）"""
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if (df.empty or len(df) == 0) and "MXN" in symbol:
            usd_jpy = yf.download(
                "JPY=X", period="6mo", interval="1d", progress=False
            )
            usd_mxn = yf.download(
                "MXN=X", period="6mo", interval="1d", progress=False
            )
            if not usd_jpy.empty and not usd_mxn.empty:
                df = usd_jpy / usd_mxn

        return df
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------
# 3. 日時・ヘッダー表示
# ---------------------------------------------------------
now = datetime.datetime.now()
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
weekday_str = weekdays[now.weekday()]
reiwa_year = now.year - 2018
jp_date_str = f"令和{reiwa_year}年{now.month}月{now.day}日 ({weekday_str}) {now.strftime('%H:%M')} 現在"

st.title("🌐 超多次元マクロ＆マルチアセット統合判定ダッシュボード")
st.caption(f"📅 リアルタイム多次元解析実行中: **{jp_date_str}**")

# ---------------------------------------------------------
# 4. サイドバー設定
# ---------------------------------------------------------
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

st.sidebar.markdown("---")

ticker_database = {
    "新興国・高金利通貨（トルコリラ等）": {
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
        "USD/TRY (ドルリラ)": {
            "yf": "TRY=X",
            "tv": "FX:USDTRY",
            "tv_ta": "FX:USDTRY",
        },
        "ZAR/JPY (ランド円)": {
            "yf": "ZARJPY=X",
            "tv": "FX_IDC:ZARJPY",
            "tv_ta": "FX_IDC:ZARJPY",
        },
    },
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
        "AUD/JPY (豪ドル円)": {
            "yf": "AUDJPY=X",
            "tv": "FX:AUDJPY",
            "tv_ta": "FX:AUDJPY",
        },
        "NZD/JPY (キウイ円)": {
            "yf": "NZDJPY=X",
            "tv": "FX:NZDJPY",
            "tv_ta": "FX:NZDJPY",
        },
    },
    "ドルストレート（対ドル）": {
        "EUR/USD (ユーロドル)": {
            "yf": "EURUSD=X",
            "tv": "FX:EURUSD",
            "tv_ta": "FX:EURUSD",
        },
        "GBP/USD (ポンドドル)": {
            "yf": "GBPUSD=X",
            "tv": "FX:GBPUSD",
            "tv_ta": "FX:GBPUSD",
        },
        "AUD/USD (豪ドルドル)": {
            "yf": "AUDUSD=X",
            "tv": "FX:AUDUSD",
            "tv_ta": "FX:AUDUSD",
        },
        "USD/CAD (ドルカナダ)": {
            "yf": "CAD=X",
            "tv": "FX:USDCAD",
            "tv_ta": "FX:USDCAD",
        },
        "USD/CHF (ドルフラン)": {
            "yf": "CHF=X",
            "tv": "FX:USDCHF",
            "tv_ta": "FX:USDCHF",
        },
    },
    "グローバル株価指数": {
        "S&P 500 (米国株)": {
            "yf": "^GSPC",
            "tv": "FOREXCOM:SPXUSD",
            "tv_ta": "FOREXCOM:SPXUSD",
        },
        "NASDAQ 100 (米ハイテク)": {
            "yf": "^IXIC",
            "tv": "FOREXCOM:NAS100",
            "tv_ta": "FOREXCOM:NAS100",
        },
        "日経平均株価 (NK225)": {
            "yf": "^N225",
            "tv": "OANDA:JP225USD",
            "tv_ta": "OANDA:JP225USD",
        },
        "ドイツ DAX": {
            "yf": "^GDAXI",
            "tv": "GLOBALPRIME:GER30",
            "tv_ta": "GLOBALPRIME:GER30",
        },
    },
    "コモディティ（商品）": {
        "Gold (金先物)": {
            "yf": "GC=F",
            "tv": "OANDA:XAUUSD",
            "tv_ta": "OANDA:XAUUSD",
        },
        "Silver (銀先物)": {
            "yf": "SI=F",
            "tv": "OANDA:XAGUSD",
            "tv_ta": "OANDA:XAGUSD",
        },
        "WTI原油 (USOIL)": {
            "yf": "CL=F",
            "tv": "TVC:USOIL",
            "tv_ta": "TVC:USOIL",
        },
        "Copper (銅先物)": {
            "yf": "HG=F",
            "tv": "COMEX:HG1!",
            "tv_ta": "COMEX:HG1!",
        },
    },
    "先行リスク・金利指標": {
        "MOVE指数 (債券恐怖指数)": {
            "yf": "^MOVE",
            "tv": "INDEX:MOVE",
            "tv_ta": "INDEX:MOVE",
        },
        "米10年実質金利": {
            "yf": "^TNX",
            "tv": "FRED:DFII10",
            "tv_ta": "FRED:DFII10",
        },
        "米10年債利回り (US10Y)": {
            "yf": "^TNX",
            "tv": "TVC:US10Y",
            "tv_ta": "TVC:US10Y",
        },
        "米2年債利回り (US02Y)": {
            "yf": "ZT=F",
            "tv": "TVC:US02Y",
            "tv_ta": "TVC:US02Y",
        },
        "DXY (ドルインデックス)": {
            "yf": "DX-Y.NYB",
            "tv": "CAPITALCOM:DXY",
            "tv_ta": "CAPITALCOM:DXY",
        },
        "VIX (株式恐怖指数)": {
            "yf": "^VIX",
            "tv": "CBOE:VIX",
            "tv_ta": "CBOE:VIX",
        },
    },
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

    timeframe_map = {
        "1分": "1",
        "3分": "3",
        "5分": "5",
        "15分": "15",
        "30分": "30",
        "45分": "45",
        "1時間": "60",
        "3時間": "180",
        "6時間": "360",
        "12時間": "720",
        "1日": "D",
        "1週": "W",
        "1ヶ月": "1M",
    }

    selected_tf_label = st.sidebar.selectbox(
        "チャート時間軸を選択:", list(timeframe_map.keys()), index=10
    )
    selected_interval = timeframe_map[selected_tf_label]

# =========================================================
# 5. メイン画面描画処理
# =========================================================

# --- モード①：銘柄別・詳細分析 ---
if analysis_mode == "📊 銘柄別・詳細分析":

    # ① 経済指標カレンダー（上部にコンパクト配置）
    st.subheader("📅 ① 経済指標カレンダー（本日の警戒イベント）")
    calendar_html = """
    <div class="tradingview-widget-container" style="height:180px;width:100%;">
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "colorTheme": "dark",
      "isTransparent": false,
      "width": "100%",
      "height": "180",
      "locale": "ja",
      "importanceFilter": "0,1",
      "currencyFilter": "USD,JPY,EUR,GBP,AUD,TRY,MXN"
    }
      </script>
    </div>
    """
    components.html(calendar_html, height=190)

    st.markdown("---")

    # ② 多次元マクロ環境判定
    st.subheader(
        "💡 ② 多次元マクロ相場環境判定 (動的アラートシステム搭載)"
    )

    with st.spinner("マクロ環境データ（金利・原油・VIX・DXY）取得中..."):
        macro_data = fetch_macro_data()

    us10y, us10y_ma = macro_data.get("us10y", (None, None))
    us02y, us02y_ma = macro_data.get("us02y", (None, None))
    vix, vix_ma = macro_data.get("vix", (None, None))
    dxy, dxy_ma = macro_data.get("dxy", (None, None))
    oil, oil_ma = macro_data.get("oil", (None, None))

    macro_score = 0
    reasons = []

    if us10y is not None and us10y_ma is not None:
        if us10y > us10y_ma:
            macro_score += 1
            reasons.append(
                f"・米10年金利 ({us10y:.2f}%) 20日平均超 ➔"
                " ドル買い・金利高圧力 (+1)"
            )
        else:
            macro_score -= 1
            reasons.append(
                f"・米10年金利 ({us10y:.2f}%) 20日平均割れ ➔ ドル売り圧力"
                " (-1)"
            )

    if us02y is not None and us02y_ma is not None:
        if us02y > us02y_ma:
            macro_score += 1
            reasons.append(
                f"・米2年金利 ({us02y:.2f}%) 利下げ観測後退 ➔ ドル下支え (+1)"
            )
        else:
            macro_score -= 1
            reasons.append(
                f"・米2年金利 ({us02y:.2f}%) 利下げ織り込み ➔ ドル上値抑制"
                " (-1)"
            )

    if dxy is not None and dxy_ma is not None:
        if dxy > dxy_ma:
            macro_score += 1
            reasons.append(
                f"・ドル指数 ({dxy:.2f}) 上昇トレンド ➔"
                " グローバルなドル独歩高 (+1)"
            )
        else:
            macro_score -= 1
            reasons.append(
                f"・ドル指数 ({dxy:.2f}) 下落トレンド ➔"
                " 他通貨への資金分散 (-1)"
            )

    if oil is not None and oil_ma is not None:
        if oil > oil_ma:
            macro_score += 1
            reasons.append(
                f"・WTI原油 (${oil:.1f}) 上昇 ➔ インフレ高まり・金利止まり"
                " (+1)"
            )
        else:
            macro_score -= 1
            reasons.append(
                f"・WTI原油 (${oil:.1f}) 軟調 ➔ インフレ沈静化・金利低下"
                " (-1)"
            )

    if vix is not None and vix_ma is not None:
        if vix < vix_ma:
            macro_score += 1
            reasons.append(
                f"・株VIX ({vix:.1f}) 安定 ➔"
                " リスクオン（株高・クロス円上昇） (+1)"
            )
        else:
            macro_score -= 1
            reasons.append(
                f"・株VIX ({vix:.1f}) 警戒域 ➔"
                " リスクオフ（円買い・安全資産逃避） (-1)"
            )

    if macro_score >= 4:
        st.error(
            "🚨 **【自動シグナル発動】強力なドル買・金利高トレンド発生中！**"
            " ドル売り・クロス円ショートは厳重警戒。"
        )
    elif macro_score <= -4:
        st.error(
            "🚨 **【自動シグナル発動】リスクオフ・ドル売り圧力が急拡大！**"
            " 新興国通貨・高金利通貨の急落に警戒してください。"
        )

    if vix is not None and vix_ma is not None and vix > (vix_ma * 1.2):
        st.warning(
            "⚠️ **【ボラティリティ警報】VIX指数が急騰しています。**"
            " 急な価格の飛散に注意してください。"
        )

    col_sc, col_re = st.columns([1, 2])
    with col_sc:
        st.metric("マクロ総合評価スコア", f"{macro_score:+d} / +5")
        if macro_score >= 3:
            st.success("🔥 ドル高・リスクオン優勢環境")
        elif macro_score <= -3:
            st.error("❄️ ドル安・リスクオフ警戒環境")
        else:
            st.warning("⚖️ 拮抗・レンジ移行環境")

    with col_re:
        st.info(
            "\n".join(reasons)
            if reasons
            else "マクロデータを取得しています..."
        )

    st.markdown("---")

    # ③ テクニカル分析
    st.subheader(f"📊 ③ 【{selected_name}】高度テクニカル評価 & TradingView")
    df_ta = fetch_ticker_ta(selected_info["yf"])

    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        st.markdown("##### 📍 Pivot ターゲット（利確・反転目安）")
        if not df_ta.empty and len(df_ta) > 0:
            try:
                close = (
                    df_ta["Close"].iloc[:, 0]
                    if isinstance(df_ta["Close"], pd.DataFrame)
                    else df_ta["Close"]
                )
                high = (
                    df_ta["High"].iloc[:, 0]
                    if isinstance(df_ta["High"], pd.DataFrame)
                    else df_ta["High"]
                )
                low = (
                    df_ta["Low"].iloc[:, 0]
                    if isinstance(df_ta["Low"], pd.DataFrame)
                    else df_ta["Low"]
                )

                c_val, h_val, l_val = (
                    float(close.dropna().values[-1]),
                    float(high.dropna().values[-1]),
                    float(low.dropna().values[-1]),
                )

                pivot = (h_val + l_val + c_val) / 3
                r1, r2 = (2 * pivot) - l_val, pivot + (h_val - l_val)
                s1, s2 = (2 * pivot) - h_val, pivot - (h_val - l_val)

                st.write(f"🔴 **第2抵抗 (R2):** `{r2:,.2f}`")
                st.write(f"🔴 **第1抵抗 (R1):** `{r1:,.2f}`")
                st.write(f"🟢 **第1支持 (S1):** `{s1:,.2f}`")
                st.write(f"🟢 **第2支持 (S2):** `{s2:,.2f}`")
            except Exception:
                st.warning("ピボットポイント算出中...")
        else:
            st.warning("最新の価格データを取得できませんでした。")

    with col_t2:
        st.markdown("##### 🤖 TradingView AIテクニカル判定")
        tech_widget = f"""
        <div class="tradingview-widget-container" style="height:250px;width:100%;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
          {{
          "interval": "1D",
          "width": "100%",
          "height": "250",
          "symbol": "{selected_info['tv_ta']}",
          "showIntervalTabs": true,
          "displayMode": "single",
          "locale": "ja",
          "colorTheme": "dark"
        }}
          </script>
        </div>
        """
        components.html(tech_widget, height=260)

    st.markdown("---")

    # ④ メインチャート
    st.subheader(
        f"📈 ④ リアルタイムチャート [{selected_name}] ({selected_tf_label}表示)"
    )
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:520px;width:100%;">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{selected_info['tv']}",
        "interval": "{selected_interval}",
        "timezone": "Asia/Tokyo",
        "theme": "dark",
        "style": "1",
        "locale": "ja",
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_html, height=540)

# --- モード②：ファンダメンタルズ＆高度先行指標 ---
elif (
    analysis_mode == "🏛️ ファンダメンタルズ＆高度先行指標（PMI/MOVE/金利）"
):
    st.subheader(
        "🏛️ ファンダメンタルズ＆先行マクロ指標（構造的相場分析）"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🇺🇸 CPI & インフレ率",
        "📦 貿易収支 & FF金利",
        "👷 雇用統計 & PMI",
        "⚡ MOVE指数 & 10年実質金利",
        "🛢️ 原油 & 銅 (景気体感)",
    ])

    with tab1:
        st.markdown(
            "##### 📈 米国CPI（消費者物価指数）: インフレの着地点を追跡"
        )
        components.html(
            """
        <div class="tradingview-widget-container" style="height:420px;width:100%;">
          <div id="cpi_chart" style="height:100%;width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({"autosize": true, "symbol": "ECONOMICS:USCPI", "interval": "M", "theme": "dark", "style": "2", "locale": "ja", "container_id": "cpi_chart"});
          </script>
        </div>
        """,
            height=440,
        )

    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.caption("米貿易収支")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="tb_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "ECONOMICS:USTRBAL", "interval": "M", "theme": "dark", "style": "2", "locale": "ja", "container_id": "tb_chart"});
              </script>
            </div>
            """,
                height=390,
            )
        with col_f2:
            st.caption("FF金利（政策金利）")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="rate_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "ECONOMICS:USINTR", "interval": "M", "theme": "dark", "style": "2", "locale": "ja", "container_id": "rate_chart"});
              </script>
            </div>
            """,
                height=390,
            )

    with tab3:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.caption("NFP (非農業部門雇用者数)")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="nfp_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "ECONOMICS:USNFP", "interval": "M", "theme": "dark", "style": "2", "locale": "ja", "container_id": "nfp_chart"});
              </script>
            </div>
            """,
                height=390,
            )
        with col_p2:
            st.caption("ISM 製造業景況指数 (PMI)")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="pmi_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "ECONOMICS:USPMI", "interval": "M", "theme": "dark", "style": "2", "locale": "ja", "container_id": "pmi_chart"});
              </script>
            </div>
            """,
                height=390,
            )

    with tab4:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.caption("MOVE指数 (債券VIX)")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="move_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "INDEX:MOVE", "interval": "D", "theme": "dark", "style": "1", "locale": "ja", "container_id": "move_chart"});
              </script>
            </div>
            """,
                height=390,
            )
        with col_m2:
            st.caption("米10年実質金利 (FRED)")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="real_rate_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "FRED:DFII10", "interval": "D", "theme": "dark", "style": "1", "locale": "ja", "container_id": "real_rate_chart"});
              </script>
            </div>
            """,
                height=390,
            )

    with tab5:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.caption("WTI原油先物")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="oil_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "TVC:USOIL", "interval": "D", "theme": "dark", "style": "1", "locale": "ja", "container_id": "oil_chart"});
              </script>
            </div>
            """,
                height=390,
            )
        with col_c2:
            st.caption("COMEX 銅先物")
            components.html(
                """
            <div class="tradingview-widget-container" style="height:380px;width:100%;">
              <div id="copper_chart" style="height:100%;width:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({"autosize": true, "symbol": "COMEX:HG1!", "interval": "D", "theme": "dark", "style": "1", "locale": "ja", "container_id": "copper_chart"});
              </script>
            </div>
            """,
                height=390,
            )

# --- モード③：通貨強弱＆ポジション偏り ---
elif analysis_mode == "⚔️ 通貨強弱＆ポジション偏り（CFTC/IMM）":
    st.subheader("⚔️ グローバル通貨ヒートマップ & 投機筋ポジション")
    col_h1, col_h2 = st.columns([2, 1])

    with col_h1:
        components.html(
            """
        <div class="tradingview-widget-container" style="height:520px;width:100%;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-forex-heat-map.js" async>
          {"width": "100%", "height": "520", "currencies": ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "TRY", "MXN"], "colorTheme": "dark", "locale": "ja"}
          </script>
        </div>
        """,
            height=540,
        )

    with col_h2:
        st.info(
            """
        **【投機筋（IMM）の偏りチェック】**
        * **円ショート過剰:** 巻き戻し（円高）に警戒。
        * **ドルロング偏重:** 指標悪化時のドル急落に注意。
        * **高金利通貨:** キャリー解除のリスクオフ急落を監視。
        """
        )
        components.html(
            """
        <div class="tradingview-widget-container" style="height:280px;width:100%;">
          <div id="usdjpy_mini" style="height:100%;width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({"autosize": true, "symbol": "FX:USDJPY", "interval": "D", "theme": "dark", "style": "3", "locale": "ja", "container_id": "usdjpy_mini"});
          </script>
        </div>
        """,
            height=290,
        )

# --- モード④：モメンタム＆変動率ランキング ---
elif analysis_mode == "🔥 モメンタム＆変動率ランキング":
    st.subheader("🔥 Marketスクリーナー (強弱テクニカル一覧)")
    components.html(
        """
    <div class="tradingview-widget-container" style="height:580px;width:100%;">
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      {"width": "100%", "height": "580", "defaultColumn": "overview", "defaultScreen": "general", "market": "forex", "colorTheme": "dark", "locale": "ja"}
      </script>
    </div>
    """,
        height=600,
    )

# --- モード⑤：リアルタイム・マクロニュース＆市況 ---
elif analysis_mode == "📰 リアルタイム・マクロニュース＆市況":
    st.subheader("📰 グローバル・マクロニュースフィード")
    components.html(
        """
    <div class="tradingview-widget-container" style="height:600px;width:100%;">
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
      {
      "feedMode": "all_symbols",
      "colorTheme": "dark",
      "isTransparent": false,
      "displayMode": "regular",
      "width": "100%",
      "height": "600",
      "locale": "ja"
    }
      </script>
    </div>
    """,
        height=620,
    )

# =========================================================
# 6. バックグラウンドAI学習エンジン ＆ 勝率モニタリング統合
# =========================================================
import datetime
import sqlite3
import threading
import time
import pandas as pd
import streamlit as st
import yfinance as yf

DB_PATH = "trades.db"


# --- A. データベース初期化 (マルチスレッド対応) ---
def get_db_connection():
    # check_same_thread=False を指定してスレッド間衝突を防止
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        symbol TEXT,
        signal_type TEXT,
        entry_price REAL,
        target_time TEXT,
        exit_price REAL,
        result TEXT,
        vix_val REAL
    )
    """
    )
    conn.commit()
    conn.close()


# --- ヘルパー: yfinanceのClose列を安全に1次元Seriesとして抽出 ---
def safe_extract_close(df):
    if df.empty or "Close" not in df:
        return None
    close_data = df["Close"]
    if isinstance(close_data, pd.DataFrame):
        close_data = close_data.iloc[:, 0]
    return close_data.dropna()


# --- B. 常時バックグラウンドで動くAI監視ロジック ---
def ai_background_logger():
    init_db()
    while True:
        try:
            now = datetime.datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")

            conn = get_db_connection()
            cursor = conn.cursor()

            # ① 15分経過したシグナルの「答え合わせ」
            cursor.execute(
                "SELECT id, signal_type, entry_price FROM signals WHERE result"
                " = 'PENDING' AND target_time <= ?",
                (now_str,),
            )
            pending_list = cursor.fetchall()

            if pending_list:
                df = yf.download(
                    "JPY=X", period="1d", interval="1m", progress=False
                )
                close_s = safe_extract_close(df)
                if close_s is not None and len(close_s) > 0:
                    curr_p = float(close_s.iloc[-1])

                    for row in pending_list:
                        sig_id, sig_type, entry_p = row
                        res = "LOSE"
                        if (sig_type == "BUY" and curr_p > entry_p) or (
                            sig_type == "SELL" and curr_p < entry_p
                        ):
                            res = "WIN"
                        cursor.execute(
                            "UPDATE signals SET exit_price = ?, result = ?"
                            " WHERE id = ?",
                            (curr_p, res, sig_id),
                        )

            # ② 新規シグナルの検出 (5分足MA乖離)
            df_5m = yf.download(
                "JPY=X", period="1d", interval="5m", progress=False
            )
            close_5m = safe_extract_close(df_5m)

            if close_5m is not None and len(close_5m) >= 20:
                last_c = float(close_5m.iloc[-1])
                ma20 = float(close_5m.tail(20).mean())

                sig = None
                if last_c > ma20 * 1.0003:
                    sig = "BUY"
                elif last_c < ma20 * 0.9997:
                    sig = "SELL"

                if sig:
                    # 直近10分以内に同じシグナルが出ていないか検証
                    ten_mins_ago = (
                        now - datetime.timedelta(minutes=10)
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "SELECT id FROM signals WHERE signal_type = ? AND"
                        " timestamp >= ?",
                        (sig, ten_mins_ago),
                    )
                    if not cursor.fetchone():
                        target_dt = (
                            now + datetime.timedelta(minutes=15)
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO signals (timestamp, symbol,"
                            " signal_type, entry_price, target_time, result,"
                            " vix_val) VALUES (?, ?, ?, ?, ?, 'PENDING', 0)",
                            (now_str, "USD/JPY", sig, last_c, target_dt),
                        )

            conn.commit()
            conn.close()
        except Exception as e:
            # デバッグ用にエラーを出力したい場合はprint(e)
            pass

        time.sleep(300)  # 5分ごとに巡回


# アプリ起動時にバックグラウンドスレッドを起動（二重起動防止ロジック付き）
@st.cache_resource
def start_ai_thread():
    init_db()
    # 既存のバックグラウンドスレッドがあるか確認
    for thread in threading.enumerate():
        if thread.name == "AI_Logger_Thread":
            return True

    t = threading.Thread(
        target=ai_background_logger, name="AI_Logger_Thread", daemon=True
    )
    t.start()
    return True


start_ai_thread()


# --- C. Streamlit画面にAIの勝率を表示 ---
st.markdown("---")
st.subheader("🤖 AI自己学習シグナル＆勝率モニタリング")


def load_perf():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM signals", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df_perf = load_perf()

if not df_perf.empty:
    completed = df_perf[df_perf["result"].isin(["WIN", "LOSE"])]
    pending = df_perf[df_perf["result"] == "PENDING"]

    total = len(completed)
    wins = len(completed[completed["result"] == "WIN"])
    rate = (wins / total * 100) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI検証済み総数", f"{total} 回")
    c2.metric("AI現在の勝率", f"{rate:.1f} %")
    c3.metric("勝ち数", f"{wins} 勝")
    c4.metric("15分後判定待ち", f"{len(pending)} 件")

    st.markdown("##### 📜 直近のAIシグナルと15分後の答え合わせ履歴")
    st.dataframe(
        df_perf.sort_values(by="id", ascending=False).head(10)[
            ["timestamp", "signal_type", "entry_price", "exit_price", "result"]
        ],
        use_container_width=True,
    )
else:
    st.info(
        "💡"
        " バックグラウンドでAIが初回データの収集を開始しました。しばらくお待ちください。"
    )