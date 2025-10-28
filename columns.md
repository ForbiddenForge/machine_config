# File Parser Implementation Guide

## Problem Statement

The current Market Analysis Automation system only accepts Excel files with a very specific template format. A CSV file with different column names and ordering cannot be processed. This guide provides a step-by-step solution to make the system flexible enough to handle various file formats and column naming conventions.

-----

## Solution Overview

Create a column mapping system that:

1. Accepts both CSV and Excel files
1. Automatically maps different column names to expected standard names
1. Validates required columns are present
1. Provides clear error messages
1. Includes a preview endpoint for testing files

**Estimated Time:** 1.5-2 days

-----

## Step 1: Understand Current Template Requirements

### Find the Upload Endpoint

Look in `server.py` for the file upload route (around line 251):

```python
@app.post("/submarket-mappings", response_model=SubmarketMappingFeatureCollection)
async def get_submarket_mappings(file: UploadFile = File(...)):
```

### What to Document

1. **How it reads the file:**
   
   ```python
   file_contents = await file.read()
   df = pd.read_excel(file_contents)
   ```
1. **What columns it expects:**
- Look for `df['column_name']` references
- Check validation code
- Find error messages about format
1. **Required vs Optional columns:**
- Which columns must have data?
- Which can be empty?

### Action Items

- [ ] Open `server.py` and examine the upload endpoint
- [ ] List all column names referenced in the code
- [ ] Ask your boss: “Can you send me an example of the Excel template that normally works?”
- [ ] Get the problematic CSV file to analyze

-----

## Step 2: Document the Expected Format

Create a reference document showing the expected schema:

```python
# Expected columns (update with actual columns from your analysis)
EXPECTED_COLUMNS = {
    'Address': 'Full street address',
    'City': 'City name',
    'State': 'Two-letter state code',
    'Zip': 'ZIP code',
    'PropertyType': 'Type of property',
    'Units': 'Number of units',
    # Add more as you discover them
}

REQUIRED_COLUMNS = ['Address', 'City', 'State']  # Columns that MUST be present
OPTIONAL_COLUMNS = ['Zip', 'PropertyType', 'Units']  # Nice to have
```

-----

## Step 3: Create the Column Mapping System

### Create New File: `market_analysis_automation/utils/file_parser.py`

