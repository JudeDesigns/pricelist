#!/usr/bin/env python3
"""
Debug script to test Gemini API on VPS
"""

import os
import sys

print("=" * 80)
print("GEMINI API DEBUG TEST")
print("=" * 80)

# 1. Check environment variables
print("\n1. Checking environment variables...")
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    print(f"   ✅ GEMINI_API_KEY is set: {api_key[:20]}...{api_key[-10:]}")
else:
    print("   ❌ GEMINI_API_KEY is NOT set")
    print("\n   Please set it:")
    print("   export GEMINI_API_KEY=AIzaSyCN1Jk6IxIDYGzZ8uI63DWdrfTF6A8Sfxc")
    sys.exit(1)

# 2. Check if google-generativeai is installed
print("\n2. Checking if google-generativeai is installed...")
try:
    import google.generativeai as genai
    print("   ✅ google-generativeai is installed")
except ImportError as e:
    print(f"   ❌ google-generativeai is NOT installed: {e}")
    print("\n   Please install it:")
    print("   pip install google-generativeai")
    sys.exit(1)

# 3. Configure Gemini
print("\n3. Configuring Gemini API...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ Gemini API configured")
except Exception as e:
    print(f"   ❌ Failed to configure Gemini: {e}")
    sys.exit(1)

# 4. List available models
print("\n4. Listing available Gemini models...")
try:
    models = genai.list_models()
    print("   Available models:")
    for model in models:
        if 'gemini' in model.name.lower():
            print(f"      - {model.name}")
    print("   ✅ Successfully listed models")
except Exception as e:
    print(f"   ❌ Failed to list models: {e}")
    sys.exit(1)

# 5. Test simple text generation
print("\n5. Testing simple text generation...")
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say 'Hello, Gemini is working!'")
    print(f"   Response: {response.text}")
    print("   ✅ Text generation works")
except Exception as e:
    print(f"   ❌ Text generation failed: {e}")
    sys.exit(1)

# 6. Test with a sample PDF (if provided)
print("\n6. Testing PDF parsing...")
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"   ⚠️  PDF file not found: {pdf_path}")
    else:
        print(f"   Reading PDF: {pdf_path}")
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            print(f"   PDF size: {len(pdf_bytes)} bytes")
            
            prompt = """
Extract ALL products from this price list.
Return in CSV format:
Product ID,Product Description,Cost

Extract EVERY product you can find.
"""
            
            print("   Sending to Gemini 2.5 Pro...")
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content([
                {
                    'mime_type': 'application/pdf',
                    'data': pdf_bytes
                },
                prompt
            ])
            
            print("\n   ✅ Gemini response received!")
            print("\n   First 1000 characters of response:")
            print("   " + "=" * 70)
            print(response.text[:1000])
            print("   " + "=" * 70)
            
            # Count lines
            lines = response.text.strip().split('\n')
            print(f"\n   Total lines in response: {len(lines)}")
            print(f"   (Header line + {len(lines)-1} product lines)")
            
        except Exception as e:
            print(f"   ❌ PDF parsing failed: {e}")
            import traceback
            traceback.print_exc()
else:
    print("   ⚠️  No PDF file provided")
    print("   Usage: python test_gemini_debug.py /path/to/pdf/file.pdf")

print("\n" + "=" * 80)
print("DEBUG TEST COMPLETE")
print("=" * 80)

