import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
import numpy as np
import pandas as pd
import yfinance as yf

load_dotenv()

app = FastAPI(title="Fizzy")
templates = Jinja2Templates(directory="templates")

APP_NAME = os.getenv("APP_NAME", "Fizzy")
APP_TAGLINE = os.getenv("APP_TAGLINE", "Your voice-powered AI trading assistant")
OWNER_NAME = os.getenv("OWNER_NAME", "Your Name")
PUBLIC_EMAIL = os.getenv("PUBLIC_EMAIL", "hello@yourdomain.com")
CONTACT_URL = os.getenv("CONTACT_URL", "https://yourdomain.com/contact")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

WATCHLIST = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]
PORTFOLIO = {"cash": 10000.0, "positions": {}, "history": []}

TRANSLATIONS = {
    "en": {
        "greeting": f"Hi! I am {APP_NAME}. I can help you analyze the market and answer trading questions.",
        "default": "I can help with market overview, risk checks, watchlist questions, and trade planning.",
        "contact": f"Public contact: {PUBLIC_EMAIL}. For formal contact, use {CONTACT_URL}.",
        "not_financial_advice": "This is educational analysis and not financial advice. Always manage risk carefully.",
        "focus": "Focus on trend, risk, confirmation, and position sizing before entering a trade.",
    },
    "es": {
        "greeting": f"¡Hola! Soy {APP_NAME}. Puedo ayudarte a analizar el mercado y responder preguntas de trading.",
        "default": "Puedo ayudarte con visión general del mercado, evaluación de riesgo y planificación de operaciones.",
        "contact": f"Contacto público: {PUBLIC_EMAIL}. Para contacto formal: {CONTACT_URL}.",
        "not_financial_advice": "Este es un análisis educativo y no constituye asesoramiento financiero.",
        "focus": "Enfócate en tendencia, riesgo, confirmación y tamaño de posición antes de operar.",
    },
    "fr": {
        "greeting": f"Salut ! Je suis {APP_NAME}. Je peux t’aider à analyser le marché et répondre aux questions de trading.",
        "default": "Je peux t’aider avec l’analyse du marché, l’évaluation des risques et la planification des trades.",
        "contact": f"Contact public : {PUBLIC_EMAIL}. Pour un contact formel : {CONTACT_URL}.",
        "not_financial_advice": "Ceci est une analyse éducative et non un conseil financier.",
        "focus": "Concentrez-vous sur la tendance, le risque, la confirmation et la taille de position avant d’entrer en trade.",
    },
    "ar": {
        "greeting": f"مرحبًا! أنا {APP_NAME}. أستطيع مساعدتك في تحليل السوق والإجابة عن أسئلة التداول.",
        "default": "أستطيع مساعدتك في نظرة عامة للسوق، تقييم المخاطر، ومراجعة قائمة المراقبة.",
        "contact": f"التواصل العام: {PUBLIC_EMAIL}. للتواصل الرسمي: {CONTACT_URL}.",
        "not_financial_advice": "هذا تحليل تعليمي وليس نصيحة مالية.",
        "focus": "ركز على الاتجاه، المخاطر، التأكيد، وحجم المركز قبل الدخول في صفقة.",
    },
}


def get_language(lang: str) -> str:
    return lang if lang in TRANSLATIONS else DEFAULT_LANGUAGE


def rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_val = 100 - (100 / (1 + rs))
    return float(rsi_val.iloc[-1]) if not rsi_val.empty else 50.0


def compute_signal(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"signal": "No data", "score": 0, "action": "wait"}

    close = df["Close"].astype(float)
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else last
    change_pct = ((last - prev) / prev) * 100 if prev else 0.0
    sma5 = float(close.tail(5).mean())
    sma20 = float(close.tail(20).mean())
    sma50 = float(close.tail(50).mean())
    rsi_value = rsi(close)

    score = 50
    if last > sma20:
        score += 15
    else:
        score -= 10
    if last > sma50:
        score += 10
    else:
        score -= 10
    if rsi_value > 60:
        score += 10
    elif rsi_value < 40:
        score -= 10
    if change_pct > 0:
        score += 8
    else:
        score -= 8

    if score >= 60:
        action = "bullish"
    elif score <= 40:
        action = "bearish"
    else:
        action = "neutral"

    return {
        "last": last,
        "change_pct": change_pct,
        "sma5": sma5,
        "sma20": sma20,
        "sma50": sma50,
        "rsi": rsi_value,
        "score": int(max(0, min(100, score))),
        "action": action,
    }


def get_market_data(symbol: str) -> Dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo", interval="1d")
        if hist.empty:
            return {"symbol": symbol, "error": "No data"}
        signal = compute_signal(hist)
        return {
            "symbol": symbol,
            "name": ticker.info.get("shortName", symbol),
            "last": signal["last"],
            "change_pct": signal["change_pct"],
            "sma5": signal["sma5"],
            "sma20": signal["sma20"],
            "sma50": signal["sma50"],
            "rsi": signal["rsi"],
            "score": signal["score"],
            "action": signal["action"],
        }
    except Exception as exc:
        return {"symbol": symbol, "error": str(exc)}


