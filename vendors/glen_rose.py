"""
Glen Rose Meat Company vendor parser.

Product ID Format: Supports hyphenated format (e.g., 130324002-01)
Examples: 130324002-01, 112233-02, 123456

This vendor's PDFs are typically image-based and require OCR.
"""

import re
from .base_parser import BaseParser


class GlenRoseParser(BaseParser):
    """Parser for Glen Rose Meat Company PDFs"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "Glen Rose Meat Company"
        self.product_id_format = "hyphenated"
        self.max_product_id_length = 15  # Longer to support hyphenated IDs
        self.requires_dollar_sign = False  # Glen Rose prices don't have $ sign!
    
    def extract_product_id(self, text):
        """
        Extract product ID from text (supports hyphenated format).
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        text = text.strip()

        # Glen Rose specific pattern: 8-11 digits, hyphen, 2-3 digits
        # Examples: 711000005-01, 714200005-01, 130324002-01
        match = re.match(r'^(\d{8,11}-\d{2,3})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining

        # Fallback: Try shorter hyphenated format (6-10 digits, 1-3 digits)
        match = re.match(r'^(\d{6,10}-\d{1,3})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining

        # Last resort: Match continuous digits (non-hyphenated)
        match = re.match(r'^(\d+)', text)
        if not match:
            return None, text

        digits = match.group(1)
        remaining = text[len(digits):].strip()

        # If more than 8 digits without hyphen, might be missing hyphen
        if len(digits) >= 10:
            # Try to split: first 9 digits, hyphen, last 2 digits
            product_id = digits[:9] + '-' + digits[9:11] if len(digits) >= 11 else digits
            remaining = digits[11:] + ' ' + remaining if len(digits) > 11 else remaining
        else:
            product_id = digits

        return product_id, remaining
    
    def validate_product_id(self, product_id):
        """
        Validate Glen Rose product ID.

        Args:
            product_id: Product ID to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not product_id:
            return False

        # Allow N/A for products without IDs
        if product_id.upper() in ['N/A', 'NA', '-']:
            return True

        # Primary format: 8-11 digits, hyphen, 2-3 digits (e.g., 711000005-01)
        if re.match(r'^\d{8,11}-\d{2,3}$', product_id):
            return True

        # Fallback: Allow shorter hyphenated format (6-10 digits, 1-3 digits)
        if re.match(r'^\d{6,10}-\d{1,3}$', product_id):
            return True

        # Allow non-hyphenated numeric IDs (fallback)
        if product_id.isdigit() and 6 <= len(product_id) <= 11:
            return True

        return False

    def clean_cost(self, cost_str):
        """
        Glen Rose: Clean and format cost string.
        Glen Rose prices typically don't have dollar signs - just numbers like "2.25" or "12.10"
        """
        if not cost_str:
            return None

        cost_str = str(cost_str).strip()

        # Skip non-price text (common in Glen Rose PDFs)
        skip_words = ['FROZEN', 'OUT', 'PRAWN', 'BRAWLEY', 'CENTRAL', 'VALLEY',
                      'QUAN', 'GREATER', 'OMAHA', 'JBS', 'SWIFT', 'ROMA', 'PRIME',
                      'AVG', 'IMP', 'HP', 'AS', 'BONELESS', 'BONE', 'IN']
        if any(word in cost_str.upper() for word in skip_words):
            return None

        # If it has a dollar sign, extract the number after it
        if '$' in cost_str:
            match = re.search(r'\$\s*(\d{1,4}(?:\.\d{2})?)', cost_str)
            if match:
                try:
                    cost_value = float(match.group(1))
                    return f"${cost_value:.2f}"
                except ValueError:
                    return None

        # Glen Rose format: just a number like "2.25" or "12.10"
        # Pattern: decimal number with 1-4 digits before decimal, exactly 2 after
        match = re.search(r'^(\d{1,4}\.\d{2})$', cost_str)
        if match:
            try:
                cost_value = float(match.group(1))
                # Sanity check: price should be between $0.01 and $9999.99
                if 0.01 <= cost_value <= 9999.99:
                    return f"${cost_value:.2f}"
            except ValueError:
                pass

        return None

    def parse_table_row(self, row):
        """
        Parse a table row from Glen Rose PDF.

        Glen Rose table structure:
        [Product ID] [Description] [Category] [Status/Notes] [Price]
        Example: 711000005-01 | CHUCK ROLL DICED | CHUCK | | 6.20

        Args:
            row: Table row (list of cell values)

        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not row or len(row) < 3:
            return None

        # Clean the row - remove None and empty strings
        row_clean = [str(cell).strip() if cell else '' for cell in row]

        # DEBUG: Print the row
        print(f"  DEBUG [Glen Rose Table]: Row has {len(row_clean)} columns: {row_clean}")

        # Glen Rose: Price is ALWAYS the LAST column (no $ sign, just numbers like "6.20")
        raw_price = row_clean[-1]

        # Validate price format
        cost_cleaned = self.clean_cost(raw_price)
        if not cost_cleaned:
            print(f"  DEBUG [Glen Rose Table]: Invalid price: '{raw_price}'")
            return None

        print(f"  DEBUG [Glen Rose Table]: Found price: {cost_cleaned}")

        # Product ID is ALWAYS the FIRST column
        raw_id = row_clean[0]
        if not raw_id:
            print(f"  DEBUG [Glen Rose Table]: No product ID in first column")
            return None

        print(f"  DEBUG [Glen Rose Table]: Raw ID from first column: '{raw_id}'")

        # Extract and validate product ID
        product_id, extra_text = self.extract_product_id(raw_id)
        if not product_id:
            print(f"  DEBUG [Glen Rose Table]: Could not extract product ID from: '{raw_id}'")
            return None

        if not self.validate_product_id(product_id):
            print(f"  DEBUG [Glen Rose Table]: Invalid product ID format: '{product_id}'")
            return None

        print(f"  DEBUG [Glen Rose Table]: Valid product ID: '{product_id}'")

        # Description is in the SECOND column (index 1)
        # Everything else (category, status) is ignored
        if len(row_clean) < 2 or not row_clean[1]:
            print(f"  DEBUG [Glen Rose Table]: No description in second column")
            return None

        description = row_clean[1].strip()
        print(f"  DEBUG [Glen Rose Table]: Description: '{description}'")

        # Add extra text from product ID if any
        if extra_text:
            description = extra_text + ' ' + description

        # Clean up multiple spaces
        description = re.sub(r'\s+', ' ', description).strip()

        # Validate description
        if not self.is_valid_description(description):
            print(f"  DEBUG [Glen Rose Table]: Invalid description: '{description}'")
            return None

        print(f"  DEBUG [Glen Rose Table]: ✅ SUCCESS - ID: {product_id}, Desc: {description}, Cost: {cost_cleaned}")

        return {
            'product_id': product_id,
            'description': description,
            'cost': cost_cleaned
        }
    
    def parse_text_line(self, line):
        """
        Parse a text line from Glen Rose PDF (OCR-based).
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not line or not line.strip():
            return None

        # Skip headers
        if 'product id' in line.lower() or 'item' in line.lower() and 'description' in line.lower():
            return None

        # Glen Rose: Prices usually don't have $ sign, just look for price pattern
        # Must have a price-like pattern: digits with decimal (e.g., "2.25", "12.10")
        if not re.search(r'\d{1,4}\.\d{2}', line):
            return None

        print(f"  DEBUG [Glen Rose]: Parsing line: '{line[:100]}...'") if len(line) > 100 else print(f"  DEBUG [Glen Rose]: Parsing line: '{line}'")

        # Glen Rose specific pattern (from working code):
        # Pattern: 8-11 digits, hyphen, 2-3 digits, description, price/status
        # Handles: numbers with decimals, /LB, /CS, /EA, OUT, QUOTE
        pattern = r'(\b\d{8,11}-\d{2,3}\b)\s+(.*?)\s+([\d\.,]+\s*(?:/LB|/CS|/EA)?|OUT|QUOTE)\s*$'
        match = re.search(pattern, line, re.MULTILINE | re.IGNORECASE)

        if not match:
            # Fallback: Try shorter hyphenated format
            pattern = r'(\b\d{6,10}-\d{1,3}\b)\s+(.*?)\s+([\d\.,]+\s*(?:/LB|/CS|/EA)?|OUT|QUOTE)\s*$'
            match = re.search(pattern, line, re.MULTILINE | re.IGNORECASE)
        
        if match:
            product_id = match.group(1).strip()
            description = match.group(2).strip()
            cost_str = match.group(3).strip()
            
            print(f"  DEBUG [Glen Rose]: Matched! ID={product_id}, Desc={description[:30]}..., Cost={cost_str}")
            
            # Validate product ID
            if not self.validate_product_id(product_id):
                print(f"  DEBUG [Glen Rose]: Invalid product ID: {product_id}")
                return None
            
            # Clean cost
            cost_cleaned = self.clean_cost(cost_str)
            if not cost_cleaned:
                print(f"  DEBUG [Glen Rose]: Invalid cost: {cost_str}")
                return None
            
            # Clean up description
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Validate description
            if not self.is_valid_description(description):
                print(f"  DEBUG [Glen Rose]: Invalid description: {description}")
                return None
            
            return {
                'product_id': product_id,
                'description': description,
                'cost': cost_cleaned
            }
        
        # Fallback: Try splitting by multiple spaces
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
                
                if not product_id or not self.validate_product_id(product_id):
                    return None
                
                cost_cleaned = self.clean_cost(parts[cost_idx])
                if not cost_cleaned:
                    return None
                
                # Description is everything between product_id and cost
                if cost_idx > 1:
                    description = ' '.join(parts[1:cost_idx]).strip()
                else:
                    description = parts[1].strip() if len(parts) > 1 else ''
                
                # Add any extra text from product ID to description
                if extra_text:
                    description = extra_text + ' ' + description
                
                # Clean up multiple spaces
                description = re.sub(r'\s+', ' ', description).strip()
                
                # Validate before returning
                if self.is_valid_description(description):
                    return {
                        'product_id': product_id,
                        'description': description,
                        'cost': cost_cleaned
                    }
        
        print(f"  DEBUG [Glen Rose]: No match found for line")
        return None

