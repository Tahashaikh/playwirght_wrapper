import os
import csv
import time
import json
import pyodbc
from conftest import get_file_location, get_environment_config


def database_connection(connection_string, query, values=None):
    start_time = time.time()
    try:
        with pyodbc.connect(connection_string) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                if values:
                    cursor.execute(query, values)
                    print(f"Query executed successfully with params: {str(values)} - {query}")
                else:
                    cursor.execute(query)
                    print(f"Query executed successfully without params - {query}")

                is_update = 'update' in query.lower()

                if is_update:
                    result = f"{cursor.rowcount} rows affected"
                else:
                    if cursor.description:
                        columns = [column[0] for column in cursor.description]
                        rows = cursor.fetchall()
                        if rows:
                            result = [dict(zip(columns, row)) for row in rows]
                        else:
                            result = "No rows returned"
                    else:
                        result = f"{cursor.rowcount} rows affected"

                execution_time = time.time() - start_time
                print(f"Query execution time: {execution_time} seconds")

                return result

    except pyodbc.Error as e:
        error_message = f"Error executing query: {e}"
        print(error_message)
        raise e


def database_connection_all(connection_branch, query, values=None):
    connection_string = update_connection_string(connection_branch)
    start_time = time.time()
    try:
        with pyodbc.connect(connection_string) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                if values:
                    cursor.execute(query, values)
                    print(f"Query executed successfully with params: {str(values)} - {query}")
                else:
                    cursor.execute(query)
                    print(f"Query executed successfully without params - {query}")

                is_update = 'update' in query.lower()

                if is_update:
                    result = f"{cursor.rowcount} rows affected"
                else:
                    if cursor.description:
                        columns = [column[0] for column in cursor.description]
                        rows = cursor.fetchall()
                        if rows:
                            result = [dict(zip(columns, row)) for row in rows]
                        else:
                            result = "No rows returned"
                    else:
                        result = f"{cursor.rowcount} rows affected"

                execution_time = time.time() - start_time
                print(f"Query execution time: {execution_time} seconds")

                return result

    except pyodbc.Error as e:
        error_message = f"Error executing query: {e}"
        print(error_message)
        raise e


def update_connection_string(connection_branch=None):
    env_file_path = get_file_location('env_config.json')
    print(f"env_file_path: {env_file_path}")
    ENVIRONMENT, run_only_on = get_environment_config(env_file_path)

    connection_string = (
        "Driver={{IBM DB2 ODBC Driver}};"
        "Hostname={HOSTNAME};"
        "Port=50000;"
        "Protocol=TCPIP;"
        "Database={DATABASE};"
        "UID={UID};"
        "PWD={PWD};"
    )

    if connection_branch is None:
        print("Connection Branch =", "OBS")
        box_value = ENVIRONMENT.get('OBS')
    elif (1 <= connection_branch <= 4999 and connection_branch not in [1999, 1001, 786, 787, 6001, 6002, 6003, 6004]
          and connection_branch not in range(8000, 9001)):
        print("Connection Branch =", "BOX2")
        box_value = ENVIRONMENT.get('BOX2')
    elif 5000 <= connection_branch <= 5999:
        print("Connection Branch =", "BOX3")
        box_value = ENVIRONMENT.get('BOX3')
    elif connection_branch == 1001:
        print("Connection Branch =", "BOX4")
        box_value = ENVIRONMENT.get('BOX4')
    elif connection_branch == 1999:
        print("Connection Branch =", "CPU")
        box_value = ENVIRONMENT.get('CPU')
    elif connection_branch == 787:
        print("Connection Branch =", "CC")
        box_value = ENVIRONMENT.get('CC')
    else:
        print("Branch code not in range.")
        return None

    uid = ENVIRONMENT.get('UID') if connection_branch is not None else ENVIRONMENT.get('OBS_UID')
    pwd = ENVIRONMENT.get('PWD') if connection_branch is not None else ENVIRONMENT.get('OBS_PWD')
    database = ENVIRONMENT.get('DATABASE') if connection_branch is not None else ENVIRONMENT.get('OBS_DATABASE')
    updatedConnectionString = connection_string.format(HOSTNAME=box_value, DATABASE=database, UID=uid, PWD=pwd)
    return updatedConnectionString


def write_to_csv(data, table_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    updated_scripts_dir = os.path.join(project_root, 'system_generated_scripts')
    os.makedirs(updated_scripts_dir, exist_ok=True)

    csv_file_path = os.path.join(updated_scripts_dir, f"{table_name}.csv")

    if data and isinstance(data, list) and len(data) > 0:
        keys = data[0].keys()
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"Data written to CSV file: {csv_file_path}")
    else:
        print("No data to write to CSV.")


def write_to_csv2(data, table_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    updated_scripts_dir = os.path.join(project_root, 'system_generated_scripts')
    os.makedirs(updated_scripts_dir, exist_ok=True)

    csv_file_path = os.path.join(updated_scripts_dir, f"{table_name}.csv")

    if data and isinstance(data, list) and len(data) > 0:
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                existing_data = list(reader)
        else:
            existing_data = []

        existing_data_dict = {row['id']: row for row in existing_data}

        for row in data:
            if 'id' in row and row['id'] in existing_data_dict:
                existing_data_dict[row['id']].update(row)
            else:
                existing_data_dict[row.get('id', str(len(existing_data_dict) + 1))] = row

        keys = set().union(*(row.keys() for row in existing_data_dict.values()))
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(existing_data_dict.values())
        print(f"Data written to CSV file: {csv_file_path}")
    else:
        print("No data to write to CSV.")


def execute_query(connection_branch, query, values=None):
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Executing Query~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    data = database_connection_all(connection_branch, query, values)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Query Executed~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    return data

