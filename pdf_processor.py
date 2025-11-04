import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import cv2
import numpy as np
import os

# Configure tesseract path for Linux systems
tesseract_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract']
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break

# Try to import PyMuPDF (fitz) for faster image extraction
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Import vendor parsers
from vendors import get_parser, VENDOR_PARSERS

# Import Gemini parser
try:
    from gemini_parser import parse_pdf_with_gemini
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  Gemini parser not available (google-generativeai not installed)")

# ============================================================================
# VENDOR CONFIGURATION (Legacy - kept for compatibility)
# ============================================================================

VENDOR_CONFIGS = {
    'rw_zant': {
        'name': 'RW Zant',
        'product_id_format': 'numeric_only',
        'max_product_id_length': 6,
        'requires_dollar_sign': True,
        'description': 'RW Zant vendor - numeric product IDs only'
    },
    'glen_rose': {
        'name': 'Glen Rose Meat Company',
        'product_id_format': 'hyphenated',
        'max_product_id_length': 10,
        'requires_dollar_sign': True,
        'description': 'Glen Rose - supports hyphenated product IDs'
    },
    'kruse_sons': {
        'name': 'Kruse & Sons',
        'product_id_format': 'numeric_code',
        'max_product_id_length': 3,
        'requires_dollar_sign': False,
        'description': 'Kruse & Sons - simple numeric codes (1-3 digits)'
    },
    'quirch_foods': {
        'name': 'Quirch Foods',
        'product_id_format': 'numeric',
        'max_product_id_length': 10,
        'requires_dollar_sign': True,
        'description': 'Quirch Foods - 6 or 10 digit numeric product IDs'
    },
    'purcell': {
        'name': 'Purcell',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Purcell - flexible alphanumeric product IDs'
    },
    'laras_meat': {
        'name': 'Laras Meat',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Laras Meat - flexible alphanumeric product IDs'
    },
    'maui_prices': {
        'name': 'Maui Prices',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Maui Prices - flexible alphanumeric product IDs'
    },
    'cd_international': {
        'name': 'C&D International Fishery',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'C&D International Fishery - flexible alphanumeric product IDs'
    },
    'royalty_distribution': {
        'name': 'Royalty Distribution',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Royalty Distribution - flexible alphanumeric product IDs'
    },
    'la_poultry': {
        'name': 'Los Angeles Poultry Co',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Los Angeles Poultry Co - flexible alphanumeric product IDs'
    },
    'tnt_produce': {
        'name': 'TNT Produce Company',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'TNT Produce Company - flexible alphanumeric product IDs'
    },
    'apsic_wholesale': {
        'name': 'APSIC Wholesale',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'APSIC Wholesale - flexible alphanumeric product IDs'
    },
    'delmar_cow': {
        'name': 'Del Mar Distributions COW',
        'product_id_format': 'hyphenated',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Del Mar Distributions COW - hyphenated format (e.g., 330020-61)'
    },
    'delmar_steer': {
        'name': 'Del Mar Distributions Steer',
        'product_id_format': 'hyphenated',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Del Mar Distributions Steer - hyphenated format (e.g., 330020-61)'
    },
    'gladway': {
        'name': 'Gladway Pricing',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Gladway Pricing - flexible alphanumeric product IDs'
    },
    'union_fish': {
        'name': 'Union Fish',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Union Fish - flexible alphanumeric product IDs'
    },
    'solomon_wholesale': {
        'name': 'Solomon Wholesale',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Solomon Wholesale - flexible alphanumeric product IDs'
    },
    'da_price': {
        'name': 'D&A PRICE',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'D&A PRICE - flexible alphanumeric product IDs'
    },
    'broadleaf': {
        'name': 'Broadleaf',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Broadleaf - flexible alphanumeric product IDs'
    },
    'cofoods': {
        'name': 'Cofoods Inc',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Cofoods Inc - flexible alphanumeric product IDs'
    },
    'monarch_trading': {
        'name': 'Monarch Trading',
        'product_id_format': 'flexible',
        'max_product_id_length': 15,
        'requires_dollar_sign': False,
        'description': 'Monarch Trading - flexible alphanumeric product IDs'
    },
    'unknown': {
        'name': 'Unknown Vendor',
        'product_id_format': 'flexible',
        'max_product_id_length': 20,
        'requires_dollar_sign': False,
        'description': 'Unknown vendor - will be parsed with Gemini AI'
    }
}