```python
import pandas as pd
from typing import Dict, Optional, Tuple, List
import io
import logging

logger = logging.getLogger(__name__)


class FileParser:
    """Handle different file formats and column mappings"""
    
    # Define what columns we need and common variations
    # UPDATE THIS based on what you find in Step 1
    COLUMN_MAPPINGS = {
        'Address': ['address', 'street_address', 'street', 'addr', 'location', 'property_address'],
        'City': ['city', 'town', 'municipality'],
        'State': ['state', 'st', 'province'],
        'Zip': ['zip', 'zipcode', 'zip_code', 'postal_code', 'postal'],
        'PropertyType': ['property_type', 'type', 'propertytype', 'asset_type'],
        'Units': ['units', 'unit_count', 'number_of_units', 'total_units'],
        # Add more mappings as you discover what columns are needed
    }
    
    @staticmethod
    def read_file(file_contents: bytes, filename: str) -> pd.DataFrame:
        """
        Read Excel or CSV file.
        
        Args:
            file_contents: Raw file bytes
            filename: Original filename (used to determine format)
            
        Returns:
            pandas DataFrame with file contents
            
        Raises:
            ValueError: If file format is unsupported
        """
        try:
            if filename.endswith('.csv'):
                # CSV file - try different encodings if needed
                try:
                    df = pd.read_csv(io.BytesIO(file_contents))
                except UnicodeDecodeError:
                    # Try with different encoding
                    df = pd.read_csv(io.BytesIO(file_contents), encoding='latin-1')
                    
            elif filename.endswith(('.xlsx', '.xls')):
                # Excel file
                df = pd.read_excel(io.BytesIO(file_contents))
            else:
                raise ValueError(
                    f"Unsupported file format: {filename}. "
                    f"Supported formats: .csv, .xlsx, .xls"
                )
            
            logger.info(f"Successfully read {filename}: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise ValueError(f"Could not read file: {str(e)}")
    
    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Map different column names to standard names.
        
        Args:
            df: Input DataFrame with various column names
            
        Returns:
            DataFrame with standardized column names
        """
        # Create a lowercase version for case-insensitive matching
        df_lower = df.copy()
        df_lower.columns = [col.lower().strip() for col in df.columns]
        
        normalized_df = pd.DataFrame()
        mapping_log = {}
        
        for standard_name, possible_names in FileParser.COLUMN_MAPPINGS.items():
            found = False
            
            for possible_name in possible_names:
                if possible_name in df_lower.columns:
                    # Use the original dataframe's column
                    original_col = df.columns[df_lower.columns.tolist().index(possible_name)]
                    normalized_df[standard_name] = df[original_col]
                    mapping_log[standard_name] = original_col
                    found = True
                    break
            
            if not found:
                # Column not found - set to None (will be caught in validation)
                normalized_df[standard_name] = None
                mapping_log[standard_name] = "NOT FOUND"
        
        logger.info(f"Column mapping: {mapping_log}")
        return normalized_df
    
    @staticmethod
    def validate_required_columns(
        df: pd.DataFrame, 
        required_columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if all required columns are present and have data.
        
        Args:
            df: DataFrame to validate
            required_columns: List of column names that must be present
            
        Returns:
            Tuple of (is_valid, missing_columns)
        """
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(f"{col} (column not found)")
            elif df[col].isna().all():
                missing_columns.append(f"{col} (column is empty)")
        
        is_valid = len(missing_columns) == 0
        return is_valid, missing_columns
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean up common data issues.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Strip whitespace from string columns
        for col in df_clean.select_dtypes(include=['object']).columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].str.strip()
        
        # Remove duplicate rows
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed_dupes = initial_rows - len(df_clean)
        
        if removed_dupes > 0:
            logger.info(f"Removed {removed_dupes} duplicate rows")
        
        return df_clean
    
    @staticmethod
    def standardize_state_codes(
        df: pd.DataFrame, 
        state_column: str = 'State'
    ) -> pd.DataFrame:
        """
        Convert state names to 2-letter codes.
        
        Args:
            df: DataFrame with state column
            state_column: Name of the state column
            
        Returns:
            DataFrame with standardized state codes
        """
        state_map = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
            'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
            'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
            'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
            'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
            'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
            'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
            'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
            'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
            'wisconsin': 'WI', 'wyoming': 'WY'
        }
        
        if state_column in df.columns:
            df[state_column] = df[state_column].apply(
                lambda x: state_map.get(str(x).lower(), str(x).upper()[:2]) 
                if pd.notna(x) else x
            )
        
        return df
```

-----

## Step 4: Update the Upload Endpoint

### Modify `server.py`

**Before (current restrictive code):**

```python
@app.post("/submarket-mappings", response_model=SubmarketMappingFeatureCollection)
async def get_submarket_mappings(file: UploadFile = File(...)):
    # Only accepts Excel
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    file_contents = await file.read()
    df = pd.read_excel(io.BytesIO(file_contents))
    # ... rest of processing
```

**After (flexible version):**

