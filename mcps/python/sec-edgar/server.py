#!/usr/bin/env python3
"""
SEC Edgar MCP Server

Provides access to SEC Edgar filings (10-K, 10-Q) and company facts via the SEC API.
Unlimited rate limits (with proper User-Agent header).
"""

import json
import sys
import requests
from typing import Any, Optional
from datetime import datetime


# SEC requires a User-Agent header with contact info
USER_AGENT = "skills-mcp/1.0 (thomaschangsf@gmail.com)"
BASE_URL = "https://data.sec.gov"


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


def get_cik(symbol: str) -> Optional[str]:
    """
    Get CIK (Central Index Key) from ticker symbol.
    
    Returns 10-digit CIK with leading zeros.
    """
    try:
        # Try ticker lookup via company tickers JSON first
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(tickers_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        
        if response.status_code == 200:
            tickers_data = response.json()
            for entry in tickers_data.values():
                if entry.get("ticker", "").upper() == symbol.upper():
                    return str(entry.get("cik_str", "")).zfill(10)
        
        return None
        
    except Exception as e:
        return None


def get_company_facts(symbol: str) -> dict[str, Any]:
    """
    Get comprehensive company facts from SEC Edgar.
    
    Returns financial statement data including:
    - Assets, liabilities, equity
    - Revenue, net income, EPS
    - Cash flows
    - Share counts
    """
    try:
        cik = get_cik(symbol)
        if not cik:
            return {
                "success": False,
                "error": f"Could not find CIK for symbol: {symbol}"
            }
        
        url = f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"SEC API returned status {response.status_code}"
            }
        
        data = response.json()
        
        # Extract key facts from US-GAAP
        facts = data.get("facts", {}).get("us-gaap", {})
        
        # Helper to get most recent annual value
        def get_recent_annual(concept: str, default="N/A"):
            if concept not in facts:
                return default
            
            units = facts[concept].get("units", {})
            # Try USD first, then shares
            for unit_type in ["USD", "shares", "pure"]:
                if unit_type in units:
                    values = units[unit_type]
                    # Get most recent 10-K filing (annual)
                    annual_values = [
                        v for v in values 
                        if v.get("form") == "10-K" and v.get("val") is not None
                    ]
                    if annual_values:
                        # Sort by filed date, get most recent
                        annual_values.sort(key=lambda x: x.get("filed", ""), reverse=True)
                        return annual_values[0].get("val", default)
            
            return default
        
        result = {
            "Symbol": symbol.upper(),
            "CIK": cik,
            "CompanyName": data.get("entityName", "N/A"),
            
            # Balance Sheet
            "Assets": get_recent_annual("Assets"),
            "Liabilities": get_recent_annual("Liabilities"),
            "StockholdersEquity": get_recent_annual("StockholdersEquity"),
            "CurrentAssets": get_recent_annual("AssetsCurrent"),
            "CurrentLiabilities": get_recent_annual("LiabilitiesCurrent"),
            "CashAndEquivalents": get_recent_annual("CashAndCashEquivalentsAtCarryingValue"),
            
            # Income Statement
            "Revenue": get_recent_annual("Revenues"),
            "RevenueFromContractWithCustomerExcludingAssessedTax": get_recent_annual("RevenueFromContractWithCustomerExcludingAssessedTax"),
            "CostOfRevenue": get_recent_annual("CostOfRevenue"),
            "GrossProfit": get_recent_annual("GrossProfit"),
            "OperatingIncome": get_recent_annual("OperatingIncomeLoss"),
            "NetIncome": get_recent_annual("NetIncomeLoss"),
            "EarningsPerShareBasic": get_recent_annual("EarningsPerShareBasic"),
            "EarningsPerShareDiluted": get_recent_annual("EarningsPerShareDiluted"),
            
            # Cash Flow
            "OperatingCashFlow": get_recent_annual("NetCashProvidedByUsedInOperatingActivities"),
            "InvestingCashFlow": get_recent_annual("NetCashProvidedByUsedInInvestingActivities"),
            "FinancingCashFlow": get_recent_annual("NetCashProvidedByUsedInFinancingActivities"),
            "CapitalExpenditures": get_recent_annual("PaymentsToAcquirePropertyPlantAndEquipment"),
            
            # Share Data
            "CommonStockSharesOutstanding": get_recent_annual("CommonStockSharesOutstanding"),
            "WeightedAverageNumberOfSharesOutstandingBasic": get_recent_annual("WeightedAverageNumberOfSharesOutstandingBasic"),
        }
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch SEC data for {symbol}"
        }


