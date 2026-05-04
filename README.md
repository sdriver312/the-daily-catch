# 🎣 The Daily Catch
### A pre-market levels dashboard for MNQ (Micro E-mini Nasdaq-100)

Every morning before the NY session, you need to know where the fish are.  
This dashboard tells you exactly that — key price levels, overnight context,  
and a bias read so you're not trading blind.

---

## What You Get

| Column | What's In It |
|---|---|
| **Camarilla (CAMS)** | R3 / R4 / R5 resistance, S3 / S4 / S5 support — color-coded green to red |
| **Prev Day** | PDH, PDO, PDC, PDL + previous week H/L |
| **VWAP & Opening Range** | Live session VWAP, 15-min opening range, prev RTH session OHLC |
| **Overnight / Globex** | High, mid, low and range of the overnight session |

The **NY Session Bias** banner at the top scores 5 factors and tells you  
whether to look long, short, or stand aside when the bell rings.

---

## Requirements

- Windows 10 / 11 (also works on Mac/Linux)
- Python 3.10 or higher → [python.org/downloads](https://www.python.org/downloads/)
- An internet connection (data pulled live from Yahoo Finance — free, no account needed)

---

## Installation

**1. Clone the repo**
```
git clone https://github.com/sdriver312/the-daily-catch.git
cd the-daily-catch
```

**2. Install dependencies**
```
pip install -r requirements.txt
```

**3. Run the dashboard**
```
streamlit run dashboard.py
```

Your browser will open automatically at `http://localhost:8501`.  
Close the terminal window to shut it down.

> **Windows tip:** If `pip` isn't recognized, try `python -m pip install -r requirements.txt`

---

## Daily Workflow

1. Open a terminal and run `streamlit run dashboard.py`
2. Check the **Bias banner** — that's your directional read for the session
3. Note the **R3/S3 range** — that's your value area for the day
4. R4/S4 are your breakout triggers. R5/S5 are the "uh oh" levels
5. Go catch something

---

## Data & Disclaimers

- Price data via [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance) — ~15 min delayed during RTH
- Camarilla R5/S5 calculated as a 1.168× Fibonacci extension of the R3→R4 range
- Dashboard auto-refreshes every 5 minutes
- **This is not financial advice.** It's a tool. Use your own judgment.

---

*Built for the NY session. Tight lines.*
