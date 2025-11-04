"""
Los Angeles Poultry Co Parser
Handles PDF parsing for Los Angeles Poultry Co price lists
Uses Gemini AI for extraction
"""

import re
from typing import List, Dict, Optional
from .base_parser import BaseParser


class LAPoultryParser(BaseParser):
    """Parser for Los Angeles Poultry Co price lists"""
    
    def __init__(self):
        super().__init__()
        self.vendor_name = "Los Angeles Poultry Co"
        self.vendor_code = "la_poultry"
        self.product_id_format = "flexible"
        self.max_product_id_length = 15
        self.requires_dollar_sign = False
    
    def validate_product_id(self, product_id):
        """
        Validate LA Poultry product ID format.
        Accepts alphanumeric IDs with optional hyphens (3-15 characters).
        Also accepts N/A for products without IDs.
        
        Args:
            product_id: Product ID string to validate
            
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
    
    def parse_table(self, table_data: List[List[str]]) -> List[Dict[str, str]]:
        """
        Parse table data from LA Poultry PDF.
        
        Args:
            table_data: List of rows, each row is a list of cell values
            
        Returns:
            List of dictionaries with keys: product_id, description, cost
        """
        extracted_items = []
        
        for row in table_data:
            if not row or len(row) < 2:
                continue
            
            # Skip header rows
            if any(header in str(row).lower() for header in ['product', 'item', 'description', 'price', 'cost']):
                continue
            
            # Try to extract product ID, description, and price
            product_id = None
            description = None
            price = None
            
            # Look for product ID (usually first column)
            for cell in row:
                if cell and self.validate_product_id(str(cell).strip()):
                    product_id = str(cell).strip()
                    break
            
            # If no valid ID found, use N/A
            if not product_id:
                product_id = 'N/A'
            
            # Look for description (usually longest text field)
            for cell in row:
                cell_str = str(cell).strip()
                if cell_str and len(cell_str) > 5 and not self.is_price(cell_str):
                    description = cell_str
                    break
            
            # Look for price (usually last column with $ or decimal)
            for cell in reversed(row):
                cell_str = str(cell).strip()
                if self.is_price(cell_str):
                    price = cell_str
                    break
            
            # Add item if we have at least description and price
            if description and price:
                extracted_items.append({
                    'product_id': product_id,
                    'description': description,
                    'cost': price
                })
        
        return extracted_items
    
    def parse_text_lines(self, text_lines: List[str]) -> List[Dict[str, str]]:
        """
        Parse text lines from LA Poultry PDF.
        
        Args:
            text_lines: List of text lines from PDF
            
        Returns:
            List of dictionaries with keys: product_id, description, cost
        """
        extracted_items = []
        
        for line in text_lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Skip header lines
            if any(header in line.lower() for header in ['product', 'item', 'description', 'price', 'cost']):
                continue
            
            # Try to extract product ID, description, and price
            # Pattern: ID Description Price
            parts = line.split()
            if len(parts) < 2:
                continue
            
            # Check if first part is a valid product ID
            product_id = 'N/A'
            start_idx = 0
            if self.validate_product_id(parts[0]):
                product_id = parts[0]
                start_idx = 1
            
            # Last part should be price
            if not self.is_price(parts[-1]):
                continue
            
            price = parts[-1]
            
            # Everything in between is description
            description = ' '.join(parts[start_idx:-1])
            
            if description:
                extracted_items.append({
                    'product_id': product_id,
                    'description': description,
                    'cost': price
                })
        
        return extracted_items
    
    def is_price(self, text: str) -> bool:
        """Check if text looks like a price"""
        if not text:
            return False
        # Look for patterns like $4.99, 4.99, $29.00/LB, etc.
        return bool(re.search(r'\$?\d{1,5}\.\d{2}', text))