# Default vendor if not specified
DEFAULT_VENDOR = 'rw_zant'

def is_valid_product_id(product_id, vendor='rw_zant'):
    """
    Validate product ID based on vendor configuration.
    """
    if not product_id:
        return False

    # Remove any whitespace
    product_id = product_id.strip()

    # Get vendor config
    config = VENDOR_CONFIGS.get(vendor, VENDOR_CONFIGS[DEFAULT_VENDOR])
    product_id_format = config['product_id_format']
    max_length = config['max_product_id_length']

    # Check format based on vendor
    if product_id_format == 'numeric_only':
        # RW Zant: Only digits, no hyphens, max 6 digits
        if not product_id.isdigit():
            return False
        if len(product_id) > max_length:
            return False

    elif product_id_format == 'hyphenated':
        # Glen Rose: Allow hyphens (e.g., 123456-01)
        if '-' in product_id:
            parts = product_id.split('-')
            if not all(part.isdigit() for part in parts):
                return False
            # First part should be max 6 digits
            if len(parts[0]) > 6:
                return False
        else:
            # No hyphen - must be purely numeric
            if not product_id.isdigit():
                return False
            if len(product_id) > 6:
                return False

    # Minimum length check (at least 4 digits)
    if len(product_id.replace('-', '')) < 4:
        return False

    return True

def extract_product_id_from_text_rw_zant(text):
    """
    RW Zant: Extract product ID from text (numeric only, max 6 digits).
    If there are more than 6 digits at the start, only take the first 6.
    Position 7+ becomes part of the description.
    """
    text = text.strip()

    # Find leading digits only (no hyphens for RW Zant)
    match = re.match(r'^(\d+)', text)
    if not match:
        return None, text

    digits = match.group(1)
    remaining = text[len(digits):].strip()

    # If more than 6 digits, split at position 6
    if len(digits) > 6:
        product_id = digits[:6]
        # Add the extra digits to the description
        remaining = digits[6:] + ' ' + remaining
    else:
        product_id = digits

    return product_id, remaining

def extract_product_id_from_text_glen_rose(text):
    """
    Glen Rose: Extract product ID from text, supporting hyphenated format.
    Supports formats like: 123456, 123456-01, 1234567890 (splits to 123456 + 7890)
    """
    text = text.strip()

    # Find leading digits, optionally followed by hyphen and more digits
    # This captures: 123456 or 123456-01 or 123456789
    match = re.match(r'^(\d+(?:-\d+)?)', text)
    if not match:
        return None, text

    product_id_candidate = match.group(1)
    remaining = text[len(product_id_candidate):].strip()

    # If it contains a hyphen, it's already in the right format (e.g., 123456-01)
    if '-' in product_id_candidate:
        return product_id_candidate, remaining

    # If no hyphen, check if we have more than 6 digits
    if len(product_id_candidate) > 6:
        # Split at position 6 - rest goes to description
        product_id = product_id_candidate[:6]
        # Add the extra digits to the description
        remaining = product_id_candidate[6:] + ' ' + remaining
    else:
        product_id = product_id_candidate

    return product_id, remaining

def extract_product_id_from_text(text, vendor='rw_zant'):
    """
    Extract product ID from text based on vendor configuration.
    """
    if vendor == 'rw_zant':
        return extract_product_id_from_text_rw_zant(text)
    elif vendor == 'glen_rose':
        return extract_product_id_from_text_glen_rose(text)
    else:
        # Default to RW Zant
        return extract_product_id_from_text_rw_zant(text)

