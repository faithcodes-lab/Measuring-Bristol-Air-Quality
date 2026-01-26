import csv
import zipfile
import io
import math
import urllib.parse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- CONFIGURATION ---
PASSWORD = urllib.parse.quote_plus("")
DB_CONNECTION_STRING = f'mysql+mysqlconnector://root:{PASSWORD}@localhost/pollution_db'

# File Names
ZIP_FILE = 'cropped.zip'
CSV_NAME_IN_ZIP = 'cleansed.csv'
SKIPPED_FILE_NAME = 'import_skipped.csv' #logs rows that failed to import, empty file means all rows imported successfully.

# Reference CSVs
CONSTITUENCY_FILE = 'constituency.csv'
STATION_FILE = 'station.csv'
SCHEMA_FILE = 'data_schema.csv'

BATCH_SIZE = 1000

# --- COLUMN MAPPINGS (Matches your SQL Schema) ---
DB_MAPPING = {
    'Constituency': {
        'constituency_id': 'Constituency_ID',
        'constituency_name': 'Constituency_Name',
        'mp_name': 'MP_Name'
    },
    'Station': {
        'station_id': 'Site_ID',
        'station_name': 'Station_Name',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'constituency_id': 'Constituency_ID'
    },
    'Data_Schema': {
        'measure': 'Reading',
        'description': 'Description',
        'unit': 'Unit'
    }
}

# Reading Table Columns
READING_COLUMNS = [
    'Date_Time', 'Site_ID', 'NOx', 'NO2', 'NO', 'PM10', 'O3', 'Temperature',
    'ObjectId', 'ObjectId2', 'NVPM10', 'VPM10', 'NVPM2_5', 'PM2_5', 'VPM2_5',
    'CO', 'RH', 'Pressure', 'SO2'
]

def get_column_indices(header):
    indices = {}
    for col_name in READING_COLUMNS:
        if col_name in header:
            indices[col_name] = header.index(col_name)
    return indices

# --- CLEANING FUNCTIONS ---
def clean_metric(val):
    try:
        f = float(val)
        if not math.isfinite(f) or f < 0: return None
        return f
    except (ValueError, TypeError): return None

def clean_temp(val):
    try:
        f = float(val)
        if not math.isfinite(f): return None
        return f
    except (ValueError, TypeError): return None

def clean_int(val):
    try:
        f = float(val)
        if not math.isfinite(f): return None
        return int(f)
    except (ValueError, TypeError, OverflowError): return None

def process_reading_row(row, indices):
    """
    Parses a row from cleansed.csv into the 'Reading' table format.
    Handles date format mismatches (YYYY/MM/DD vs YYYY-MM-DD).
    """
    try:
        if not row[indices['ObjectId2']] or not row[indices['Site_ID']]:
            return "SKIP_ROW_BAD_KEY"
        
        # --- FIX: HANDLE DATE FORMAT VARIATIONS ---
        raw_date = row[indices['Date_Time']]
        
        # Normalize date: Replace '/' with '-' and remove timezone '+00' if present
        # Converts '2019/04/29 23:00:00+00' -> '2019-04-29 23:00:00'
        clean_date_str = raw_date.replace('/', '-').split('+')[0].strip()
        
        dt_obj = datetime.strptime(clean_date_str, '%Y-%m-%d %H:%M:%S')
        unix_ts = int(dt_obj.timestamp())
        
        return {
            'Reading_ID':   clean_int(row[indices['ObjectId2']]),
            'Site_ID':     clean_int(row[indices['Site_ID']]),
            'Date_Time':   unix_ts,
            'ObjectID':    clean_int(row[indices['ObjectId']]),
            'NOx':         clean_metric(row[indices['NOx']]),
            'NO2':         clean_metric(row[indices['NO2']]),
            'NO':          clean_metric(row[indices['NO']]),
            'PM10':        clean_metric(row[indices['PM10']]),
            'O3':          clean_metric(row[indices['O3']]),
            'Temperature': clean_temp(row[indices['Temperature']]),
            'NVPM10':      clean_metric(row[indices['NVPM10']]),
            'VPM10':       clean_metric(row[indices['VPM10']]),
            'NVPM2_5':     clean_metric(row[indices['NVPM2_5']]),
            'PM2_5':       clean_metric(row[indices['PM2_5']]),
            'VPM2_5':      clean_metric(row[indices['VPM2_5']]),
            'CO':          clean_metric(row[indices['CO']]),
            'RH':          clean_metric(row[indices['RH']]),
            'Pressure':    clean_metric(row[indices['Pressure']]),
            'SO2':         clean_metric(row[indices['SO2']])
        }
    except Exception as e:
        # I added the actual error message here so you can see it in the CSV if it fails again
        return f"SKIP_ROW_ERROR: {str(e)}"

# --- IMPORTERS ---

