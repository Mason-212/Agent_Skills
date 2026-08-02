# SEC Edgar MCP Server

Access SEC Edgar filings and company financial data - unlimited rate limits with proper User-Agent.

## Tools

### get_company_facts
Get comprehensive financial data from most recent 10-K:

**Balance Sheet:**
- Assets, Liabilities, Stockholders Equity
- Current Assets, Current Liabilities
- Cash and Equivalents

**Income Statement:**
- Revenue, Cost of Revenue, Gross Profit
- Operating Income, Net Income
- EPS (Basic and Diluted)

**Cash Flow:**
- Operating, Investing, Financing Cash Flow
- Capital Expenditures

**Share Data:**
- Common Stock Shares Outstanding
- Weighted Average Shares Outstanding

**Arguments:**
- `symbol` (required): Stock ticker

**Example:**
```json
{
  "name": "get_company_facts",
  "arguments": {
    "symbol": "NVDA"
  }
}
```

### get_filings
Get list of recent SEC filings with URLs.

**Arguments:**
- `symbol` (required): Stock ticker
- `form_type` (required): "10-K" (annual), "10-Q" (quarterly), "8-K" (current events)
- `count` (optional): Number of filings (default: 5)

**Example:**
```json
{
  "name": "get_filings",
  "arguments": {
    "symbol": "NVDA",
    "form_type": "10-K",
    "count": 3
  }
}
```

### search_filing_text
Search for specific terms in most recent filing. Returns text context around matches.

**Use cases:**
- Find RPO (Remaining Performance Obligations)
- Find backlog disclosures
- Find customer concentration
- Find specific contract terms
- Find any disclosure by keyword

**Arguments:**
- `symbol` (required): Stock ticker
- `form_type` (required): "10-K" or "10-Q"
- `search_terms` (required): Array of terms to search

**Example:**
```json
{
  "name": "search_filing_text",
  "arguments": {
    "symbol": "NVDA",
    "form_type": "10-K",
    "search_terms": ["remaining performance obligations", "RPO", "backlog"]
  }
}
```

## Installation

Auto-configured by `scripts/dev_refresh_skills_and_tools.sh`.

Manual installation:
1. Install dependencies: `uv sync` or `pip install requests>=2.31.0`
2. Run server: `uv run server.py` or `python server.py`

## Rate Limits

SEC Edgar API has no documented rate limits when using proper User-Agent header.

**Best practices:**
- Use as primary source for audited financial data (Tier 1)
- Cross-reference with yfinance for real-time metrics
- Search filing text for disclosures not available in structured data

## Data Quality

**Tier 1 (Audited):**
- All data from 10-K/10-Q filings
- XBRL-tagged financial statements
- Most recent annual (10-K) or quarterly (10-Q) data

**Advantages over yfinance/Alpha Vantage:**
- ✅ Direct access to raw filings
- ✅ Search for specific disclosures (RPO, backlog, contracts)
- ✅ Unlimited rate limits
- ✅ Historical filings access
- ✅ 100% audited data (Tier 1 source)

**Limitations:**
- ❌ Not real-time (filings lag by quarters)
- ❌ Requires parsing for unstructured data
- ❌ Company-specific terminology varies

## Recommended Strategy

**For think skill equity analysis:**
1. **yfinance**: Real-time fundamentals (PE, margins, growth)
2. **SEC Edgar**: Deep-dive verification (10-K data, RPO, contracts)
3. **Alpha Vantage**: Specialized data (technical indicators, commodities)

**Example workflow:**
```
1. Define universe via web search
2. Pull real-time fundamentals via yfinance (5-10 stocks)
3. Deep-dive top 2-3 candidates via SEC Edgar:
   - Verify revenue, margins from 10-K
   - Search for RPO growth
   - Check customer concentration
4. Fill gaps with web search for forward estimates
```
