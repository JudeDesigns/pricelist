"""
Purcell Vendor Parser
Handles Purcell specific product ID and pricing formats
"""

import re
from vendors.base_parser import BaseParser


class PurcellParser(BaseParser):
    """Parser for Purcell price lists"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "Purcell"
        self.vendor_code = "purcell"
        self.product_id_format = "flexible"
        self.max_product_id_length = 15
        self.requires_dollar_sign = False
    
    def extract_product_id(self, text):
        """
        Extract product ID from text.
        Purcell format: Flexible - can be numeric or alphanumeric
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        text = text.strip()
        
        # Try to match alphanumeric codes at the start
        # Pattern: letters/numbers/hyphens (e.g., "ABC123", "12345", "A-123")
        match = re.match(r'^([A-Za-z0-9\-]{3,15})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining
        
        return None, text
    
    def validate_product_id(self, product_id):
        """
        Validate Purcell product ID.
        Format: Flexible alphanumeric or N/A
        
        Args:
            product_id: Product ID to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not product_id or not isinstance(product_id, str):
            return False
        
        # Allow N/A for products without IDs
        if product_id.upper() in ['N/A', 'NA', '-']:
            return True
        
        # Allow alphanumeric with optional hyphens (3-15 characters)
        if re.match(r'^[A-Za-z0-9\-]{3,15}$', product_id):
            return True
        
        return False
    
    def clean_cost(self, cost_str):
        """
        Clean and format cost string for Purcell.
        
        Args:
            cost_str: Raw cost string
        
        Returns:
            str or None: Formatted cost or None if invalid
        """
        if not cost_str:
            return None
        
        # Handle special cases
        if cost_str.upper() in ['OUT', 'QUOTE', 'N/A', 'TBD']:
            return cost_str.upper()
        
        # Extract price using regex
        price_match = re.search(r'(\d{1,5}(?:\.\d{2})?)', cost_str)
        if not price_match:
            return None
        
        price_value = price_match.group(1)
        price_float = float(price_value)
        
        # Sanity check: reject prices over $1000
        if price_float > 1000:
            return None
        
        return f'${price_float:.2f}'
    
    def parse_table_row(self, row):
        """
        Parse a table row from Purcell PDF.
        
        Args:
            row: Table row (list of cell values)
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not row or len(row) < 2:
            return None
        
        # Clean the row
        row_clean = [str(cell).strip() if cell else '' for cell in row]
        
        print(f"  DEBUG [Purcell Table]: Row has {len(row_clean)} columns: {row_clean}")
        
        # Try to find product ID in first column
        raw_id = row_clean[0]
        
        # Description is typically in second column
        description = row_clean[1] if len(row_clean) > 1 else ''
        
        # Price is typically in last column
        raw_price = row_clean[-1]
        
        # Skip if no description
        if not description or len(description) < 2:
            print(f"  DEBUG [Purcell Table]: No valid description")
            return None
        
        # Skip if no price
        if not raw_price or not re.search(r'\d', raw_price):
            print(f"  DEBUG [Purcell Table]: No price found: '{raw_price}'")
            return None
        
        print(f"  DEBUG [Purcell Table]: Raw ID: '{raw_id}', Desc: '{description}', Price: '{raw_price}'")
        
        # Extract and validate product ID (or use N/A if no ID)
        if not raw_id or not raw_id.strip():
            product_id = 'N/A'
            print(f"  DEBUG [Purcell Table]: No product ID, using N/A")
        else:
            product_id, extra_text = self.extract_product_id(raw_id)
            if not product_id or not self.validate_product_id(product_id):
                # If no valid ID found, use N/A
                product_id = 'N/A'
                print(f"  DEBUG [Purcell Table]: Invalid product ID '{raw_id}', using N/A")
        
        print(f"  DEBUG [Purcell Table]: Valid product ID: '{product_id}'")
        
        # Clean the cost
        cost = self.clean_cost(raw_price)
        if not cost:
            print(f"  DEBUG [Purcell Table]: Invalid cost: '{raw_price}'")
            return None
        
        print(f"  DEBUG [Purcell Table]: ✅ SUCCESS - ID: {product_id}, Desc: {description}, Cost: {cost}")
        
        return {
            'product_id': product_id,
            'description': description.strip(),
            'cost': cost
        }
    
    def parse_text_line(self, line):
        """
        Parse a text line from Purcell PDF (OCR-based).
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not line or not line.strip():
            return None
        
        # Skip lines without prices
        if not re.search(r'\d+\.\d{2}', line):
            return None
        
        print(f"  DEBUG [Purcell]: Parsing line: '{line}'")
        
        # Pattern: Product ID (optional), description, price
        # Try with product ID first
        pattern = r'^([A-Za-z0-9\-]{3,15})\s+(.+?)\s+\$?\s*(\d{1,5}\.\d{2})\s*$'
        match = re.search(pattern, line)
        
        if match:
            product_id = match.group(1)
            description = match.group(2).strip()
            cost = match.group(3)
            
            if self.validate_product_id(product_id) and self.is_valid_description(description):
                cost_clean = self.clean_cost(cost)
                if cost_clean:
                    print(f"  DEBUG [Purcell]: ✅ Matched! ID={product_id}, Desc={description}, Cost={cost_clean}")
                    return {
                        'product_id': product_id,
                        'description': description,
                        'cost': cost_clean
                    }
        
        # Try without product ID (use N/A)
        pattern = r'^(.+?)\s+\$?\s*(\d{1,5}\.\d{2})\s*$'
        match = re.search(pattern, line)
        
        if match:
            description = match.group(1).strip()
            cost = match.group(2)
            
            if self.is_valid_description(description):
                cost_clean = self.clean_cost(cost)
                if cost_clean:
                    print(f"  DEBUG [Purcell]: ✅ Matched! ID=N/A, Desc={description}, Cost={cost_clean}")
                    return {
                        'product_id': 'N/A',
                        'description': description,
                        'cost': cost_clean
                    }
        
        return None