def is_valid_description(description):
    """Validate that description looks like actual product text"""
    if not description:
        return False

    description = description.strip()

    # Must have at least 3 characters
    if len(description) < 3:
        return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', description):
        return False

    # Should not be mostly numbers (more than 70% digits is suspicious)
    digit_count = sum(c.isdigit() for c in description)
    if len(description) > 0 and (digit_count / len(description)) > 0.7:
        return False

    # Should not be just special characters
    alpha_count = sum(c.isalpha() for c in description)
    if alpha_count < 2:
        return False

    return True

def process_pdf(filepath, vendor='rw_zant'):
    """
    Process a PDF file and extract price list data.
    Returns a list of dictionaries with keys: product_id, description, cost

    Args:
        filepath: Path to the PDF file
        vendor: Vendor code (e.g., 'rw_zant', 'glen_rose')
    """
    extracted_data = []

    # Use Gemini AI for these vendors (if available)
    gemini_vendors = ['glen_rose', 'kruse_sons', 'quirch_foods', 'purcell', 'laras_meat', 'maui_prices',
                      'cd_international', 'royalty_distribution', 'la_poultry', 'tnt_produce',
                      'apsic_wholesale', 'delmar_cow', 'delmar_steer',
                      'gladway', 'union_fish', 'solomon_wholesale', 'da_price', 'broadleaf',
                      'cofoods', 'monarch_trading', 'unknown']
    if vendor in gemini_vendors and HAS_GEMINI:
        vendor_name = VENDOR_CONFIGS[vendor]['name']
        print(f"\n🤖 {vendor_name} detected - Using GEMINI AI for parsing")
        try:
            gemini_data = parse_pdf_with_gemini(filepath, vendor)
            if gemini_data and len(gemini_data) > 0:
                return gemini_data
        except Exception as e:
            print(f"⚠️  Gemini AI parsing failed: {e}")
            print(f"   Falling back to OCR-based extraction...")
            # Fall through to OCR method

    # Glen Rose fallback: Use image-based table extraction (OCR + regex)
    if vendor == 'glen_rose':
        print("\n🖼️  Glen Rose detected - Using IMAGE-BASED table extraction")
        try:
            image_data = extract_image_tables_structured(filepath, vendor)
            if image_data and len(image_data) > 0:
                return image_data
        except Exception as e:
            print(f"Image-based table extraction failed: {e}")
            raise Exception(f"Failed to extract data from Glen Rose PDF: {str(e)}")

    # Kruse Sons fallback: Use image-based table extraction (OCR + regex)
    if vendor == 'kruse_sons':
        print("\n🖼️  Kruse & Sons detected - Using IMAGE-BASED table extraction")
        try:
            image_data = extract_image_tables_structured(filepath, vendor)
            if image_data and len(image_data) > 0:
                return image_data
        except Exception as e:
            print(f"Image-based table extraction failed: {e}")
            raise Exception(f"Failed to extract data from Kruse & Sons PDF: {str(e)}")

    # Quirch Foods fallback: Use image-based table extraction (OCR + regex)
    if vendor == 'quirch_foods':
        print("\n🖼️  Quirch Foods detected - Using IMAGE-BASED table extraction")
        try:
            image_data = extract_image_tables_structured(filepath, vendor)
            if image_data and len(image_data) > 0:
                return image_data
        except Exception as e:
            print(f"Image-based table extraction failed: {e}")
            raise Exception(f"Failed to extract data from Quirch Foods PDF: {str(e)}")

    # Gemini-supported vendors fallback: Use image-based table extraction (OCR + regex)
    if vendor in ['purcell', 'laras_meat', 'maui_prices', 'cd_international', 'royalty_distribution', 'la_poultry', 'tnt_produce',
                  'apsic_wholesale', 'delmar_cow', 'delmar_steer',
                  'gladway', 'union_fish', 'solomon_wholesale', 'da_price', 'broadleaf',
                  'cofoods', 'monarch_trading']:
        vendor_name = VENDOR_CONFIGS[vendor]['name']
        print(f"\n🖼️  {vendor_name} detected - Using IMAGE-BASED table extraction")
        try:
            image_data = extract_image_tables_structured(filepath, vendor)
            if image_data and len(image_data) > 0:
                return image_data
        except Exception as e:
            print(f"Image-based table extraction failed: {e}")
            raise Exception(f"Failed to extract data from {vendor_name} PDF: {str(e)}")

    # RW Zant and others: Try text-based extraction first
    try:
        text_data = extract_text_tables(filepath, vendor)
        if text_data and len(text_data) > 0:
            return text_data
    except Exception as e:
        print(f"Text extraction failed: {e}")

    # If text extraction fails or returns no data, try OCR
    try:
        ocr_data = extract_image_tables(filepath, vendor)
        if ocr_data and len(ocr_data) > 0:
            return ocr_data
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        raise Exception(f"Failed to extract data from PDF: {str(e)}")

    return extracted_data

