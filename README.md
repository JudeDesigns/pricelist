# PDF Price List Extractor

A Flask web application that extracts product information (Product ID, Description, and Cost) from PDF price lists. Supports both text-based and image-based tables using OCR.

## Features

- Upload up to 30 PDF files simultaneously
- Extracts data from both text-based and image-based tables
- Automatic vendor name extraction from filenames
- Clean, responsive web interface
- Error handling for individual files
- Results organized by vendor

## Prerequisites

Before running this application, you need to install:

1. **Python 3.8+**
2. **Tesseract OCR** (for image-based PDF processing)

### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

3. **Poppler** (for PDF to image conversion)

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download from: http://blog.alivate.com.au/poppler-windows/

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Activate the virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Upload Files**: Click on the upload area or drag and drop PDF files (up to 30 files)
2. **File Naming**: Name your files with vendor name followed by date/numbers:
   - Example: `AcmeSupplies_20250106.pdf`
   - Example: `GlobalVendor_2025.pdf`
3. **Process**: Click "Process Files" to extract data
4. **View Results**: Review extracted data organized by vendor

## Project Structure

```
Document_automation/
├── app.py                  # Main Flask application
├── pdf_processor.py        # PDF processing logic
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── process.html
│   └── results.html
├── static/                 # Static files
│   └── css/
│       └── style.css
└── uploads/                # Temporary file storage (auto-created)
```

## How It Works

1. **Text-based PDFs**: Uses `pdfplumber` to extract tables directly from PDF text
2. **Image-based PDFs**: Converts PDF pages to images, then uses Tesseract OCR to extract text
3. **Data Parsing**: Identifies Product ID, Description, and Cost columns
4. **Vendor Extraction**: Extracts vendor name from filename (string part before numbers)

## Troubleshooting

### Tesseract not found
If you get a "Tesseract not found" error:
- Make sure Tesseract is installed
- On Windows, you may need to add Tesseract to your PATH or specify the path in `pdf_processor.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### Poor OCR results
- Ensure PDFs are high quality
- The system works best with clear, well-formatted tables
- You may need to adjust preprocessing parameters in `pdf_processor.py`

### File upload errors
- Check file size limits (default: 100MB total)
- Ensure files are valid PDFs
- Check available disk space

## Future Enhancements

- Export results to CSV/Excel
- Database storage for historical data
- Improved table detection algorithms
- Support for more document formats
- Batch processing queue
- User authentication

## License

MIT License

