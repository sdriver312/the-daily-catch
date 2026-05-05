# 🎣 The Daily Catch
### A pre-market levels dashboard for MNQ (Micro E-mini Nasdaq-100)

Every morning before the NY session, you need to know where the fish are.  
This dashboard tells you exactly that — key price levels, overnight context,  
and a bias read so you're not trading blind.

---

## What You Get

| Column | What's In It |
|---|---|
| **Camarilla (CAMS)** | R3/R4/R5 resistance, S3/S4/S5 support — color-coded green to red |
| **Prev Day** | PDH, PDO, PDC, PDL |
| **Prev Week** | PWH, PWM, PWL, weekly range |
| **Overnight / Globex** | High, mid, low and range of the overnight session |

The **NY Session Bias** banner scores 5 factors and tells you whether to look long, short, or stand aside. The dashboard title color matches the bias — green for bullish, red for bearish.

---

## Windows 11 Installation (Fresh)

### Step 1 — Install Python

1. Go to **[python.org/downloads](https://www.python.org/downloads/)** and click the big yellow Download button
2. Run the installer
3. **⚠️ Critical:** Before clicking Install, check the box that says **"Add Python to PATH"** at the bottom of the first screen
4. Click **Install Now** and let it finish

### Step 2 — Download the Dashboard

**Option A — With Git (recommended):**
1. Go to **[git-scm.com](https://git-scm.com/download/win)** and install Git for Windows (all defaults are fine)
2. Open **Command Prompt** (press `Win + R`, type `cmd`, press Enter)
3. Run:
```
git clone https://github.com/sdriver312/the-daily-catch.git
cd the-daily-catch
```

**Option B — Without Git:**
1. Go to **github.com/sdriver312/the-daily-catch**
2. Click the green **Code** button → **Download ZIP**
3. Extract the ZIP somewhere easy (e.g. `C:\Users\YourName\the-daily-catch`)
4. Open Command Prompt and navigate there:
```
cd C:\Users\YourName\the-daily-catch
```

### Step 3 — Install Dependencies

In Command Prompt, run:
```
pip install -r requirements.txt
```
This downloads all required packages. Takes 1–2 minutes. You'll see a lot of text — that's normal.

> **If pip isn't recognized**, try:
> ```
> python -m pip install -r requirements.txt
> ```

### Step 4 — Run the Dashboard

```
streamlit run dashboard.py
```

Your browser will open automatically at `http://localhost:8501`.  
To stop the dashboard, go back to Command Prompt and press `Ctrl + C`.

---

## Every Morning After That

Open Command Prompt, navigate to the folder, and run:
```
streamlit run dashboard.py
```

> **Tip — make it one click:** Create a file called `run.bat` in the dashboard folder containing:
> ```
> streamlit run dashboard.py
> pause
> ```
> Double-click it each morning instead of opening Command Prompt manually.

---

## Getting Updates

If the dashboard gets updated, pull the latest version:
```
git pull
```

---

## Data & Disclaimers

- Price data via [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance) — ~15 min delayed during RTH
- Camarilla levels use the full Globex session daily bar — matches TradingView's Camarilla D indicator
- R5/S5 formula: `Close ± (High − Low)` — confirmed against TradingView
- Dashboard auto-refreshes every 60 seconds
- **This is not financial advice.** It's a tool. Use your own judgment.

---

*Built for the NY session. Tight lines.*
