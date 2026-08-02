#!/usr/bin/env python3
"""
yfinance MCP Server

Provides stock fundamentals data via Yahoo Finance API (yfinance library).
More generous rate limits than Alpha Vantage.
"""

import yfinance as yf
from typing import Any
from fastmcp import FastMCP

mcp = FastMCP("yfinance")


@mcp.tool()
def get_company_overview(symbol: str) -> dict[str, Any]:
    """
    Get comprehensive company fundamentals including valuation metrics (PE, PEG, P/S), profitability (margins, ROE, ROA), growth rates, and price data. Similar to Alpha Vantage COMPANY_OVERVIEW but with more generous rate limits.
    
    Args:
        symbol: Stock ticker symbol (e.g., NVDA, AAPL, TSLA)
    
    Returns:
        Dictionary with company fundamentals
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # Extract key metrics
    result = {
        "Symbol": symbol.upper(),
        "Name": info.get("longName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Currency": info.get("currency", "USD"),
        "Exchange": info.get("exchange", "N/A"),
        
        # Valuation metrics
        "MarketCapitalization": info.get("marketCap", "N/A"),
        "PERatio": info.get("trailingPE", "N/A"),
        "ForwardPE": info.get("forwardPE", "N/A"),
        "PEGRatio": info.get("pegRatio", "N/A"),
        "PriceToSalesRatio": info.get("priceToSalesTrailing12Months", "N/A"),
        "PriceToBookRatio": info.get("priceToBook", "N/A"),
        
        # Profitability
        "ProfitMargin": info.get("profitMargins", "N/A"),
        "OperatingMargin": info.get("operatingMargins", "N/A"),
        "ReturnOnAssets": info.get("returnOnAssets", "N/A"),
        "ReturnOnEquity": info.get("returnOnEquity", "N/A"),
        
        # Per-share metrics
        "EPS": info.get("trailingEps", "N/A"),
        "ForwardEPS": info.get("forwardEps", "N/A"),
        "BookValue": info.get("bookValue", "N/A"),
        "DividendPerShare": info.get("dividendRate", "N/A"),
        "DividendYield": info.get("dividendYield", "N/A"),
        
        # Revenue & Income
        "Revenue": info.get("totalRevenue", "N/A"),
        "RevenuePerShare": info.get("revenuePerShare", "N/A"),
        "QuarterlyRevenueGrowth": info.get("revenueGrowth", "N/A"),
        "QuarterlyEarningsGrowth": info.get("earningsGrowth", "N/A"),
        
        # Balance sheet
        "TotalCash": info.get("totalCash", "N/A"),
        "TotalDebt": info.get("totalDebt", "N/A"),
        "CurrentRatio": info.get("currentRatio", "N/A"),
        "DebtToEquity": info.get("debtToEquity", "N/A"),
        
        # Price data
        "CurrentPrice": info.get("currentPrice", "N/A"),
        "TargetHighPrice": info.get("targetHighPrice", "N/A"),
        "TargetLowPrice": info.get("targetLowPrice", "N/A"),
        "TargetMeanPrice": info.get("targetMeanPrice", "N/A"),
        "52WeekHigh": info.get("fiftyTwoWeekHigh", "N/A"),
        "52WeekLow": info.get("fiftyTwoWeekLow", "N/A"),
        
        # Analyst recommendations
        "RecommendationMean": info.get("recommendationMean", "N/A"),
        "RecommendationKey": info.get("recommendationKey", "N/A"),
        "NumberOfAnalystOpinions": info.get("numberOfAnalystOpinions", "N/A"),
    }
    
    return result


@mcp.tool()
def get_earnings(symbol: str) -> dict[str, Any]:
    """
    Get historical earnings (EPS) data by fiscal year.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with earnings history
    """
    ticker = yf.Ticker(symbol)
    earnings = ticker.earnings
    
    if earnings is None or earnings.empty:
        return {
            "symbol": symbol.upper(),
            "earnings": [],
            "note": "No earnings data available"
        }
    
    # Convert to dict format
    earnings_list = []
    for index, row in earnings.iterrows():
        earnings_list.append({
            "fiscalYear": str(index),
            "revenue": float(row.get("Revenue", 0)) if "Revenue" in row else "N/A",
            "earnings": float(row.get("Earnings", 0)) if "Earnings" in row else "N/A",
        })
    
    return {
        "symbol": symbol.upper(),
        "earnings": earnings_list
    }


@mcp.tool()
def get_financials(symbol: str, statement_type: str = "income") -> dict[str, Any]:
    """
    Get financial statements (income statement, balance sheet, or cash flow).
    
    Args:
        symbol: Stock ticker symbol
        statement_type: Type of statement - 'income', 'balance', or 'cashflow'
    
    Returns:
        Dictionary with financial statement data
    """
    ticker = yf.Ticker(symbol)
    
    # Get appropriate statement
    if statement_type == "income":
        data = ticker.financials
    elif statement_type == "balance":
        data = ticker.balance_sheet
    elif statement_type == "cashflow":
        data = ticker.cashflow
    else:
        raise ValueError(f"Invalid statement_type: {statement_type}. Must be 'income', 'balance', or 'cashflow'")
    
    if data is None or data.empty:
        return {
            "symbol": symbol.upper(),
            "statement_type": statement_type,
            "financials": {},
            "note": "No financial data available"
        }
    
    # Convert to dict format (transpose so years are keys)
    data_dict = data.to_dict()
    
    # Convert Timestamp keys to strings
    data_dict_str = {}
    for date_key, values in data_dict.items():
        date_str = date_key.strftime("%Y-%m-%d") if hasattr(date_key, 'strftime') else str(date_key)
        data_dict_str[date_str] = {k: (float(v) if isinstance(v, (int, float)) else str(v)) 
                                    for k, v in values.items()}
    
    return {
        "symbol": symbol.upper(),
        "statement_type": statement_type,
        "financials": data_dict_str
    }


if __name__ == "__main__":
    mcp.run()