```python
from market_analysis_automation.utils.file_parser import FileParser

@app.post("/submarket-mappings", response_model=SubmarketMappingFeatureCollection)
async def get_submarket_mappings(file: UploadFile = File(...)):
    """
    Upload a file containing property addresses for analysis.
    Supports both Excel (.xlsx, .xls) and CSV (.csv) formats.
    Column names are automatically mapped to expected format.
    """
    try:
        # Read file contents
        file_contents = await file.read()
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Parse file (supports CSV and Excel)
        df = FileParser.read_file(file_contents, file.filename)
        logger.info(f"Read file with {len(df)} rows and columns: {df.columns.tolist()}")
        
        # Clean the data
        df = FileParser.clean_dataframe(df)
        logger.info(f"After cleaning: {len(df)} rows")
        
        # Normalize column names
        df = FileParser.normalize_columns(df)
        logger.info(f"Normalized columns to: {df.columns.tolist()}")
        
        # Standardize state codes
        df = FileParser.standardize_state_codes(df)
        
        # Validate required columns are present
        # UPDATE THIS list based on what you found in Step 1
        required_columns = ['Address', 'City', 'State']
        is_valid, missing = FileParser.validate_required_columns(df, required_columns)
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing)}. "
                       f"Please ensure your file contains these data fields."
            )
        
        logger.info(f"Validation passed. Processing {len(df)} addresses.")
        
        # Continue with existing processing
        # The rest of the code stays the same because df now has the right column names
        # ... existing logic ...
        
    except ValueError as e:
        # File reading/format errors
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )
```

-----

## Step 5: Add Helper Endpoint for Testing

### Create Column Analysis Endpoint

Add this new endpoint to `server.py` (in the routers section):

```python
@app.post("/analyze-file-columns")
async def analyze_file_columns(file: UploadFile = File(...)):
    """
    Analyze uploaded file and show what columns it has vs what we expect.
    Useful for debugging column mapping issues before running full analysis.
    
    Returns:
        - Original column names found in file
        - How columns will be mapped to standard names
        - Sample data from each column
        - Whether required columns will be satisfied
    """
    file_contents = await file.read()
    
    try:
        # Read the file
        df = FileParser.read_file(file_contents, file.filename)
        found_columns = df.columns.tolist()
        
        # Clean the data
        df = FileParser.clean_dataframe(df)
        
        # Normalize columns
        normalized_df = FileParser.normalize_columns(df)
        
        # Analyze the mapping
        mapping_results = {}
        for standard_name in FileParser.COLUMN_MAPPINGS.keys():
            if standard_name in normalized_df.columns and not normalized_df[standard_name].isna().all():
                # Find which original column was used
                mapped_from = None
                for orig_col in found_columns:
                    if orig_col in df.columns and df[orig_col].equals(normalized_df[standard_name]):
                        mapped_from = orig_col
                        break
                
                mapping_results[standard_name] = {
                    "found": True,
                    "mapped_from": mapped_from,
                    "sample_values": normalized_df[standard_name].head(3).tolist(),
                    "non_null_count": normalized_df[standard_name].notna().sum()
                }
            else:
                mapping_results[standard_name] = {
                    "found": False,
                    "mapped_from": None,
                    "sample_values": [],
                    "non_null_count": 0
                }
        
        # Check required columns
        required_columns = ['Address', 'City', 'State']  # Update based on Step 1
        is_valid, missing = FileParser.validate_required_columns(
            normalized_df, 
            required_columns
        )
        
        return {
            "filename": file.filename,
            "total_rows": len(df),
            "rows_after_cleaning": len(df),
            "original_columns": found_columns,
            "mapping_results": mapping_results,
            "validation": {
                "is_valid": is_valid,
                "missing_required": missing,
                "required_columns": required_columns
            },
            "message": "✅ File is ready for analysis" if is_valid else "❌ File is missing required columns",
            "next_steps": "Upload this file to /submarket-mappings to run full analysis" if is_valid else "Add the missing columns to your file and try again"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error analyzing file: {str(e)}"
        )
```

-----

## Step 6: Testing Strategy

### Test 1: Analyze the Problematic CSV

```bash
# Use the /analyze-file-columns endpoint first
curl -X POST "http://localhost:8000/analyze-file-columns" \
  -F "file=@problematic_file.csv"
```

**Expected Output:**

```json
{
  "filename": "problematic_file.csv",
  "total_rows": 150,
  "original_columns": ["street_address", "city_name", "state_code"],
  "mapping_results": {
    "Address": {
      "found": true,
      "mapped_from": "street_address",
      "sample_values": ["123 Main St", "456 Oak Ave", "789 Pine Rd"]
    },
    "City": {
      "found": true,
      "mapped_from": "city_name",
      "sample_values": ["Chicago", "Boston", "Seattle"]
    }
  },
  "validation": {
    "is_valid": true,
    "missing_required": []
  }
}
```

