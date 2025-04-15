import csv
import json
import numbers
import os
import random
import time
from textwrap import indent
from tkinter import messagebox

import pandas as pd
import re
import ast
import astor
import logging
import tkinter as tk
from conftest import get_folder_location

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir))
log_dir = os.path.join(project_root, 'logs')
log_file = os.path.join(log_dir, 'parser.log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def replace_goto_calls(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    code = ''.join(lines)
    goto_pattern = re.compile(r'page\.goto\(([^)]+)\)', re.DOTALL)
    updated_code = goto_pattern.sub(r'page.goto(base_url)', code)
    with open(file_path, 'w') as file:
        file.write(updated_code)


def sanitize_name(name: str) -> str:
    name = (name.replace("data-e2e", "").replace("data-test", "")
            .replace("input", "").replace("type", ""))
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    return name


def extract_cleaned_string_literals(code_line):
    pattern = r"'(?:\\'|[^'])*'|\"(?:\\\"|[^\"])*\""
    matches = re.findall(pattern, code_line)
    strings = [re.sub(r"(^'|'$)|(^\"|\"$)", "", match).replace("\\'", "'").replace('\\"', '"') for match in matches]
    return strings


def extract_complete_string_literals(code_line):
    pattern = r"'(?:\\'|[^'])*'|\"(?:\\\"|[^\"])*\""
    matches = re.findall(pattern, code_line)
    return matches


def find_replaceable_lines(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip().startswith('#'):
                if (
                        'fill(' in line or 'get_by_text(' in line or 'filter' in line or 'type(' in line or 'get_by_placeholder(' in line or "get_by_role('cell'" in line or "get_by_role('row'" in line or 'get_by_role("cell"' in line or 'get_by_role("row"' in line) and (
                        all(keyword not in line for keyword in
                            ('str(', 'random', 'randint', 'expect('))):
                    results.append((line_number, line.strip()))
    except Exception as e:
        logging.error(f"Error reading file {filepath}: {e}")
    return results


def save_data_to_csv(data, csv_path):
    try:
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        logging.info(f"Data saved to CSV at {csv_path}")
    except Exception as e:
        logging.error(f"Error saving data to CSV at {csv_path}: {e}")


def extract_function_name(script_content):
    match = re.search(r'def (\w+)\(', script_content)
    return match.group(1) if match else 'run'


def method_exists(file_path, method_name):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        uncommented_content = re.sub(r'#.*', '', content)
        pattern = rf'\bdef {method_name}\('
        return bool(re.search(pattern, uncommented_content))
    except Exception as e:
        logging.error(f"Error checking method existence in file {file_path}: {e}")
        return False


def convert_list_to_dict(column_names, values):
    result = {}
    for i, column in enumerate(column_names):
        if i < len(values[0]):
            result[column] = f"'{values[0][i]}'"
        else:
            result[column] = None
    return result


def pre_defined_variables(list_values):
    # check if the list_values has any of the key if yes then replace the value with a new value
    predefined_variables = [
        ('usernamebox', 'username'),
        ('passwordbox', 'password'),
        ('PasswordTextBox', 'password'),
        ('AmountTextBox', 'random.randint(1000, 9999)'),
        ('NarrationTextBox', "'Automation NarrationTextBox'"),
        ('NoLabelNarration2TextBox', "'Automation NarrationTextBox2'"),
        ('NoLabelNarration3TextBox', "'Automation NarrationTextBox3'"),
        ('CustomerNameTextBox', "'Playwright Automation'"),
        ('ChequeDateTextBox', "row['TDATE']"),
        ('RemarksTextAreaRemarksTextArea', "'Automation Remarks'")
    ]
    for key, value in predefined_variables:
        if key in list_values:
            list_values[key] = value
    return list_values


def add_method(file_path, method_name, column_values):
    column_formate = convert_list_to_dict(column_values[0], column_values[1])
    key_value_pairs = pre_defined_variables(column_formate)
    updated_values_format = "{\n" + ",\n".join(
        [f"              '{k}': {v}" for k, v in key_value_pairs.items()]) + "\n             }"
    method_code = f"""

\ndef {method_name}():\n# System Generated Method kindly modified it before use
    result = execute_query(int(current_branch_code), Queries.fetch_customer,
                           values=(current_branch_code, "586", "81"))

    if isinstance(result, list):
        data = [{updated_values_format} for row in result]
        return pd.DataFrame(data)\n
"""
    imports_needed = """import pandas as pd
import random
import socket
from database.Queries import *
from database.database_connection import *
from utils.general_methods import *
from utils.utils import *
from conftest import *
from faker import Faker

fake = Faker()

test_data = read_json(get_file_location('test_data.json'))
current_branch_code = test_data['branch_code']
username = test_data['username']
username1 = test_data['username1']
authorizer = test_data['authorizer']
authorizer1 = test_data['authorizer1']
password = test_data['password']
cpu_brn = test_data['CPU_BRN']
KHI_MAIN_BRN = test_data['KHI_MAIN_BRN']


def update_system_ip(Enable=False):
    if Enable:
        current_system_ip = get_system_ip()
        execute_query(int(current_branch_code), Queries.update_user_system_ip,
                      values=(current_system_ip, current_branch_code, username))
    else:
        execute_query(int(current_branch_code), Queries.update_user_system_ip,
                      values=(None, current_branch_code, username))
"""

    try:
        with open(file_path, 'r') as file:
            content = file.read()

        if method_exists(file_path, method_name):
            logging.info(f"Method '{method_name}' already exists in {file_path}.")
            return

        normalized_content = re.sub(r'\s+', ' ', content.strip())
        normalized_imports_needed = re.sub(r'\s+', ' ', imports_needed.strip())

        if normalized_imports_needed not in normalized_content:
            with open(file_path, 'r+') as file:
                existing_content = file.read()
                file.seek(0, 0)
                file.write(f"{imports_needed}\n\n{existing_content}")

        with open(file_path, 'a') as file:
            file.write(method_code)

        logging.info(f"Added method '{method_name}' to {file_path}")
    except Exception as e:
        logging.error(f"Error adding method '{method_name}' to {file_path}: {e}")


def extract_comments(script_content):
    comments = {}
    lines = script_content.split('\n')
    for index, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            comments[index + 1] = '\n' + '    ' + stripped_line

    return comments


def read_values_from_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)
        values = df.values.tolist()
        return df.columns.tolist(), values
    except Exception as e:
        logging.error(f"Error reading values from CSV at {csv_path}: {e}")
        return [], []


def generate_Josn_operations(column_names, name):
    values = ""
    for i in list(column_names):
        value = f"'{i}': {i}"
        values = f"{values}, {value}".removeprefix(",").removeprefix(" ")
    lines = "data_values = {" + f"{values}" + "}\nadd_voucher_records(os.path.basename(__file__), **" + f"{name}" + ", **data_values)\n"
    return lines.replace('\n', '\n' + ' ' * 4)


def process_script_with_ast(script_path, updated_script_path, csv_path, script_name, allure_parameters):
    logging.info(f"Processing script: {script_path}")

    try:
        with open(script_path, 'r') as file:
            script_content = file.read()
        multiline_comment_lines = ""
        comments = extract_comments(script_content)

        tree = ast.parse(script_content.strip())
        static_code = []
        function_name = extract_function_name(script_content)
        column_names, csv_data = read_values_from_csv(csv_path)
        comment_lines = sorted(comments.keys())
        current_comment_index = 0

        for node in ast.walk(tree):
            # ast_dump = ast.dump(node, indent=4)
            # print(ast_dump)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                try:
                    top_comments = node.value.value
                    new_comments = (str(top_comments)).replace("'", "").replace(",,", "")
                    data_dict = {}
                    for line in new_comments.splitlines():
                        if line:
                            key, value = line.split(":", 1)
                            data_dict[key.strip()] = value.replace(",", "").replace("<", "").replace(">", "").strip()
                    data_dict["Scenario_name"] = script_name
                    headers = list(data_dict.keys())
                    rows = [list(data_dict.values())]
                    csv_file_path = project_root + "/Scenarios_discription.csv"
                    if os.path.exists(csv_file_path):
                        with open(csv_file_path, 'r', newline='') as file:
                            reader = csv.reader(file)
                            existing_rows = list(reader)
                        for row in rows:
                            if row not in existing_rows:
                                with open(csv_file_path, 'a', newline='') as file:
                                    writer = csv.writer(file)
                                    writer.writerows(rows)
                    else:
                        with open(csv_file_path, 'w', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(headers)
                            writer.writerows(rows)
                except Exception as e:
                    logging.error(f"Comment is not proper {script_path}: {e}")
                # create a file on the project and write the data

            # if isinstance(node, ast.Assign):
            #     for target in node.targets:
            #         if isinstance(target, ast.Name) and target.id == "Order" or target.id == "order":
            #             if isinstance(node.value, ast.Constant):
            #                     order = node.value.value
            if ast.unparse(node) == 'None':
                break
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if (isinstance(node.value.func,
                                   ast.Name) and node.value.func.id == "get_voucher_ref_detail"):
                        static_code.append("\n# Add Posting Data in JSON".replace('\n', '\n' + ' ' * 4))
                        static_code.append(astor.to_source(node).strip().replace('\n', ' ').replace('    ', ''))
                        static_code.append(generate_Josn_operations(column_names, node.targets[0].id))
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Str):
                    multiline_comment_lines += f"{node.value.s}\n"
                elif isinstance(node.value, ast.Call):
                    func = node.value.func
                    if isinstance(func, ast.Name) and func.id in {"remove_voucher_records","handle_popups"}:
                        static_code.append(astor.to_source(node).strip().replace('\n', ' ').replace('    ', ''))
                    elif isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "screenshot":
                        static_code.append("\n# Add Posting Data in JSON".replace('\n', '\n' + ' ' * 4))
                        static_code.append(
                            astor.to_source(node).replace(astor.to_source(node),
                                                          "voucher = get_voucher_ref_detail(page)"))
                        static_code.append(generate_Josn_operations(column_names, "voucher"))
                    elif (isinstance(func, ast.Attribute) and not (
                            func.attr == 'close' and getattr(func.value, 'id', None) in {'browser', 'context'})
                          and not func.attr == "screenshot"):

                        line_number = node.lineno
                        static_code.append(astor.to_source(node).strip().replace('\n', ' ').replace('    ', ''))
                        while current_comment_index < len(comment_lines) and comment_lines[
                            current_comment_index] <= line_number:
                            static_code.insert(len(static_code) - 1, comments[comment_lines[current_comment_index]])
                            current_comment_index += 1
            elif isinstance(node, ast.FunctionDef):
                function_name = node.name
                function_name = function_name if function_name.startswith('test_') else 'test_' + function_name
            elif isinstance(node, ast.If):
                static_code.append("page.wait_for_timeout(3000)".replace('\n', '\n' + ' ' * 4))
                static_code.append(astor.to_source(node).replace('\n', '\n' + ' ' * 4))

        # column_names, csv_data = read_values_from_csv(csv_path)
        param_names = ', '.join(column_names)
        static_code_str = '\n    '.join(static_code)
        top_comment = f'"""{multiline_comment_lines}"""'
        script_name = script_name.replace('.', '_')
        func_name = f'{script_name}_data'.removeprefix('test_')
        db_operations_path = os.path.join(project_root, 'database', 'database_operations.py')
        if script_name.startswith('test_TLR_PC_'):
            sys_ip = """update_system_ip(Enable=True)"""
        else:
            sys_ip = """update_system_ip()"""
        if not method_exists(db_operations_path, func_name):
            pass
            default = """@pytest.mark.order()"""
        else:
            default = """@pytest.mark.order(1)\n@pytest.mark.dataAvailable"""
            # default = """@pytest.mark.dataAvailable"""

        updated_script_content = f"""
{top_comment}        
import pytest
import random
import pandas as pd
import allure

from database.database_operations import *
from utils.general_methods import *
from utils.popup_handler import handle_popups
from playwright.sync_api import Page, expect
from utils.pre_req_test import user_setups
current_data = datetime.now().strftime("%d/%m/%Y")
csv_data = read_values_from_csv(f"{{os.path.dirname(__file__)}}"+r'\\{script_name}.csv')\n


{default}
#@pytest.mark.skip(reason='Skipping')
@allure.feature(f"{allure_parameters[0]}")
@allure.story(f"{script_name.replace('test_', '')}")
@pytest.mark.parametrize('count, {param_names}, skip', csv_data)
def {script_name}(page: Page, count, {', '.join(column_names)}, skip, base_url) -> None:
    allure.dynamic.title(f"{script_name.replace('test_', '')}_TC_{{count}}")
    if skip:
        pytest.skip("{script_name.replace('test_', '')}.csv has no data")
    user_setups(brncd, usernamebox)
    {sys_ip}
    {static_code_str}\n


"""

        with open(updated_script_path, 'w') as file:
            file.write(updated_script_content)

        logging.info(f"Updated script saved to {updated_script_path}")

    except Exception as e:
        logging.error(f"Error processing script {script_path}: {e}")


def get_py_files(folder):
    py_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                py_files.append([os.path.abspath(os.path.join(root, file)), file])
    return py_files


def rename_scripts(directory):
    try:
        py_files = get_py_files(directory)
        for filename in py_files:
            if not filename[1].startswith('test_'):
                new_filename = 'test_' + filename[1]
                old_path = filename[0]
                new_path = filename[0].replace(filename[1], new_filename)
                os.rename(old_path, new_path)
        return True
    except Exception as e:
        print(f"An error occurred while renaming files: {e}")
        logging.error(f"An error occurred while renaming files: {e}")
        return False


def unique_variable_name(name_list, value):
    count = 0
    if value.isnumeric():
        value = f"numeric_{value}"
    elif value == "":
        value = "unique_var"
    value = value.replace("GenericDropDown", "").replace("GenericTextBox", "")
    unique_value = value
    while unique_value in name_list:
        count += 1
        unique_value = f"{value}{count}"
    return unique_value


def get_lines_to_replace(file):
    all_matches = []
    csv_variables = []
    fill_data = {}
    try:
        result = find_replaceable_lines(file)
        for line in result:
            extracted_lines_strings = extract_complete_string_literals(line[1])
            extracted_lines_strings_with_out_quotes = extract_cleaned_string_literals(line[1])
            if len(extracted_lines_strings) == 1:
                if 'get_by_text' in line[1]:
                    get_by_txt = unique_variable_name(csv_variables, "get_by_txt")
                    csv_variables.append(get_by_txt)
                    fill_data[get_by_txt] = extracted_lines_strings_with_out_quotes[0]
                    generated_line = (line[1].replace(extracted_lines_strings[0], f"str({get_by_txt})"))
                    all_matches.append([line[1], generated_line])
            elif 2 <= len(extracted_lines_strings) < 4:
                if 'get_by_role' in line[1] and 'fill' in line[1] and 'name=' in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[2]
                    var_val = line[1].replace(extracted_lines_strings[2], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
                elif ("get_by_role('t" in line[1] or 'get_by_role("t' in line[1]) and 'fill' in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[1]
                    var_val = line[1].replace(extracted_lines_strings[1], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
                elif 'get_by_text' in line[1] and 'fill' in line[1] and 'get_by_role' not in line[1]:
                    get_by_txt_data = unique_variable_name(csv_variables, "get_by_txt_data")
                    csv_variables.append(get_by_txt_data)
                    fill_data[get_by_txt_data] = extracted_lines_strings_with_out_quotes[0]
                    get_by_txt_data_val = unique_variable_name(csv_variables, "get_by_txt_data_val")
                    csv_variables.append(get_by_txt_data_val)
                    fill_data[get_by_txt_data_val] = extracted_lines_strings_with_out_quotes[1]
                    var_val = (line[1].replace(extracted_lines_strings[0], f'str({get_by_txt_data})')
                               .replace(extracted_lines_strings[1], f'str({get_by_txt_data_val})'))
                    all_matches.append([line[1], var_val])
                elif 'get_by_label' in line[1] and 'locator' in line[1] and 'fill' in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[1]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[2]
                    var_val = line[1].replace(extracted_lines_strings[2], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
                elif 'get_by_text' in line[1] and 'press' in line[1]:
                    get_by_txt = unique_variable_name(csv_variables, "get_by_txt")
                    csv_variables.append(get_by_txt)
                    fill_data[get_by_txt] = extracted_lines_strings_with_out_quotes[0]
                    generated_line = (line[1].replace(extracted_lines_strings[0], f"str({get_by_txt})"))
                    all_matches.append([line[1], generated_line])
                elif 'get_by_text' in line[1] and 'click(' in line[1] and 'get_by_role' not in line[1]:
                    get_by_txt = unique_variable_name(csv_variables, "get_by_txt")
                    csv_variables.append(get_by_txt)
                    fill_data[get_by_txt] = extracted_lines_strings_with_out_quotes[0]
                    generated_line = (line[1].replace(extracted_lines_strings[0], f"str({get_by_txt})"))
                    all_matches.append([line[1], generated_line])
                elif 'get_by_role' in line[1] and 'get_by_text' in line[1] and 'click(' in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[1]
                    generated_line = (line[1].replace(extracted_lines_strings[1], f"str({unique_column_name})"))
                    all_matches.append([line[1], generated_line])
                elif ('fill(' in line[1] or 'type(' in line[1] or "filter" in line[1] or "get_by_role('cell'" in
                      line[1] or "get_by_role('row'" in line[1] or 'get_by_role("row"' in line[
                          1] or 'get_by_role("cell"' in
                      line[1]) and ('filter(has_text=re.compile' not in line[1] and 'get_by_role("t' not in line[1]
                                    and "get_by_role('t" not in line[1]):
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[1]
                    var_val = line[1].replace(extracted_lines_strings[1], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
            elif len(extracted_lines_strings) == 4:
                if ('fill(' in line[1] and "filter" in line[1] and 'filter(has_text=re.compile' not in line[1]) or (
                        'type(' in line[1] and "filter" in line[1] and 'filter(has_text=re.compile' not in line[1]):
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    column_name2 = sanitize_name(str(extracted_lines_strings_with_out_quotes[2]))
                    column_name = unique_variable_name(csv_variables, column_name)
                    column_name2 = unique_variable_name(csv_variables, column_name2)
                    csv_variables.append(column_name)
                    csv_variables.append(column_name2)
                    fill_data[column_name] = extracted_lines_strings_with_out_quotes[1]
                    fill_data[column_name2] = extracted_lines_strings_with_out_quotes[3]
                    csv_variables.append(column_name)
                    csv_variables.append(column_name2)
                    var_val = (line[1].replace(extracted_lines_strings[1], f'str({column_name})')
                               .replace(extracted_lines_strings[3], f'str({column_name2})'))
                    all_matches.append([line[1], var_val])
                elif 'filter' in line[1] and "press" in line[1] and 'filter(has_text=re.compile' not in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[0]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[1]
                    var_val = line[1].replace(extracted_lines_strings[1], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
                elif 'filter(has_text=re.compile' in line[1] and "fill" in line[1]:
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[2]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[3]
                    var_val = line[1].replace(extracted_lines_strings[3], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
                elif ('get_by_placeholder' in line[1] and "fill" in line[1]) or (
                        'get_by_placeholder' in line[1] and "type" in line[1]):
                    column_name = sanitize_name(str(extracted_lines_strings_with_out_quotes[2]))
                    unique_column_name = unique_variable_name(csv_variables, column_name)
                    csv_variables.append(unique_column_name)
                    fill_data[unique_column_name] = extracted_lines_strings_with_out_quotes[3]
                    var_val = line[1].replace(extracted_lines_strings[3], f"str({unique_column_name})")
                    all_matches.append([line[1], var_val])
            else:
                print(f"More then 2 literals are found\n Error extracting fill data from {file} in {line[1]}")
                logging.error(f"More then 2 literals are found\n Error extracting fill data from {file} in {line[1]}")
        return all_matches, fill_data
    except Exception as e:
        print(f"Error extracting fill data from {file}: {e}")
        logging.error(f"Error extracting fill data from {file}: {e}")
        return []


def replace_strings_in_fileline(file_path, search_replace_list):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        with open(file_path, 'w') as file:
            for line in lines:
                for search, replace in search_replace_list:
                    if line.strip() == search:
                        file.writelines(f"    {replace}\n")
                        search_replace_list.remove([search, replace])
                        break
                else:
                    file.write(line)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        logging.error(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")


def formate_fill_lines_in_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()

    patterns = [
        re.compile(
            r'(\.(?:locator|get_by_text|get_by_role)\([^)]*\)\s*\.\s*(?:fill|filter)\([^)]*?\))',
            re.DOTALL
        ),
        re.compile(
            r'(\.to_contain_text\([^)]*\))',
            re.DOTALL
        )
    ]

    def join_multiline(match):
        # Join all parts into a single line
        lines = match.group(1).splitlines()
        # Preserve the leading whitespace characters
        leading_whitespace = ''
        if lines[0].startswith(' '):
            leading_whitespace = lines[0][:len(lines[0]) - len(lines[0].lstrip())]
        # Join the lines, preserving the leading whitespace characters
        joined_line = leading_whitespace + ''.join(line.lstrip() for line in lines)
        # If the match is not a to_contain_text call, replace multiple whitespace characters with a single space
        if not match.group(0).startswith('.to_contain_text'):
            joined_line = re.sub(r'\s+', ' ', joined_line)
        return joined_line

    # Substitute the multiline expressions with the joined version
    joined_code = code
    for pattern in patterns:
        joined_code = pattern.sub(join_multiline, joined_code)

    with open(file_path, 'w') as file:
        file.write(joined_code)


def generate_databaseOperation_method(csv_path, script_name):
    column_header_value = read_values_from_csv(csv_path)
    script_name = script_name.replace('.', '_')
    method_name = f'{script_name}_data'
    func_name = method_name.removeprefix('test_')
    db_operations_path = os.path.join(project_root, 'database', 'database_operations.py')
    if not method_exists(db_operations_path, func_name):
        add_method(db_operations_path, func_name, column_header_value)


def remove_expect_lines_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    with open(file_path, 'w') as file:
        for line in lines:
            if 'expect(' not in line.strip():
                file.write(line)


def Runner(source_dir, generation_dir):
    recorded_scripts_dir = source_dir
    updated_scripts_dir = generation_dir

    print("Source", recorded_scripts_dir)
    print("Destination", updated_scripts_dir)
    script_count = 0
    csv_count = 0

    rename_scripts(recorded_scripts_dir)
    for script_file in get_py_files(recorded_scripts_dir):
        script_path = script_file[0]
        if os.path.isfile(script_path):
            script_name = os.path.splitext(script_file[1])[0]
            updated_script_path = script_path.replace(recorded_scripts_dir, updated_scripts_dir)
            script_directory = updated_script_path.replace(script_file[1], "")
            if not os.path.exists(script_directory):
                os.makedirs(script_directory)
            allure_params = script_directory.replace(updated_scripts_dir, "").removesuffix('\\').removeprefix(
                '\\').split('\\')
            path_csv = os.path.join(script_directory, f'{script_name}.csv')
            formate_fill_lines_in_file(script_path)
            match_lines, fill_data, = get_lines_to_replace(script_path)
            save_data_to_csv([fill_data], path_csv)
            path_csv = path_csv.replace(os.path.dirname(updated_scripts_dir), '').removeprefix('\\')
            process_script_with_ast(script_path, updated_script_path, path_csv, script_name, allure_params)
            formate_fill_lines_in_file(updated_script_path)
            replace_goto_calls(updated_script_path)
            match_lines2, fill_data, = get_lines_to_replace(updated_script_path)
            replace_strings_in_fileline(updated_script_path, match_lines2)
            generate_databaseOperation_method(path_csv, script_name)
            script_count += 1
            csv_count += 1

    logging.info(f"Scripts have been parsed, updated, and saved successfully.")
    logging.info(f"Total scripts updated: {script_count}")
    print(f"Total scripts updated: {script_count}")
    logging.info(f"Total CSV files generated: {csv_count}")
    print(f"Total CSV files generated: {csv_count}")

    with open(log_file, 'a') as log:
        log.write('\n')


def execute(source_folder_name, destination_folder):
    if os.path.isfile(source_folder_name):
        messagebox.showerror('Python Error', 'Error: Source folder location should be a directory, not a file.')
        return
    if not os.path.isabs(source_folder_name):
        source_folder = get_folder_location(source_folder_name)
    else:
        source_folder = source_folder_name
    if not source_folder or not os.path.exists(source_folder):
        messagebox.showwarning('Python Warning', 'Warning: Source folder not found.')
        return
    if not os.path.isabs(destination_folder):
        destination_folder_path = os.path.join(os.path.dirname(source_folder), destination_folder)
    else:
        destination_folder_path = destination_folder
    if not os.path.exists(os.path.dirname(destination_folder_path)):
        os.makedirs(destination_folder_path, exist_ok=True)
    Runner(source_folder, destination_folder_path)


def Parser_UI():
    # Create main window
    window = tk.Tk()
    window.title("Playwright Parser Utility")
    window.configure(bg='#000000')
    # Create form
    frame = tk.Frame(window)
    frame.pack(padx=5, pady=5)

    # Add source folder label and entry
    source_label = tk.Label(frame, text="Source Folder Path/Name:", bg='#ffffff', fg='#003366',
                            font=("Helvetica", 12, 'bold'))
    source_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')
    source_folder_field = tk.Entry(frame, width=50, bg='#f5f5f5', fg='#003366', font=("Helvetica", 12, 'bold'))
    source_folder_field.insert(0, "golden_scripts2")
    source_folder_field.grid(row=0, column=1, padx=30, pady=10)

    # Add destination folder label and entry
    destination_label = tk.Label(frame, text="Destination Folder Name:", bg='#ffffff', fg='#003366',
                                 font=("Helvetica", 12, 'bold'))
    destination_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')
    destination_folder_field = tk.Entry(frame, width=50, bg='#f5f5f5', fg='#003366', font=("Helvetica", 12, 'bold'))
    destination_folder_field.insert(0, "system_generated_scripts")
    destination_folder_field.grid(row=1, column=1, padx=30, pady=10)

    def generate():
        start_time = time.time()
        source_folder_name = source_folder_field.get().strip('"').strip("'")
        destination_folder = destination_folder_field.get().strip('"').strip("'")
        if not source_folder_name or not destination_folder:
            messagebox.showerror('Error', 'Error: Source and destination folders are required.', bg='#003366',
                                 fg='#ffffff')
            return
        execute(source_folder_name, destination_folder)
        end_time = time.time()
        elapsed_time = end_time - start_time
        source_folder_field.delete(0, tk.END)
        destination_folder_field.delete(0, tk.END)
        window.destroy()
        messagebox.showinfo("Result", f"The parser is executed in {elapsed_time:.2f} seconds.")

    generate_button = tk.Button(frame, text="Generate", command=generate, bg='#007bff', fg='white',
                                font=("Helvetica", 14, 'bold'), relief=tk.FLAT)
    generate_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

    # Run window
    window.mainloop()


Parser_UI()