"""
Gemini AI PDF Parser for Glen Rose Meat Company
Uses Google's Gemini AI to extract product information from PDFs
"""

import os
import re
import google.generativeai as genai
from typing import List, Dict, Optional
import io

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def parse_pdf_with_gemini(filepath: str, vendor: str = 'glen_rose') -> List[Dict[str, str]]:
    """
    Parse a PDF using Gemini AI to extract product information.
    
    Args:
        filepath: Path to the PDF file
        vendor: Vendor code (e.g., 'glen_rose')
    
    Returns:
        List of dictionaries with keys: product_id, description, cost
    """
    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY environment variable not set")
    
    print(f"\n🤖 Using Gemini AI to parse {vendor} PDF...")

    # Read PDF file as bytes
    print(f"   Reading PDF file...")
    with open(filepath, 'rb') as f:
        pdf_bytes = f.read()

    # Create the prompt based on vendor
    prompt = get_vendor_prompt(vendor)

    # Use Gemini to extract data
    print(f"   Sending to Gemini 2.5 Pro for analysis...")
    # Using gemini-2.5-pro for BEST ACCURACY (slower but more reliable)
    # Alternative: 'gemini-2.5-flash' for faster processing (less accurate)
    # Alternative: 'gemini-2.0-flash-exp' for experimental fastest processing
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Send PDF as inline data (more reliable than file upload)
    import mimetypes
    mime_type = mimetypes.guess_type(filepath)[0] or 'application/pdf'

    response = model.generate_content([
        {
            'mime_type': mime_type,
            'data': pdf_bytes
        },
        prompt
    ])
    
    print(f"   ✅ Received response from Gemini 2.5 Pro")

    # Debug: Print first 500 chars of response
    print(f"\n   🔍 DEBUG - First 500 chars of Gemini response:")
    print(f"   {response.text[:500]}")
    print(f"   {'='*60}\n")

    # Parse the CSV response
    extracted_data = parse_gemini_csv_response(response.text, vendor)

    print(f"   ✅ Extracted {len(extracted_data)} products")

    # No need to clean up - we used inline data, not file upload

    return extracted_data