### Test 2: Update Column Mappings

If columns don’t map automatically:

```python
# In file_parser.py, add the missing column names
COLUMN_MAPPINGS = {
    'Address': [
        'address', 
        'street_address',
        'street_address',  # ← Add what the CSV actually has
        # ... rest
    ],
}
```

### Test 3: Run Full Analysis

```bash
# Now try the actual analysis endpoint
curl -X POST "http://localhost:8000/submarket-mappings" \
  -F "file=@problematic_file.csv"
```

### Test 4: Edge Cases

Create test files for:

- CSV with extra columns (should ignore them)
- CSV with columns in different order (should work)
- Excel file (should still work)
- File with empty rows (should clean them)
- File with state names instead of codes (should convert)
- File with whitespace in cells (should trim)

-----

## Step 7: Add User Documentation

### Create: `docs/FILE_UPLOAD_GUIDE.md`

```markdown
# File Upload Guide

## Supported Formats
- Excel (.xlsx, .xls)
- CSV (.csv)

## Required Columns

Your file must contain these data points (column names can vary):

### Address Information (Required)
- **Address/Street/Location**: Full street address
- **City/Town**: City name
- **State/Province**: Two-letter state code (or full state name)

### Property Details (Optional but recommended)
- **Property Type**: Type of property (Apartment, Senior Housing, etc.)
- **Units/Unit Count**: Number of units
- **Zip/Postal Code**: ZIP code

## Column Name Flexibility

The system automatically recognizes common variations:

| Standard Name | Accepted Variations |
|--------------|---------------------|
| Address | address, street_address, street, addr, location, property_address |
| City | city, town, municipality |
| State | state, st, province |
| Zip | zip, zipcode, zip_code, postal_code, postal |
| PropertyType | property_type, type, propertytype, asset_type |
| Units | units, unit_count, number_of_units, total_units |

## Testing Your File

Before running a full analysis, test if your file will work:

### 1. Check Column Mapping
```bash
POST /analyze-file-columns
```

This shows:

- What columns were found
- How they’ll be mapped
- Sample data
- Whether required columns are present

### 2. Review Results

Look for:

- ✅ All required columns found
- ✅ Sample values look correct
- ❌ Missing columns → Add them to your file

### 3. Run Analysis

```bash
POST /submarket-mappings
```

## Common Issues

### “Missing required columns: Address”

**Problem:** No address column found  
**Solution:**

- Add a column with address data
- Name it “Address” or “street_address” or similar

### “Invalid file format”

**Problem:** Unsupported file type  
**Solution:** Convert to .csv, .xlsx, or .xls

### “Error reading file”

**Problem:** File is corrupted or has encoding issues  
**Solution:**

- Open and re-save the file
- For CSV: try saving with UTF-8 encoding

### “File is missing required columns”

**Problem:** Required data fields not found  
**Solution:** Use `/analyze-file-columns` to see what’s missing

## Tips for Success

1. **Use clear column names**: “Address” is better than “Col1”
1. **One property per row**: Don’t merge rows
1. **No empty rows**: Delete blank rows in your spreadsheet
1. **State codes**: Use “IL” not “Illinois” (but both work!)
1. **Test first**: Use the analyze endpoint before running full analysis

## Example Files

### Good CSV Format:

```csv
Address,City,State,Zip,PropertyType,Units
123 Main St,Chicago,IL,60601,Apartment,150
456 Oak Ave,Boston,MA,02101,Senior Housing,80
```

### Also Works:

```csv
street_address,city_name,state_code,property_type,unit_count
123 Main St,Chicago,IL,Apartment,150
456 Oak Ave,Boston,MA,Senior Housing,80
```

Both formats will be automatically mapped to the correct columns!

```
---

## Step 8: Create Unit Tests (Optional but Recommended)

