# Fizzy

Fizzy is a public AI trading assistant with voice input and speech output.

Core features:
- browser voice recognition
- browser text-to-speech
- trading dashboard with watchlist
- technical signal summaries
- paper-trading simulation
- public, safe profile and contact configuration
- optional OpenAI integration

## Features included
- Market overview / watchlist cards
- Price, trend, and momentum scoring
- RSI and moving average signals
- Paper-trading portfolio simulation
- Quick trade journal and cash tracking
- Voice-driven chat
- Multi-language support

## Quick start

1. Create a virtual environment
   python -m venv .venv
   source .venv/bin/activate

2. Install dependencies
   pip install -r requirements.txt

3. Copy environment file
   cp .env.example .env

4. Run the app
   uvicorn app:app --reload

5. Open in your browser
   http://127.0.0.1:8000

## Notes
- This app uses `yfinance` to pull market data. Internet access is required.
- For public repos, do not commit personal Gmail, phone numbers, exchange keys, or brokerage credentials.
- This project is educational and simulation-focused, not financial advice.