def extract_text_tables(filepath, vendor='rw_zant'):
    """
    Extract tables from text-based PDFs using pdfplumber.
    Strategy: Split page into left/right halves FIRST, then process each independently.
    """
    print(f"\n📋 Using vendor configuration: {VENDOR_CONFIGS[vendor]['name']}")
    print(f"   Product ID format: {VENDOR_CONFIGS[vendor]['product_id_format']}")

    extracted_data = []
    existing_ids = set()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\n=== Processing Page {page_num + 1} ===")

            width = page.width
            height = page.height

            # Process LEFT half
            left_bbox = (0, 0, width / 2, height)
            left_crop = page.crop(left_bbox)
            left_items = process_half_page(left_crop, "LEFT", vendor)

            for item in left_items:
                if item['product_id'] not in existing_ids:
                    extracted_data.append(item)
                    existing_ids.add(item['product_id'])

            # Process RIGHT half
            right_bbox = (width / 2, 0, width, height)
            right_crop = page.crop(right_bbox)
            right_items = process_half_page(right_crop, "RIGHT", vendor)

            for item in right_items:
                if item['product_id'] not in existing_ids:
                    extracted_data.append(item)
                    existing_ids.add(item['product_id'])

            print(f"Page {page_num + 1}: {len(left_items)} left + {len(right_items)} right = {len(left_items) + len(right_items)} items")

    print(f"\n*** TOTAL: {len(extracted_data)} unique items ***\n")
    return extracted_data

def process_half_page(cropped_page, side_name, vendor='rw_zant'):
    """Process a single half of a page (left or right)"""
    items = []

    # Use text-based strategy for better table detection
    table_settings = {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
    }

    try:
        tables = cropped_page.extract_tables(table_settings=table_settings)

        if tables:
            print(f"  {side_name}: Found {len(tables)} table(s)")
            for table in tables:
                parsed = parse_simple_table(table, vendor)
                items.extend(parsed)
                print(f"  {side_name}: Extracted {len(parsed)} items from table")
    except Exception as e:
        print(f"  {side_name}: Table extraction error: {e}")

    # Fallback: text extraction
    if not items:
        try:
            text = cropped_page.extract_text()
            if text:
                parsed = parse_text_data(text, vendor)
                items.extend(parsed)
                print(f"  {side_name}: Extracted {len(parsed)} items from text")
        except Exception as e:
            print(f"  {side_name}: Text extraction error: {e}")

    return items

