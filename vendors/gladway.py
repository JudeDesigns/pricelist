"""
Gladway Pricing Parser
Handles PDF price lists from Gladway Pricing
"""

import re
from .base_parser import BaseParser

class GladwayParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.vendor_name = "Gladway Pricing"
        self.vendor_code = "gladway"
        self.product_id_format = "flexible"  # Alphanumeric product IDs
        self.max_product_id_length = 15
        self.requires_dollar_sign = False
    
    def parse_table(self, table):
        """Parse a table from the PDF"""
        items = []
        
        for row in table:
            if len(row) < 3:
                continue
            
            # Try to extract: Product ID | Description | Price
            product_id = str(row[0]).strip() if row[0] else "N/A"
            description = str(row[1]).strip() if row[1] else ""
            price_str = str(row[2]).strip() if row[2] else ""
            
            # Validate and clean
            if not self.validate_product_id(product_id):
                product_id = "N/A"
            
            if not self.validate_description(description):
                continue
            
            price = self.extract_price(price_str)
            if price:
                items.append({
                    'product_id': product_id,
                    'description': description,
                    'price': price
                })
        
        return items
    
    def validate_product_id(self, product_id):
        """Validate product ID format - flexible alphanumeric"""
        if not product_id or product_id == "N/A":
            return True
        
        # Allow alphanumeric with hyphens, 3-15 characters
        pattern = r'^[A-Za-z0-9\-]{3,15}$'
        return bool(re.match(pattern, product_id))
    
    def parse_text_line(self, line):
        """Parse a single text line"""
        # Pattern: Product ID | Description | Price
        parts = re.split(r'\s{2,}|\t', line)
        
        if len(parts) >= 3:
            product_id = parts[0].strip()
            description = parts[1].strip()
            price_str = parts[2].strip()
            
            if not self.validate_product_id(product_id):
                product_id = "N/A"
            
            if self.validate_description(description):
                price = self.extract_price(price_str)
                if price:
                    return {
                        'product_id': product_id,
                        'description': description,
                        'price': price
                    }
        
        return None
    
    def extract_price(self, price_str):
        """Extract price from string"""
        if not price_str:
            return None
        
        # Remove common non-numeric characters except decimal point
        price_str = re.sub(r'[^\d\.]', '', price_str)
        
        try:
            price = float(price_str)
            if price > 0:
                return f"${price:.2f}"
        except ValueError:
            pass
        
        return None

