"""
Kruse & Sons Vendor Parser
Handles Kruse & Sons specific product ID and pricing formats
"""

import re
from vendors.base_parser import BaseParser


class KruseSonsParser(BaseParser):
    """Parser for Kruse & Sons price lists"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "Kruse & Sons"
        self.vendor_code = "kruse_sons"
        self.product_id_format = "numeric_code"
        self.max_product_id_length = 10
        self.requires_dollar_sign = False  # Prices are just numbers
    
    def extract_product_id(self, text):
        """
        Extract product ID from text.
        Kruse & Sons format: Simple numeric codes (e.g., 01, 03, 05, 07)
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        text = text.strip()
        
        # Match 1-3 digit codes at the start
        match = re.match(r'^(\d{1,3})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining
        
        return None, text
    
    def validate_product_id(self, product_id):
        """
        Validate Kruse & Sons product ID.
        Format: 1-3 digit numeric code or N/A

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

        # Must be 1-3 digits
        if re.match(r'^\d{1,3}$', product_id):
            return True

        return False
    
    def clean_cost(self, cost_str):
        """
        Clean and format cost string for Kruse & Sons.
        Kruse & Sons format: Price per lb (e.g., 1.85, 2.44, 3.00)
        
        Args:
            cost_str: Raw cost string
        
        Returns:
            Formatted cost string or None if invalid
        """
        if not cost_str:
            return None
        
        cost_str = cost_str.strip().upper()
        
        # Extract price (just a decimal number)
        # Pattern: X.XX or XX.XX
        match = re.search(r'(\d{1,5}\.\d{2})', cost_str)
        if not match:
            # Try without decimal
            match = re.search(r'(\d{1,5})', cost_str)
            if match:
                cost_value = float(match.group(1))
            else:
                return None
        else:
            cost_value = float(match.group(1))
        
        # Validate price range
        if not (0.01 <= cost_value <= 9999.99):
            return None
        
        # Format as $X.XX/LB (Kruse & Sons prices are per pound)
        return f"${cost_value:.2f}/LB"
    
    def is_valid_description(self, description):
        """
        Validate a description for Kruse & Sons.
        
        Args:
            description: Description to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not description or not isinstance(description, str):
            return False
        
        # Ignore category headers (start with **)
        if description.strip().startswith('**'):
            return False
        
        # Must have at least 2 letters
        alpha_count = sum(1 for c in description if c.isalpha())
        if alpha_count < 2:
            return False
        
        return True
    
    def parse_table_row(self, row):
        """
        Parse a table row from Kruse & Sons PDF.
        
        Kruse & Sons table structure:
        [Code] [Item] [Packed] [Case Wt.] [Price per lb.]
        
        Args:
            row: Table row (list of cell values)
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not row or len(row) < 3:
            return None
        
        # Clean the row
        row_clean = [str(cell).strip() if cell else '' for cell in row]
        
        print(f"  DEBUG [Kruse & Sons Table]: Row has {len(row_clean)} columns: {row_clean}")
        
        # Code is in first column (index 0)
        raw_id = row_clean[0]

        # Item is in second column (index 1)
        description = row_clean[1] if len(row_clean) > 1 else ''

        # CRITICAL: Price is ALWAYS in the LAST column (rightmost)
        raw_price = row_clean[-1]

        # Skip if description starts with ** (category header)
        if description.startswith('**'):
            print(f"  DEBUG [Kruse & Sons Table]: Skipping category header: {description}")
            return None

        # Skip if no price in last column
        if not raw_price or not re.search(r'\d', raw_price):
            print(f"  DEBUG [Kruse & Sons Table]: No price found in last column: '{raw_price}'")
            return None

        print(f"  DEBUG [Kruse & Sons Table]: Raw ID: '{raw_id}', Desc: '{description}', Price (last col): '{raw_price}'")

        # Extract and validate product ID (or use N/A if no ID)
        if not raw_id or not raw_id.strip():
            product_id = 'N/A'
            print(f"  DEBUG [Kruse & Sons Table]: No product ID, using N/A")
        else:
            product_id, extra_text = self.extract_product_id(raw_id)
            if not product_id or not self.validate_product_id(product_id):
                # If no valid ID found, use N/A
                product_id = 'N/A'
                print(f"  DEBUG [Kruse & Sons Table]: Invalid product ID '{raw_id}', using N/A")
        
        print(f"  DEBUG [Kruse & Sons Table]: Valid product ID: '{product_id}'")
        
        # Validate description
        if not description or not self.is_valid_description(description):
            print(f"  DEBUG [Kruse & Sons Table]: Invalid description: '{description}'")
            return None
        
        # Clean cost
        cost_cleaned = self.clean_cost(raw_price)
        if not cost_cleaned:
            print(f"  DEBUG [Kruse & Sons Table]: Invalid cost: '{raw_price}'")
            return None
        
        print(f"  DEBUG [Kruse & Sons Table]: ✅ SUCCESS - ID: {product_id}, Desc: {description}, Cost: {cost_cleaned}")
        
        return {
            'product_id': product_id,
            'description': description,
            'cost': cost_cleaned
        }
    
    def parse_text_line(self, line):
        """
        Parse a text line from Kruse & Sons PDF (OCR-based).
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not line or not line.strip():
            return None
        
        # Skip lines without numbers (no price)
        if not re.search(r'\d{1,2}\.\d{2}', line):
            return None
        
        # Skip category headers (lines with **)
        if '**' in line:
            return None
        
        print(f"  DEBUG [Kruse & Sons]: Parsing line: '{line}'")
        
        # Kruse & Sons pattern: Code  Item  ...  Price
        # Pattern: 1-3 digits, description, price at end
        pattern = r'^(\d{1,3})\s+(.+?)\s+(\d{1,2}\.\d{2})\s*$'
        match = re.search(pattern, line)
        
        if not match:
            # Try alternative pattern with more flexible spacing
            pattern = r'(\d{1,3})\s+(.+?)\s+(\d{1,2}\.\d{2})'
            match = re.search(pattern, line)
        
        if match:
            product_id = match.group(1).strip()
            description = match.group(2).strip()
            cost_str = match.group(3).strip()
            
            print(f"  DEBUG [Kruse & Sons]: Matched! ID={product_id}, Desc={description[:30]}..., Cost={cost_str}")
            
            # Validate product ID
            if not self.validate_product_id(product_id):
                print(f"  DEBUG [Kruse & Sons]: Invalid product ID: {product_id}")
                return None
            
            # Validate description
            if not self.is_valid_description(description):
                print(f"  DEBUG [Kruse & Sons]: Invalid description: {description}")
                return None
            
            # Clean cost
            cost_cleaned = self.clean_cost(cost_str)
            if not cost_cleaned:
                print(f"  DEBUG [Kruse & Sons]: Invalid cost: {cost_str}")
                return None
            
            # Clean up description
            description = re.sub(r'\s+', ' ', description).strip()
            
            return {
                'product_id': product_id,
                'description': description,
                'cost': cost_cleaned
            }
        
        return None