def get_vendor_prompt(vendor: str) -> str:
    """
    Get the Gemini prompt for a specific vendor.

    Args:
        vendor: Vendor code

    Returns:
        Prompt string for Gemini
    """
    if vendor == 'glen_rose':
        return """
Please extract ALL product information from this PDF price list.

For each product, extract:
1. Product ID (format: XXXXXXXXX-XX, e.g., 711000005-01)
2. Product Description (full description including any notes in parentheses)
3. Cost (price with unit if specified, e.g., $4.99/LB, $29.00/CS, or just $6.20)

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Include products marked as "OUT", "QUOTE", "FROZEN", etc.
- Preserve the exact Product ID format with hyphens
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full description including parentheses and special characters
- Include the unit in the cost if present (/LB, /CS, /EA)
- If a product shows "OUT", use "OUT" as the cost
- If a product shows "QUOTE", use "QUOTE" as the cost
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description (e.g., "BEEF CHUCK - 10 LB", "BEEF CHUCK - 20 LB")

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

If a product has multiple prices:
711000005-01,CHUCK ROLL DICED (REGULAR TRIM) - Small,$5.99/LB
711000005-01,CHUCK ROLL DICED (REGULAR TRIM) - Large,$6.20/LB

If a product has no ID:
N/A,BEEF LIVER SLICED,$3.49/LB

Example rows:
711006119,FROZEN BEEF CHUCK ROLL DICED ASADA MARINATED,$4.99/LB
732450512,FROZEN CHICKEN THIGH DICED 3/4 AL PASTOR,$1.99/LB
58120000,FROZEN CHILE RELLENO,$29.00/CS
711000005-01,CHUCK ROLL DICED (REGULAR TRIM),$6.20
713004159-01,T-BONE STEAKS,QUOTE

Do NOT include any explanatory text, ONLY the CSV data with header.
"""
    elif vendor == 'kruse_sons':
        return """
Please extract ALL product information from this PDF price list.

This is a Kruse & Sons price list with the following table structure:
- Code column: Product ID (1-3 digit numbers like 01, 03, 05, 07, etc.)
- Item column: Product Description
- Price per lb. column: Price (decimal numbers like 1.85, 2.44, 3.00)

CRITICAL INSTRUCTIONS FOR KRUSE & SONS:
- The PRICE is ALWAYS the LAST number on each row
- Look for the rightmost decimal number (e.g., 1.85, 2.44, 3.00) - this is the price
- Extract EVERY product from EVERY page
- ONLY extract rows that have a numeric Code (1-3 digits)
- If a product does NOT have a Code, use "N/A" in the Product ID column
- IGNORE rows where the Item starts with "**" (these are category headers like **HAMS**, **BACON**)
- ONLY include rows that have a price (the last number on the row)
- The Code is the Product ID (e.g., 01, 03, 05, 07, 11, 12, etc.)
- Keep the full Item description
- All prices are per pound (/LB)
- If a product has MULTIPLE PRICES for different variations, create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
01,SHORT-SHANK HAMS,1.85
03,BONELESS PIT HAM (W/A),2.44
05,BONELESS BLACK FOREST HAM (W/A),2.54
07,B-GRADE BACON,3.00
30,SMOKED PASTRAMI WATER ADDED,5.74

If a product has no Code:
N/A,BEEF LIVER SLICED,3.49

REMEMBER: The price is ALWAYS the LAST number on each row!

Do NOT include:
- Category headers (rows with ** in Item column)
- Rows without a price (no last number)
- Any explanatory text

Return ONLY the CSV data with header.
"""
    elif vendor == 'quirch_foods':
        return """
Please extract ALL product information from this PDF price list.

This is a Quirch Foods price list with the following table structure:
Column 1: Master Description (category header - IGNORE THIS)
Column 2: Item Number (Product ID - 6 or 10 digits)
Column 3: Item Brand (brand name - IGNORE THIS)
Column 4: Item Description (Product Description - ALWAYS starts with Frzn, Fsh, Chkn, Misc, or Prep)
Column 5: Grade (quality grade - IGNORE THIS)
Column 6: Total (Price with $ sign)

CRITICAL: Extract from Column 4 (Item Description), NOT Column 3 (Item Brand)!

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- ONLY extract rows that have an Item Number in Column 2 (6 or 10 digits)
- If a product does NOT have an Item Number, use "N/A" in the Product ID column
- ONLY extract the Item Description from Column 4 (starts with: Frzn, Fsh, Chkn, Misc, or Prep)
- DO NOT extract Item Brand from Column 3 (brand names like "Los Fortres", "Central Valley", "Swift", "Ibp")
- IGNORE Master Description in Column 1 (like "Beef Offal", "Beef Backrib", "Beef Chuck")
- ONLY include rows that have a price in the Total column (Column 6)
- CRITICAL: If there are ANY words before Frzn/Fsh/Chkn/Misc/Prep, IGNORE them and start from the prefix
- Extract ONLY the text starting from Frzn/Fsh/Chkn/Misc/Prep onwards
- Include the $ sign in the price
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

TABLE EXAMPLE:
| Master Description | Item Number | Item Brand      | Item Description              | Grade    | Total  |
|--------------------|-------------|-----------------|-------------------------------|----------|--------|
| Beef Offal         | 111702307   | Los Fortres     | Frzn Rose Meat Mx             | Imported | $3.49  |
|                    | 111722903   | Central Valley  | Prep Beef Feet Scalded        |          | $3.74  |
|                    | 111131869   | Swift           | Fsh Beef Liver Vac            |          | $1.25  |

EXTRACT THIS:
111702307,Frzn Rose Meat Mx,$3.49
111722903,Prep Beef Feet Scalded,$3.74
111131869,Fsh Beef Liver Vac,$1.25

EXAMPLE: If Item Description column contains "Some Brand Name Frzn Beef Product"
EXTRACT: "Frzn Beef Product" (ignore "Some Brand Name" before "Frzn")

EXAMPLE: If Item Description column contains "Swift Ibp Fsh Liver Sliced"
EXTRACT: "Fsh Liver Sliced" (ignore "Swift Ibp" before "Fsh")

DO NOT EXTRACT:
- "Los Fortres" (this is Item Brand, not Item Description)
- "Central Valley" (this is Item Brand, not Item Description)
- "Swift" (this is Item Brand, not Item Description)
- "Beef Offal" (this is Master Description, not a product)

VALID Item Description examples (Column 4 - note the prefix):
- Frzn Rose Meat Mx
- Frzn Beef Feet
- Frzn Beef Small Intestine
- Fsh Beef Liver Vac
- Fsh Chuck Clod Xt Ang Ch
- Prep Beef Feet Scalded
- Chkn Breast Boneless
- Misc Product Name

INVALID examples (DO NOT extract these):
- Los Fortres (Item Brand - Column 3)
- Central Valley (Item Brand - Column 3)
- Swift (Item Brand - Column 3)
- Ibp (Item Brand - Column 3)
- Beef Offal (Master Description - Column 1)
- Beef Chuck (Master Description - Column 1)

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
111702307,Frzn Rose Meat Mx,$3.49
111722903,Prep Beef Feet Scalded,$3.74
111131869,Fsh Beef Liver Vac,$1.25
189010,Frzn Beef Feet,$3.95
190372,Frzn Beef Small Intestine,$1.82
111112834,Frzn Beef Bones,$1.43
111113031,Frzn Beef Tongue #1,$7.18

Do NOT include:
- Item Brand names (Column 3)
- Master Description rows (Column 1)
- Rows without an Item Number
- Rows without a price in Total column
- Any explanatory text

Return ONLY the CSV data with header.
"""

    elif vendor == 'purcell':
        return """
Please extract ALL product information from this PDF price list.

This is a Purcell price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
ABC123,BEEF CHUCK ROLL,$5.99
N/A,BEEF LIVER SLICED,$3.49
P-456,CHICKEN BREAST,$2.99

Return ONLY the CSV data with header.
"""

    elif vendor == 'laras_meat':
        return """
Please extract ALL product information from this PDF price list.

This is a Laras Meat price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
LM-001,BEEF CHUCK ROLL,$5.99
N/A,BEEF LIVER SLICED,$3.49
123,CHICKEN BREAST,$2.99

Return ONLY the CSV data with header.
"""

    elif vendor == 'maui_prices':
        return """
Please extract ALL product information from this PDF price list.

This is a Maui Prices price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
MP-001,BEEF CHUCK ROLL,$5.99
N/A,BEEF LIVER SLICED,$3.49
456,CHICKEN BREAST,$2.99

Return ONLY the CSV data with header.
"""

    elif vendor == 'cd_international':
        return """
Please extract ALL product information from this C&D International Fishery PDF price list.

DOCUMENT STRUCTURE ANALYSIS:
This document has a HIERARCHICAL structure with:
1. Main Headers (e.g., "Fish Fillet", "Whole fish", "SQUID", "Others")
2. Sub-headers (product categories with full descriptions, e.g., "Tilapia Fillet, shallow skin, Fortune's Wind")
3. Size variations under each sub-header (e.g., "2/3BULK", "3/5Bulk", "3/5ivp") with their prices

CRITICAL INSTRUCTIONS:
1. First, identify the document structure - find all main headers and sub-headers
2. For each sub-header (product category), find ALL size variations listed below it
3. For EACH size variation, create a SEPARATE row with:
   - Product ID: Use "N/A" (most products don't have IDs)
   - Product Description: COMBINE the sub-header + size variation
   - Cost: The price for that specific size

EXAMPLE from the document:

Sub-header: "Tilapia Fillet, shallow skin, Fortune's Wind"
Size variations below it:
- 2/5oz Retail 10x2lbs IQF → $1.85
- 2/3BULK → $1.85
- 3/5Bulk → $1.95
- 3/5ivp → $2.00

Should extract as:
N/A,Tilapia Fillet shallow skin Fortune's Wind - 2/5oz Retail 10x2lbs IQF,$1.85
N/A,Tilapia Fillet shallow skin Fortune's Wind - 2/3BULK,$1.85
N/A,Tilapia Fillet shallow skin Fortune's Wind - 3/5Bulk,$1.95
N/A,Tilapia Fillet shallow skin Fortune's Wind - 3/5ivp,$2.00

Sub-header: "Whole G/S Tilapia 1x40lbs, IWP, fortune's wind brand"
Size variations below it:
- 350/550 → $1.20
- 550/750 → $1.30
- 750up → $1.35

Should extract as:
N/A,Whole G/S Tilapia 1x40lbs IWP fortune's wind brand - 350/550,$1.20
N/A,Whole G/S Tilapia 1x40lbs IWP fortune's wind brand - 550/750,$1.30
N/A,Whole G/S Tilapia 1x40lbs IWP fortune's wind brand - 750up,$1.35

IMPORTANT:
- Extract EVERY size variation as a separate row
- ALWAYS combine sub-header + size variation in the description
- Use "N/A" for Product ID (unless a specific ID is shown)
- Keep all details from both the sub-header and size variation
- Extract ALL products from ALL sections (Fish Fillet, Whole fish, SQUID, Others)

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Return ONLY the CSV data with header.
"""

    elif vendor == 'la_poultry':
        return """
Please extract ALL product information from this PDF price list.

This is a Los Angeles Poultry (LA Poultry) price list.

CRITICAL INSTRUCTIONS FOR LA POULTRY:
- This vendor does NOT have Product IDs
- Use "N/A" for ALL Product IDs (first column)
- Extract EVERY product from EVERY page
- Keep the COMPLETE product description in the second column
- Extract the price/cost in the third column

CSV FORMAT RULES - VERY IMPORTANT:
- Use EXACTLY 3 columns: Product ID, Product Description, Cost
- First column is ALWAYS "N/A" (no quotes needed)
- Second column contains the FULL product description - MUST be wrapped in double quotes "..." if it contains commas
- Third column contains ONLY the price (e.g., $2.99, 1.85, $3.49/LB)
- Do NOT split the description across multiple columns
- Do NOT put part of the description in the Product ID column
- ALWAYS wrap descriptions in quotes to handle commas properly

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows (note the quotes around descriptions):
N/A,"CHICKEN BREAST BONELESS SKINLESS 40# CS",$2.99
N/A,"CHICKEN THIGHS FRESH",$1.85
N/A,"CHICKEN WINGS JUMBO 40# CS",$3.49
N/A,"TURKEY BREAST WHOLE",$4.25
N/A,"Tilapia Fillet, shallow skin, Fortune's Wind 2/3BULK",$1.80
N/A,"Swai fillet, Belly off, Vietnam, 100%, Lucky spot Brand, 7/9 1x15lbs IQF",$2.15

REMEMBER:
- ALL Product IDs should be "N/A" for this vendor!
- ALWAYS wrap the description in double quotes
- Put the ENTIRE description in the second column
- Put ONLY the price in the third column

Do NOT include:
- Category headers
- Rows without a price
- Any explanatory text

Return ONLY the CSV data with header.
"""

    elif vendor == 'tnt_produce':
        return """
Please extract ALL product information from this PDF price list.

This is a TNT Produce Company price list.

CRITICAL INSTRUCTIONS FOR TNT PRODUCE:
- This vendor does NOT have Product IDs
- Use "N/A" for ALL Product IDs
- Extract ONLY the product description and price
- Extract EVERY product from EVERY page
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- Include unit information if present (/LB, /CS, /EA, /BOX, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
N/A,TOMATOES ROMA,$1.25/LB
N/A,LETTUCE ICEBERG,$0.89/EA
N/A,ONIONS YELLOW,$0.65/LB
N/A,POTATOES RUSSET 50LB,$18.99/BOX

REMEMBER: ALL Product IDs should be "N/A" for this vendor!

Do NOT include:
- Category headers
- Rows without a price
- Any explanatory text

Return ONLY the CSV data with header.
"""

    elif vendor == 'royalty_distribution':
        return """
Please extract ALL product information from this PDF price list.

This is a Royalty Distribution price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
RD-001,BEEF RIBEYE STEAK,$9.99/LB
N/A,PORK CHOPS BONELESS,$5.49/LB
789,CHICKEN THIGHS,$3.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'apsic_wholesale':
        return """
