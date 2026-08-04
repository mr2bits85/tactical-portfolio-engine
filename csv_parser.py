import csv
import io
from typing import List, Dict, Any


class FidelityPortfolioParser:
    """
    Parses Fidelity Active Trader Pro 'All Accounts' CSV exports.
    Treats the CSV as the authoritative source for portfolio state.
    """

    EXPECTED_HEADER_PREFIX = "Account,Symbol"

    @staticmethod
    def parse_csv(file_contents: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parses the raw CSV string and groups holdings by Account.
        Returns: { 'ROTH *1234': [{symbol_data}, ...], 'IRA *6789': [...] }
        """
        lines = file_contents.strip().splitlines()

        # 1. Dynamic Header Discovery
        header_index = -1
        for i, line in enumerate(lines):
            if line.startswith(FidelityPortfolioParser.EXPECTED_HEADER_PREFIX):
                header_index = i
                break

        if header_index == -1:
            raise ValueError("Could not find the expected header row starting with 'Account,Symbol'")

        # 2. Extract Data
        csv_data = lines[header_index:]
        reader = csv.DictReader(csv_data)

        grouped_portfolios = {}

        for row in reader:
            account_id = row.get("Account", "").strip()
            if not account_id:
                continue  # Skip blank rows

            if account_id not in grouped_portfolios:
                grouped_portfolios[account_id] = []

            # Clean and map the data
            holding = {
                "symbol": row.get("Symbol", "").strip(),
                "description": row.get("Description", "").strip(),
                "quantity": FidelityPortfolioParser._parse_float(row.get("Quantity")),
                "last_price": FidelityPortfolioParser._parse_float(row.get("Last")),
                "avg_cost": FidelityPortfolioParser._parse_float(row.get("$ Avg Cost")),
                "basis": FidelityPortfolioParser._parse_float(row.get("Basis")),
                "value": FidelityPortfolioParser._parse_float(row.get("Value")),
                "earnings_date": row.get("Earnings Date", "").strip() or None,
                "div_ex_date": row.get("Div Ex-Date", "").strip() or None
            }

            grouped_portfolios[account_id].append(holding)

        return grouped_portfolios

    @staticmethod
    def _parse_float(value: str) -> float:
        """Safely strips currency symbols and commas, returns float."""
        if not value or value.strip() in ['--', 'n/a', 'N/A']:
            return 0.0
        clean_val = value.replace('$', '').replace(',', '').strip()
        try:
            return float(clean_val)
        except ValueError:
            return 0.0