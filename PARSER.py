import ast
import csv
import re
import os
import time
import logging
import pandas as pd
from collections import defaultdict
import tkinter as tk
from tkinter import messagebox
from screeninfo.screeninfo import get_monitors
from conftest import get_folder_location
from utils.utils import *


def setup_logging():
    log_dir = get_root_path_join('logs')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = get_root_path_join('logs', 'parser.log')

    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return log_file


def rename_scripts(directory):
    try:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('test_'):
                    new_filename = f'test_{filename}'
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, new_filename)
                    os.rename(old_path, new_path)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_python_files(directory):
    py_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append((os.path.join(root, file), file))
    return py_files


def replace_goto_calls(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        code = ''.join(lines)
        goto_pattern = re.compile(r'page\.goto\((.*?)\)(?!\.click\(\))', re.DOTALL)
        updated_code = goto_pattern.sub('page.goto(base_url)', code)
        with open(file_path, 'w') as file:
            file.write(updated_code)
    except Exception as e:
        print(f"Error replacing goto calls in {file_path}: {e}")


def sanitize_locator(name):
    try:
        name = (name.replace("data-e2e", "")
                .replace("data-test", "")
                .replace("input", "")
                .replace("type", ""))
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        return name
    except Exception as e:
        print(f"An error occurred during sanitization: {e}")
        return None


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
            result[column] = f"{values[0][i]}"
        else:
            result[column] = None
    return result


def replace_multiple_variables(original_dict, replacement_dict, indent=12):
    indent_space = ' ' * indent
    formatted_result = "{\n" + ",\n".join(
        [
            f"{indent_space}'{k}': {replacement_dict[k]}" if k in replacement_dict else f"{indent_space}'{k}': '{v}'"
            for k, v in original_dict.items()]
    ) + "\n        }"

    return formatted_result


def add_method(file_path, method_name, column_values):
    values = convert_list_to_dict(column_values[0], column_values[1])
    replacement_dict = {
        'brncd': f'current_branch_code',
        'usernamebox': f'username',
        'passwordbox': f'password',
        'PasswordTextBox': f'password',
        'UserNameTextBox': f'authorizer',
        'PasswordTextBox1': f'password',
    }
    formatted_dict = replace_multiple_variables(values, replacement_dict)

    method_code = f"""\ndef {method_name}():
    result = execute_query(int(current_branch_code), Queries.fetch_customer,
                           values=(current_branch_code, "586", "81"))

    if isinstance(result, list):
        data = [{formatted_dict} for row in result]
        return pd.DataFrame(data)\n
"""
    imports_needed = """import pandas as pd
import random
import socket
from database.Queries import *
from database.database_connection import *
from utils.utils import *
from conftest import *

\ntest_data = read_json(get_file_location('test_data.json'))
current_branch_code = test_data['branch_code']
username = test_data['username']
authorizer = test_data['authorizer']
password = test_data['password']

\ndef update_system_ip(Enable=True):
    if Enable:
        current_system_ip = get_system_ip()
        execute_query(int(current_branch_code), Queries.update_user_system_ip,
                      values=(current_system_ip, current_branch_code, username))
    else:
        execute_query(int(current_branch_code), Queries.update_user_system_ip,
                      values=("null", current_branch_code, username))
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


def generate_database_operation_method(csv_path, script_name):
    column_header_value = read_values_from_csv(csv_path)
    method_name = f'{script_name}_data'
    func_name = method_name.removeprefix('test_')
    db_operations_path = get_root_path_join('database', 'database_operations.py')
    if not method_exists(db_operations_path, func_name):
        add_method(db_operations_path, func_name, column_header_value)


def read_values_from_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)
        values = df.values.tolist()
        return df.columns.tolist(), values
    except Exception as e:
        logging.error(f"Error reading values from CSV at {csv_path}: {e}")
        return [], []


def extract_page_lines(script_content, exclude_keywords=None):
    target_strings = ['fill', 'get_by_text', 'filter',
                      'get_by_role', 'goto',
                      'get_by_placeholder',
                      'get_by_label',
                      'click']

    if exclude_keywords is None:
        exclude_keywords = set()
    else:
        exclude_keywords = set(exclude_keywords)

    lines = script_content.splitlines()
    line_map = {i + 1: line.strip() for i, line in enumerate(lines)}

    target_lines = []
    excluded_lines = []

    tree = ast.parse(script_content)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Expr, ast.Assign)):
            start_lineno = node.lineno
            end_lineno = getattr(node, 'end_lineno', start_lineno)
            code_lines = [line_map.get(i, '') for i in range(start_lineno, end_lineno + 1)]
            code_line = '\n'.join(code_lines)
            # if any(string in code_line for string in target_strings):
            if 'page.' in code_line:
                if any(keyword in code_line for keyword in exclude_keywords):
                    excluded_lines.extend([(i, line) for i, line in enumerate(code_lines, start_lineno)])
                else:
                    target_lines.extend([(i, line) for i, line in enumerate(code_lines, start_lineno)])

    return target_lines, excluded_lines


def extract_single_line_comments(script_content):
    single_line_comments = []
    lines = script_content.splitlines()

    for lineno, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            single_line_comments.append((lineno, stripped_line))

    return single_line_comments


def extract_multi_line_comments(script_content):
    multi_line_comments = []
    multi_line_comment_pattern = re.compile(r"(?:'''(.*?)'''|\"\"\"(.*?)\"\"\")", re.DOTALL)

    for match in multi_line_comment_pattern.finditer(script_content):
        comment = match.group(1) if match.group(1) else match.group(2)
        start_lineno = script_content.count('\n', 0, match.start()) + 1
        end_lineno = start_lineno + comment.count('\n') + 1
        multi_line_comments.append((start_lineno, end_lineno, '"""' + comment + '\n"""\n'))

    return multi_line_comments


def extract_page_lines_and_comments(script_content, exclude_keywords=None):
    page_lines, excluded_lines = extract_page_lines(script_content, exclude_keywords)
    single_line_comments = extract_single_line_comments(script_content)
    multi_line_comments = extract_multi_line_comments(script_content)
    return page_lines, single_line_comments, multi_line_comments, excluded_lines


def extract_and_replace_fill_values(script_content):
    class AST_Visitor(ast.NodeVisitor):
        def __init__(self):
            self.lines = []
            self.values = []
            self.locators = []
            self.updated_lines = []
            self.locator_count = defaultdict(int)
            self.ignore_lines = set()

        def get_string_value(self, node):
            if isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Call):
                if any(keyword in ast.unparse(node.func) for keyword in ['str', 'random', 'randint']):
                    return None
                else:
                    return self.get_string_value(node.args[0])
            elif isinstance(node, ast.Num):
                return node.n
            return None

        def get_function_name(self, node):
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return self.get_function_name(node.value)
            return None

        def _generate_unique_locator(self, variable_name):
            occurrence_index = self.locator_count[variable_name]
            unique_locator = f'{variable_name}{occurrence_index}' if occurrence_index > 0 else variable_name
            self.locator_count[variable_name] += 1
            return unique_locator

        @staticmethod
        def replace_string_literal(original_line, var_name, value):
            updated_line = original_line.replace(f"'{value}'", f'str({var_name})')
            updated_line = updated_line.replace(f'"{value}"', f'str({var_name})')
            return updated_line

        def add_value_and_locator(self, value, locator):
            self.values.append(value)
            self.locators.append(locator)

        def track_updated_line(self, node, updated_line):
            self.lines.append((node.lineno, updated_line))
            self.updated_lines.append((node.lineno, updated_line))

        def visit_Call(self, node):
            line_number = node.lineno
            if any(line.strip().startswith('expect') for line in
                   script_content.splitlines()[line_number - 1:line_number]):
                return

            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                locator_node = node.func.value

                if method_name == 'fill' and isinstance(locator_node, ast.Call):
                    if hasattr(locator_node.func, 'attr') and locator_node.func.attr == 'get_by_text':
                        value_node = locator_node.args[0] if locator_node.args else None
                        fill_value_node = node.args[0] if node.args else None

                        get_text_value = self.get_string_value(value_node)
                        fill_value = self.get_string_value(fill_value_node)

                        get_by_text_var = self._generate_unique_locator('get_by_text_data')
                        get_fill_value_var = self._generate_unique_locator('get_by_text_data_val')

                        if get_text_value is not None:
                            self.add_value_and_locator(get_text_value, get_by_text_var)

                        if fill_value is not None:
                            self.add_value_and_locator(fill_value, get_fill_value_var)

                        updated_line = script_content.splitlines()[node.lineno - 1].strip()
                        if get_text_value:
                            updated_line = self.replace_string_literal(updated_line, get_by_text_var, get_text_value)

                        if fill_value:
                            updated_line = self.replace_string_literal(updated_line, get_fill_value_var, fill_value)

                        self.track_updated_line(node, updated_line)
                        return

                if method_name == 'type':
                    value_node = node.args[1] if method_name == 'type' and len(node.args) == 2 else node.args[0] \
                        if node.args else None

                    fill_value = self.get_string_value(value_node)

                    if value_node is not None:
                        if node.args:
                            locator_str = ast.get_source_segment(script_content, node.func.value.args[0]) if isinstance(
                                locator_node, ast.Call) else ast.get_source_segment(script_content, node.args[0])
                        else:
                            locator_str = None

                        sanitized_locator = sanitize_locator(str(locator_str))
                        self.locator_count[sanitized_locator] += 1

                        if self.locator_count[sanitized_locator] > 1:
                            sanitized_locator = f"{sanitized_locator}{self.locator_count[sanitized_locator] - 1}"

                        if fill_value is not None:
                            self.add_value_and_locator(fill_value, sanitized_locator)

                        updated_line = ast.get_source_segment(script_content, node)
                        updated_line = self.replace_string_literal(updated_line, sanitized_locator, fill_value)
                        self.track_updated_line(node, updated_line)

                # if method_name == 'fill':
                #     value_node = node.args[1] if method_name == 'fill' and len(node.args) == 2 else node.args[0] \
                #         if node.args else None
                #
                #     fill_value = self.get_string_value(value_node)
                #
                #     if value_node is not None:
                #         if node.args:
                #             locator_str = ast.get_source_segment(script_content, node.func.value.args[0]) if isinstance(
                #                 locator_node, ast.Call) else ast.get_source_segment(script_content, node.args[0])
                #         else:
                #             locator_str = None
                #
                #         sanitized_locator = sanitize_locator(str(locator_str))
                #         self.locator_count[sanitized_locator] += 1
                #
                #         if self.locator_count[sanitized_locator] > 1:
                #             sanitized_locator = f"{sanitized_locator}{self.locator_count[sanitized_locator] - 1}"
                #
                #         if fill_value is not None:
                #             self.add_value_and_locator(fill_value, sanitized_locator)
                #
                #         updated_line = ast.get_source_segment(script_content, node)
                #         updated_line = self.replace_string_literal(updated_line, sanitized_locator, fill_value)
                #         self.track_updated_line(node, updated_line)

                if method_name == 'fill':
                    value_node = node.args[1] if method_name == 'fill' and len(node.args) == 2 else node.args[0] \
                        if node.args else None

                    fill_value = self.get_string_value(value_node)

                    if value_node is not None:
                        if node.args:
                            locator_str = ast.get_source_segment(script_content, node.func.value.args[0]) if isinstance(
                                locator_node, ast.Call) else ast.get_source_segment(script_content, node.args[0])
                        else:
                            locator_str = None

                        sanitized_locator = sanitize_locator(str(locator_str))

                        if sanitized_locator is None or sanitized_locator.strip() == '':
                            updated_line = ast.get_source_segment(script_content, node)
                            empty_locator = self._generate_unique_locator('date')
                            updated_line = updated_line.replace(f'"{fill_value}"', f"str({empty_locator})")
                            self.add_value_and_locator(fill_value, empty_locator)
                            self.track_updated_line(node, updated_line)
                        else:
                            self.locator_count[sanitized_locator] += 1

                            if self.locator_count[sanitized_locator] > 1:
                                sanitized_locator = f"{sanitized_locator}{self.locator_count[sanitized_locator] - 1}"

                            if fill_value is not None:
                                self.add_value_and_locator(fill_value, sanitized_locator)

                            updated_line = ast.get_source_segment(script_content, node)
                            updated_line = self.replace_string_literal(updated_line, sanitized_locator, fill_value)
                            self.track_updated_line(node, updated_line)

                elif method_name == 'get_by_text':
                    value_node = node.args[0] if node.args else None
                    get_text_value = self.get_string_value(value_node)

                    get_fill_value_var = self._generate_unique_locator('get_by_text')

                    if get_text_value is not None:
                        self.add_value_and_locator(get_text_value, get_fill_value_var)

                        full_line = script_content.splitlines()[node.lineno - 1].strip()
                        updated_line = self.replace_string_literal(full_line, get_fill_value_var, get_text_value)
                        self.track_updated_line(node, updated_line)

                elif method_name == 'get_by_role':
                    value_node = node.args[0] if node.args else None
                    get_role_value = self.get_string_value(value_node)

                    if get_role_value in ['cell', 'row']:
                        full_line = script_content.splitlines()[node.lineno - 1].strip()
                        name_node = node.keywords[0].value if node.keywords else None

                        if name_node:
                            name_value = self.get_string_value(name_node)
                            name_var = self._generate_unique_locator('get_by_role_name')
                            self.add_value_and_locator(name_value, name_var)
                            updated_line = re.sub(r'name="[^"]+"', 'name=str({})'.format(name_var), full_line)
                        self.track_updated_line(node, updated_line)

                elif method_name == 'filter':
                    has_text_arg = next((kwarg for kwarg in node.keywords if kwarg.arg == 'has_text'), None)
                    if has_text_arg and isinstance(has_text_arg.value, ast.Str):
                        has_text = self.get_string_value(has_text_arg.value)
                        if has_text_arg.value is not None:
                            if isinstance(locator_node, ast.Call):
                                locator_str = ast.get_source_segment(script_content, node.func.value.args[0])
                            else:
                                if node.args:
                                    locator_str = ast.get_source_segment(script_content, node.args[0])
                                else:
                                    locator_str = None

                            if locator_str is not None:
                                sanitized_locator = sanitize_locator(str(locator_str))
                                self.locator_count[sanitized_locator] += 1

                                if self.locator_count[sanitized_locator] > 1:
                                    sanitized_locator = f"{sanitized_locator}{self.locator_count[sanitized_locator] - 1}"

                                self.add_value_and_locator(has_text, sanitized_locator)
                                full_line = script_content.splitlines()[node.lineno - 1].strip()
                                updated_line = self.replace_string_literal(full_line, sanitized_locator, has_text)
                                self.track_updated_line(node, updated_line)

                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value,
                                                                         ast.Name) and node.func.value.id == 'random' and node.func.attr == 'randint':
                    if len(node.args) == 2 and all(isinstance(arg, ast.Constant) for arg in node.args):
                        start = node.args[0].value
                        end = node.args[1].value
                        updated_line = script_content.splitlines()[node.lineno - 1].strip()
                        original_call = f'random.randint({start}, {end})'
                        str_call = f'str(random.randint({start}, {end}))'
                        if original_call in updated_line and str_call not in updated_line:
                            updated_line = updated_line.replace(original_call, str_call)
                            self.track_updated_line(node, updated_line)

                        return

            self.generic_visit(node)

    tree = ast.parse(script_content)
    visitor = AST_Visitor()
    visitor.visit(tree)

    return visitor.lines, visitor.values, visitor.locators, visitor.updated_lines


def create_csv_file(locators, values, csv_filename):
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=locators)
        writer.writeheader()
        writer.writerow(dict(zip(locators, values)))


def generate_updated_script(original_lines, updated_lines):
    updated_lines_dict = dict(updated_lines)
    original_lines_dict = dict(original_lines)
    all_lines = {**original_lines_dict, **updated_lines_dict}
    sorted_lines = [all_lines[lineno] for lineno in sorted(all_lines)]

    return '\n    '.join(sorted_lines)


def process_script_with_ast(script_content_path, updated_script_path, csv_path, script_name, allure_parameters):
    try:

        """Read the script content from the file"""
        with open(script_content_path, 'r') as f:
            script_content = f.read()

        """Extract relevant information from the script"""
        exclude_keywords = ['expect(', 'random', 'randint', 'str(']
        page_lines, single_line_comments, multi_line_comments, excluded_lines = extract_page_lines_and_comments(
            script_content, exclude_keywords)

        """Extract relevant information from the script"""
        lines_with_methods, values, locators, updated_lines = extract_and_replace_fill_values(script_content)

        """Create CSV file from the extracted data & Read values from the created CSV file"""
        create_csv_file(locators, values, csv_path)

        """Generate updated script lines"""
        updated_script = generate_updated_script(page_lines + single_line_comments, updated_lines + excluded_lines)

        """Combine all multi-line comments into a single string"""
        multiline_comment_lines = ""
        for start_lineno, end_lineno, comment in multi_line_comments:
            multiline_comment_lines += f"{comment}\n"

        """Prepare the parameterized parameters string for pytest"""
        parametrize_params = ', '.join(locators)

        """ Generate the updated script content"""
        updated_script_content = f"""{multiline_comment_lines}
import pytest
import random
import pandas as pd
import allure
from database.database_operations import *
from playwright.sync_api import Page, expect
from utils.pre_req_test import pre_req_user_setup

\ndef read_values_from_csv():
    pre_req_user_setup()
    df = pd.read_csv(f"{{os.path.dirname(__file__)}}"+r'\\{script_name}.csv')
    df.index += 1
    df.reset_index(inplace=True)
    df.rename(columns={{'index': 'count'}}, inplace=True)
    return df.values.tolist()

\ncsv_data = read_values_from_csv()

\n@allure.feature('{allure_parameters[0]}')
@allure.story('{script_name.replace('test_', '')}')
@pytest.mark.parametrize('count, {parametrize_params}', csv_data)
def {script_name}(page: Page,count, {', '.join(locators)}, base_url) -> None:
    allure.dynamic.title(f"{script_name.replace('test_', '')}_TC_{{count}}")
    update_system_ip()
    {updated_script}
"""

        """ Write the updated script content to the specified path"""
        with open(updated_script_path, 'w') as file:
            file.write(updated_script_content)

        logging.info(f"Updated script saved to {updated_script_path}")

    except Exception as e:
        logging.error(f"Error processing script {script_content_path}: {e}")


def runner(destination_dir):
    source_dir = get_folder_location('golden_scripts')
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir, exist_ok=True)

    script_count = 0
    csv_count = 0

    rename_scripts(source_dir)
    for script_file in get_python_files(source_dir):
        script_path = script_file[0]
        if os.path.isfile(script_path):
            script_name = os.path.splitext(script_file[1])[0]
            updated_script_path = script_path.replace(source_dir, destination_dir)
            script_directory = updated_script_path.replace(script_file[1], "")
            if not os.path.exists(script_directory):
                os.makedirs(script_directory)
            csv_path = os.path.join(script_directory, f'{script_name}.csv')
            allure_params = script_directory.replace(f"{script_name}.py", '').removesuffix('\\').split('\\')
            """Final Processing"""
            process_script_with_ast(script_path, updated_script_path, csv_path, script_name, allure_params)
            # generate_database_operation_method(csv_path, script_name)
            replace_goto_calls(updated_script_path)
            script_count += 1
            csv_count += 1

    logging.info(f"Scripts have been parsed, updated, and saved successfully.")
    logging.info(f"Total scripts updated: {script_count}")
    print(f"Total scripts updated: {BOLD}{GREEN}{script_count}{RESET}")
    logging.info(f"Total CSV files generated: {csv_count}")
    print(f"Total CSV files generated: {BOLD}{GREEN}{csv_count}{RESET}")


def PARSER():
    root = tk.Tk()
    root.title("Parser Utility")
    root.configure(bg='#000000')

    root.geometry('900x200')
    tk.Label(root, text="Parser Utility",
             bg='#000000', fg='#FFFFFF',
             font=("Helvetica", 18, 'bold')).grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    tk.Label(root, text="Enter the output directory for the generated scripts:",
             bg='#000000', fg='#FFFFFF',
             font=("Helvetica", 14)).grid(row=1, column=0, padx=20, pady=5)
    tk.Label(root, text="(Default: system generated scripts)",
             bg='#000000', fg='#FFFFFF',
             font=("Helvetica", 12, 'bold')).grid(row=2, column=0, padx=20, pady=5)

    system_generated_scripts_dir_entry = tk.Entry(root, width=30, bg='#000000', fg='#FFFFFF',
                                                  font=("Helvetica", 14),
                                                  highlightbackground='#007bff', highlightcolor='#007bff',
                                                  highlightthickness=2, insertbackground='white')
    system_generated_scripts_dir_entry.grid(row=1, column=1, padx=20, pady=5)

    def run_parser():
        system_generated_scripts_dir = system_generated_scripts_dir_entry.get()
        if not system_generated_scripts_dir:
            root.withdraw()
            response = messagebox.askyesno("Default Directory", "No directory was entered by you.\nDo you want to "
                                                                "generate the scripts in default directory?")
            if response:
                system_generated_scripts_dir = 'system_generated_scripts'
            else:
                messagebox.showerror("Invalid Input", "Please enter a valid directory.")
                root.deiconify()
                return
        root.withdraw()
        log_file = setup_logging()
        start_time = time.time()
        runner(system_generated_scripts_dir)
        end_time = time.time()
        total_time = end_time - start_time
        logging.info(f"Total time taken: {total_time:.2f} seconds")
        print(f"{BOLD}{GREEN}Total time taken: {total_time:.2f} seconds")
        root.destroy()
        with open(log_file, 'a') as log:
            log.write('\n')

    system_generated_scripts_dir_entry.bind('<Return>', lambda event: run_parser())

    run_button = tk.Button(root, text="Generate", command=lambda: run_parser(), bg='#007bff', fg='white',
                           font=("Helvetica", 14, 'bold'), relief=tk.FLAT)
    run_button.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky='ew')
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    primary_monitor = get_monitors()[1] if len(get_monitors()) > 1 else get_monitors()[0]
    x = primary_monitor.x + (primary_monitor.width / 4) - (root.winfo_width() / 4)
    y = primary_monitor.y + (primary_monitor.height / 4) - (root.winfo_height() / 4)
    root.geometry(f"+{int(x)}+{int(y)}")

    root.mainloop()


PARSER()