Please extract ALL product information from this APSIC Wholesale PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
APS-123,CHICKEN BREAST FRESH,$5.99/LB
N/A,PORK CHOPS BONELESS,$7.49/LB
456,BEEF GROUND 80/20,$4.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'delmar_cow':
        return """
Please extract ALL product information from this Del Mar Distributions COW PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs follow this format: 6 digits, hyphen, 2 digits (e.g., 330020-61)
- The 2 digits AFTER the hyphen are PART OF the Product ID (e.g., 330020-61 is ONE complete ID)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, cuts, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
330020-61,BEEF RIBEYE CHOICE,$12.99/LB
445678-22,BEEF CHUCK ROAST,$8.49/LB
N/A,BEEF BRISKET WHOLE,$6.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'delmar_steer':
        return """
Please extract ALL product information from this Del Mar Distributions Steer PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs follow this format: 6 digits, hyphen, 2 digits (e.g., 330020-61)
- The 2 digits AFTER the hyphen are PART OF the Product ID (e.g., 330020-61 is ONE complete ID)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, cuts, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
330020-61,BEEF TENDERLOIN PRIME,$15.99/LB
445678-22,BEEF SIRLOIN CHOICE,$10.49/LB
N/A,BEEF SHORT RIBS,$9.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'gladway':
        return """
Please extract ALL product information from this Gladway Pricing PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
GW-123,CHICKEN BREAST BONELESS SKINLESS,$6.99/LB
N/A,PORK CHOPS CENTER CUT,$8.49/LB
456,BEEF GROUND 85/15,$5.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'union_fish':
        return """
