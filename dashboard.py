import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, time as dtime
import pytz
from streamlit_autorefresh import st_autorefresh

# ── Config ────────────────────────────────────────────────────────────────────
TICKER = "NQ=F"
ET = pytz.timezone("America/New_York")

st.set_page_config(page_title="MNQ Daily Dashboard", layout="wide")

st_autorefresh(interval=60_000, key="autorefresh")

now_et = datetime.now(ET)
st.markdown(
    f"<div style='color:#555; font-size:0.72rem; margin-bottom:-10px; font-family:\"IBM Plex Mono\",monospace; letter-spacing:0.05em;'>"
    f"{now_et.strftime('%A %B %d, %Y  %H:%M ET')}</div>",
    unsafe_allow_html=True,
)

# ── Global Typography ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

/* ── Bloomberg terminal base ── */
html, body, [class*="css"], .stApp, .stMarkdown, button, input {
    font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
}

/* Dim the default Streamlit background slightly warmer */
.stApp { background-color: #0d0d0d !important; }

/* ── Metrics ── */
[data-testid="stMetricLabel"] p   {
    font-size: 2.52rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ff9900 !important;
}
[data-testid="stMetricValue"] div {
    font-size: 1.35rem !important;
    font-weight: 600 !important;
    color: #f0f0f0 !important;
}
[data-testid="stMetricDelta"]     { font-size: 1.35rem !important; }
[data-testid="stMetricDelta"] svg { width: 0.7rem !important; height: 0.7rem !important; }
[data-testid="metric-container"]  { padding: 4px 0 !important; }

/* ── Subheaders ── */
h3 {
    font-size: 1.0rem !important;
    margin-bottom: 4px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #ff9900 !important;
}

/* ── Captions / small text ── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.70rem !important;
    color: #666 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Dividers ── */
hr { border-color: #2a2a2a !important; }

/* ── Refresh button — Windows 95 VB CommandButton ── */
.stButton > button {
    background:      #d4d0c8 !important;
    color:           #000000 !important;
    border:          none !important;
    border-radius:   0px !important;
    font-family:     'MS Sans Serif', 'Microsoft Sans Serif', Arial, sans-serif !important;
    font-size:       11px !important;
    font-weight:     400 !important;
    text-transform:  none !important;
    letter-spacing:  0 !important;
    padding:         4px 16px 4px 14px !important;
    box-shadow:
        inset  1px  1px 0px #ffffff,
        inset  2px  2px 0px #dfdfdf,
        inset -1px -1px 0px #808080,
        inset -2px -2px 0px #404040,
        0 0 0 1px #000000 !important;
}
.stButton > button:hover {
    background: #d4d0c8 !important;
    color:      #000000 !important;
}
.stButton > button:active {
    box-shadow:
        inset -1px -1px 0px #ffffff,
        inset -2px -2px 0px #dfdfdf,
        inset  1px  1px 0px #808080,
        inset  2px  2px 0px #404040,
        0 0 0 1px #000000 !important;
    padding: 5px 14px 3px 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last_trading_day(ref_date):
    d = ref_date
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

def prev_trading_day(d):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

def next_trading_day(d):
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d

# ── Data Fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_daily(ticker):
    df = yf.download(ticker, period="30d", interval="1d",
                     progress=False, auto_adjust=True)
    return clean(df)

@st.cache_data(ttl=60)
def fetch_intraday(ticker):
    df = yf.download(ticker, period="10d", interval="5m",
                     progress=False, auto_adjust=True)
    df = clean(df)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(ET)
    return df

# ── Level Calculations ────────────────────────────────────────────────────────
def camarilla_pivots(h, l, c):
    r = h - l
    k = 1.1
    h4 = round(c + r * k / 2, 2)
    h3 = round(c + r * k / 4, 2)
    l3 = round(c - r * k / 4, 2)
    l4 = round(c - r * k / 2, 2)
    return {
        "R5": round(c + r, 2),   # TradingView: Close + (High − Low)
        "R4": h4,
        "R3": h3,
        "S3": l3,
        "S4": l4,
        "S5": round(c - r, 2),   # TradingView: Close − (High − Low)
    }

def floor_pivots(h, l, c):
    pp = round((h + l + c) / 3, 2)
    r  = h - l
    return {
        "R5": round(pp + 4 * r, 2),
        "R4": round(pp + 3 * r, 2),
        "R3": round(pp + 2 * r, 2),
        "R2": round(pp + r,     2),
        "R1": round(2 * pp - l, 2),
        "PP": pp,
        "S1": round(2 * pp - h, 2),
        "S2": round(pp - r,     2),
        "S3": round(pp - 2 * r, 2),
        "S4": round(pp - 3 * r, 2),
        "S5": round(pp - 4 * r, 2),
    }

def get_globex_levels(intraday, trade_date):
    p = prev_trading_day(trade_date)
    mask = (
        ((intraday.index.date == p) & (intraday.index.time >= dtime(16, 0))) |
        ((intraday.index.date == trade_date) & (intraday.index.time < dtime(9, 30)))
    )
    g = intraday[mask]
    if g.empty:
        return None, None
    return round(float(g["High"].max()), 2), round(float(g["Low"].min()), 2)


# ── News Feed ────────────────────────────────────────────────────────────────
import feedparser


NEWS_FEEDS = {
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
    "CNBC":        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Reuters":     "https://feeds.reuters.com/reuters/businessNews",
}

@st.cache_data(ttl=300)
def fetch_news():
    cutoff = datetime.now(ET) - timedelta(hours=24)
    items  = []
    for source, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                if parsed:
                    pub = datetime(*parsed[:6], tzinfo=pytz.UTC).astimezone(ET)
                else:
                    pub = datetime.now(ET)
                if pub < cutoff:          # drop stale stories
                    continue
                items.append({
                    "source":    source,
                    "title":     entry.get("title", "").strip(),
                    "link":      entry.get("link", "#"),
                    "published": pub,
                })
        except Exception:
            pass
    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:12]

def time_ago(dt):
    mins = max(0, int((datetime.now(ET) - dt).total_seconds() / 60))
    if mins < 1:   return "just now"
    if mins < 60:  return f"{mins}m ago"
    return f"{mins // 60}h {mins % 60}m ago"


def calc_atr(daily_df, period=14):
    """Average True Range over N daily periods."""
    if len(daily_df) < period + 1:
        return None
    h  = daily_df["High"]
    l  = daily_df["Low"]
    pc = daily_df["Close"].shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 2)


# ── Bias Engine ───────────────────────────────────────────────────────────────
def determine_bias(price, pd_high, pd_low, pd_close, cam_h3, cam_l3,
                   globex_h, globex_l):
    cam_mid = round((cam_h3 + cam_l3) / 2, 2)
    score, reasons = 0, []

    if price > pd_close:
        score += 2
        reasons.append(("▲", f"Above PDC {pd_close:.2f} — bullish structure carry"))
    else:
        score -= 2
        reasons.append(("▼", f"Below PDC {pd_close:.2f} — bearish structure carry"))

    if price > cam_mid:
        score += 1
        reasons.append(("▲", f"Above Cam midpoint {cam_mid:.2f} (R3/S3 equilibrium)"))
    else:
        score -= 1
        reasons.append(("▼", f"Below Cam midpoint {cam_mid:.2f} (R3/S3 equilibrium)"))

    if globex_h and globex_l:
        mid = round((globex_h + globex_l) / 2, 2)
        if price > mid:
            score += 1
            reasons.append(("▲", f"Above Globex midpoint {mid:.2f}"))
        else:
            score -= 1
            reasons.append(("▼", f"Below Globex midpoint {mid:.2f}"))

    if price > cam_h3:
        score += 1
        reasons.append(("▲", f"Above Cam R3 {cam_h3:.2f} — breakout zone"))
    elif price < cam_l3:
        score -= 1
        reasons.append(("▼", f"Below Cam S3 {cam_l3:.2f} — breakdown zone"))
    else:
        reasons.append(("—", f"Inside Cam S3/R3 range — value area"))

    pd_range = pd_high - pd_low
    if pd_range > 0:
        pos = (price - pd_low) / pd_range
        if pos > 0.65:
            score += 1
            reasons.append(("▲", f"Upper third of PD range ({pos:.0%} from PDL)"))
        elif pos < 0.35:
            score -= 1
            reasons.append(("▼", f"Lower third of PD range ({pos:.0%} from PDL)"))
        else:
            reasons.append(("—", f"Middle of PD range ({pos:.0%} from PDL)"))

    if score >= 3:
        return "BULLISH", "#00c853", score, reasons
    elif score == 2:
        return "LEANING BULLISH", "#69f0ae", score, reasons
    elif score == -2:
        return "LEANING BEARISH", "#ff6d00", score, reasons
    elif score <= -3:
        return "BEARISH", "#d50000", score, reasons
    else:
        return "NEUTRAL / WAIT", "#9e9e9e", score, reasons

# ── App Layout ────────────────────────────────────────────────────────────────
today      = now_et.date()
trade_date = last_trading_day(today)

LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 56" width="64" height="46"
     style="vertical-align:middle; filter:drop-shadow(0 0 6px rgba(0,200,83,0.5))">
  <!-- Candle 1 — bearish -->
  <line x1="14" y1="10" x2="14" y2="47" stroke="#d50000" stroke-width="1.8" stroke-linecap="round"/>
  <rect x="9"  y="22" width="10" height="17" fill="#d50000" rx="2"/>
  <!-- Candle 2 — bullish, taller -->
  <line x1="40" y1="6"  x2="40" y2="47" stroke="#00c853" stroke-width="1.8" stroke-linecap="round"/>
  <rect x="35" y="12" width="10" height="24" fill="#00c853" rx="2"/>
  <!-- Candle 3 — bullish, highest -->
  <line x1="66" y1="3"  x2="66" y2="43" stroke="#00c853" stroke-width="1.8" stroke-linecap="round"/>
  <rect x="61" y="8"  width="10" height="22" fill="#00c853" rx="2"/>
  <!-- Trend line -->
  <line x1="9" y1="39" x2="71" y2="18"
        stroke="rgba(255,255,255,0.22)" stroke-width="1.5" stroke-dasharray="5,3"/>
</svg>"""

BULL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="{w}" height="{w}"'
    ' style="flex-shrink:0;filter:drop-shadow(0 0 10px rgba(0,200,83,0.4))">'
    '<path d="M24 32 Q13 6 27 16" stroke="#a07828" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<path d="M56 32 Q67 6 53 16" stroke="#a07828" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<circle cx="40" cy="47" r="26" fill="#c8860a"/>'
    '<ellipse cx="40" cy="59" rx="13" ry="9" fill="#b07320"/>'
    '<circle cx="36" cy="60" r="2" fill="#7a4e10"/>'
    '<circle cx="44" cy="60" r="2" fill="#7a4e10"/>'
    '<circle cx="30" cy="42" r="5" fill="white"/>'
    '<circle cx="50" cy="42" r="5" fill="white"/>'
    '<circle cx="31" cy="42" r="3" fill="#111"/>'
    '<circle cx="51" cy="42" r="3" fill="#111"/>'
    '<circle cx="32" cy="41" r="1" fill="white"/>'
    '<circle cx="52" cy="41" r="1" fill="white"/>'
    '<path d="M33 53 Q40 58 47 53" stroke="#7a4e10" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    '</svg>'
)

BEAR_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="{w}" height="{w}"'
    ' style="flex-shrink:0;filter:drop-shadow(0 0 10px rgba(213,0,0,0.4))">'
    '<circle cx="18" cy="24" r="12" fill="#3e1a06"/>'
    '<circle cx="62" cy="24" r="12" fill="#3e1a06"/>'
    '<circle cx="18" cy="24" r="6" fill="#7a4e2a"/>'
    '<circle cx="62" cy="24" r="6" fill="#7a4e2a"/>'
    '<circle cx="40" cy="47" r="26" fill="#3e1a06"/>'
    '<ellipse cx="40" cy="58" rx="13" ry="9" fill="#7a4e2a"/>'
    '<ellipse cx="40" cy="52" rx="5" ry="3.5" fill="#1a0800"/>'
    '<circle cx="29" cy="42" r="5" fill="white"/>'
    '<circle cx="51" cy="42" r="5" fill="white"/>'
    '<circle cx="30" cy="42" r="3" fill="#111"/>'
    '<circle cx="52" cy="42" r="3" fill="#111"/>'
    '<circle cx="31" cy="41" r="1" fill="white"/>'
    '<circle cx="53" cy="41" r="1" fill="white"/>'
    '<path d="M24 36 Q29 31 34 36" stroke="#1a0800" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    '<path d="M46 36 Q51 31 56 36" stroke="#1a0800" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    '<path d="M33 61 Q40 57 47 61" stroke="#1a0800" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    '</svg>'
)

# Title row — placeholder filled with bias color after data loads
title_col, spacer_col, btn_col = st.columns([7, 2, 1])
with title_col:
    title_slot = st.empty()
with btn_col:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    if st.button("⟳ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Data Load ─────────────────────────────────────────────────────────────────
with st.spinner("Fetching market data..."):
    daily    = fetch_daily(TICKER)
    intraday = fetch_intraday(TICKER)

if len(daily) < 3:
    st.error("Not enough data returned. Markets may be closed or the ticker is unavailable.")
    st.stop()

daily_dates = [d.date() if hasattr(d, "date") else d for d in daily.index]

# After 4 PM ET the RTH session is complete — flip to next-session mode
rth_closed    = now_et.time() >= dtime(16, 0)
complete_rows = [
    i for i, d in enumerate(daily_dates)
    if d < trade_date or (rth_closed and d == trade_date)
]
if not complete_rows:
    st.error("Cannot find a completed prior trading day in fetched data.")
    st.stop()

prev_idx = complete_rows[-1]

curr_price = round(float(daily.iloc[-1]["Close"]), 2)

# Full Globex session OHLC — matches TradingView daily bar
# After 4PM today's daily bar may not have settled yet, so use intraday full-day bars
if rth_closed:
    full_bars = intraday[intraday.index.date == trade_date]
    if not full_bars.empty:
        pd_date  = trade_date
        pd_high  = round(float(full_bars["High"].max()), 2)
        pd_low   = round(float(full_bars["Low"].min()),  2)
        pd_open  = round(float(full_bars["Open"].iloc[0]), 2)
        pd_close = round(float(full_bars["Close"].iloc[-1]), 2)
    else:
        rth_closed = False  # force fallback below
if not rth_closed:
    prev     = daily.iloc[prev_idx]
    pd_date  = daily_dates[prev_idx]
    pd_open  = round(float(prev["Open"]),  2)
    pd_high  = round(float(prev["High"]),  2)
    pd_low   = round(float(prev["Low"]),   2)
    pd_close = round(float(prev["Close"]), 2)

# Weekly H/L — full Globex daily bars
week_slice = daily.iloc[max(0, prev_idx - 4): prev_idx + 1]
pw_high = round(float(week_slice["High"].max()), 2)
pw_low  = round(float(week_slice["Low"].min()),  2)

camarilla  = camarilla_pivots(pd_high, pd_low, pd_close)
floor_piv  = floor_pivots(pd_high, pd_low, pd_close)
pd_range   = round(pd_high - pd_low, 2)
atr_14     = calc_atr(daily)

# After 4 PM the overnight session for tomorrow has begun
globex_target = next_trading_day(trade_date) if rth_closed else trade_date
globex_h, globex_l = get_globex_levels(intraday, globex_target)


today_bars = intraday[intraday.index.date == trade_date]

bias, bias_color, score, reasons = determine_bias(
    curr_price, pd_high, pd_low, pd_close,
    camarilla["R3"], camarilla["S3"],
    globex_h, globex_l,
)

# Fill title with bias color now that we know it
title_slot.markdown(
    f'<div style="padding-top:0px; margin-top:-20px; margin-left:-1rem;">'
    f'<div style="display:flex; align-items:center; gap:14px;">'
    f'{LOGO_SVG}'
    f'<span style="font-size:5em; font-weight:700; color:{bias_color};'
    f'letter-spacing:3px; line-height:1.1; font-family:\'IBM Plex Mono\',monospace;'
    f'text-shadow:0 0 20px {bias_color}55;">MNQ DAILY DASHBOARD</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ── Two-column layout: main content | news rail ───────────────────────────────
main_col, news_col = st.columns([4, 1])

# ── News Rail (right) ─────────────────────────────────────────────────────────
with news_col:

    st.markdown(
        "<div style='color:#ff9900; font-family:\"IBM Plex Mono\",monospace; "
        "font-size:0.78rem; font-weight:700; letter-spacing:0.12em; "
        "text-transform:uppercase; margin-bottom:10px; border-bottom:1px solid #2a2a2a; "
        "padding-bottom:6px;'>Market News</div>",
        unsafe_allow_html=True,
    )
    news = fetch_news()
    if news:
        source_colors = {
            "MarketWatch": "#69f0ae",
            "CNBC":        "#ff9900",
            "Reuters":     "#64b5f6",
        }
        cards = ""
        for item in news:
            color = source_colors.get(item["source"], "#aaa")
            ago   = time_ago(item["published"])
            cards += f"""
            <div style="border-bottom:1px solid #1a1a1a; padding:7px 0;">
              <div style="color:{color}; font-size:0.65rem; text-transform:uppercase;
                          letter-spacing:0.06em; margin-bottom:3px;">
                {item["source"]} &nbsp;·&nbsp;
                <span style="color:#555;">{ago}</span>
              </div>
              <div style="font-size:1.00em; line-height:1.35; color:#c8c8c8;">
                <a href="{item["link"]}" target="_blank"
                   style="color:#c8c8c8; text-decoration:none;">{item["title"]}</a>
              </div>
            </div>"""
        st.markdown(
            f"<div style='font-family:\"IBM Plex Mono\",monospace;'>{cards}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("News unavailable.")

# ── Main Content (left) ───────────────────────────────────────────────────────
with main_col:
    # Bias Banner
    if bias == "BULLISH":
        animal = BULL_SVG.format(w=82)
    elif bias == "LEANING BULLISH":
        animal = BULL_SVG.format(w=62)
    elif bias == "BEARISH":
        animal = BEAR_SVG.format(w=82)
    elif bias == "LEANING BEARISH":
        animal = BEAR_SVG.format(w=62)
    else:
        animal = ""

    st.markdown(
        f"""
        <div style="background:{bias_color}22; border-left:6px solid {bias_color};
                    padding:18px 24px; border-radius:8px; margin-bottom:8px;
                    display:flex; align-items:center; justify-content:space-between;">
          <div>
            <div style="color:{bias_color}; font-size:2rem; font-weight:700; letter-spacing:2px;">
              NY SESSION BIAS: {bias}
            </div>
            <div style="color:#aaa; margin-top:4px;">
              Score: <b style="color:{bias_color}">{score:+d}</b> &nbsp;|&nbsp;
              Ref: <b>{curr_price:.2f}</b> &nbsp;|&nbsp;
              PDR: <b>{pd_range:.2f} pts</b> &nbsp;|&nbsp;
              ATR14: <b>{f"{atr_14:.2f} pts" if atr_14 else "loading..."}</b> &nbsp;|&nbsp;
              {"NEXT SESSION — " + str(next_trading_day(trade_date)) if rth_closed else "SESSION — " + str(trade_date)}
            </div>
          </div>
          {animal}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Bias factors (click to expand)", expanded=False):
        for arrow, text in reasons:
            color = "#00c853" if arrow == "▲" else ("#d50000" if arrow == "▼" else "#888")
            st.markdown(
                f'<span style="color:{color}; font-size:1.1rem">**{arrow}**</span>&nbsp; {text}',
                unsafe_allow_html=True,
            )

    # Chart
    fig = go.Figure()
    if not today_bars.empty:
        fig.add_trace(go.Candlestick(
            x=today_bars.index,
            open=today_bars["Open"],
            high=today_bars["High"],
            low=today_bars["Low"],
            close=today_bars["Close"],
            name="NQ",
            increasing_line_color="#00c853",
            decreasing_line_color="#d50000",
        ))
    chart_levels = [
        ("R4",  camarilla["R4"], "rgba(105,240,174,1)",    "solid",   2.5),
        ("R3",  camarilla["R3"], "rgba(185,246,202,0.85)", "dashdot", 1.5),
        ("PDH", pd_high,         "rgba(100,149,237,1)",    "dash",    1.8),
        ("PDC", pd_close,        "rgba(180,180,180,0.65)", "dot",     1.2),
        ("PDL", pd_low,          "rgba(100,149,237,1)",    "dash",    1.8),
        ("S3",  camarilla["S3"], "rgba(255,171,145,0.85)", "dashdot", 1.5),
        ("S4",  camarilla["S4"], "rgba(255,112,67,1)",     "solid",   2.5),
    ]
    if globex_h:
        chart_levels.append(("Glob H", globex_h, "rgba(180,100,255,0.85)", "dash", 1.3))
        chart_levels.append(("Glob L", globex_l, "rgba(180,100,255,0.85)", "dash", 1.3))
    for label, val, color, dash, width in chart_levels:
        fig.add_hline(
            y=val, line_color=color, line_dash=dash, line_width=width,
            annotation_text=f"  {label}  {val:.0f}",
            annotation_font_color=color, annotation_font_size=12,
            annotation_position="right",
        )
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=680,
        margin=dict(r=130, l=10, t=10, b=10),
        xaxis_title="Time (ET)",
        yaxis_title="Price",
        legend=dict(orientation="h", y=1.01, x=0),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Levels Grid
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.subheader("Camarilla (CAMS)")
        cam_colors = {
            "R5": "#00e676",
            "R4": "#69f0ae",
            "R3": "#b9f6ca",
            "S3": "#ffab91",
            "S4": "#ff7043",
            "S5": "#d50000",
        }
        cam_html = ""
        for name in ["R5", "R4", "R3", "S3", "S4", "S5"]:
            val   = camarilla[name]
            delta = curr_price - val
            color = cam_colors[name]
            arrow = "▲" if delta > 0 else "▼"
            cam_html += f"""
            <div style="background:{color}18; border-left:4px solid {color};
                        padding:6px 12px; margin:3px 0; border-radius:5px;">
              <span style="color:{color}; font-weight:700; font-size:1.4rem">{name}</span>
              <span style="color:#f0f0f0; float:right; font-size:1.4rem; font-weight:600">{val:.2f}</span>
              <br>
              <span style="color:#aaa; font-size:0.88rem">{arrow} {delta:+.2f} from price</span>
            </div>"""
        st.markdown(cam_html, unsafe_allow_html=True)

    with c2:
        st.subheader(f"Pivots  ({pd_date})")
        fp_colors = {
            "R5": "#00e676",
            "R4": "#48f595",
            "R3": "#69f0ae",
            "R2": "#a5f3c8",
            "R1": "#b9f6ca",
            "PP": "#ff9900",
            "S1": "#ffab91",
            "S2": "#ff8a65",
            "S3": "#ff7043",
            "S4": "#e64a19",
            "S5": "#d50000",
        }
        fp_html = ""
        for name in ["R5", "R4", "R3", "R2", "R1", "PP", "S1", "S2", "S3", "S4", "S5"]:
            val   = floor_piv[name]
            delta = curr_price - val
            color = fp_colors[name]
            arrow = "▲" if delta > 0 else "▼"
            fp_html += (
                f"<div style='background:{color}18; border-left:4px solid {color};"
                f"padding:6px 12px; margin:3px 0; border-radius:5px;'>"
                f"<span style='color:{color}; font-weight:700; font-size:1.4rem'>{name}</span>"
                f"<span style='color:#f0f0f0; float:right; font-size:1.4rem; font-weight:600'>{val:.2f}</span>"
                f"<br><span style='color:#aaa; font-size:0.88rem'>{arrow} {delta:+.2f} from price</span>"
                f"</div>"
            )
        st.markdown(fp_html, unsafe_allow_html=True)

    with c3:
        st.subheader(f"Prev Day  ({pd_date})")
        st.metric("PDH — High",  f"{pd_high:.2f}",  f"{curr_price - pd_high:+.2f}")
        st.metric("PDO — Open",  f"{pd_open:.2f}",  f"{curr_price - pd_open:+.2f}")
        st.metric("PDC — Close", f"{pd_close:.2f}", f"{curr_price - pd_close:+.2f}")
        st.metric("PDL — Low",   f"{pd_low:.2f}",   f"{curr_price - pd_low:+.2f}")

    with c4:
        st.subheader("Overnight / Globex")
        if globex_h and globex_l:
            glo_mid   = round((globex_h + globex_l) / 2, 2)
            glo_range = round(globex_h - globex_l, 2)
            st.metric("Globex High",  f"{globex_h:.2f}", f"{curr_price - globex_h:+.2f}")
            st.metric("Globex Mid",   f"{glo_mid:.2f}",  f"{curr_price - glo_mid:+.2f}")
            st.metric("Globex Low",   f"{globex_l:.2f}", f"{curr_price - globex_l:+.2f}")
            st.metric("Globex Range", f"{glo_range:.2f} pts")
        else:
            st.info("No Globex data yet.\n(Pre-market or weekend)")

    st.caption(
        "Data: Yahoo Finance via yfinance (15-min delayed during RTH).  "
        "Camarilla R5/S5 = Close ± (High − Low).  "
        "Bias is informational — not financial advice."
    )