def extract_image_tables_structured(filepath, vendor='glen_rose'):
    """
    Extract tables from image-based PDFs using OCR with regex pattern matching.
    Specifically designed for Glen Rose PDFs with complex table layouts.
    Uses PyMuPDF (fitz) if available for faster processing, otherwise falls back to pdf2image.
    """
    print(f"\n📋 Using vendor configuration: {VENDOR_CONFIGS[vendor]['name']}")
    print(f"   Product ID format: {VENDOR_CONFIGS[vendor]['product_id_format']}")
    print(f"   Extraction method: IMAGE-BASED with REGEX PATTERN MATCHING")

    extracted_data = []
    existing_ids = set()

    # Get vendor-specific parser
    parser = get_parser(vendor)

    # Convert PDF pages to images with higher DPI for better OCR accuracy
    # Higher DPI = clearer text = better OCR results
    DPI = 400  # Increased from 300 for better quality

    if HAS_PYMUPDF:
        print(f"\n🖼️  Using PyMuPDF for faster image extraction (DPI={DPI})...")
        images = []
        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=DPI)
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        doc.close()
        print(f"   Converted {len(images)} page(s)")
    else:
        print(f"\n🖼️  Converting PDF to images (DPI={DPI})...")
        images = convert_from_path(filepath, dpi=DPI)
        print(f"   Converted {len(images)} page(s)")

    for page_num, image in enumerate(images):
        print(f"\n=== Processing Page {page_num + 1} ===")

        # Convert PIL Image to numpy array for OpenCV processing
        img_array = np.array(image)

        # Preprocess image for better OCR
        processed_img = preprocess_image(img_array, enhance=True)

        # Run OCR to get raw text with improved configuration
        print(f"   Running OCR with enhanced settings...")
        # OEM 3 = Default (best accuracy)
        # PSM 6 = Assume a single uniform block of text
        # Additional flags for better accuracy:
        # - preserve_interword_spaces=1: Keep spaces between words
        # - tessedit_char_whitelist: Limit to expected characters (optional)
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        raw_text = pytesseract.image_to_string(processed_img, config=custom_config)

        # Parse the raw text using vendor-specific text line parser
        lines = raw_text.split('\n')
        print(f"   Found {len(lines)} lines of text")

        items_found = 0
        for line in lines:
            if not line.strip():
                continue

            # Use vendor-specific text line parser
            result = parser.parse_text_line(line)
            if result and result['product_id'] not in existing_ids:
                extracted_data.append(result)
                existing_ids.add(result['product_id'])
                items_found += 1

        print(f"   Extracted {items_found} items from this page")

    print(f"\n✅ Total items extracted: {len(extracted_data)}")
    return extracted_data

def group_ocr_into_rows(ocr_data, vertical_threshold=10):
    """
    Group OCR results into table rows based on vertical position.

    Args:
        ocr_data: Dictionary from pytesseract.image_to_data()
        vertical_threshold: Maximum vertical distance to consider text on same row

    Returns:
        List of rows, where each row is a list of text values
    """
    # Extract text with positions
    items = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if not text:
            continue

        conf = int(ocr_data['conf'][i])
        if conf < 30:  # Skip low-confidence text
            continue

        x = ocr_data['left'][i]
        y = ocr_data['top'][i]
        width = ocr_data['width'][i]
        height = ocr_data['height'][i]

        items.append({
            'text': text,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'center_y': y + height / 2
        })

    if not items:
        return []

    # Sort by vertical position (top to bottom)
    items.sort(key=lambda item: item['center_y'])

    # Group items into rows based on vertical proximity
    rows = []
    current_row = []
    current_y = items[0]['center_y']

    for item in items:
        # If this item is close to the current row's Y position, add it to current row
        if abs(item['center_y'] - current_y) <= vertical_threshold:
            current_row.append(item)
        else:
            # Start a new row
            if current_row:
                # Sort current row by X position (left to right)
                current_row.sort(key=lambda item: item['x'])
                # Extract just the text values
                row_texts = [item['text'] for item in current_row]
                rows.append(row_texts)

            current_row = [item]
            current_y = item['center_y']

    # Don't forget the last row
    if current_row:
        current_row.sort(key=lambda item: item['x'])
        row_texts = [item['text'] for item in current_row]
        rows.append(row_texts)

    return rows