Please extract ALL product information from this Union Fish PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description (include fish species, cut, size)
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, fresh/frozen), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
UF-789,SALMON FILLET FRESH ATLANTIC,$14.99/LB
N/A,TUNA STEAK YELLOWFIN FROZEN,$12.49/LB
123,SHRIMP PEELED DEVEINED 16/20,$9.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'solomon_wholesale':
        return """
Please extract ALL product information from this Solomon Wholesale PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
SW-456,CHICKEN THIGHS BONE-IN,$4.99/LB
N/A,TURKEY BREAST WHOLE,$7.49/LB
789,PORK SHOULDER BONELESS,$5.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'da_price':
        return """
Please extract ALL product information from this D&A PRICE PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, cuts, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
DA-123,BEEF RIBEYE CHOICE,$13.99/LB
N/A,CHICKEN WINGS FRESH,$5.49/LB
456,PORK RIBS BABY BACK,$8.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'broadleaf':
        return """
Please extract ALL product information from this Broadleaf PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
BL-789,PRODUCE LETTUCE ROMAINE,$2.99/EA
N/A,TOMATOES VINE RIPE,$3.49/LB
123,ONIONS YELLOW JUMBO,$1.99/LB

Return ONLY the CSV data with header.
"""

    elif vendor == 'cofoods':
        return """
Please extract ALL product information from this Cofoods Inc PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- **CRITICAL**: Numbers separated by slashes (e.g., "18/20", "19/119", "16/20") are SIZE CODES and are PART OF THE DESCRIPTION, NOT Product IDs
- If you see patterns like "18/20" or "19/119", these should be included in the Product Description, NOT in the Product ID column
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description including size codes
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, cuts, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
CF-456,SHRIMP 18/20 PEELED DEVEINED,$9.99/LB
N/A,CHICKEN WINGS 19/119 FRESH,$6.49/LB
789,PORK CHOPS 16/20 BONE-IN,$5.99/LB

REMEMBER: "18/20", "19/119", "16/20" etc. are SIZE CODES in the description, NOT Product IDs!

Return ONLY the CSV data with header.
"""

    elif vendor == 'monarch_trading':
        return """
Please extract ALL product information from this Monarch Trading PDF price list.

IMPORTANT INSTRUCTIONS:
- Extract EVERY product from EVERY page
- Product IDs can be alphanumeric (letters, numbers, hyphens)
- If a product does NOT have a Product ID, use "N/A" in the Product ID column
- Keep the full product description
- Extract prices (look for decimal numbers like 3.49, 12.99, etc.)
- If a product has MULTIPLE PRICES for different variations (sizes, grades, cuts, etc.), create SEPARATE rows for each variation
- For variations, append the variation details to the description

Return the data in CSV format with this EXACT header:
Product ID,Product Description,Cost

Example rows:
MT-123,SALMON FILLET FRESH,$15.99/LB
N/A,SHRIMP PEELED DEVEINED,$11.49/LB
456,TUNA STEAK FROZEN,$13.99/LB

Return ONLY the CSV data with header.
"""

    else:
        # Default prompt for other vendors
        return """
Please extract ALL product information from this PDF price list.

For each product, extract:
1. Product ID
2. Product Description
3. Cost/Price

Return the data in CSV format with this header:
Product ID,Product Description,Cost

Do NOT include any explanatory text, ONLY the CSV data with header.
"""


