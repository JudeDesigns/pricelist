"""
Generic parser for unknown vendors.
Uses flexible parsing rules and relies on Gemini AI for extraction.
"""

import re
from .base_parser import BaseParser

class GenericParser(BaseParser):
    """Parser for unknown/generic vendors"""

    def __init__(self):
        super().__init__()
        self.vendor_name = "Unknown Vendor"
        self.product_id_format = "flexible"
        self.max_product_id_length = 20
        self.requires_dollar_sign = False
    
    def parse_text_line(self, line):
        """
        Generic parsing - very flexible.
        This is mainly a placeholder as Gemini AI will do the actual parsing.
        """
        # Skip empty lines
        if not line.strip():
            return None
        
        # For unknown vendors, we rely on Gemini AI
        # This method is just a fallback
        return None
    
    def validate_product_id(self, product_id):
        """Very flexible validation for unknown vendors"""
        if not product_id:
            return False
        
        # Accept any alphanumeric product ID up to 20 characters
        product_id = product_id.strip()
        if len(product_id) > 20:
            return False
        
        # Must contain at least one alphanumeric character
        return any(c.isalnum() for c in product_id)