### Create: `tests/test_file_parser.py`

```python
import pytest
import pandas as pd
from market_analysis_automation.utils.file_parser import FileParser


class TestFileParser:
    
    def test_normalize_columns_standard_names(self):
        """Test with already standard column names"""
        df = pd.DataFrame({
            'Address': ['123 Main St'],
            'City': ['Chicago'],
            'State': ['IL']
        })
        
        result = FileParser.normalize_columns(df)
        assert 'Address' in result.columns
        assert 'City' in result.columns
        assert 'State' in result.columns
    
    def test_normalize_columns_variations(self):
        """Test with different column name variations"""
        df = pd.DataFrame({
            'street_address': ['123 Main St'],
            'city_name': ['Chicago'],
            'state_code': ['IL']
        })
        
        result = FileParser.normalize_columns(df)
        assert 'Address' in result.columns
        assert 'City' in result.columns
        assert 'State' in result.columns
        assert result['Address'].iloc[0] == '123 Main St'
    
    def test_normalize_columns_case_insensitive(self):
        """Test case-insensitive matching"""
        df = pd.DataFrame({
            'ADDRESS': ['123 Main St'],
            'CITY': ['Chicago']
        })
        
        result = FileParser.normalize_columns(df)
        assert 'Address' in result.columns
        assert 'City' in result.columns
    
    def test_validate_required_columns_success(self):
        """Test validation with all required columns present"""
        df = pd.DataFrame({
            'Address': ['123 Main St'],
            'City': ['Chicago'],
            'State': ['IL']
        })
        
        is_valid, missing = FileParser.validate_required_columns(
            df, 
            ['Address', 'City', 'State']
        )
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_required_columns_missing(self):
        """Test validation with missing columns"""
        df = pd.DataFrame({
            'Address': ['123 Main St'],
            'City': ['Chicago']
        })
        
        is_valid, missing = FileParser.validate_required_columns(
            df, 
            ['Address', 'City', 'State']
        )
        
        assert is_valid is False
        assert 'State' in str(missing)
    
    def test_clean_dataframe_removes_empty_rows(self):
        """Test that empty rows are removed"""
        df = pd.DataFrame({
            'Address': ['123 Main St', None, '456 Oak Ave'],
            'City': ['Chicago', None, 'Boston']
        })
        
        result = FileParser.clean_dataframe(df)
        assert len(result) == 2  # Empty row removed
    
    def test_clean_dataframe_strips_whitespace(self):
        """Test that whitespace is trimmed"""
        df = pd.DataFrame({
            'Address': ['  123 Main St  '],
            'City': [' Chicago ']
        })
        
        result = FileParser.clean_dataframe(df)
        assert result['Address'].iloc[0] == '123 Main St'
        assert result['City'].iloc[0] == 'Chicago'
    
    def test_standardize_state_codes(self):
        """Test state name to code conversion"""
        df = pd.DataFrame({
            'State': ['Illinois', 'Massachusetts', 'TX']
        })
        
        result = FileParser.standardize_state_codes(df)
        assert result['State'].iloc[0] == 'IL'
        assert result['State'].iloc[1] == 'MA'
        assert result['State'].iloc[2] == 'TX'
```

### Run tests:

```bash
pytest tests/test_file_parser.py -v
```

-----

## Implementation Checklist

### Day 1 Morning (2-3 hours)

- [ ] Find current upload endpoint in `server.py`
- [ ] Document expected columns
- [ ] Get problematic CSV from boss
- [ ] Analyze differences between CSV and expected format

### Day 1 Afternoon (3-4 hours)

- [ ] Create `market_analysis_automation/utils/file_parser.py`
- [ ] Implement `read_file()` method
- [ ] Implement `normalize_columns()` method
- [ ] Add column mappings for the specific CSV

### Day 2 Morning (2-3 hours)

- [ ] Update upload endpoint in `server.py`
- [ ] Add `/analyze-file-columns` helper endpoint
- [ ] Test with boss’s CSV file
- [ ] Verify it works end-to-end

