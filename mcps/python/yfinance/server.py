#!/usr/bin/env python3
"""
yfinance MCP Server

Provides stock fundamentals data via Yahoo Finance API (yfinance library).
More generous rate limits than Alpha Vantage.
"""

import json
import sys
import yfinance as yf
from typing import Any


def create_tool_definition(name: str, description: str, parameters: dict) -> dict:
    """Create MCP tool definition."""
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys())
        }
    }


def get_company_overview(symbol: str) -> dict[str, Any]:
    """
    Get company fundamentals similar to Alpha Vantage COMPANY_OVERVIEW.
    
    Returns trailing/forward PE, EPS, margins, market cap, growth rates, etc.
    """
    try:
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
            "PriceToSalesRatioTTM": info.get("priceToSalesTrailing12Months", "N/A"),
            "PriceToBookRatio": info.get("priceToBook", "N/A"),
            "EVToRevenue": info.get("enterpriseToRevenue", "N/A"),
            "EVToEBITDA": info.get("enterpriseToEbitda", "N/A"),
            
            # Per-share metrics
            "EPS": info.get("trailingEps", "N/A"),
            "DilutedEPSTTM": info.get("trailingEps", "N/A"),
            "BookValue": info.get("bookValue", "N/A"),
            "DividendPerShare": info.get("dividendRate", "N/A"),
            "DividendYield": info.get("dividendYield", "N/A"),
            
            # Profitability
            "ProfitMargin": info.get("profitMargins", "N/A"),
            "OperatingMarginTTM": info.get("operatingMargins", "N/A"),
            "GrossProfitTTM": info.get("grossProfits", "N/A"),
            "ReturnOnAssetsTTM": info.get("returnOnAssets", "N/A"),
            "ReturnOnEquityTTM": info.get("returnOnEquity", "N/A"),
            
            # Revenue and growth
            "RevenueTTM": info.get("totalRevenue", "N/A"),
            "RevenuePerShareTTM": info.get("revenuePerShare", "N/A"),
            "QuarterlyRevenueGrowthYOY": info.get("revenueGrowth", "N/A"),
            "QuarterlyEarningsGrowthYOY": info.get("earningsGrowth", "N/A"),
            
            # Price data
            "CurrentPrice": info.get("currentPrice", "N/A"),
            "52WeekHigh": info.get("fiftyTwoWeekHigh", "N/A"),
            "52WeekLow": info.get("fiftyTwoWeekLow", "N/A"),
            "50DayMovingAverage": info.get("fiftyDayAverage", "N/A"),
            "200DayMovingAverage": info.get("twoHundredDayAverage", "N/A"),
            
            # Share data
            "SharesOutstanding": info.get("sharesOutstanding", "N/A"),
            "Beta": info.get("beta", "N/A"),
            
            # Analyst data
            "AnalystTargetPrice": info.get("targetMeanPrice", "N/A"),
            "NumberOfAnalystOpinions": info.get("numberOfAnalystOpinions", "N/A"),
        }
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch data for {symbol}. Check symbol validity."
        }


def get_earnings(symbol: str) -> dict[str, Any]:
    """Get earnings data (historical EPS)."""
    try:
        ticker = yf.Ticker(symbol)
        earnings = ticker.earnings
        
        if earnings is None or earnings.empty:
            return {"success": False, "message": "No earnings data available"}
        
        # Convert to dict for JSON serialization
        earnings_dict = earnings.to_dict('index')
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "earnings": earnings_dict
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_financials(symbol: str, statement_type: str = "income") -> dict[str, Any]:
    """
    Get financial statements.
    
    statement_type: "income", "balance", "cashflow"
    """
    try:
        ticker = yf.Ticker(symbol)
        
        if statement_type == "income":
            data = ticker.financials
        elif statement_type == "balance":
            data = ticker.balance_sheet
        elif statement_type == "cashflow":
            data = ticker.cashflow
        else:
            return {
                "success": False,
                "error": f"Invalid statement_type: {statement_type}. Use: income, balance, cashflow"
            }
        
        if data is None or data.empty:
            return {"success": False, "message": f"No {statement_type} statement data available"}
        
        # Convert to dict
        data_dict = data.to_dict()
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "statement_type": statement_type,
                "financials": data_dict
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_call_tool(tool_name: str, arguments: dict) -> dict:
    """Handle tool execution."""
    if tool_name == "get_company_overview":
        return get_company_overview(arguments.get("symbol", ""))
    
    elif tool_name == "get_earnings":
        return get_earnings(arguments.get("symbol", ""))
    
    elif tool_name == "get_financials":
        return get_financials(
            arguments.get("symbol", ""),
            arguments.get("statement_type", "income")
        )
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def handle_list_tools() -> dict:
    """List available tools."""
    return {
        "tools": [
            create_tool_definition(
                "get_company_overview",
                "Get comprehensive company fundamentals including valuation metrics (PE, PEG, P/S), profitability (margins, ROE, ROA), growth rates, and price data. Similar to Alpha Vantage COMPANY_OVERVIEW but with more generous rate limits.",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., NVDA, AAPL, TSLA)"
                    }
                }
            ),
            create_tool_definition(
                "get_earnings",
                "Get historical earnings (EPS) data by fiscal year.",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    }
                }
            ),
            create_tool_definition(
                "get_financials",
                "Get financial statements (income statement, balance sheet, or cash flow).",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "statement_type": {
                        "type": "string",
                        "description": "Type of statement: 'income', 'balance', or 'cashflow'"
                    }
                }
            )
        ]
    }


def main():
    """Main MCP server loop."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            
            if request.get("method") == "tools/list":
                response = handle_list_tools()
            
            elif request.get("method") == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                response = handle_call_tool(tool_name, arguments)
            
            else:
                response = {"error": "Unknown method"}
            
            # Send response
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