def parse_gemini_csv_response(response_text: str, vendor: str) -> List[Dict[str, str]]:
    """
    Parse the CSV response from Gemini and clean the data.
    
    Args:
        response_text: Raw response text from Gemini
        vendor: Vendor code
    
    Returns:
        List of dictionaries with keys: product_id, description, cost
    """
    print(f"\n   📊 Parsing Gemini CSV response...")
    
    # Extract CSV content (remove markdown code blocks if present)
    csv_content = extract_csv_from_response(response_text)
    
    # Parse CSV lines
    lines = csv_content.strip().split('\n')
    if not lines:
        print(f"   ⚠️  No data found in response")
        return []
    
    # Skip header line
    header = lines[0].lower()
    if 'product' not in header:
        print(f"   ⚠️  Warning: Expected CSV header not found")
        # Try to parse anyway
        data_lines = lines
    else:
        data_lines = lines[1:]
    
    # Parse each line
    extracted_data = []
    for line_num, line in enumerate(data_lines, start=2):
        if not line.strip():
            continue
        
        # Parse CSV line (handle quoted fields)
        parsed = parse_csv_line(line)
        if not parsed or len(parsed) < 3:
            print(f"   ⚠️  Line {line_num}: Could not parse: {line[:50]}...")
            continue
        
        product_id = parsed[0].strip()
        description = parsed[1].strip()
        cost = parsed[2].strip()
        
        # Clean and validate the data
        cleaned = clean_product_data(product_id, description, cost, vendor)
        if cleaned:
            extracted_data.append(cleaned)
        else:
            print(f"   ⚠️  Line {line_num}: Invalid data: ID={product_id}, Desc={description[:30]}, Cost={cost}")
    
    return extracted_data