def get_watchlist_data() -> List[Dict[str, Any]]:
    items = []
    for symbol in WATCHLIST:
        data = get_market_data(symbol)
        items.append(data)
    return items


def build_local_trade_response(message: str, language: str) -> str:
    text = message.lower()
    lang = get_language(language)
    t = TRANSLATIONS[lang]

    if "hello" in text or "hi" in text or "hey" in text:
        return t["greeting"]

    if "contact" in text or "email" in text or "reach" in text:
        return t["contact"]

    if "risk" in text or "danger" in text:
        return "Risk management matters most. Limit losses, size carefully, and avoid chasing breakouts without confirmation."

    if "trend" in text or "bullish" in text or "bearish" in text or "market" in text:
        if "btc" in text or "bitcoin" in text:
            return "Bitcoin trend analysis: check wider momentum, support zones, and volume. A strong breakout with confirmation can be bullish, but risk must stay controlled."
        if "eth" in text or "ethereum" in text:
            return "Ethereum trend analysis: validate higher lows, relative strength, and volume before assuming bullish continuation."
        if any(sym in text for sym in ["nvda", "aapl", "tsla", "msft", "amzn"]):
            return "For equities, confirm trend, volume, and key levels. Favor structured entries and enforce risk limits on every trade."
        return "Trend analysis should combine price action, volume, key levels, and confirmation. Do not rely on a single signal alone."

    if "strategy" in text or "plan" in text or "trade" in text:
        return "A solid trading plan includes a clear entry, stop loss, target, position size, and exit rule. Review the setup before execution."

    if "watchlist" in text:
        return "Keep a tight watchlist of high-quality setups. Prioritize clean structure, strong trend, and favorable risk-reward."

    if "summary" in text or "overview" in text:
        return "Market overview: first check trend, volatility, sector strength, and risk sentiment. Then look for clean setups with managed exposure."

    return t["default"] + " " + t["not_financial_advice"] + " " + t["focus"]


def ai_trade_response(message: str, language: str) -> str:
    if not client:
        return build_local_trade_response(message, language)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are {APP_NAME}, a voice-enabled AI trading assistant. "
                        f"You help with market analysis, trade setup ideas, and risk management. "
                        f"Use public information only. "
                        f"Never claim certainty or promise profit. "
                        f"Always mention that this is educational and not financial advice."
                    ),
                },
                {"role": "user", "content": message},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return build_local_trade_response(message, language)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "tagline": APP_TAGLINE,
            "owner_name": OWNER_NAME,
            "public_email": PUBLIC_EMAIL,
            "contact_url": CONTACT_URL,
        },
    )


@app.get("/api/market")
async def api_market():
    return {"items": get_watchlist_data()}


@app.get("/api/signal")
async def api_signal(symbol: str = "AAPL"):
    return get_market_data(symbol)


@app.get("/api/portfolio")
async def api_portfolio():
    return PORTFOLIO


@app.post("/api/trade")
async def api_trade(symbol: str = Form(...), side: str = Form(...), quantity: float = Form(...)):
    symbol = symbol.upper()
    side = side.lower()
    qty = float(quantity)
    if qty <= 0:
        return {"status": "error", "message": "Quantity must be greater than zero."}

    market = get_market_data(symbol)
    if "error" in market:
        return {"status": "error", "message": f"Unable to fetch price for {symbol}"}

    price = float(market["last"])
    value = price * qty
    if side == "buy":
        if PORTFOLIO["cash"] < value:
            return {"status": "error", "message": "Insufficient cash for this buy order."}
        PORTFOLIO["cash"] -= value
        PORTFOLIO["positions"].setdefault(symbol, {"qty": 0.0, "avg": 0.0})
        pos = PORTFOLIO["positions"][symbol]
        total_qty = pos["qty"] + qty
        pos["avg"] = ((pos["avg"] * pos["qty"]) + (price * qty)) / total_qty if total_qty else 0
        pos["qty"] = total_qty
    elif side == "sell":
        pos = PORTFOLIO["positions"].get(symbol)
        if not pos or pos["qty"] < qty:
            return {"status": "error", "message": "Not enough shares to sell."}
        PORTFOLIO["cash"] += value
        pos["qty"] -= qty
        if pos["qty"] == 0:
            PORTFOLIO["positions"].pop(symbol, None)
    else:
        return {"status": "error", "message": "Side must be buy or sell."}

    PORTFOLIO["history"].append({
        "symbol": symbol,
        "side": side,
        "quantity": qty,
        "price": price,
        "timestamp": pd.Timestamp.utcnow().isoformat()
    })

    return {"status": "ok", "portfolio": PORTFOLIO}


@app.post("/chat")
async def chat(language: str = Form("en"), message: str = Form(...)):
    answer = ai_trade_response(message, language)
    return {"answer": answer}


@app.get("/health")
async def health():
    return {"status": "ok", "app": APP_NAME}
