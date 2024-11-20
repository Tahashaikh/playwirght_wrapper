import os
import pandas as pd
import logging
import inspect
import database.database_operations as db_ops
from conftest import get_folder_location

# Create log directory if it doesn't exist, and configure logging to write to a file
log_dir = get_folder_location('logs')
log_file = os.path.join(log_dir, 'extractor.log')

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get all the functions from the database_operations module
data_providers = {
    name: func
    for name, func in inspect.getmembers(db_ops, predicate=inspect.isfunction)
    if name.endswith('_data')
}

# Log the functions that were discovered
logging.debug(f"Discovered data provider functions: {data_providers}")


# Function that takes a script name and returns a DataFrame or None
def data_provider(script_name):
    # Get the name of the data provider function
    provider_func_name = f"{script_name.replace('.py', '').removeprefix('test_')}_data"

    # Check if the function exists
    if provider_func_name in data_providers:
        # Call the function
        result = data_providers[provider_func_name]()
        # Check if the result is a DataFrame
        if isinstance(result, (pd.DataFrame, dict)):
            return pd.DataFrame(result) if isinstance(result, dict) else result
        else:
            logging.error(f"The function {provider_func_name} did not return a any data 'Check Query'")
            return pd.DataFrame()

        # Return the result as a DataFrame

    else:
        raise ValueError(f"No data provider function defined for script: {script_name}")


# Function that takes a CSV path and a DataFrame, and updates the CSV file
def update_csv(csv_path, data_frame):
    try:
        # Check if the file exists
        if os.path.exists(csv_path):
            # Read the existing CSV file
            existing_df = pd.read_csv(csv_path)
            logging.info(f"Processing existing CSV file: {csv_path}")

            # Get the header of the existing CSV file
            header = existing_df.columns.tolist()
            # Create an empty DataFrame with the same header
            empty_df = pd.DataFrame(columns=header)

            # Check if the data_frame is not empty
            if not data_frame.empty:
                # Check if the data_frame columns match the header
                if header != data_frame.columns.tolist():
                    raise ValueError(f"The columns of the DataFrame do not match the columns of the CSV file.")

                # Drop duplicates from the data_frame
                data_frame = data_frame.drop_duplicates()
                # Concatenate the empty DataFrame with the data_frame
                combined_df = pd.concat([empty_df, data_frame], ignore_index=True, sort=False)
                # Write the combined DataFrame to the CSV file
                combined_df.to_csv(csv_path, index=False)
                logging.info(f"Replaced all rows with new data in {csv_path}.")
            else:
                # Write the empty DataFrame to the CSV file
                empty_df.to_csv(csv_path, index=False)
                logging.info(f"Cleared all rows, leaving only headers in {csv_path}.")
        else:
            # Write the data_frame to the CSV file
            data_frame.to_csv(csv_path, index=False)
            logging.info(f"Created new CSV file: {csv_path}")

    except Exception as e:
        logging.error(f"Error updating CSV file {csv_path}: {e}")


# Function that takes a folder path, processes all the scripts in the folder, and updates the corresponding CSV files
def process_scripts(folder_path):
    total_files_processed = 0
    total_rows_added = 0

    try:
        # Iterate over all the files in the folder
        for root, _, files in os.walk(folder_path):
            for file in files:
                # Check if the file is a Python script
                if file.endswith('.py'):
                    script_name = file
                    csv_name = file.replace('.py', '.csv')
                    csv_path = os.path.join(root, csv_name)

                    # Check if the script has a data provider function
                    if script_name.replace('.py', '_data').removeprefix('test_') in data_providers:
                        logging.info(f"Processing script: {script_name}")
                        # Get the data from the data provider function
                        data = data_provider(script_name)
                        # Check if the data is a DataFrame

                        if isinstance(data, pd.DataFrame):
                            initial_row_count = len(data)
                            update_csv(csv_path, data)
                            if not data.empty:
                                total_files_processed += 1
                                total_rows_added += initial_row_count
                        else:
                            logging.error(f"Data returned from {script_name} is not a DataFrame.")
                    else:
                        logging.info(f"No action defined for script: {script_name}")

        logging.info(f"Total files processed: {total_files_processed}")
        logging.info(f"Total rows added: {total_rows_added}")

    except Exception as e:
        logging.error(f"Error processing scripts in folder {folder_path}: {e}")


if __name__ == '__main__':
    # Get the folder path from the conftest file
    folder_path = get_folder_location('system_generated_scripts')
    # Start the script
    logging.info(f"Starting the data utility script with folder path: {folder_path}")
    # Process all the scripts in the folder
    process_scripts(folder_path)
    # Log the completion of the script
    logging.info("Script execution completed.")
    # Append a newline to the log file
    with open(log_file, 'a') as log:
        log.write('\n')