def get_filings(symbol: str, form_type: str = "10-K", count: int = 5) -> dict[str, Any]:
    """
    Get recent filings for a company.
    
    Args:
        symbol: Stock ticker
        form_type: Filing type (10-K, 10-Q, 8-K, etc.)
        count: Number of recent filings to return
    """
    try:
        cik = get_cik(symbol)
        if not cik:
            return {
                "success": False,
                "error": f"Could not find CIK for symbol: {symbol}"
            }
        
        url = f"{BASE_URL}/submissions/CIK{cik}.json"
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"SEC API returned status {response.status_code}"
            }
        
        data = response.json()
        recent_filings = data.get("filings", {}).get("recent", {})
        
        # Filter by form type
        forms = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_docs = recent_filings.get("primaryDocument", [])
        
        matching_filings = []
        for i, form in enumerate(forms):
            if form == form_type:
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}"
                
                matching_filings.append({
                    "form": form,
                    "filingDate": filing_dates[i],
                    "accessionNumber": accession_numbers[i],
                    "url": filing_url
                })
                
                if len(matching_filings) >= count:
                    break
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "cik": cik,
                "form_type": form_type,
                "filings": matching_filings
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def search_filing_text(symbol: str, form_type: str, search_terms: list[str]) -> dict[str, Any]:
    """
    Search for specific terms in a company's most recent filing.
    
    Useful for finding:
    - RPO (Remaining Performance Obligations)
    - Backlog
    - Customer concentration
    - Contract terms
    """
    try:
        # Get most recent filing of this type
        filings_result = get_filings(symbol, form_type, count=1)
        
        if not filings_result.get("success"):
            return filings_result
        
        filings = filings_result["data"]["filings"]
        if not filings:
            return {
                "success": False,
                "error": f"No {form_type} filings found for {symbol}"
            }
        
        filing_url = filings[0]["url"]
        
        # Fetch filing content
        response = requests.get(filing_url, headers={"User-Agent": USER_AGENT}, timeout=15)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Could not fetch filing from {filing_url}"
            }
        
        content = response.text.lower()
        
        # Search for terms and extract context
        matches = []
        for term in search_terms:
            term_lower = term.lower()
            index = content.find(term_lower)
            
            if index != -1:
                # Extract 200 characters before and after
                start = max(0, index - 200)
                end = min(len(content), index + len(term_lower) + 200)
                context = content[start:end]
                
                matches.append({
                    "term": term,
                    "found": True,
                    "context": context
                })
            else:
                matches.append({
                    "term": term,
                    "found": False,
                    "context": None
                })
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "form_type": form_type,
                "filing_date": filings[0]["filingDate"],
                "filing_url": filing_url,
                "matches": matches
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_call_tool(tool_name: str, arguments: dict) -> dict:
    """Handle tool execution."""
    if tool_name == "get_company_facts":
        return get_company_facts(arguments.get("symbol", ""))
    
    elif tool_name == "get_filings":
        return get_filings(
            arguments.get("symbol", ""),
            arguments.get("form_type", "10-K"),
            arguments.get("count", 5)
        )
    
    elif tool_name == "search_filing_text":
        return search_filing_text(
            arguments.get("symbol", ""),
            arguments.get("form_type", "10-K"),
            arguments.get("search_terms", [])
        )
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def handle_list_tools() -> dict:
    """List available tools."""
    return {
        "tools": [
            create_tool_definition(
                "get_company_facts",
                "Get comprehensive financial data from SEC Edgar including balance sheet (assets, liabilities, equity), income statement (revenue, net income, EPS), cash flows (operating, investing, financing, CapEx), and share counts. Data from most recent 10-K filing. Unlimited rate limits.",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., NVDA, AAPL, TSLA)"
                    }
                }
            ),
            create_tool_definition(
                "get_filings",
                "Get list of recent SEC filings (10-K annual reports, 10-Q quarterly reports, 8-K current reports) with filing dates and URLs to full documents. Use to access raw filings for detailed analysis.",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "form_type": {
                        "type": "string",
                        "description": "Filing type: '10-K' (annual), '10-Q' (quarterly), '8-K' (current events)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of recent filings to return (default: 5)"
                    }
                }
            ),
            create_tool_definition(
                "search_filing_text",
                "Search for specific terms in a company's most recent filing. Useful for finding RPO (Remaining Performance Obligations), backlog, customer concentration, contract terms, or any specific disclosure. Returns text context around matches.",
                {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "form_type": {
                        "type": "string",
                        "description": "Filing type to search: '10-K' or '10-Q'"
                    },
                    "search_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of terms to search for (e.g., ['RPO', 'remaining performance obligations', 'backlog'])"
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
