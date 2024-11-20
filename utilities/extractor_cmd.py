import os
import sys
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import inspect
from conftest import get_folder_location
from database import database_operations

# Logging setup
log_dir = get_folder_location('logs')
log_file = os.path.join(log_dir, 'enhanced_extractor.log')

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Discover database functions
data_providers = {
    name: func
    for name, func in inspect.getmembers(database_operations, predicate=inspect.isfunction)
    if name.endswith('_data')
}
logging.debug(f"Discovered data provider functions: {data_providers}")


# Data provider function
def data_provider(script_name):
    provider_func_name = f"{script_name.replace('.py', '').replace('.csv', '').removeprefix('test_')}_data"
    if provider_func_name in data_providers:
        try:
            result = data_providers[provider_func_name]()
            if isinstance(result, (pd.DataFrame, dict)):
                return pd.DataFrame(result) if isinstance(result, dict) else result
            else:
                raise ValueError(f"Function {provider_func_name} did not return valid data.")
        except Exception as e:
            logging.error(f"Error in data provider {provider_func_name}: {e}")
            return pd.DataFrame()
    else:
        raise ValueError(f"No data provider function defined for script: {script_name}")


# CSV updater
def update_csv(csv_path, data_frame):
    try:
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            # If headers mismatch, reset the CSV to headers only
            if not data_frame.empty and existing_df.columns.tolist() != data_frame.columns.tolist():
                logging.warning(f"Column mismatch in {csv_path}. Resetting CSV to headers only.")
                data_frame.iloc[0:0].to_csv(csv_path, index=False)  # Save only headers
                return False
            # Update the CSV with new data
            combined_df = pd.concat([existing_df, data_frame]).drop_duplicates()
            combined_df.to_csv(csv_path, index=False)
            logging.info(f"Updated CSV file: {csv_path}.")
        else:
            data_frame.to_csv(csv_path, index=False)
            logging.info(f"Created new CSV file: {csv_path}.")
        return True
    except Exception as e:
        logging.error(f"Error updating CSV {csv_path}: {e}")
        raise


# Process a single script
def process_single_script(script_name, folder_path):
    script_path = os.path.join(folder_path, script_name)
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script file {script_name} not found in folder {folder_path}.")

    try:
        logging.info(f"Processing single script: {script_name}")
        data = data_provider(script_name)
        if not data.empty:
            csv_name = script_name.replace('.py', '.csv')
            csv_path = os.path.join(folder_path, csv_name)
            update_csv(csv_path, data)
            logging.info(f"Successfully processed script {script_name}.")
        else:
            logging.warning(f"No data returned for script: {script_name}. Resetting CSV to headers only.")
            # Reset the CSV file to include only headers
            csv_name = script_name.replace('.py', '.csv')
            csv_path = os.path.join(folder_path, csv_name)
            pd.DataFrame(columns=[]).to_csv(csv_path, index=False)  # Save only headers
    except ValueError as e:
        logging.error(str(e))
        raise
    except Exception as e:
        logging.error(f"Error processing script {script_name}: {e}")
        raise


def process_script(script_name, folder_path, summary_stats):
    try:
        data = data_provider(script_name)
        if data.empty:
            logging.warning(f"Data provider for {script_name} returned no data. Resetting CSV to headers only.")
            csv_name = script_name.replace('.py', '.csv')
            csv_path = os.path.join(folder_path, csv_name)
            pd.DataFrame(columns=[]).to_csv(csv_path, index=False)  # Save only headers
            summary_stats["errors"] += 1
            return

        csv_name = script_name.replace('.py', '.csv')
        csv_path = os.path.join(folder_path, csv_name)
        initial_rows = len(data)
        success = update_csv(csv_path, data)
        if success:
            summary_stats["files_processed"] += 1
            summary_stats["rows_added"] += initial_rows
        else:
            summary_stats["errors"] += 1
    except Exception as e:
        summary_stats["errors"] += 1
        logging.error(f"Error processing script {script_name}: {e}")


# Process all scripts
def process_all_scripts(folder_path):
    summary_stats = {"files_processed": 0, "rows_added": 0, "errors": 0}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.py'):
                    futures.append(executor.submit(process_script, file, root, summary_stats))
        for future in futures:
            future.result()
    logging.info(f"Processing Summary: {summary_stats}")
    print("Processing Summary:")
    print(f"Total Files Processed: {summary_stats['files_processed']}")
    print(f"Total Rows Added: {summary_stats['rows_added']}")
    print(f"Total Errors Encountered: {summary_stats['errors']}")


# CLI handler
def main():
    parser = argparse.ArgumentParser(description="CLI Tool for processing scripts and updating CSV files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: run (all scripts)
    run_parser = subparsers.add_parser("run", help="Process scripts in the specified folder or a single file.")
    run_parser.add_argument("--folder", type=str, default=get_folder_location("system_generated_scripts"),
                            help="Folder containing Python scripts to process.")
    run_parser.add_argument("--f", type=str, help="Single file to process in the folder.")

    args = parser.parse_args()

    if args.command == "run":
        if args.f:
            try:
                process_single_script(args.f, args.folder)
                print(f"Successfully processed single script: {args.f}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            process_all_scripts(args.folder)


if __name__ == '__main__':
    main()
