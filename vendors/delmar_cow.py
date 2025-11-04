"""
Del Mar Distributions COW Parser
Handles Del Mar Distributions COW price list PDFs
"""

from .base_parser import BaseParser
import re

class DelMarCowParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.vendor_name = "Del Mar Distributions COW"
        self.vendor_code = "delmar_cow"
        self.product_id_format = "hyphenated"  # Format: 6 digits - 2 digits (e.g., 330020-61)
        self.max_product_id_length = 15
        self.requires_dollar_sign = False
    
    def parse_table_row(self, row):
        """Parse a single table row"""
        if len(row) < 3:
            return None
        
        product_id = row[0].strip()
        description = row[1].strip()
        price = row[2].strip()
        
        # Validate product ID (flexible alphanumeric format)
        if not self.validate_product_id(product_id):
            product_id = "N/A"
        
        # Validate price
        if not self.validate_price(price):
            return None
        
        return {
            'product_id': product_id,
            'description': description,
            'price': price
        }
    
    def validate_product_id(self, product_id):
        """Validate product ID format - hyphenated format (e.g., 330020-61)"""
        if not product_id or product_id == "N/A":
            return True

        # Primary format: 6 digits, hyphen, 2 digits (e.g., 330020-61)
        primary_pattern = r'^\d{6}-\d{2}$'
        if re.match(primary_pattern, product_id):
            return True

        # Fallback: Allow flexible alphanumeric with hyphens, 3-15 characters
        fallback_pattern = r'^[A-Za-z0-9\-]{3,15}$'
        return bool(re.match(fallback_pattern, product_id))
    
    def parse_text_line(self, line):
        """Parse a single text line"""
        # Pattern: Product ID | Description | Price
        # Example: "COW-123 | BEEF RIBEYE | $12.99"
        
        parts = line.split('|')
        if len(parts) >= 3:
            product_id = parts[0].strip()
            description = parts[1].strip()
            price = parts[2].strip()
            
            if not self.validate_product_id(product_id):
                product_id = "N/A"
            
            if self.validate_price(price):
                return {
                    'product_id': product_id,
                    'description': description,
                    'price': price
                }
        
        # Try regex pattern for space-separated format
        # Pattern: Product ID followed by description and price
        pattern = r'^([A-Za-z0-9\-]{3,15})\s+(.+?)\s+(\$?\d+\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            product_id = match.group(1)
            description = match.group(2).strip()
            price = match.group(3)
            
            if self.validate_price(price):
                return {
                    'product_id': product_id,
                    'description': description,
                    'price': price
                }
        
        return None

