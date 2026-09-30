# Fizzy

Fizzy is a public AI trading assistant that can listen and speak. It includes:
- voice input using the browser microphone
- speech output using browser text-to-speech
- a chat interface for trading questions
- a simple market-analysis response engine
- optional OpenAI integration for richer answers

This starter project is designed for a public repo. Keep private keys and personal details in a local .env file and never commit them.

## Features
- Name: Fizzy
- Voice recognition and speaking
- Trading assistant style prompts
- Market summary, trend, risk, and strategy guidance
- Public-safe profile and contact details
- Simple FastAPI backend and browser frontend

## Quick start

1. Create a virtual environment
   python -m venv .venv
   source .venv/bin/activate

2. Install dependencies
   pip install -r requirements.txt

3. Copy environment example
   cp .env.example .env

4. Run the app
   uvicorn app:app --reload

5. Open the app in a browser
   http://127.0.0.1:8000

## Environment variables

Example values are in `.env.example`.

- APP_NAME
- APP_TAGLINE
- OWNER_NAME
- PUBLIC_EMAIL
- CONTACT_URL
- OPENAI_API_KEY
- DEFAULT_LANGUAGE

## Important
- Do not store private Gmail, phone numbers, exchange keys, or brokerage credentials in public source control.
- Use a public email or contact form instead.
- This app is for learning and simulation. It is not financial advice.

## Notes
- If `OPENAI_API_KEY` is not set, Fizzy uses a local trading assistant fallback.
- Voice input uses the browser's speech recognition API, which works best in modern Chromium-based browsers.