def extract_image_tables(filepath, vendor='rw_zant'):
    """Extract tables from image-based PDFs using OCR (legacy method for non-Glen Rose)"""
    print(f"\n📋 Using vendor configuration: {VENDOR_CONFIGS[vendor]['name']}")
    print(f"   Product ID format: {VENDOR_CONFIGS[vendor]['product_id_format']}")

    extracted_data = []

    # Convert PDF pages to images with higher DPI for better OCR
    DPI = 400  # Increased from 300 for better quality
    print(f"\n🖼️  Converting PDF to images (DPI={DPI})...")
    images = convert_from_path(filepath, dpi=DPI)
    print(f"   Converted {len(images)} page(s)")

    for image in images:
        # Convert PIL Image to numpy array for OpenCV processing
        img_array = np.array(image)

        # Preprocess image for better OCR with enhancement
        processed_img = preprocess_image(img_array, enhance=True)

        # Perform OCR with improved configuration for tables
        # OEM 3 = Default (best accuracy)
        # PSM 6 = Assume a single uniform block of text
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        ocr_text = pytesseract.image_to_string(processed_img, config=custom_config)

        # Parse the OCR text
        parsed_data = parse_text_data(ocr_text, vendor)
        extracted_data.extend(parsed_data)

        # Also try with different PSM mode for better table detection
        try:
            custom_config_alt = r'--oem 3 --psm 4'  # PSM 4 = Assume a single column of text
            ocr_text_alt = pytesseract.image_to_string(processed_img, config=custom_config_alt)
            parsed_data_alt = parse_text_data(ocr_text_alt, vendor)

            # Add any new data not already captured
            existing_ids = {item['product_id'] for item in extracted_data}
            for item in parsed_data_alt:
                if item['product_id'] not in existing_ids:
                    extracted_data.append(item)
        except:
            pass

    return extracted_data

def preprocess_image(img_array, enhance=True):
    """
    Preprocess image for better OCR results.

    Args:
        img_array: Input image as numpy array
        enhance: Whether to apply additional enhancement (default: True)

    Returns:
        Preprocessed image ready for OCR
    """
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    if enhance:
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This improves contrast and makes text clearer
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    # This is better than simple denoising for text
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # Apply adaptive thresholding for better text extraction
    # This works better than global thresholding for documents with varying lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Optional: Morphological operations to clean up text
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def parse_simple_table(table, vendor='rw_zant'):
    """
    Simple parser for single-column tables (after page split).
    Uses vendor-specific parser for extraction logic.
    """
    parsed_data = []

    if not table or len(table) < 2:
        return parsed_data

    # Get vendor-specific parser
    parser = get_parser(vendor)

    # Skip header row, process data rows
    for row in table[1:]:
        if not row or len(row) < 3:
            continue

        # Clean row - remove None and empty values
        row_clean = [str(item).strip() if item is not None else '' for item in row]
        row_clean = [item for item in row_clean if item]

        if len(row_clean) < 3:
            continue

        # Use vendor-specific parser to parse the row
        result = parser.parse_table_row(row_clean)
        if result:
            parsed_data.append(result)

    return parsed_data

def parse_text_data(text, vendor='rw_zant'):
    """Parse text data to extract product information using vendor-specific parser"""
    parsed_data = []

    if not text:
        return parsed_data

    # Get vendor-specific parser
    parser = get_parser(vendor)

    lines = text.split('\n')

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check if vendor requires dollar sign in text lines
        if parser.requires_dollar_sign and '$' not in line:
            continue

        # Use vendor-specific parser to parse the line
        result = parser.parse_text_line(line)
        if result:
            parsed_data.append(result)

    return parsed_data

def clean_cost(cost_str):
    """
    Clean and format cost string - must contain a dollar sign.
    Extracts the price value immediately after the $ sign.
    """
    if not cost_str:
        return None

    cost_str = str(cost_str).strip()

    # Check if the string contains a dollar sign
    if '$' not in cost_str:
        return None

    # Extract price pattern: $XX.XX or $X.XX or $XXX.XX
    # Match dollar sign followed by digits with optional decimal
    price_match = re.search(r'\$\s*(\d{1,4}(?:\.\d{2})?)', cost_str)

    if not price_match:
        print(f"  WARNING: Found $ but couldn't extract price from: '{cost_str}'")
        return None

    price_value = price_match.group(1)

    # Validate it's a reasonable price (not too high)
    try:
        price_float = float(price_value)

        # Sanity check: prices should be under $1000 for food items
        if price_float > 1000:
            print(f"  WARNING: Price too high (${price_float}), skipping")
            return None

        # Format to 2 decimal places
        formatted_price = f'${price_float:.2f}'
        return formatted_price
    except ValueError:
        print(f"  WARNING: Invalid price value: '{price_value}'")
        return None