def import_csv_to_db(conn, file_path, table_name):
    print(f"--- Processing {file_path} into table '{table_name}' ---")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data_batch = []
            mapping = DB_MAPPING.get(table_name, {})
            
            for row in reader:
                record = {}
                
                # Special Case: Data_Schema needs 'Reading' column populated too
                if table_name == 'Data_Schema':
                     record['Ident'] = row['measure'].strip()      # PRIMARY KEY IN TABLE
                     record['Reading'] = row['measure'].strip()    # Reading name
                     record['Description'] = row['description'].strip()
                     record['Unit'] = row['unit'].strip()
                     
                     data_batch.append(record)
                     continue 
                
                for csv_header, db_col in mapping.items():
                    if csv_header in row:
                        val = row[csv_header].strip()
                        if '_id' in csv_header.lower() and val.isdigit():
                            val = int(val)
                        record[db_col] = val
                
                if record:
                    data_batch.append(record)
            
            if data_batch:
                # Generate SQL INSERT statement dynamically
                keys = data_batch[0].keys()
                cols = ', '.join(keys)
                params = ', '.join([f':{k}' for k in keys])
                
                stmt = text(f"INSERT INTO {table_name} ({cols}) VALUES ({params})")
                conn.execute(stmt, data_batch)
                print(f"Successfully inserted {len(data_batch)} rows into {table_name}.")
            else:
                print(f"Warning: No data found for {table_name}")

    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        # Re-raise exception to trigger rollback in main function
        raise e 

# --- MAIN EXECUTION ---
def import_data():
    engine = create_engine(DB_CONNECTION_STRING, echo=False)
    
    insert_reading_stmt = text("""
        INSERT INTO Reading (
            Reading_ID, Site_ID, Date_Time, ObjectID, NOx, NO2, NO, PM10, O3, 
            Temperature, NVPM10, VPM10, NVPM2_5, PM2_5, VPM2_5, CO, RH, Pressure, SO2
        ) VALUES (
            :Reading_ID, :Site_ID, :Date_Time, :ObjectID, :NOx, :NO2, :NO, :PM10, :O3, 
            :Temperature, :NVPM10, :VPM10, :NVPM2_5, :PM2_5, :VPM2_5, :CO, :RH, :Pressure, :SO2
        )
    """)

    try:
        print("Connecting to database...")
        with engine.connect() as conn:
            print("Connection successful.")
            
            # --- 1. Import Reference Tables ---
            trans = conn.begin_nested()
            try:
                import_csv_to_db(conn, CONSTITUENCY_FILE, 'Constituency')
                import_csv_to_db(conn, STATION_FILE, 'Station')
                import_csv_to_db(conn, SCHEMA_FILE, 'Data_Schema')
                trans.commit()
            except Exception as e:
                trans.rollback()
                print(f"CRITICAL ERROR importing reference tables: {e}")
                return

            print("\n--- Processing Main Readings ---")
            
            # --- 2. Import Readings ---
            data_batch = []
            raw_row_batch = []
            total_inserted = 0
            total_skipped = 0

            with open(SKIPPED_FILE_NAME, 'w', newline='', encoding='utf-8') as skip_file:
                skip_writer = csv.writer(skip_file)
                
                with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
                    with zf.open(CSV_NAME_IN_ZIP, 'r') as infile:
                        infile_text = io.TextIOWrapper(infile, encoding='utf-8-sig')
                        csv_reader = csv.reader(infile_text)
                        
                        header = next(csv_reader)
                        indices = get_column_indices(header)
                        skip_writer.writerow(header + ["ErrorMessage"])
                        
                        for row in csv_reader:
                            processed = process_reading_row(row, indices)
                            
                            if isinstance(processed, str):
                                total_skipped += 1
                                skip_writer.writerow(row + [processed])
                                continue
                            
                            data_batch.append(processed)
                            raw_row_batch.append(row)
                            
                            if len(data_batch) >= BATCH_SIZE:
                                total_inserted, total_skipped = process_batch(
                                    conn, insert_reading_stmt, data_batch, raw_row_batch, 
                                    skip_writer, total_inserted, total_skipped
                                )
                                data_batch = []
                                raw_row_batch = []
                                
                                if total_inserted % (BATCH_SIZE * 20) == 0:
                                    print(f"  ...processed {total_inserted} rows...")
                        
                        if data_batch:
                            total_inserted, total_skipped = process_batch(
                                conn, insert_reading_stmt, data_batch, raw_row_batch, 
                                skip_writer, total_inserted, total_skipped
                            )
            
            conn.commit()
            print(f"\nImport complete! Total Inserted: {total_inserted}, Skipped: {total_skipped}")

    except SQLAlchemyError as e:
        print(f"\n--- DATABASE ERROR ---")
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def process_batch(conn, stmt, data_batch, raw_row_batch, skip_writer, total_inserted, total_skipped):
    trans = conn.begin_nested()
    try:
        conn.execute(stmt, data_batch)
        trans.commit()
        return total_inserted + len(data_batch), total_skipped
    except SQLAlchemyError:
        trans.rollback()
        for i, record in enumerate(data_batch):
            try:
                conn.execute(stmt, [record])
                total_inserted += 1
            except SQLAlchemyError as e:
                total_skipped += 1
                # Log the specific database error (e.g., Foreign Key Constraint)
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                skip_writer.writerow(raw_row_batch[i] + [error_msg])
        return total_inserted, total_skipped

if __name__ == "__main__":
    import_data()