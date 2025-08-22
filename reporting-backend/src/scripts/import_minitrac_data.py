#!/usr/bin/env python3
"""
Import Minitrac historical equipment data from Excel to PostgreSQL
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime
import numpy as np

# Add parent directory to path to import our services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.postgres_service import PostgreSQLService

def create_minitrac_schema(conn):
    """Create the Minitrac tables in PostgreSQL"""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist (for clean reimport)
    cursor.execute("""
        DROP TABLE IF EXISTS minitrac_equipment CASCADE;
    """)
    
    # Create main equipment table with essential fields
    cursor.execute("""
        CREATE TABLE minitrac_equipment (
            id SERIAL PRIMARY KEY,
            unit_num VARCHAR(50) UNIQUE,
            category VARCHAR(50),
            grp VARCHAR(50),
            serial VARCHAR(100),
            make VARCHAR(100),
            model VARCHAR(100),
            year VARCHAR(20),
            unit_desc TEXT,
            div VARCHAR(50),
            type VARCHAR(50),
            status VARCHAR(50),
            
            -- Attachment info
            attach_to VARCHAR(50),
            num_attach VARCHAR(50),
            
            -- Options
            opt_1 VARCHAR(100),
            opt_2 VARCHAR(100),
            opt_3 VARCHAR(100),
            opt_4 VARCHAR(100),
            opt_5 VARCHAR(100),
            opt_6 VARCHAR(100),
            opt_7 VARCHAR(100),
            opt_8 VARCHAR(100),
            
            -- Rental rates (storing first 4 rate cycles)
            rate_cyc_1 VARCHAR(20),
            rate_amt_1 DECIMAL(12,2),
            rate_cyc_2 VARCHAR(20),
            rate_amt_2 DECIMAL(12,2),
            rate_cyc_3 VARCHAR(20),
            rate_amt_3 DECIMAL(12,2),
            rate_cyc_4 VARCHAR(20),
            rate_amt_4 DECIMAL(12,2),
            
            -- Contract info
            cont_div VARCHAR(50),
            cont_typ VARCHAR(50),
            cont_no VARCHAR(50),
            contr_stat VARCHAR(50),
            contr_rate DECIMAL(12,2),
            contr_cyc VARCHAR(20),
            contr_periods INTEGER,
            
            -- Customer info
            bill_cust VARCHAR(100),
            ship_cust VARCHAR(100),
            ship_name VARCHAR(200),
            ship_addr1 VARCHAR(200),
            ship_addr2 VARCHAR(200),
            ship_addr3 VARCHAR(200),
            ship_zip VARCHAR(20),
            
            -- Invoice info
            last_invc_div VARCHAR(50),
            last_invc_typ VARCHAR(50),
            last_invc_num VARCHAR(50),
            last_invc_date DATE,
            
            -- Key dates
            contr_date DATE,
            contr_from_date DATE,
            contr_thru_date DATE,
            check_out_date DATE,
            check_in_date DATE,
            purch_opt_date DATE,
            contr_review_date DATE,
            
            -- Asset info
            fixed_asset VARCHAR(50),
            acq_setup_date DATE,
            acq_date DATE,
            acq_cost DECIMAL(12,2),
            new_used VARCHAR(20),
            acq_source VARCHAR(100),
            unit_cost_gross DECIMAL(12,2),
            unit_cost_depr DECIMAL(12,2),
            net_book_val DECIMAL(12,2),
            as_of_date DATE,
            
            -- License info
            license_num VARCHAR(50),
            lic_effect_dt DATE,
            lic_exp_dt DATE,
            lic_review_dt DATE,
            license_fee DECIMAL(12,2),
            
            -- Meter readings
            meter_su_dt DATE,
            meter_su_read INTEGER,
            meter_su_src VARCHAR(50),
            meter_su_ref VARCHAR(50),
            last_meter_dt DATE,
            last_meter_read INTEGER,
            last_meter_src VARCHAR(50),
            last_meter_ref VARCHAR(50),
            curr_meter_dt DATE,
            curr_meter_read INTEGER,
            curr_meter_src VARCHAR(50),
            curr_meter_ref VARCHAR(50),
            
            -- Engine info
            eng_make VARCHAR(100),
            eng_model VARCHAR(100),
            eng_serial VARCHAR(100),
            eng_yr VARCHAR(20),
            eng_code VARCHAR(50),
            eng_type VARCHAR(50),
            eng_warranty VARCHAR(100),
            frame_no VARCHAR(100),
            
            -- Financial info
            mtd_income DECIMAL(12,2),
            mtd_expense DECIMAL(12,2),
            ytd_income DECIMAL(12,2),
            ytd_expense DECIMAL(12,2),
            atd_income DECIMAL(12,2),
            atd_expense DECIMAL(12,2),
            
            -- Insurance info
            insurance_req VARCHAR(50),
            insurance_carrier VARCHAR(100),
            insured_value DECIMAL(12,2),
            ins_from_dt DATE,
            ins_thru_dt DATE,
            ins_review_dt DATE,
            
            -- Warranty dates (OEM and Dealer)
            wty_oem1_from DATE,
            wty_oem1_thru DATE,
            wty_dlr1_from DATE,
            wty_dlr1_thru DATE,
            
            -- Market values
            mkt_amt1 DECIMAL(12,2),
            mkt_date1 DATE,
            mkt_amt2 DECIMAL(12,2),
            mkt_date2 DATE,
            
            -- Usage stats
            st0_numdays_mtd INTEGER,
            st1_numdays_mtd INTEGER,
            st2_numdays_mtd INTEGER,
            st0_numdays_ytd INTEGER,
            st1_numdays_ytd INTEGER,
            st2_numdays_ytd INTEGER,
            st0_numdays_atd INTEGER,
            st1_numdays_atd INTEGER,
            st2_numdays_atd INTEGER,
            
            -- Metadata
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_file VARCHAR(255)
        );
    """)
    
    # Create indexes for common search fields
    cursor.execute("""
        CREATE INDEX idx_minitrac_unit_num ON minitrac_equipment(unit_num);
        CREATE INDEX idx_minitrac_serial ON minitrac_equipment(serial);
        CREATE INDEX idx_minitrac_make ON minitrac_equipment(make);
        CREATE INDEX idx_minitrac_model ON minitrac_equipment(model);
        CREATE INDEX idx_minitrac_status ON minitrac_equipment(status);
        CREATE INDEX idx_minitrac_bill_cust ON minitrac_equipment(bill_cust);
        CREATE INDEX idx_minitrac_ship_cust ON minitrac_equipment(ship_cust);
        CREATE INDEX idx_minitrac_category ON minitrac_equipment(category);
        
        -- Full text search index
        CREATE INDEX idx_minitrac_search ON minitrac_equipment 
        USING gin(to_tsvector('english', 
            COALESCE(unit_num, '') || ' ' || 
            COALESCE(serial, '') || ' ' || 
            COALESCE(make, '') || ' ' || 
            COALESCE(model, '') || ' ' || 
            COALESCE(unit_desc, '') || ' ' ||
            COALESCE(ship_name, '')
        ));
    """)
    
    conn.commit()
    print("✓ Created minitrac_equipment table and indexes")

def parse_date(date_val):
    """Parse various date formats from Excel"""
    if pd.isna(date_val) or date_val == '' or date_val == 0:
        return None
    
    # If it's already a datetime object
    if isinstance(date_val, pd.Timestamp):
        return date_val.date()
    
    # If it's a numpy datetime64
    if isinstance(date_val, np.datetime64):
        return pd.Timestamp(date_val).date()
    
    # If it's a string, try to parse it
    if isinstance(date_val, str):
        try:
            return pd.to_datetime(date_val).date()
        except:
            return None
    
    # If it's a number (Excel date serial number)
    if isinstance(date_val, (int, float)):
        try:
            # Excel dates start from 1900-01-01
            return pd.to_datetime('1900-01-01') + pd.Timedelta(days=int(date_val) - 2)
        except:
            return None
    
    return None

def parse_decimal(val):
    """Parse decimal values, handling various formats"""
    if pd.isna(val) or val == '' or val == 'N/A':
        return None
    try:
        return float(val)
    except:
        return None

def parse_int(val):
    """Parse integer values"""
    if pd.isna(val) or val == '' or val == 'N/A':
        return None
    try:
        return int(float(val))
    except:
        return None

def import_data(excel_file, conn):
    """Import data from Excel file to PostgreSQL"""
    print(f"Reading Excel file: {excel_file}")
    df = pd.read_excel(excel_file)
    print(f"✓ Loaded {len(df)} records from Excel")
    
    cursor = conn.cursor()
    
    # Prepare data for insertion
    records = []
    for _, row in df.iterrows():
        record = (
            row.get('UNIT_NUM'),
            row.get('CATEGORY'),
            row.get('Grp'),
            row.get('SERIAL'),
            row.get('MAKE'),
            row.get('MODEL'),
            str(row.get('YEAR')) if pd.notna(row.get('YEAR')) else None,
            row.get('UNIT_DESC'),
            row.get('Div'),
            row.get('TYPE'),
            row.get('Status'),
            row.get('ATTACH_TO'),
            row.get('NUM_ATTACH'),
            row.get('OPT_1'),
            row.get('OPT_2'),
            row.get('OPT_3'),
            row.get('OPT_4'),
            row.get('OPT_5'),
            row.get('OPT_6'),
            row.get('OPT_7'),
            row.get('OPT_8'),
            row.get('RATE_CYC_1'),
            parse_decimal(row.get('RATE_AMT_1')),
            row.get('RATE_CYC_2'),
            parse_decimal(row.get('RATE_AMT_2')),
            row.get('RATE_CYC_3'),
            parse_decimal(row.get('RATE_AMT_3')),
            row.get('RATE_CYC_4'),
            parse_decimal(row.get('RATE_AMT_4')),
            row.get('ContDiv'),
            row.get('ContTyp'),
            row.get('ContNo'),
            row.get('CONTR_STAT'),
            parse_decimal(row.get('CONTR_RATE')),
            row.get('CONTR_CYC'),
            parse_int(row.get('CONTR_PERIODS')),
            row.get('BILL_CUST'),
            row.get('SHIP_CUST'),
            row.get('SHIP_NAME'),
            row.get('SHIP_ADDR1'),
            row.get('SHIP_ADDR2'),
            row.get('SHIP_ADDR3'),
            row.get('SHIP_ZIP'),
            row.get('Last_Invc_Div'),
            row.get('Last_Invc_Typ'),
            row.get('Last_Invc_Num'),
            parse_date(row.get('Last_Invc_Date')),
            parse_date(row.get('Contr_Date')),
            parse_date(row.get('Contr_From_Date')),
            parse_date(row.get('Contr_Thru_Date')),
            parse_date(row.get('Check_Out_Date')),
            parse_date(row.get('Check_In_Date')),
            parse_date(row.get('Purch_Opt_Date')),
            parse_date(row.get('Contr_Review_Date')),
            row.get('Fixed_Asset'),
            parse_date(row.get('Acq_Setup_Date')),
            parse_date(row.get('Acq_Date')),
            parse_decimal(row.get('Acq_Cost')),
            row.get('New_Used'),
            row.get('Acq_Source'),
            parse_decimal(row.get('Unit_Cost_Gross')),
            parse_decimal(row.get('Unit_Cost_Depr')),
            parse_decimal(row.get('Net_Book_Val')),
            parse_date(row.get('As_Of_Date')),
            row.get('License_Num'),
            parse_date(row.get('Lic_Effect_Dt')),
            parse_date(row.get('Lic_Exp_Dt')),
            parse_date(row.get('Lic_Review_Dt')),
            parse_decimal(row.get('License_Fee')),
            parse_date(row.get('Meter_SU_Dt')),
            parse_int(row.get('Meter_SU_Read')),
            row.get('Meter_SU_Src'),
            row.get('Meter_SU_Ref'),
            parse_date(row.get('Last_Meter_Dt')),
            parse_int(row.get('Last_Meter_Read')),
            row.get('Last_Meter_Src'),
            row.get('Last_Meter_Ref'),
            parse_date(row.get('Curr_Meter_Dt')),
            parse_int(row.get('Curr_Meter_Read')),
            row.get('Curr_Meter_Src'),
            row.get('Curr_Meter_Ref'),
            row.get('ENG_MAKE'),
            row.get('ENG_MODEL'),
            row.get('ENG_SERIAL'),
            str(row.get('Eng_Yr')) if pd.notna(row.get('Eng_Yr')) else None,
            row.get('ENG_CODE'),
            row.get('ENG_TYPE'),
            row.get('ENG_WARRANTY'),
            row.get('FRAME_NO'),
            parse_decimal(row.get('MTD_INCOME')),
            parse_decimal(row.get('MTD_EXPENSE')),
            parse_decimal(row.get('YTD_INCOME')),
            parse_decimal(row.get('YTD_EXPENSE')),
            parse_decimal(row.get('ATD_INCOME')),
            parse_decimal(row.get('ATD_EXPENSE')),
            row.get('Insurance_Req'),
            row.get('Insurance_Carrier'),
            parse_decimal(row.get('Insured_Value')),
            parse_date(row.get('Ins_From_Dt')),
            parse_date(row.get('Ins_Thru_Dt')),
            parse_date(row.get('Ins_Review_Dt')),
            parse_date(row.get('Wty_OEM1_From')),
            parse_date(row.get('Wty_OEM1_Thru')),
            parse_date(row.get('Wty_DLR1_From')),
            parse_date(row.get('Wty_DLR1_Thru')),
            parse_decimal(row.get('MKT_AMT1')),
            parse_date(row.get('MKT_DATE1')),
            parse_decimal(row.get('MKT_AMT2')),
            parse_date(row.get('MKT_DATE2')),
            parse_int(row.get('St0_NumDaysMTD')),
            parse_int(row.get('St1_NumDaysMTD')),
            parse_int(row.get('St2_NumDaysMTD')),
            parse_int(row.get('St0_NumDaysYTD')),
            parse_int(row.get('St1_NumDaysYTD')),
            parse_int(row.get('St2_NumDaysYTD')),
            parse_int(row.get('St0_NumDaysATD')),
            parse_int(row.get('St1_NumDaysATD')),
            parse_int(row.get('St2_NumDaysATD')),
            os.path.basename(excel_file)
        )
        records.append(record)
    
    # Insert data in batches
    insert_query = """
        INSERT INTO minitrac_equipment (
            unit_num, category, grp, serial, make, model, year, unit_desc, div, type, status,
            attach_to, num_attach, opt_1, opt_2, opt_3, opt_4, opt_5, opt_6, opt_7, opt_8,
            rate_cyc_1, rate_amt_1, rate_cyc_2, rate_amt_2, rate_cyc_3, rate_amt_3, rate_cyc_4, rate_amt_4,
            cont_div, cont_typ, cont_no, contr_stat, contr_rate, contr_cyc, contr_periods,
            bill_cust, ship_cust, ship_name, ship_addr1, ship_addr2, ship_addr3, ship_zip,
            last_invc_div, last_invc_typ, last_invc_num, last_invc_date,
            contr_date, contr_from_date, contr_thru_date, check_out_date, check_in_date,
            purch_opt_date, contr_review_date, fixed_asset, acq_setup_date, acq_date,
            acq_cost, new_used, acq_source, unit_cost_gross, unit_cost_depr, net_book_val, as_of_date,
            license_num, lic_effect_dt, lic_exp_dt, lic_review_dt, license_fee,
            meter_su_dt, meter_su_read, meter_su_src, meter_su_ref,
            last_meter_dt, last_meter_read, last_meter_src, last_meter_ref,
            curr_meter_dt, curr_meter_read, curr_meter_src, curr_meter_ref,
            eng_make, eng_model, eng_serial, eng_yr, eng_code, eng_type, eng_warranty, frame_no,
            mtd_income, mtd_expense, ytd_income, ytd_expense, atd_income, atd_expense,
            insurance_req, insurance_carrier, insured_value, ins_from_dt, ins_thru_dt, ins_review_dt,
            wty_oem1_from, wty_oem1_thru, wty_dlr1_from, wty_dlr1_thru,
            mkt_amt1, mkt_date1, mkt_amt2, mkt_date2,
            st0_numdays_mtd, st1_numdays_mtd, st2_numdays_mtd,
            st0_numdays_ytd, st1_numdays_ytd, st2_numdays_ytd,
            st0_numdays_atd, st1_numdays_atd, st2_numdays_atd,
            source_file
        ) VALUES %s
        ON CONFLICT (unit_num) DO UPDATE SET
            category = EXCLUDED.category,
            serial = EXCLUDED.serial,
            make = EXCLUDED.make,
            model = EXCLUDED.model,
            status = EXCLUDED.status,
            imported_at = CURRENT_TIMESTAMP
    """
    
    # Insert in batches of 1000
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        execute_values(cursor, insert_query, batch)
        print(f"✓ Imported {min(i + batch_size, len(records))}/{len(records)} records")
    
    conn.commit()
    print(f"✓ Successfully imported {len(records)} equipment records")

def main():
    """Main function to run the import"""
    excel_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'MTrEquipment250226.xlsx'
    )
    
    if not os.path.exists(excel_file):
        print(f"Error: Excel file not found at {excel_file}")
        sys.exit(1)
    
    try:
        # Get PostgreSQL service
        pg_service = PostgreSQLService()
        
        # Use connection from the service
        with pg_service.get_connection() as conn:
            if conn is None:
                print("Error: Could not establish PostgreSQL connection")
                print("Please ensure POSTGRES_URL or DATABASE_URL environment variable is set")
                sys.exit(1)
                
            # Create schema
            create_minitrac_schema(conn)
            
            # Import data
            import_data(excel_file, conn)
            
            # Verify import
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM minitrac_equipment")
            count = cursor.fetchone()[0]
            print(f"\n✓ Verification: {count} records in database")
            
            # Show sample data
            cursor.execute("""
                SELECT unit_num, serial, make, model, status, ship_name 
                FROM minitrac_equipment 
                WHERE ship_name IS NOT NULL 
                LIMIT 5
            """)
            print("\nSample imported data:")
            for row in cursor.fetchall():
                print(f"  Unit: {row[0]}, Serial: {row[1]}, Make: {row[2]}, Model: {row[3]}, Status: {row[4]}, Customer: {row[5]}")
            
            cursor.close()
            print("\n✓ Import completed successfully!")
        
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()