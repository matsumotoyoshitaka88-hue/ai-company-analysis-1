"""EDINET API client for fetching company filings and financial data.

EDINET API v2 endpoints:
- /api/v2/documents.json: List filings by date
- /api/v2/documents/{docID}: Download specific filing
- /api/v2/EdinetcodeDlInfo.csv: Download company code list
"""
from __future__ import annotations

import io
import json
import logging
import zipfile
from datetime import date, timedelta
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

EDINET_BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"


class EdinetClient:
    """Async client for EDINET API v2."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.edinet_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_documents(
        self,
        filing_date: date,
        doc_type: str = "2",  # 2=有価証券報告書
    ) -> list[dict[str, Any]]:
        """List filings for a given date.

        Args:
            filing_date: The date to search.
            doc_type: Document type code. "2" for 有価証券報告書.

        Returns:
            List of filing metadata dicts.
        """
        client = await self._get_client()
        params = {
            "date": filing_date.isoformat(),
            "type": doc_type,
            "Subscription-Key": self.api_key,
        }
        resp = await client.get(f"{EDINET_BASE_URL}/documents.json", params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        return results

    async def search_filings(
        self,
        edinet_code: str,
        doc_type_code: str = "120",  # 120=有価証券報告書
        days_back: int = 400,
    ) -> list[dict[str, Any]]:
        """Search recent filings for a specific company.

        Scans recent dates to find filings by the specified company.
        Uses parallel requests in batches for speed.

        Args:
            edinet_code: EDINET code of the company.
            doc_type_code: "120" for 有価証券報告書, "140" for 四半期報告書.
            days_back: How many days back to search.

        Returns:
            List of matching filings sorted by filing date (newest first).
        """
        import asyncio

        filings: list[dict[str, Any]] = []
        today = date.today()

        # Search in parallel batches of 10 days at a time
        batch_size = 10
        for batch_start in range(0, days_back, batch_size * 30):
            # Process 30-day chunks, each chunk searched in parallel
            for chunk_offset in range(0, 30 * batch_size, 30):
                offset = batch_start + chunk_offset
                if offset >= days_back:
                    break

                dates_to_check = []
                for day in range(30):
                    d = today - timedelta(days=offset + day)
                    if d < today - timedelta(days=days_back):
                        break
                    dates_to_check.append(d)

                # Fetch all dates in this chunk concurrently
                async def _fetch_date(check_date: date) -> list[dict[str, Any]]:
                    try:
                        docs = await self.list_documents(check_date)
                        return [
                            doc for doc in docs
                            if doc.get("edinetCode") == edinet_code
                            and doc.get("docTypeCode") == doc_type_code
                        ]
                    except Exception:
                        return []

                results = await asyncio.gather(
                    *[_fetch_date(d) for d in dates_to_check]
                )
                for batch in results:
                    filings.extend(batch)

                if filings:
                    filings.sort(key=lambda d: d.get("submitDateTime", ""), reverse=True)
                    return filings

        return filings

    async def download_xbrl(self, doc_id: str) -> dict[str, bytes]:
        """Download XBRL data for a filing.

        Args:
            doc_id: Document ID from EDINET.

        Returns:
            Dict mapping filename to file content bytes.
        """
        client = await self._get_client()
        params = {
            "type": "1",  # 1=XBRL
            "Subscription-Key": self.api_key,
        }
        resp = await client.get(
            f"{EDINET_BASE_URL}/documents/{doc_id}",
            params=params,
            timeout=120.0,
        )
        resp.raise_for_status()

        files: dict[str, bytes] = {}
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                # Include inline XBRL (.htm), XBRL (.xbrl), and JSON
                if name.endswith((".xbrl", ".htm", ".json")):
                    # Skip audit docs - focus on PublicDoc
                    if "AuditDoc" in name:
                        continue
                    files[name] = zf.read(name)

        return files

    async def get_company_list(self) -> list[dict[str, Any]]:
        """Download the full EDINET company code list.

        Returns:
            List of company dicts with edinetCode, securities code, name, etc.
        """
        client = await self._get_client()
        params = {
            "type": "2",  # CSV format
            "Subscription-Key": self.api_key,
        }
        resp = await client.get(
            f"{EDINET_BASE_URL}/EdinetcodeDlInfo.csv",
            params=params,
            timeout=120.0,
        )
        resp.raise_for_status()

        # The response is a ZIP containing a CSV
        companies: list[dict[str, Any]] = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if name.endswith(".csv"):
                    import csv

                    content = zf.read(name).decode("cp932", errors="replace")
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        companies.append(dict(row))

        return companies


class XbrlParser:
    """Parse financial data from XBRL files."""

    # Key financial metrics to extract (element local names)
    METRICS = {
        # Income statement
        "NetSales": "revenue",
        "Revenue": "revenue",
        "RevenueIFRS": "revenue",
        "OperatingIncome": "operating_income",
        "OperatingProfit": "operating_income",
        "OperatingProfitIFRS": "operating_income",
        "OrdinaryIncome": "ordinary_income",
        "ProfitLoss": "net_income",
        "NetIncome": "net_income",
        "ProfitLossAttributableToOwnersOfParent": "net_income",
        # Balance sheet
        "TotalAssets": "total_assets",
        "TotalAssetsIFRS": "total_assets",
        "Assets": "total_assets",
        "NetAssets": "net_assets",
        "TotalNetAssets": "net_assets",
        "Equity": "net_assets",
        "EquityAttributableToOwnersOfParent": "shareholders_equity",
        "ShareholdersEquity": "shareholders_equity",
        "TotalLiabilities": "total_liabilities",
        "Liabilities": "total_liabilities",
        "CurrentAssets": "current_assets",
        "CurrentLiabilities": "current_liabilities",
        # Cash flow
        "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
        "CashFlowsFromUsedInOperatingActivities": "operating_cash_flow",
        "NetCashProvidedByUsedInInvestingActivities": "investing_cash_flow",
        "CashFlowsFromUsedInInvestingActivities": "investing_cash_flow",
        "NetCashProvidedByUsedInFinancingActivities": "financing_cash_flow",
        "CashFlowsFromUsedInFinancingActivities": "financing_cash_flow",
        # Per share
        "BasicEarningsLossPerShare": "eps",
        "DividendPaidPerShare": "dividend_per_share",
        # Employees
        "NumberOfEmployees": "employees",
    }

    @staticmethod
    def parse_inline_xbrl(content: bytes) -> dict[str, Any]:
        """Parse inline XBRL (iXBRL) and extract financial metrics.

        This is a simplified parser that extracts tagged numeric values.
        For production, consider using a full XBRL library.
        """
        import re
        from xml.etree import ElementTree

        metrics: dict[str, Any] = {}
        text = content.decode("utf-8", errors="replace")

        # Try to parse as XML first
        try:
            root = ElementTree.fromstring(text)
            # Look for ix:nonFraction elements (inline XBRL)
            namespaces = {
                "ix": "http://www.xbrl.org/2013/inlineXBRL",
                "ixt": "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12",
            }
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "nonFraction":
                    name = elem.get("name", "")
                    local_name = name.split(":")[-1] if ":" in name else name
                    if local_name in XbrlParser.METRICS and elem.text:
                        metric_key = XbrlParser.METRICS[local_name]
                        # Skip negative sign indicator
                        sign = elem.get("sign", "")
                        try:
                            raw = elem.text.replace(",", "").replace(" ", "").replace("\u00a0", "")
                            if not raw or raw == "-":
                                continue
                            value = float(raw)
                            # Check for scale attribute
                            scale = elem.get("scale", "0")
                            value *= 10 ** int(scale)
                            if sign == "-":
                                value = -value
                            # Keep largest absolute value (prefer consolidated over standalone)
                            if metric_key not in metrics or abs(value) > abs(metrics[metric_key]):
                                metrics[metric_key] = value
                        except (ValueError, TypeError):
                            pass
        except ElementTree.ParseError:
            # Fallback: regex-based extraction
            for xbrl_name, metric_key in XbrlParser.METRICS.items():
                pattern = rf'name="[^"]*:{xbrl_name}"[^>]*>([^<]+)<'
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        value = float(match.replace(",", "").replace(" ", ""))
                        if metric_key not in metrics:
                            metrics[metric_key] = value
                    except (ValueError, TypeError):
                        pass

        return metrics

    @staticmethod
    def parse_xbrl_json(content: bytes) -> dict[str, Any]:
        """Parse XBRL-JSON format (newer EDINET filings).

        Args:
            content: JSON bytes from EDINET.

        Returns:
            Dict of financial metrics.
        """
        metrics: dict[str, Any] = {}
        try:
            data = json.loads(content)
            facts = data.get("facts", {})

            for namespace_facts in facts.values():
                if not isinstance(namespace_facts, dict):
                    continue
                for element_name, fact_data in namespace_facts.items():
                    local_name = element_name.split(":")[-1] if ":" in element_name else element_name
                    if local_name in XbrlParser.METRICS:
                        metric_key = XbrlParser.METRICS[local_name]
                        if isinstance(fact_data, dict):
                            for period_key, period_val in fact_data.items():
                                if isinstance(period_val, dict) and "value" in period_val:
                                    try:
                                        value = float(str(period_val["value"]).replace(",", ""))
                                        if metric_key not in metrics:
                                            metrics[metric_key] = value
                                    except (ValueError, TypeError):
                                        pass
        except (json.JSONDecodeError, KeyError):
            pass

        return metrics
