# Logo Not Appearing in Generated Contracts - Fix Guide

## Problem
The logo in the template doesn't appear in the generated contract.

## Root Cause
The `docxtpl` library (which generates contracts from Word templates) has limitations:
- **Does NOT support**: Text boxes, floating images, or shapes with text
- **DOES support**: Inline images, images in headers/footers, direct image insertion

## Solution Steps

### Step 1: Check Current Logo Placement
1. Open `static/contract_templates/50_50 template med placeholders.docx` in Word
2. Click on the logo
3. Check if:
   - It's inside a text box (you'll see a text box border)
   - It has "Layout Options" showing (means it's floating)

### Step 2: Fix the Logo

#### If Logo is in a Text Box:
1. Click inside the text box
2. Click on the logo to select it
3. Press `Ctrl+X` to cut
4. Click outside the text box
5. Delete the text box
6. Press `Ctrl+V` to paste the logo directly
7. Continue to Step 3

#### If Logo is Floating:
1. Right-click the logo
2. Select "Wrap Text" → "In Line with Text"
3. The logo should now move with the text flow

### Step 3: Verify Logo Settings
1. Right-click the logo → "Size and Position"
2. Go to "Text Wrapping" tab
3. Ensure "Inline with text" is selected
4. Click OK

### Step 4: Position the Logo
- If you want the logo at the top, place it at the beginning of the document
- Or insert it in the header:
  1. Double-click at the top of the page to open header
  2. Insert → Pictures → select your logo
  3. Make sure it's "Inline with text"
  4. Close header

### Step 5: Test
1. Save the template
2. Go to contracts page: http://localhost:8000/dashboard/contracts
3. Fill out the form and generate a contract
4. Check if the logo appears in the generated document

## Alternative: Add Logo to Header

If you want the logo in the header on every page:

1. Double-click at the top of any page to open the Header
2. Go to Insert → Pictures
3. Select your logo file (PNG or JPG recommended)
4. Resize if needed
5. Ensure "Inline with text" is selected
6. Add any placeholder text like `{{project_code}}` if needed
7. Close the header

The logo will now appear on all pages and will be preserved in generated contracts.

## Common Issues

### Logo Still Missing?
- **Check file format**: PNG and JPG work best
- **Check file size**: Very large images may cause issues
- **Check anchoring**: Must be inline, not anchored to paragraph
- **Check grouping**: If logo is grouped with other shapes, ungroup it first

### Logo Appears But Wrong Size?
- Resize in the template before generating
- The generated contract will match the template size exactly

## Test Script

Run this to test logo preservation:
```bash
python test_logo_preservation.py
```

Then open `test_contract_with_logo.docx` to verify the logo appears.
