"""
Quirch Foods Vendor Parser
Handles Quirch Foods specific product ID and pricing formats
"""

import re
from vendors.base_parser import BaseParser


class QuirchFoodsParser(BaseParser):
    """Parser for Quirch Foods price lists"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "Quirch Foods"
        self.vendor_code = "quirch_foods"
        self.product_id_format = "numeric"
        self.max_product_id_length = 10
        self.requires_dollar_sign = True  # Prices have $ sign
    
    def extract_product_id(self, text):
        """
        Extract product ID from text.
        Quirch Foods format: 6 or 10 digit numbers (e.g., 111702307, 189010)
        
        Args:
            text: Text to extract product ID from
        
        Returns:
            tuple: (product_id, remaining_text)
        """
        text = text.strip()
        
        # Match 6 or 10 digit numbers
        match = re.match(r'^(\d{10}|\d{6})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining
        
        # Fallback: Match any sequence of 6-10 digits
        match = re.match(r'^(\d{6,10})\b', text)
        if match:
            product_id = match.group(1)
            remaining = text[len(product_id):].strip()
            return product_id, remaining
        
        return None, text
    
    def validate_product_id(self, product_id):
        """
        Validate Quirch Foods product ID.
        Format: 6 or 10 digit numbers or N/A

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

        # Must be exactly 6 or 10 digits
        if re.match(r'^\d{10}$', product_id):
            return True

        if re.match(r'^\d{6}$', product_id):
            return True

        # Allow 7-9 digits as fallback
        if re.match(r'^\d{7,9}$', product_id):
            return True

        return False
    
    def clean_cost(self, cost_str):
        """
        Clean and format cost string for Quirch Foods.
        Quirch Foods format: Price with $ sign (e.g., $3.49, $1.25, $11.52)
        
        Args:
            cost_str: Raw cost string
        
        Returns:
            Formatted cost string or None if invalid
        """
        if not cost_str:
            return None
        
        cost_str = cost_str.strip()
        
        # Extract price with $ sign
        # Pattern: $X.XX or $XX.XX
        match = re.search(r'\$\s*(\d{1,5}\.\d{2})', cost_str)
        if not match:
            # Try without $ sign
            match = re.search(r'(\d{1,5}\.\d{2})', cost_str)
            if not match:
                return None
        
        cost_value = float(match.group(1))
        
        # Validate price range
        if not (0.01 <= cost_value <= 9999.99):
            return None
        
        # Format as $X.XX
        return f"${cost_value:.2f}"
    
    def is_valid_description(self, description):
        """
        Validate a description for Quirch Foods.

        Quirch Foods descriptions always start with specific prefixes:
        - Frzn (Frozen)
        - Fsh (Fresh)
        - Chkn (Chicken)
        - Misc (Miscellaneous)
        - Prep (Prepared)

        Args:
            description: Description to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not description or not isinstance(description, str):
            return False

        # Must have at least 3 letters
        alpha_count = sum(1 for c in description if c.isalpha())
        if alpha_count < 3:
            return False

        # Check if description starts with valid Quirch Foods prefix (case-insensitive)
        description_lower = description.lower().strip()
        valid_prefixes = ['frzn', 'fsh', 'chkn', 'misc', 'prep']

        if not any(description_lower.startswith(prefix) for prefix in valid_prefixes):
            print(f"  DEBUG [Quirch Foods]: Description doesn't start with valid prefix (Frzn/Fsh/Chkn/Misc/Prep): '{description}'")
            return False

        return True
    
    def parse_table_row(self, row):
        """
        Parse a table row from Quirch Foods PDF.
        
        Quirch Foods table structure:
        [Master Description] [Item Number] [Item Brand] [Item Description] [Grade] [Total]
        
        Args:
            row: Table row (list of cell values)
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not row or len(row) < 3:
            return None
        
        # Clean the row
        row_clean = [str(cell).strip() if cell else '' for cell in row]
        
        print(f"  DEBUG [Quirch Foods Table]: Row has {len(row_clean)} columns: {row_clean}")
        
        # Find Item Number (6 or 10 digits)
        product_id = None
        product_id_idx = -1
        for idx, cell in enumerate(row_clean):
            if re.match(r'^\d{6,10}$', cell):
                product_id = cell
                product_id_idx = idx
                break
        
        if not product_id:
            print(f"  DEBUG [Quirch Foods Table]: No Item Number found")
            return None
        
        print(f"  DEBUG [Quirch Foods Table]: Found Item Number: '{product_id}' at index {product_id_idx}")
        
        # Find Total (price with $ sign, usually last column)
        cost = None
        for cell in reversed(row_clean):
            if '$' in cell and re.search(r'\d+\.\d{2}', cell):
                cost = cell
                break
        
        if not cost:
            print(f"  DEBUG [Quirch Foods Table]: No Total (price) found")
            return None
        
        print(f"  DEBUG [Quirch Foods Table]: Found Total: '{cost}'")
        
        # Find Item Description (must contain Frzn, Fsh, Chkn, Misc, or Prep)
        # The description might be in a cell with other text before it
        # We need to extract ONLY the part starting with the valid prefix
        description = None
        valid_prefixes = ['frzn', 'fsh', 'chkn', 'misc', 'prep']

        for idx in range(product_id_idx + 1, len(row_clean)):
            cell = row_clean[idx]
            if cell and not cell.startswith('$') and len(cell) > 3:
                cell_lower = cell.lower().strip()

                # Check if this cell contains a valid prefix
                for prefix in valid_prefixes:
                    # Find where the prefix starts in the cell
                    prefix_pos = cell_lower.find(prefix)
                    if prefix_pos != -1:
                        # Extract from the prefix onwards, ignoring everything before
                        description = cell[prefix_pos:].strip()
                        print(f"  DEBUG [Quirch Foods Table]: Found description starting at position {prefix_pos}: '{description}'")
                        break

                if description:
                    break
        
        if not description:
            print(f"  DEBUG [Quirch Foods Table]: No Item Description found")
            return None
        
        print(f"  DEBUG [Quirch Foods Table]: Found Item Description: '{description}'")
        
        # Validate product ID
        if not self.validate_product_id(product_id):
            print(f"  DEBUG [Quirch Foods Table]: Invalid product ID: '{product_id}'")
            return None
        
        # Validate description
        if not self.is_valid_description(description):
            print(f"  DEBUG [Quirch Foods Table]: Invalid description: '{description}'")
            return None
        
        # Clean cost
        cost_cleaned = self.clean_cost(cost)
        if not cost_cleaned:
            print(f"  DEBUG [Quirch Foods Table]: Invalid cost: '{cost}'")
            return None
        
        print(f"  DEBUG [Quirch Foods Table]: ✅ SUCCESS - ID: {product_id}, Desc: {description}, Cost: {cost_cleaned}")
        
        return {
            'product_id': product_id,
            'description': description,
            'cost': cost_cleaned
        }
    
    def parse_text_line(self, line):
        """
        Parse a text line from Quirch Foods PDF (OCR-based).
        
        Args:
            line: Text line to parse
        
        Returns:
            dict or None: {'product_id': ..., 'description': ..., 'cost': ...} or None
        """
        if not line or not line.strip():
            return None
        
        # Skip lines without prices
        if not re.search(r'\$\d+\.\d{2}', line):
            return None
        
        print(f"  DEBUG [Quirch Foods]: Parsing line: '{line}'")
        
        # Quirch Foods pattern: Item Number (6-10 digits), description, price
        # Pattern: 6-10 digits, description, $X.XX
        pattern = r'(\d{6,10})\s+(.+?)\s+(\$\d{1,5}\.\d{2})\s*$'
        match = re.search(pattern, line)
        
        if not match:
            # Try alternative pattern with more flexible spacing
            pattern = r'(\d{6,10})\s+(.+?)\s+\$\s*(\d{1,5}\.\d{2})'
            match = re.search(pattern, line)
        
        if match:
            product_id = match.group(1).strip()
            description_raw = match.group(2).strip()
            cost_str = match.group(3).strip() if len(match.groups()) == 3 else '$' + match.group(3).strip()

            print(f"  DEBUG [Quirch Foods]: Matched! ID={product_id}, Raw Desc={description_raw[:50]}..., Cost={cost_str}")

            # Extract description starting from valid prefix
            # Ignore everything before Frzn, Fsh, Chkn, Misc, or Prep
            description = None
            valid_prefixes = ['frzn', 'fsh', 'chkn', 'misc', 'prep']
            description_lower = description_raw.lower()

            for prefix in valid_prefixes:
                prefix_pos = description_lower.find(prefix)
                if prefix_pos != -1:
                    # Extract from the prefix onwards, ignoring everything before
                    description = description_raw[prefix_pos:].strip()
                    print(f"  DEBUG [Quirch Foods]: Extracted description from position {prefix_pos}: '{description}'")
                    break

            if not description:
                print(f"  DEBUG [Quirch Foods]: No valid prefix found in description: '{description_raw}'")
                return None

            # Validate product ID
            if not self.validate_product_id(product_id):
                print(f"  DEBUG [Quirch Foods]: Invalid product ID: {product_id}")
                return None

            # Validate description
            if not self.is_valid_description(description):
                print(f"  DEBUG [Quirch Foods]: Invalid description: {description}")
                return None

            # Clean cost
            cost_cleaned = self.clean_cost(cost_str)
            if not cost_cleaned:
                print(f"  DEBUG [Quirch Foods]: Invalid cost: {cost_str}")
                return None

            # Clean up description
            description = re.sub(r'\s+', ' ', description).strip()

            return {
                'product_id': product_id,
                'description': description,
                'cost': cost_cleaned
            }

        return None

