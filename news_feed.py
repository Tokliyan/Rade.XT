"""
News-sentiment signal generation — the one part of this project that
costs real money, so it's kept in its own module, on its own schedule,
away from everything else.

Headlines are free (yfinance's built-in news feed, same dependency
already used for stock prices — works for crypto tickers too, e.g.
"BTC-USD", since Yahoo aggregates crypto news the same way). The only
cost is the Claude API call that classifies sentiment.

Needs ANTHROPIC_API_KEY as an environment variable.
"""

import os


def fetch_recent_headlines(news_symbol: str, limit: int = 8) -> list:
    import yfinance as yf

    items = yf.Ticker(news_symbol).news or []
    headlines = []
    for item in items[:limit]:
        # yfinance's news item shape has varied across versions — handle
        # both the flat and the nested "content" forms defensively.
        title = item.get("title") or (item.get("content") or {}).get("title")
        if title:
            headlines.append(title)
    return headlines


def classify_sentiment(headlines: list) -> str:
    """
    Returns BUY / SELL / HOLD based on overall sentiment of the given
    headlines. Costs one Claude API call — see README for the real
    dollar estimate. Fails safe to HOLD on any error (missing API key,
    rate limit, network issue) rather than ever raising and killing the
    tick.
    """
    if not headlines:
        return "HOLD"

    try:
        import anthropic

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        prompt = (
            "You are a terse financial sentiment classifier. Given these "
            "recent news headlines about one asset, reply with exactly one "
            "word: BUY if the news is clearly net positive for the price, "
            "SELL if clearly net negative, or HOLD if mixed, unclear, or not "
            "meaningfully price-relevant. No explanation — one word only.\n\n"
            "Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
        )
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip().upper()
        if "BUY" in text:
            return "BUY"
        if "SELL" in text:
            return "SELL"
        return "HOLD"
    except Exception as e:
        print(f"[news_feed] sentiment call failed, defaulting to HOLD: {e}")
        return "HOLD"
