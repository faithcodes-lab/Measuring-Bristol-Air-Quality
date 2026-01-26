import csv
import zipfile
import io
from datetime import datetime

ZIP_FILE = 'cropped.zip' 
CSV_NAME_IN_ZIP = 'cleansed.csv'
OUTPUT_SAMPLE_FILE = 'sample_station_452.csv'
TARGET_SITE_ID = '452'  # AURN St Pauls

STATION_FILE = 'station.csv'
CONSTITUENCY_FILE = 'constituency.csv'
print(f"Extracting and converting sample data for Station {TARGET_SITE_ID}...")


# constituency_id → constituency_name
constituency_lookup = {}
with open(CONSTITUENCY_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        constituency_lookup[row['constituency_id']] = row['constituency_name']

# site_id → (station_name, constituency_name)
station_lookup = {}
with open(STATION_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sid = row['station_id']
        station_name = row['station_name']
        constituency_name = constituency_lookup.get(row['constituency_id'], "")
        station_lookup[sid] = (station_name, constituency_name)

try:
    with open(OUTPUT_SAMPLE_FILE, 'w', newline='', encoding='utf-8') as outfile:
        csv_writer = csv.writer(outfile)
        
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            with zf.open(CSV_NAME_IN_ZIP, 'r') as infile:
                infile_text = io.TextIOWrapper(infile, encoding='utf-8-sig')
                csv_reader = csv.reader(infile_text)
                header = next(csv_reader)
                
                # 1. Find Column Indices
                try:
                    site_id_idx = header.index('Site_ID')
                    date_idx = header.index('Date_Time')

                    # 2. Read Header
                    header[site_id_idx:site_id_idx] = ["station_name", "constituency_name"]
                    csv_writer.writerow(header)
                except ValueError:
                    print("Error: Required columns not found.")
                    exit()
                
                # 3. Stream, Filter, and Convert
                count = 0
                for row in csv_reader:
                    # Filter for 'AURN St Pauls' station
                    if row[site_id_idx].strip().split('.')[0] == TARGET_SITE_ID:

                        #lookup station and constituency names
                        station_name, constituency_name = station_lookup.get(
                            TARGET_SITE_ID, ("", "")
                        )

                        try:
                            # Parse original format: 2015/01/01 00:00:00
                            dt = datetime.strptime(row[date_idx], '%Y-%m-%d %H:%M:%S')
                            
                            # In class, we were given guidance to save date time as unix timestamp.
                            # QuestDB supports unix timestamps but store it as 64-bit integers 
                            # representing micro seconds unlike mysql that stores it as seconds.
                            # For this reason, I am doing the conversion to micro seconds. 
                            # timestamp() gives seconds (float), * 1,000,000 -> microseconds
                            
                            micros = int(dt.timestamp() * 1_000_000)
                            
                            row[date_idx] = micros

                            # 10 Dec 2025 — Lecture Guidance:
                            # We were advised that in NoSQL design, constituency and station details
                            # should be included within the readings document/table (denormalised model).
                            # This update reflects that guidance by embedding Station_Name and Constituency_Name.

                        
                            row[site_id_idx:site_id_idx] = [station_name, constituency_name]
                            csv_writer.writerow(row)
                            count += 1
                        except ValueError:
                            continue # Skip bad dates
                        
    print(f"Success. Wrote {count} rows to {OUTPUT_SAMPLE_FILE}")
    print("Dates converted to QuestDB-compatible Unix Microseconds.")

except FileNotFoundError:
    print(f"Error: Could not find {ZIP_FILE}. Run this next to your cropped data.")
except Exception as e:
    print(f"An error occurred: {e}")