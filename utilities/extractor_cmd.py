#!/usr/bin/env python
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import inspect
from conftest import get_folder_location
from database import database_operations

# Logging setup
log_dir = get_folder_location('logs')
log_file = os.path.join(log_dir, 'extractor_cmd.log')

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
    provider_func_name = f"{script_name.replace('.py', '').removeprefix('test_')}_data"
    if provider_func_name in data_providers:
        result = data_providers[provider_func_name]()
        if isinstance(result, (pd.DataFrame, dict)):
            return pd.DataFrame(result) if isinstance(result, dict) else result
        else:
            logging.error(f"The function {provider_func_name} did not return a any data 'Check Query'")
            return pd.DataFrame()
    else:
        logging.info(f"No data provider function defined for script: {script_name}")


# CSV updater
def update_csv(csv_path, data_frame):
    try:
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            header = existing_df.columns.tolist()
            empty_df = pd.DataFrame(columns=header)
            if not data_frame.empty and header != data_frame.columns.tolist():
                raise ValueError(f"Column mismatch in {csv_path}.")

            combined_df = pd.concat([empty_df, data_frame]).drop_duplicates()
            combined_df.to_csv(csv_path, index=False)
            logging.info(f"Updated CSV file: {csv_path}.")
        else:
            data_frame.to_csv(csv_path, index=False)
            logging.info(f"Created new CSV file: {csv_path}.")
    except Exception as e:
        logging.error(f"Error updating CSV: {e}")
        raise  # Re-raise the exception to signal failure and prevent processing from continuing


# Process a single script
def process_single_script(script_name, folder_path):
    script_path = ''
    script_name = script_name.replace('.py', '').replace('.csv', '')
    script_name = script_name + '.py'
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file == script_name:
                script_path = os.path.join(root, file)
                if not os.path.isfile(script_path):
                    raise FileNotFoundError(f"Script file {script_name} not found in folder {folder_path}.")
    try:
        logging.info(f"Processing single script: {script_name}")
        data = data_provider(script_name)
        if not data.empty:
            csv_path = script_path.replace('.py', '.csv')
            update_csv(csv_path, data)
            logging.info(f"Successfully processed script {script_name}.")
        # else:
        #     logging.error(f"No data returned for script: {script_name}.")
    except ValueError as e:
        logging.error(str(e))
        raise
    except Exception as e:
        logging.error(f"Error processing script {script_name}: {e}")
        raise


def process_script(script_name, folder_path, summary_stats):
    csv_name = script_name.replace('.py', '.csv')
    csv_path = os.path.join(folder_path, csv_name)
    try:
        data = data_provider(script_name)
        csv_name = script_name.replace('.py', '.csv')
        csv_path = os.path.join(folder_path, csv_name)
        if not data.empty:
            initial_rows = len(data)
            update_csv(csv_path, data)
            # Only increment stats if there is no error
            summary_stats["files_processed"] += 1
            summary_stats["rows_added"] += initial_rows
        # else:
        #     logging.info(f"No data returned for script: {script_name}.")
    except Exception as e:
        existing_df = pd.read_csv(csv_path)
        header = existing_df.columns.tolist()
        empty_df = pd.DataFrame(columns=header)
        empty_df.to_csv(csv_path, index=False)
        summary_stats["files_not_processed"] += 1
        # logging.error(f"Error processing script {script_name}: {e}")


# Process all scripts
def process_all_scripts(folder_path):
    summary_stats = {"files_processed": 0, "rows_added": 0, "files_not_processed": 0}
    with ThreadPoolExecutor(max_workers=50) as executor:
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
    print(f"Total Files Not Processed: {summary_stats['files_not_processed']}")


# CLI handler
def main():
    parser = argparse.ArgumentParser(description="CLI Tool for processing scripts and updating CSV files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: run (all scripts)
    run_parser = subparsers.add_parser("run", help="Process scripts in the specified folder or a single file.")
    run_parser.add_argument("--folder", type=str, default=get_folder_location("system_generated_scripts"),
                            help="Folder containing Python scripts to process.")
    run_parser.add_argument("--file", type=str, help="Single file to process in the folder.")

    args = parser.parse_args()

    if args.command == "run":
        if args.file:
            try:
                process_single_script(args.file, args.folder)
                print(f"Successfully processed single script: {args.file}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            if os.path.isabs(args.folder):
                process_all_scripts(args.folder)
            else:
                process_all_scripts(get_folder_location(args.folder, get_folder_location("system_generated_scripts")))


if __name__ == '__main__':
    main()
