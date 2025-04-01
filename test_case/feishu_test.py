import sys
import os
import datetime

# Add the parent directory to sys.path to import modules from sync_api
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from sync_api.feishu_spreadsheet import get_tenant_access_token, get_sheet_id, read_data, add_data

def test_get_tenant_access_token():
    """Test function to get and print the tenant access token."""
    try:
        token = get_tenant_access_token()
        print("Successfully retrieved token:")
        print(token)
        return True
    except Exception as e:
        print(f"Error getting token: {e}")
        return False

def test_get_sheet_id():
    """Test function to get and print sheet IDs for a given spreadsheet."""
    spreadsheet_token = "UY0ZsgMUghi9ygth0PtcMyXinRd"
    try:
        # First get the access token
        access_token = get_tenant_access_token()
        
        # Then get the sheet IDs
        sheet_map = get_sheet_id(spreadsheet_token, access_token)
        
        print("Successfully retrieved sheet IDs:")
        for sheet_title, sheet_id in sheet_map.items():
            print(f"Sheet Title: {sheet_title}, Sheet ID: {sheet_id}")
        
        return True
    except Exception as e:
        print(f"Error getting sheet IDs: {e}")
        return False

def test_read_data():
    """Test function to read data from a spreadsheet."""
    spreadsheet_token = "UY0ZsgMUghi9ygth0PtcMyXinRd"
    try:
        # First get the access token
        access_token = get_tenant_access_token()
        
        # Get sheet IDs to see available sheets
        sheet_map = get_sheet_id(spreadsheet_token, access_token)
        print("Available sheets:")
        for sheet_title, sheet_id in sheet_map.items():
            print(f"Sheet Title: {sheet_title}, Sheet ID: {sheet_id}")
        
        # Use the first sheet for testing
        if sheet_map:
            first_sheet_name = list(sheet_map.keys())[0]
            first_sheet_id = sheet_map[first_sheet_name]
            
            # Test 1: Read data using sheet_id
            print("\nTest 1: Reading data using sheet_id:")
            df1 = read_data(spreadsheet_token, sheet_id=first_sheet_id, access_token=access_token)
            print(f"Data shape: {df1.shape}")
            print(df1.head())
            
            # Test 2: Read data using sheet_name
            print("\nTest 2: Reading data using sheet_name:")
            df2 = read_data(spreadsheet_token, sheet_name=first_sheet_name, access_token=access_token)
            print(f"Data shape: {df2.shape}")
            print(df2.head())
        else:
            print("No sheets found in the spreadsheet")
            
        return True
    except Exception as e:
        print(f"Error reading data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_add_data():
    """Test function to add data to columns A and B of a spreadsheet."""
    spreadsheet_token = "UY0ZsgMUghi9ygth0PtcMyXinRd"
    try:
        # First get the access token
        access_token = get_tenant_access_token()
        
        # Get sheet IDs to see available sheets
        sheet_map = get_sheet_id(spreadsheet_token, access_token)
        if not sheet_map:
            print("No sheets found in the spreadsheet")
            return False
            
        # Use the first sheet for testing
        first_sheet_name = list(sheet_map.keys())[0]
        first_sheet_id = sheet_map[first_sheet_name]
        
        print(f"Testing adding data to sheet: {first_sheet_name} (ID: {first_sheet_id})")
        
        # Read current data to see the current state
        print("\nCurrent data before adding new rows:")
        df_before = read_data(spreadsheet_token, sheet_id=first_sheet_id, access_token=access_token)
        print(f"Data shape before: {df_before.shape}")
        print(df_before.tail())
        
        # Generate timestamp for unique test data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Test 1: Add data to column A
        print("\nTest 1: Adding data to column A")
        value_a = f"Test A - {timestamp}"
        result_a = add_data(
            spreadsheet_token=spreadsheet_token, 
            sheet_id=first_sheet_id, 
            column="A", 
            value=value_a,
            access_token=access_token
        )
        print(f"Added value to column A: {value_a}")
        print(f"API Response: {result_a}")
        
        # Test 2: Add data to column B of the same row
        print("\nTest 2: Adding data to column B")
        value_b = f"Test B - {timestamp}"
        result_b = add_data(
            spreadsheet_token=spreadsheet_token, 
            sheet_name=first_sheet_name,  # Use sheet_name instead of sheet_id to test this functionality
            column="B", 
            value=value_b,
            access_token=access_token
        )
        print(f"Added value to column B: {value_b}")
        print(f"API Response: {result_b}")
        
        # Read the data back to verify
        print("\nReading data back to verify:")
        df_after = read_data(spreadsheet_token, sheet_id=first_sheet_id, access_token=access_token)
        print(f"Data shape after: {df_after.shape}")
        print(df_after.tail())
        
        # Verify both values were added to the last row
        last_row = df_after.iloc[-1]
        print("\nVerifying last row:")
        print(last_row)
        
        return True
    except Exception as e:
        print(f"Error adding data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Uncomment the test you want to run
    # test_get_tenant_access_token()
    # test_get_sheet_id()
    test_read_data()
    # test_add_data()