def extract_csv_from_response(response_text: str) -> str:
    """
    Extract CSV content from Gemini response (remove markdown code blocks).
    
    Args:
        response_text: Raw response text
    
    Returns:
        Clean CSV content
    """
    # Remove markdown code blocks
    if '```' in response_text:
        # Extract content between ```csv and ``` or ``` and ```
        match = re.search(r'```(?:csv)?\s*\n(.*?)\n```', response_text, re.DOTALL)
        if match:
            return match.group(1)
    
    return response_text


def parse_csv_line(line: str) -> List[str]:
    """
    Parse a CSV line handling quoted fields.
    
    Args:
        line: CSV line
    
    Returns:
        List of field values
    """
    import csv
    import io
    
    reader = csv.reader(io.StringIO(line))
    try:
        return next(reader)
    except:
        # Fallback: simple split
        return line.split(',')


def clean_product_data(product_id: str, description: str, cost: str, vendor: str) -> Optional[Dict[str, str]]:
    """
    Clean and validate product data.
    
    Args:
        product_id: Raw product ID
        description: Raw description
        cost: Raw cost
        vendor: Vendor code
    
    Returns:
        Dictionary with cleaned data or None if invalid
    """
    # Clean product ID
    product_id = product_id.strip().strip('"').strip("'")
    if not product_id:
        return None

    # Allow "N/A" or "-" for products without IDs
    if product_id.upper() in ['N/A', 'NA', '-']:
        product_id = 'N/A'

    # Clean description
    description = description.strip().strip('"').strip("'")
    if not description or len(description) < 2:
        return None

    # Clean cost
    cost = cost.strip().strip('"').strip("'")
    if not cost:
        return None

    # Validate and format cost
    cost_cleaned = clean_cost(cost)
    if not cost_cleaned:
        print(f"   ⚠️  Invalid cost format: '{cost}' for product: {description[:30]}")
        return None

    # Validate product ID format based on vendor (skip validation for N/A)
    if product_id != 'N/A':
        if vendor == 'glen_rose':
            if not validate_glen_rose_product_id(product_id):
                print(f"      Invalid Glen Rose Product ID format: {product_id}")
                return None
        elif vendor == 'kruse_sons':
            if not validate_kruse_sons_product_id(product_id):
                print(f"      Invalid Kruse & Sons Product ID format: {product_id}")
                return None
        elif vendor == 'quirch_foods':
            if not validate_quirch_foods_product_id(product_id):
                print(f"      Invalid Quirch Foods Product ID format: {product_id}")
                return None
        elif vendor in ['purcell', 'laras_meat', 'maui_prices']:
            if not validate_flexible_product_id(product_id):
                print(f"      Invalid {vendor} Product ID format: {product_id}")
                return None

    return {
        'product_id': product_id,
        'description': description,
        'cost': cost_cleaned
    }


