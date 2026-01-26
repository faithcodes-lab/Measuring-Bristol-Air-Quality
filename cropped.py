import pandas as pd
import zipfile
import io

INPUT_FILE = 'Air_Quality_Continuous.csv'
OUTPUT_ZIP = 'cropped.zip'
FILE_CROPPED = 'cropped.csv'
FILE_CLEANSED = 'cleansed.csv'

# Dates
START_DATE = pd.Timestamp('2015-01-01')
END_DATE = pd.Timestamp('2023-10-22')

# Columns
METRIC_COLS = ['NOx', 'NO2', 'NO', 'PM10', 'O3', 'NVPM10', 'VPM10', 
               'NVPM2_5', 'PM2_5', 'VPM2_5', 'CO', 'RH', 'Pressure', 'SO2']

def process_data():
    print(f"Loading {INPUT_FILE} into memory (this may take a moment)...")
    
    # Load Data
    # low_memory=False avoids mixed-type warnings on large files
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Total rows loaded: {len(df)}")

    # Parse Dates
    # coerce=True turns bad dates into NaT (Not a Time) automatically
    df['Date_Time'] = pd.to_datetime(df['Date_Time'], errors='coerce')
    
    # Remove timezone (+00:00) 
    df['Date_Time'] = df['Date_Time'].dt.tz_localize(None)

    # I am dropping rows where Date_Time parsing failed
    df = df.dropna(subset=['Date_Time'])

    # Create 'Cropped' Dataset (Start Date Filter Only)
    # Filter: >= Jan 1 2015

    df_cropped = df[df['Date_Time'] >= START_DATE].copy()
    
    print(f"Rows after 2015 start filter: {len(df_cropped)}")

    # Create 'Cleansed' Dataset
    # Start with the cropped data and apply further filters
    df_clean = df_cropped.copy()

    # A. End Date Filter
    df_clean = df_clean[
    (df_clean['Date_Time'] >= START_DATE) &
    (df_clean['Date_Time'] <= END_DATE)]

    #df_clean = df_clean[df_clean['Date_Time'] <= END_DATE]

    # B. Key Validation (Drop rows missing ID or Site)
    # subset checks only specific columns for NaN
    df_clean = df_clean.dropna(subset=['Site_ID', 'ObjectId2'])

    # C. Deduplication
    # Convert ID to numeric first to handle "123" vs "123.0" mismatch
    df_clean['ObjectId2'] = pd.to_numeric(df_clean['ObjectId2'], errors='coerce')

    # Drop invalid IDs (NaNs created by to_numeric)
    df_clean = df_clean.dropna(subset=['ObjectId2'])

    # Remove duplicates based on ID
    initial_count = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['ObjectId2'])
    print(f"Duplicates removed: {initial_count - len(df_clean)}")

    # D. Metric Sanitisation (Negatives/Inf)
    for col in METRIC_COLS:
        # Convert column to numeric (coerces strings to NaN)
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Filter: Keep only values >= 0 (or NaNs)
        # Replace negative values with NaN (which acts as NULL)
        df_clean.loc[df_clean[col] < 0, col] = pd.NA

    # Temperature Sanitisation (Allow negative, remove bad strings)
    df_clean['Temperature'] = pd.to_numeric(df_clean['Temperature'], errors='coerce')

    print(f"Final cleansed rows: {len(df_clean)}")
    print("Writing to ZIP file...")
    try:
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write Cropped
            with io.StringIO() as buffer:
                df_cropped.to_csv(buffer, index=False)
                zf.writestr(FILE_CROPPED, buffer.getvalue())
            
            # Write Cleansed
            with io.StringIO() as buffer:
                df_clean.to_csv(buffer, index=False)
                zf.writestr(FILE_CLEANSED, buffer.getvalue())
                
        print(f"Successfully created {OUTPUT_ZIP}")
        
    except Exception as e:
        print(f"Error writing ZIP: {e}")

if __name__ == "__main__":
    process_data()