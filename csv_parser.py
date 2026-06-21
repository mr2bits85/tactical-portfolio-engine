"""
Broker CSV parser for ingesting raw exported files from brokerages.
Ensures seamless asset_type extraction (EQUITY/OPTION).
"""
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, TextIO, Union

logger = logging.getLogger(__name__)


class BrokerCSVParser:
    """
    A parser for broker CSV exports that normalizes column names and extracts
    asset type (EQUITY/OPTION) reliably.

    The parser is configured with a mapping from broker-specific column names
    to our internal field names.
    """

    def __init__(self, column_mapping: Dict[str, str], date_formats: Optional[List[str]] = None):
        """
        Initialize the parser with a column mapping and optional date formats.

        Args:
            column_mapping: Dictionary mapping our internal field names to a list
                of possible column names in the CSV (case-insensitive).
                Example: {
                    'symbol': ['Symbol', 'Symbol Description'],
                    'quantity': ['Quantity', 'Qty'],
                    ...
                }
            date_formats: List of date format strings to try when parsing dates.
                If None, defaults to common formats.
        """
        self.column_mapping = column_mapping
        self.date_formats = date_formats or [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d-%b-%Y',
            '%d/%m/%Y',
        ]
        # Reverse mapping: from CSV column name (lowered) to internal field name
        self._reverse_map: Dict[str, str] = {}
        for internal_field, possible_names in column_mapping.items():
            for name in possible_names:
                self._reverse_map[name.strip().lower()] = internal_field

    def _find_column(self, fieldnames: List[str], internal_field: str) -> Optional[str]:
        """
        Find the actual CSV column name for an internal field.
        Returns the first matching column name (case-insensitive) or None.
        """
        lowered = [f.lower() for f in fieldnames]
        for csv_name in self.column_mapping.get(internal_field, []):
            if csv_name.lower() in lowered:
                idx = lowered.index(csv_name.lower())
                return fieldnames[idx]
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """
        Parse a date string using the configured formats.
        Returns None if parsing fails.
        """
        if not date_str or not isinstance(date_str, str):
            return None
        date_str = date_str.strip()
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        logger.warning(f"Unable to parse date '{date_str}' with known formats.")
        return None

    def _parse_float(self, value: str) -> Optional[float]:
        """
        Parse a string to float, handling empty strings and commas.
        """
        if not value or not isinstance(value, str):
            return None
        value = value.strip().replace(',', '')
        try:
            return float(value)
        except ValueError:
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        """
        Parse a string to int.
        """
        if not value or not isinstance(value, str):
            return None
        value = value.strip().replace(',', '')
        try:
            return int(value)
        except ValueError:
            return None

    def _determine_asset_type(self, row: Dict[str, str]) -> str:
        """
        Determine asset type (EQUITY/OPTION) from the row data.
        Returns 'EQUITY' or 'OPTION'.
        """
        # First, check if there's a direct asset type column
        asset_type_col = self._find_column(list(row.keys()), 'asset_type')
        if asset_type_col and asset_type_col in row:
            val = row[asset_type_col].strip().upper()
            if val in ('EQUITY', 'STOCK', 'SHARES'):
                return 'EQUITY'
            if val in ('OPTION', 'OPTIONS', 'PUT', 'CALL'):
                return 'OPTION'
            # If the column contains something like 'Equity' or 'Option', we can check
            if 'OPT' in val:
                return 'OPTION'
            if 'EQU' in val or 'STOCK' in val or 'SHARE' in val:
                return 'EQUITY'

        # If no direct column, infer from other columns
        # Check for option-specific columns: strike_price, expiration_date, put_call
        strike_col = self._find_column(list(row.keys()), 'strike_price')
        exp_col = self._find_column(list(row.keys()), 'expiration_date')
        put_call_col = self._find_column(list(row.keys()), 'put_call')
        if (strike_col and row.get(strike_col)) or \
           (exp_col and row.get(exp_col)) or \
           (put_call_col and row.get(put_call_col)):
            return 'OPTION'

        # Check symbol format: options often have embedded dates and strikes
        symbol = row.get('symbol', '').strip()
        # Simple heuristic: if symbol contains a space and looks like it has a date
        # This is broker-specific; we can refine later.
        # For now, we'll default to EQUITY if unsure.
        return 'EQUITY'

    def parse_file(self, file_path: Union[str, TextIO]) -> List[Dict]:
        """
        Parse a broker CSV file and return a list of normalized dictionaries.

        Args:
            file_path: Path to the CSV file or a file-like object.

        Returns:
            List of dictionaries with keys matching our internal schema:
                symbol, asset_type, quantity, price, date, etc.
                (The exact keys depend on the column_mapping provided.)
        """
        if isinstance(file_path, str):
            with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
                return self._parse_csv_file(f)
        else:
            return self._parse_csv_file(file_path)

    def _parse_csv_file(self, file_obj: TextIO) -> List[Dict]:
        """
        Internal method to parse a CSV file object.
        """
        # Use csv.DictReader
        reader = csv.DictReader(file_obj)
        if not reader.fieldnames:
            logger.error("CSV file has no header")
            return []

        # Normalize fieldnames: strip whitespace
        original_fieldnames = reader.fieldnames
        reader.fieldnames = [name.strip() for name in original_fieldnames]

        results = []
        for i, row in enumerate(reader, start=2):  # line 2 is first data row
            # Normalize keys: strip whitespace
            normalized_row = {k.strip(): v for k, v in row.items()}
            # Map to internal fields
            internal_row = {}
            for internal_field, possible_names in self.column_mapping.items():
                csv_col = self._find_column(original_fieldnames, internal_field)
                if csv_col and csv_col in normalized_row:
                    internal_row[internal_field] = normalized_row[csv_col]
                else:
                    # If column not found, set to None (or empty string?)
                    internal_row[internal_field] = None

            # Determine asset type
            internal_row['asset_type'] = self._determine_asset_type(normalized_row)

            # Parse dates and numbers if we have specific fields
            # We'll do this generically: if field name ends with '_date', parse as date
            # if field name ends with '_price' or '_quantity', parse as float, etc.
            # But we can also rely on the caller to do further parsing.
            # For simplicity, we'll leave as strings and let the caller convert.
            # However, we know we need date and numeric fields for our models.
            # We'll attempt to parse common fields.
            for field in list(internal_row.keys()):
                value = internal_row[field]
                if isinstance(value, str):
                    if field.endswith('_date'):
                        parsed = self._parse_date(value)
                        if parsed is not None:
                            internal_row[field] = parsed
                    elif field.endswith('_price') or field.endswith('_quantity') or field in ('quantity', 'price', 'purchase_price', 'total_quantity'):
                        parsed = self._parse_float(value)
                        if parsed is not None:
                            internal_row[field] = parsed
                    elif field.endswith('_id') or field in ('id', 'user_id', 'account_id', 'portfolio_id'):
                        parsed = self._parse_int(value)
                        if parsed is not None:
                            internal_row[field] = parsed

            # Only add rows that have at least a symbol and asset_type
            if internal_row.get('symbol') and internal_row.get('asset_type'):
                results.append(internal_row)
            else:
                logger.warning(f"Skipping row {i} due to missing symbol or asset_type: {internal_row}")

        logger.info(f"Parsed {len(results)} rows from CSV.")
        return results


