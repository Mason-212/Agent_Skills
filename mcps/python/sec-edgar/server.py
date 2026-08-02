#!/usr/bin/env python3
"""
SEC Edgar MCP Server

Provides access to SEC EDGAR filings and company facts.
Unlimited rate limit (requires proper User-Agent).
"""

import requests
from typing import Any
from fastmcp import FastMCP

mcp = FastMCP("sec-edgar")

# Required User-Agent for SEC API (must identify yourself)
USER_AGENT = "skills-repo-mcp chang@example.com"


@mcp.tool()
def get_company_facts(symbol: str) -> dict[str, Any]:
    """
    Get company facts from SEC Edgar including financial metrics from 10-K/10-Q filings.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        Dictionary with SEC company facts
    """
    # First, get CIK from ticker
    cik = get_cik(symbol)
    if not cik:
        raise ValueError(f"Could not find CIK for symbol: {symbol}")
    
    # Get company facts
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    headers = {"User-Agent": USER_AGENT}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()


@mcp.tool()
def search_filings(symbol: str, form_type: str = "10-K") -> dict[str, Any]:
    """
    Search SEC filings for a company.
    
    Args:
        symbol: Stock ticker symbol
        form_type: Type of form (10-K, 10-Q, 8-K, etc.)
    
    Returns:
        Dictionary with recent filings
    """
    # Get CIK
    cik = get_cik(symbol)
    if not cik:
        raise ValueError(f"Could not find CIK for symbol: {symbol}")
    
    # Search filings
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    headers = {"User-Agent": USER_AGENT}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    # Filter by form type
    filings = data.get("filings", {}).get("recent", {})
    filtered_filings = []
    
    if filings:
        forms = filings.get("form", [])
        filing_dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])
        
        for i, form in enumerate(forms):
            if form == form_type:
                filtered_filings.append({
                    "form": form,
                    "filingDate": filing_dates[i] if i < len(filing_dates) else "N/A",
                    "accessionNumber": accession_numbers[i] if i < len(accession_numbers) else "N/A",
                    "primaryDocument": primary_docs[i] if i < len(primary_docs) else "N/A",
                })
    
    return {
        "symbol": symbol.upper(),
        "cik": cik,
        "form_type": form_type,
        "filings": filtered_filings[:10]  # Return most recent 10
    }


def get_cik(symbol: str) -> str | None:
    """
    Get CIK (Central Index Key) from stock ticker symbol.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        CIK as string, or None if not found
    """
    # SEC provides a ticker-to-CIK mapping
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Search for symbol
        symbol_upper = symbol.upper()
        for entry in data.values():
            if entry.get("ticker", "").upper() == symbol_upper:
                return str(entry["cik_str"])
        
        return None
    except Exception:
        return None


if __name__ == "__main__":
    mcp.run()
