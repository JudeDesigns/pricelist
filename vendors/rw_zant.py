"""
RW Zant vendor parser.

Product ID Format: Numeric only, max 6 digits
Examples: 103387, 12345, 999999
"""

import re
from .base_parser import BaseParser


class RWZantParser(BaseParser):
    """Parser for RW Zant PDFs"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "RW Zant"
        self.product_id_format = "numeric_only"
        self.max_product_id_length = 6
        self.requires_dollar_sign = True
    
    def extract_product_id(self, text):
        """
        Extract product ID from text (numeric only, max 6 digits).
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        text = text.strip()
        
        # Match digits at the start
        match = re.match(r'^(\d+)', text)
        if not match:
            return None, text
        
        digits = match.group(1)
        remaining = text[len(digits):].strip()
        
        # If more than 6 digits, split at position 6
        if len(digits) > 6:
            product_id = digits[:6]
            remaining = digits[6:] + ' ' + remaining
        else:
            product_id = digits
        
        return product_id, remaining
    
    def validate_product_id(self, product_id):
        """
        Validate RW Zant product ID.
        
        Args:
            product_id: Product ID to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not product_id:
            return False
        
        # Must be numeric only
        if not product_id.isdigit():
            return False
        
        # Max 6 digits
        if len(product_id) > 6:
            return False
        
        return True
    
    def parse_table_row(self, row):
        """
        Parse a table row from RW Zant PDF.
        
        Args:
            row: Table row (list of cell values)
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not row or len(row) < 3:
            return None
        
        # Find the column with the dollar sign (cost)
        cost_idx = -1
        for idx, cell in enumerate(row):
            if cell and '$' in str(cell):
                cost_idx = idx
                break
        
        if cost_idx < 0:
            return None
        
        # Extract raw values
        raw_id = str(row[0]).strip() if row[0] else ''
        raw_price = str(row[cost_idx]).strip()
        
        # Description is everything between product_id and cost
        description_parts = []
        for i in range(1, cost_idx):
            if row[i] and str(row[i]).strip():
                description_parts.append(str(row[i]).strip())
        
        if not raw_id or not description_parts:
            return None
        
        # Clean and validate the cost
        cost_cleaned = self.clean_cost(raw_price)
        if not cost_cleaned:
            return None
        
        # Extract product ID
        product_id, extra_text = self.extract_product_id(raw_id)
        if not product_id or not self.validate_product_id(product_id):
            return None
        
        # Build description
        description = ' '.join(description_parts)
        if extra_text:
            description = extra_text + ' ' + description
        
        # Clean up multiple spaces
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Validate description
        if not self.is_valid_description(description):
            return None
        
        return {
            'product_id': product_id,
            'description': description,
            'cost': cost_cleaned
        }
    
    def parse_text_line(self, line):
        """
        Parse a text line from RW Zant PDF.
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not line or not line.strip():
            return None
        
        # Skip lines without dollar signs
        if '$' not in line:
            return None
        
        # Skip headers
        if 'product id' in line.lower() or 'special offering' in line.lower():
            return None
        
        # Strategy 1: Split by multiple spaces or tabs
        parts = re.split(r'\s{2,}|\t', line.strip())
        
        if len(parts) >= 3:
            # Find which part has the dollar sign (cost)
            cost_idx = -1
            for idx, part in enumerate(parts):
                if '$' in part:
                    cost_idx = idx
                    break
            
            if cost_idx >= 0:
                # Extract product ID
                first_part = parts[0].strip()
                product_id, extra_text = self.extract_product_id(first_part)
                
                if not product_id:
                    return None
                
                cost_cleaned = self.clean_cost(parts[cost_idx])
                
                # Description is everything between product_id and cost
                if cost_idx > 1:
                    description = ' '.join(parts[1:cost_idx]).strip()
                else:
                    description = parts[1].strip() if len(parts) > 1 else ''
                
                # Add any extra digits from product ID to description
                if extra_text:
                    description = extra_text + ' ' + description
                
                # Clean up multiple spaces
                description = re.sub(r'\s+', ' ', description).strip()
                
                # Validate before returning
                if (self.validate_product_id(product_id) and
                    self.is_valid_description(description) and
                    cost_cleaned):
                    return {
                        'product_id': product_id,
                        'description': description,
                        'cost': cost_cleaned
                    }
        
        # Strategy 2: Try regex pattern matching
        pattern = r'^(\d+)\s+([A-Za-z][\w\s\-\.]+?)\s+(?:\(\d+\))?\s*(?:\d+[/#\w]*\s+)?(?:10#\s+)?(\$[\d,\.]+)'
        match = re.search(pattern, line)
        
        if match:
            raw_id = match.group(1).strip()
            description = match.group(2).strip()
            cost_str = match.group(3).strip()
            
            # Extract proper product ID
            product_id, extra_text = self.extract_product_id(raw_id)
            
            if not product_id:
                return None
            
            # Add extra digits to description if any
            if extra_text:
                description = extra_text + ' ' + description
            
            # Clean up multiple spaces
            description = re.sub(r'\s+', ' ', description).strip()
            
            cost_cleaned = self.clean_cost(cost_str)
            
            # Validate before returning
            if (self.validate_product_id(product_id) and
                self.is_valid_description(description) and
                cost_cleaned):
                return {
                    'product_id': product_id,
                    'description': description,
                    'cost': cost_cleaned
                }
        
        return None

