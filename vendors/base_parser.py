"""
Base parser class for vendor-specific PDF parsing.
All vendor parsers should inherit from this class.
"""

import re


class BaseParser:
    """Base class for vendor-specific parsers"""
    
    def __init__(self):
        self.vendor_name = "Base Vendor"
        self.product_id_format = "numeric_only"
        self.max_product_id_length = 6
        self.requires_dollar_sign = True
    
    def extract_product_id(self, text):
        """
        Extract product ID from text.
        Should be overridden by vendor-specific parsers.
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        raise NotImplementedError("Subclasses must implement extract_product_id()")
    
    def validate_product_id(self, product_id):
        """
        Validate a product ID.
        Should be overridden by vendor-specific parsers if needed.
        
        Args:
            product_id: Product ID to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not product_id:
            return False
        
        # Basic validation
        if len(product_id) > self.max_product_id_length:
            return False
        
        return True
    
    def parse_table_row(self, row):
        """
        Parse a table row to extract product information.
        Should be overridden by vendor-specific parsers if needed.
        
        Args:
            row: Table row (list of cell values)
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        return None
    
    def parse_text_line(self, line):
        """
        Parse a text line to extract product information.
        Should be overridden by vendor-specific parsers if needed.
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        return None
    
    def clean_cost(self, cost_str):
        """
        Clean and format cost string.
        Default implementation - can be overridden.
        
        Args:
            cost_str: Raw cost string
        
        Returns:
            str or None: Formatted cost (e.g., '$2.15') or None if invalid
        """
        if not cost_str or not isinstance(cost_str, str):
            return None
        
        # Must contain a dollar sign
        if '$' not in cost_str:
            return None
        
        # Extract price pattern: $XX.XX immediately after $ sign
        price_match = re.search(r'\$\s*(\d{1,4}(?:\.\d{2})?)', cost_str)
        if not price_match:
            print(f"  WARNING: Found $ but couldn't extract price from: '{cost_str}'")
            return None
        
        price_value = price_match.group(1)
        price_float = float(price_value)
        
        # Sanity check: reject prices over $1000
        if price_float > 1000:
            print(f"  WARNING: Price too high (${price_float}), skipping")
            return None
        
        return f'${price_float:.2f}'
    
    def is_valid_description(self, description):
        """
        Validate a description.
        Default implementation - can be overridden.
        
        Args:
            description: Description to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not description or not isinstance(description, str):
            return False
        
        # Must have at least 2 letters
        alpha_count = sum(1 for c in description if c.isalpha())
        if alpha_count < 2:
            return False
        
        return True
    
    def get_config(self):
        """
        Get vendor configuration.
        
        Returns:
            dict: Vendor configuration
        """
        return {
            'name': self.vendor_name,
            'product_id_format': self.product_id_format,
            'max_product_id_length': self.max_product_id_length,
            'requires_dollar_sign': self.requires_dollar_sign,
        }

