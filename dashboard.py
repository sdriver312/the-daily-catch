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

st_autorefresh(interval=300_000, key="autorefresh")

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

/* ── Refresh button ── */
button[kind="secondary"], button {
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-color: #ff9900 !important;
    color: #ff9900 !important;
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
    df = yf.download(ticker, period="15d", interval="1d",
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
    h4  = round(c + r * k / 2, 2)
    h3  = round(c + r * k / 4, 2)
    l3  = round(c - r * k / 4, 2)
    l4  = round(c - r * k / 2, 2)
    ext = round((h4 - h3) * 1.168, 2)
    return {
        "R5": round(h4 + ext, 2),
        "R4": h4,
        "R3": h3,
        "S3": l3,
        "S4": l4,
        "S5": round(l4 - ext, 2),
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

def get_rth_levels(intraday, session_date):
    mask = (
        (intraday.index.date == session_date) &
        (intraday.index.time >= dtime(9, 30)) &
        (intraday.index.time < dtime(16, 0))
    )
    rth = intraday[mask]
    if rth.empty:
        return None, None, None, None
    return (
        round(float(rth["High"].max()), 2),
        round(float(rth["Low"].min()), 2),
        round(float(rth["Open"].iloc[0]), 2),
        round(float(rth["Close"].iloc[-1]), 2),
    )

def calc_vwap(bars):
    if bars.empty or "Volume" not in bars.columns:
        return None
    vol = bars["Volume"].replace(0, float("nan"))
    typical = (bars["High"] + bars["Low"] + bars["Close"]) / 3
    cum_pv = (typical * vol).cumsum()
    cum_v  = vol.cumsum()
    last = (cum_pv / cum_v).dropna()
    if last.empty:
        return None
    return round(float(last.iloc[-1]), 2)

def get_weekly_rth_levels(intraday, ref_date, lookback_days=5):
    """RTH high/low across the last lookback_days sessions before ref_date."""
    rth = intraday[
        (intraday.index.date < ref_date) &
        (intraday.index.time >= dtime(9, 30)) &
        (intraday.index.time < dtime(16, 0))
    ]
    unique_dates = sorted(set(rth.index.date))
    if not unique_dates:
        return None, None
    window = set(unique_dates[-lookback_days:])
    bars = rth[[d in window for d in rth.index.date]]
    if bars.empty:
        return None, None
    return round(float(bars["High"].max()), 2), round(float(bars["Low"].min()), 2)


def get_opening_range(intraday, session_date, minutes=15):
    start  = dtime(9, 30)
    end_dt = datetime.combine(session_date, start) + timedelta(minutes=minutes)
    end    = end_dt.time()
    mask = (
        (intraday.index.date == session_date) &
        (intraday.index.time >= start) &
        (intraday.index.time < end)
    )
    or_bars = intraday[mask]
    if or_bars.empty:
        return None, None
    return round(float(or_bars["High"].max()), 2), round(float(or_bars["Low"].min()), 2)

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

# Title row
title_col, spacer_col, btn_col = st.columns([7, 2, 1])
with title_col:
    st.markdown(
        f"""<div style="padding-top:0px; margin-top:-20px; margin-left:-1rem;">
              <div style="display:flex; align-items:center; gap:14px;">
                {LOGO_SVG}
                <span style="font-size:5em; font-weight:700; color:#ff9900;
                             letter-spacing:3px; line-height:1.1;
                             font-family:'IBM Plex Mono',monospace;
                             text-shadow:0 0 30px rgba(255,153,0,0.3);">
                  MNQ DAILY DASHBOARD
                </span>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )
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

# PDH/PDL/PDO/PDC derived from intraday RTH bars — accurate to the session,
# avoids yfinance daily bar issues (incomplete bars, full Globex session vs RTH)
ref_date = trade_date if rth_closed else prev_trading_day(trade_date)
ref_rth  = get_rth_levels(intraday, ref_date)

if all(v is not None for v in ref_rth):
    pd_high, pd_low, pd_open, pd_close = ref_rth
    pd_date = ref_date
else:
    # Fallback to daily bar if intraday doesn't cover that date
    prev    = daily.iloc[prev_idx]
    pd_date = daily_dates[prev_idx]
    pd_open  = round(float(prev["Open"]),  2)
    pd_high  = round(float(prev["High"]),  2)
    pd_low   = round(float(prev["Low"]),   2)
    pd_close = round(float(prev["Close"]), 2)

camarilla = camarilla_pivots(pd_high, pd_low, pd_close)

# Weekly H/L from intraday RTH bars — now that ref_date is defined
pw_high, pw_low = get_weekly_rth_levels(intraday, ref_date, lookback_days=5)
if pw_high is None:  # fallback to daily bar if intraday window too short
    week_slice = daily.iloc[max(0, prev_idx - 4): prev_idx + 1]
    pw_high = round(float(week_slice["High"].max()), 2)
    pw_low  = round(float(week_slice["Low"].min()),  2)

# After 4 PM the overnight session for tomorrow has begun
globex_target = next_trading_day(trade_date) if rth_closed else trade_date
globex_h, globex_l = get_globex_levels(intraday, globex_target)


today_bars = intraday[intraday.index.date == trade_date]
rth_bars   = today_bars[
    (today_bars.index.time >= dtime(9, 30)) &
    (today_bars.index.time < dtime(16, 0))
]
vwap    = calc_vwap(rth_bars)
or_high, or_low = get_opening_range(intraday, trade_date, minutes=15)

bias, bias_color, score, reasons = determine_bias(
    curr_price, pd_high, pd_low, pd_close,
    camarilla["R3"], camarilla["S3"],
    globex_h, globex_l,
)

# ── Bias Banner ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{bias_color}22; border-left:6px solid {bias_color};
                padding:18px 24px; border-radius:8px; margin-bottom:8px;">
      <div style="color:{bias_color}; font-size:2rem; font-weight:700; letter-spacing:2px;">
        NY SESSION BIAS: {bias}
      </div>
      <div style="color:#aaa; margin-top:4px;">
        Score: <b style="color:{bias_color}">{score:+d}</b> &nbsp;|&nbsp;
        Reference price: <b>{curr_price:.2f}</b> &nbsp;|&nbsp;
        {"NEXT SESSION — " + str(next_trading_day(trade_date)) if rth_closed else "SESSION — " + str(trade_date)}
      </div>
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

# ── Chart ─────────────────────────────────────────────────────────────────────
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

if vwap and not rth_bars.empty:
    vol = rth_bars["Volume"].replace(0, float("nan"))
    typical  = (rth_bars["High"] + rth_bars["Low"] + rth_bars["Close"]) / 3
    vwap_line = (typical * vol).cumsum() / vol.cumsum()
    fig.add_trace(go.Scatter(
        x=vwap_line.index, y=vwap_line.values,
        mode="lines", name="VWAP",
        line=dict(color="rgba(255,255,255,0.85)", width=1.5, dash="dot"),
    ))

# R5/S5 omitted — extreme extensions, rarely in play intraday
# (label, value, color, dash, width)
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
if or_high:
    chart_levels.append(("OR H", or_high, "rgba(0,210,190,0.8)", "dot", 1.2))
    chart_levels.append(("OR L", or_low,  "rgba(0,210,190,0.8)", "dot", 1.2))

for label, val, color, dash, width in chart_levels:
    fig.add_hline(
        y=val, line_color=color, line_dash=dash, line_width=width,
        annotation_text=f"  {label}  {val:.0f}",
        annotation_font_color=color,
        annotation_font_size=12,
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

# ── Levels Grid ───────────────────────────────────────────────────────────────
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
    st.subheader(f"Prev Day  ({pd_date})")
    st.metric("PDH — High",  f"{pd_high:.2f}",  f"{curr_price - pd_high:+.2f}")
    st.metric("PDO — Open",  f"{pd_open:.2f}",  f"{curr_price - pd_open:+.2f}")
    st.metric("PDC — Close", f"{pd_close:.2f}", f"{curr_price - pd_close:+.2f}")
    st.metric("PDL — Low",   f"{pd_low:.2f}",   f"{curr_price - pd_low:+.2f}")
    st.divider()
    st.caption("**Prev Week**")
    st.metric("PWH", f"{pw_high:.2f}", f"{curr_price - pw_high:+.2f}")
    st.metric("PWL", f"{pw_low:.2f}",  f"{curr_price - pw_low:+.2f}")

with c3:
    st.subheader("VWAP & Opening Range")
    if rth_closed:
        st.metric("VWAP", "—", "populates at 9:30 AM ET")
    elif vwap:
        st.metric("VWAP", f"{vwap:.2f}", f"{curr_price - vwap:+.2f}")
    else:
        st.metric("VWAP", "—", "awaiting RTH open")
    st.divider()
    st.caption("**Opening Range (first 15 min)**")
    if rth_closed:
        st.info("OR populates at 9:45 AM ET")
    elif or_high and or_low:
        or_mid   = round((or_high + or_low) / 2, 2)
        or_range = round(or_high - or_low, 2)
        st.metric("OR High",  f"{or_high:.2f}", f"{curr_price - or_high:+.2f}")
        st.metric("OR Mid",   f"{or_mid:.2f}",  f"{curr_price - or_mid:+.2f}")
        st.metric("OR Low",   f"{or_low:.2f}",  f"{curr_price - or_low:+.2f}")
        st.metric("OR Range", f"{or_range:.2f} pts")
    else:
        st.info("OR populates at 9:45 AM ET")

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
    "Camarilla R5/S5 = Fibonacci extension of R3→R4 range.  "
    "Bias is informational — not financial advice."
)
