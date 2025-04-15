import os
import subprocess
import threading
from datetime import datetime

from conftest import get_file_location


def run_commands_from_file(file_names, Iteration=1):
    for i in range(0, Iteration):
        for files in file_names:
            os.environ['Executed_file_name'] = files
            file_path = get_file_location(files)
            with open(file_path, 'r') as file:
                lines = file.readlines()

            for line in lines:
                # Strip whitespace and check if the line is a comment
                stripped_line = line.strip()
                if stripped_line.startswith('pytest') or stripped_line.startswith('extractor') and line is not None:
                    # Execute the command
                    try:
                        os.environ['TEST_RUN_ID'] = datetime.now().strftime('%H-%M-%S')
                        subprocess.run(stripped_line, shell=True, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"An error occurred while executing {stripped_line}: {e}")


all_files = ['Advance_payment','Contract_Sight', 'Contract_Usance', 'Cust_IFDBC_Execution_List','FCIF','GENERAL_POSTING','LC']

run_commands_from_file(['IFDBC'])