def validate_glen_rose_product_id(product_id: str) -> bool:
    """
    Validate Glen Rose product ID format.

    Args:
        product_id: Product ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Primary format: 8-11 digits, hyphen, 2-3 digits
    if re.match(r'^\d{8,11}-\d{2,3}$', product_id):
        return True

    # Fallback: 6-10 digits, hyphen, 1-3 digits
    if re.match(r'^\d{6,10}-\d{1,3}$', product_id):
        return True

    # Allow non-hyphenated numeric IDs (some products might not have hyphens)
    if product_id.isdigit() and 6 <= len(product_id) <= 11:
        return True

    return False


def validate_kruse_sons_product_id(product_id: str) -> bool:
    """
    Validate Kruse & Sons product ID format.

    Args:
        product_id: Product ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Format: 1-3 digit numeric code (e.g., 01, 03, 05, 07, 11, 30, 41)
    if re.match(r'^\d{1,3}$', product_id):
        return True

    return False


def validate_quirch_foods_product_id(product_id: str) -> bool:
    """
    Validate Quirch Foods product ID format.

    Args:
        product_id: Product ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Format: 6 or 10 digit numeric code (e.g., 111702307, 189010, 111722903)
    if re.match(r'^\d{10}$', product_id):
        return True

    if re.match(r'^\d{6}$', product_id):
        return True

    # Allow 7-9 digits as fallback
    if re.match(r'^\d{7,9}$', product_id):
        return True

    return False


def validate_flexible_product_id(product_id: str) -> bool:
    """
    Validate flexible product ID format (for Purcell, Laras Meat, Maui Prices).

    Args:
        product_id: Product ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Allow alphanumeric with optional hyphens (3-15 characters)
    if re.match(r'^[A-Za-z0-9\-]{3,15}$', product_id):
        return True

    return False


def clean_cost(cost_str: str) -> Optional[str]:
    """
    Clean and format cost string.
    
    Args:
        cost_str: Raw cost string
    
    Returns:
        Cleaned cost string or None if invalid
    """
    cost_str = cost_str.strip().upper()
    
    # Handle special cases
    if cost_str in ['OUT', 'OUT OF STOCK']:
        return 'OUT OF STOCK'
    
    if cost_str in ['QUOTE', 'QUOTE REQUIRED']:
        return 'QUOTE REQUIRED'
    
    # Extract price with optional unit
    # Patterns: $4.99/LB, $29.00/CS, $6.20, 4.99/LB, 6.20
    match = re.search(r'(\$?\s*\d{1,5}(?:\.\d{2})?)\s*(/LB|/CS|/EA)?', cost_str, re.IGNORECASE)
    if not match:
        return None
    
    price_part = match.group(1).strip()
    unit_part = match.group(2).strip() if match.group(2) else ''
    
    # Remove $ and convert to float
    price_part = price_part.replace('$', '').strip()
    try:
        price_value = float(price_part)
    except ValueError:
        return None
    
    # Validate price range
    if not (0.01 <= price_value <= 99999.99):
        return None
    
    # Format as $X.XX with optional unit
    if unit_part:
        return f"${price_value:.2f}{unit_part.upper()}"
    else:
        return f"${price_value:.2f}"