# Predefined mappings for common brokers (to be extended)
FIDELITY_COLUMN_MAPPING = {
    'symbol': ['Symbol', 'Symbol Description'],
    'asset_type': ['Type', 'Asset Type'],
    'quantity': ['Quantity', 'Qty'],
    'price': ['Last Price', 'Price'],
    'date': ['Date', 'Trade Date', 'Purchase Date'],
    # For transaction_lots we might need purchase_date, purchase_price
    'purchase_date': ['Date', 'Trade Date', 'Purchase Date'],
    'purchase_price': ['Price', 'Last Price'],
}

E_TRADE_COLUMN_MAPPING = {
    'symbol': ['Symbol'],
    'asset_type': ['Type'],
    'quantity': ['Quantity'],
    'price': ['Price'],
    'date': ['Date'],
}


def create_fidelity_parser() -> BrokerCSVParser:
    """Create a parser configured for Fidelity CSV exports."""
    return BrokerCSVParser(FIDELITY_COLUMN_MAPPING)


def create_e_trade_parser() -> BrokerCSVParser:
    """Create a parser configured for E-Trade CSV exports."""
    return BrokerCSVParser(E_TRADE_COLUMN_MAPPING)


# Example usage (for testing)
if __name__ == "__main__":
    # This is just a demo; remove or adapt for actual use.
    import sys
    if len(sys.argv) < 2:
        print("Usage: python csv_parser.py <path_to_csv>")
        sys.exit(1)
    parser = create_fidelity_parser()  # or detect broker from filename
    data = parser.parse_file(sys.argv[1])
    for row in data[:5]:  # print first 5 rows
        print(row)