### Day 2 Afternoon (2-3 hours)

- [ ] Add data cleaning methods
- [ ] Add state code standardization
- [ ] Write user documentation
- [ ] Create demo for your boss
- [ ] (Optional) Write unit tests

-----

## Questions to Ask Your Boss

Before starting implementation:

1. **“Can you send me both the Excel template that works AND the CSV that doesn’t?”**
- Need to see both formats
1. **“Are there specific columns that are absolutely required for the analysis?”**
- Determines validation logic
1. **“Should I support any other file formats while I’m at it?”**
- JSON? TSV? Other formats?
1. **“If a column is missing, should I reject the file or try to continue without it?”**
- Determines error handling strategy
1. **“Do you want me to add this to the API documentation?”**
- User communication plan

-----

## Demo Script for Your Boss

When presenting your solution:

### 1. Show the Problem

```
"Here's the CSV you gave me. It has these columns: [list them]
The current system expects these columns: [list them]
That's why it fails."
```

### 2. Show the Analysis Tool

```
"I built a preview tool. Watch what happens when I upload the CSV..."
[Show /analyze-file-columns output]
"See? It automatically figured out that 'street_address' maps to 'Address'."
```

### 3. Show It Working

```
"Now let me run the actual analysis with the same CSV..."
[Upload to /submarket-mappings]
"It works! The system now accepts both formats."
```

### 4. Show the Flexibility

```
"The best part: it's flexible. If someone sends a file with 'addr' or 'location' instead of 'address', it'll still work. I added mappings for all common variations."
```

### 5. Show the Documentation

```
"I also wrote a guide for users explaining what file formats work and how to test their files before uploading."
```

-----

## Troubleshooting Guide

### Issue: Column not mapping correctly

**Symptom:** `/analyze-file-columns` shows column as “NOT FOUND”

**Solution:**

1. Check the actual column name in the CSV
1. Add it to `COLUMN_MAPPINGS` in `file_parser.py`
1. Restart the server
1. Test again

### Issue: Encoding errors when reading CSV

**Symptom:** `UnicodeDecodeError` when reading file

**Solution:**
Already handled in `read_file()` method with fallback to ‘latin-1’ encoding

### Issue: Empty columns after normalization

**Symptom:** Columns exist but all values are NaN

**Solution:**

1. Check if original column actually has data
1. Use `clean_dataframe()` to remove empty rows
1. Add better validation messages

### Issue: State codes not converting

**Symptom:** State names still present after standardization

**Solution:**

1. Check `state_map` has all needed states
1. Verify state column name matches
1. Check for typos in state names

-----

## Future Enhancements

After this is working, consider:

1. **Auto-detect delimiters**: Handle TSV, pipe-delimited files
1. **Column suggestions**: “Did you mean ‘Address’?” for close matches
1. **Fuzzy matching**: Handle typos in column names
1. **Data validation**: Check ZIP codes are valid, states are real
1. **File templates**: Generate downloadable templates for users
1. **Batch processing**: Upload multiple files at once
1. **Background processing**: Handle large files asynchronously

-----

## Success Metrics

You’ll know this is successful when:

✅ The CSV your boss provided works without modification  
✅ The existing Excel template still works  
✅ Users can upload files with different column names  
✅ Clear error messages when files are invalid  
✅ No more manual column renaming required

-----

## Summary

This implementation provides:

1. **Flexibility**: Accepts CSV and Excel with various column names
1. **Validation**: Clear feedback about what’s missing
1. **User-friendly**: Preview endpoint to test files
1. **Maintainable**: Easy to add new column mappings
1. **Robust**: Handles common data issues automatically

**Estimated total time: 1.5-2 days**

This is a perfect first-week project that solves a real problem, demonstrates your skills, and doesn’t require refactoring the entire application.

-----

## Additional Resources

- [pandas read_csv documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [pandas read_excel documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [pandas DataFrame operations](https://pandas.pydata.org/docs/reference/frame.html)