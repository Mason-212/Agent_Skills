# yfinance MCP Server

Yahoo Finance data via yfinance library - more generous rate limits than Alpha Vantage.

## Tools

### get_company_overview
Get comprehensive company fundamentals:
- **Valuation**: Trailing PE, Forward PE, PEG, P/S, P/B, EV/Revenue, EV/EBITDA
- **Profitability**: Profit margin, operating margin, ROE, ROA
- **Growth**: Revenue growth YoY, earnings growth YoY
- **Price data**: Current price, 52-week high/low, moving averages
- **Analyst data**: Target price, number of analysts

**Arguments:**
- `symbol` (required): Stock ticker (e.g., "NVDA", "AAPL")

**Example:**
```json
{
  "name": "get_company_overview",
  "arguments": {
    "symbol": "NVDA"
  }
}
```

### get_earnings
Get historical earnings (EPS) by fiscal year.

**Arguments:**
- `symbol` (required): Stock ticker

### get_financials
Get financial statements.

**Arguments:**
- `symbol` (required): Stock ticker
- `statement_type` (required): "income", "balance", or "cashflow"

## Installation

This MCP is auto-configured by `scripts/dev_refresh_skills_and_tools.sh`.

Manual installation:
1. Install dependencies: `uv sync` or `pip install yfinance>=0.2.40`
2. Run server: `uv run server.py` or `python server.py`

## Rate Limits

Yahoo Finance (via yfinance) has much more generous rate limits than Alpha Vantage:
- No documented hard daily limit
- Use as primary source for stock fundamentals
- Fall back to Alpha Vantage only if yfinance fails

## Comparison to Alpha Vantage

**yfinance advantages:**
- ✅ Better rate limits (no 25/day cap)
- ✅ Forward PE available
- ✅ More analyst data (target price, # of analysts)
- ✅ Comprehensive profitability metrics in one call

**Alpha Vantage advantages:**
- ✅ More technical indicators (SMA, EMA, RSI, etc.)
- ✅ Historical options data
- ✅ Commodities, forex, crypto
- ✅ Economic indicators (GDP, CPI, etc.)

**Recommended strategy:** Use yfinance for stock fundamentals, Alpha Vantage for specialized data.
