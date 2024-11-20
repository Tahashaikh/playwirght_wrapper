import csv
import re
import os
import allure
import pandas
import pytest
import json
from datetime import datetime
from allure_commons.types import LinkType
from screeninfo.screeninfo import get_monitors
from playwright.sync_api import sync_playwright

BOLD = '\033[1m'
GREEN = '\033[92m'
RED = '\033[91m'
ORANGE = '\033[38;5;208m'
RESET = '\033[0m'
CYAN = '\033[96m'

from playwright.sync_api import expect
expect.set_options(timeout=60_000)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
run_config = os.path.join(PROJECT_ROOT, 'run_config.json')
with open(run_config, 'r') as f:
    run_config = json.load(f)
    run_on = run_config.get("Run_On").lower()

base_dir2 = "D:\\Reports"
Execution_Day = datetime.now().strftime('%Y-%m-%d')
base_dir = os.path.join(base_dir2, f"Reports_{Execution_Day}")
os.makedirs(base_dir, exist_ok=True)
execution_history = os.path.join(base_dir2, 'execution_summary.csv')
execution_cycles_report = os.path.join(base_dir, 'execution_cycles_report.csv')
run_id = os.getenv('TEST_RUN_ID')
if not run_id:
    run_id = datetime.now().strftime('%H-%M-%S')
    os.environ['TEST_RUN_ID'] = run_id
RESULTS_DIR = os.path.join(base_dir, f"Execution_{run_id}")
date_time_of_execution = f"{run_id}"
Execution_results_csv = os.path.join(RESULTS_DIR, f'Execution_report_{Execution_Day}-{run_id}.csv')
ALLURE_RESULTS_DIR = os.path.join(RESULTS_DIR, "Allure_Results")
HTML_RESULTS_DIR = os.path.join(RESULTS_DIR, "HTML_Results")
TEST_RESULTS_DIR = os.path.join(RESULTS_DIR, "Test_Results")
iteration_dir = None


@pytest.fixture(scope='session')
def base_url():
    print("BASE_URL fixture")
    env_config = os.path.join(PROJECT_ROOT, 'database', 'env_config.json')
    data, run_only_on = get_environment_config(env_config)
    return data.get("URL")


@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    print("Session Auto uses Setup Directories")
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    os.makedirs(HTML_RESULTS_DIR, exist_ok=True)
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
    if not hasattr(setup_directories, "iteration_count"):
        setup_directories.iteration_count = 0


@pytest.fixture(scope="function")
def page(request):
    print("Running Page Fixture")
    config = request.config
    slowmo = config.getoption("--slowmo")
    global iteration_dir
    iteration_count = getattr(setup_directories, "iteration_count", 0)
    setup_directories.iteration_count += 1

    iteration_dir = os.path.join(
        TEST_RESULTS_DIR,
        # f"Iteration-{iteration_count}-"
        f"{request.node.name.split('[')[0]}_TC_{str(request.node.name.split('[')[1][0])}"
    )
    os.makedirs(iteration_dir, exist_ok=True)
    allure.dynamic.link(url=iteration_dir, link_type=LinkType.TEST_CASE, name=iteration_dir)

    params_file_path = os.path.join(iteration_dir, 'params.txt')
    with open(params_file_path, 'w') as f:
        param_pattern = re.compile(r'\[(.*?)\]')
        params = re.findall(param_pattern, request.node.name)

        for param in enumerate(params):
            f.write(f"Params: {param}\n")

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True, slow_mo=slowmo, channel='chrome',timeout=60000)
    monitors = get_monitors()
    primary_monitor = monitors[0]
    viewport_width = primary_monitor.width - 30
    viewport_height = primary_monitor.height - 140

    context = browser.new_context(
        ignore_https_errors=True,
        record_video_dir=iteration_dir,
        record_video_size={"width": viewport_width, "height": viewport_height}
    )

    page = context.new_page()

    page.set_default_timeout(45000)
    page.set_default_navigation_timeout(45000)
    page.set_viewport_size({"width": viewport_width, "height": viewport_height})

    context.tracing.start(
        screenshots=True,
        snapshots=True
    )

    yield page
    print("Running after Page Fixture")
    try:
        trace_path = os.path.join(iteration_dir, 'trace.zip')
        context.tracing.stop(path=trace_path)

        screenshot_path = os.path.join(iteration_dir,
                                       f"{request.node.name.split('[')[0]}_TC_{str(request.node.name.split('[')[1][0])}_screenshot.png")
        page.screenshot(path=screenshot_path)

        execution_bat_path = os.path.join(iteration_dir, 'trace.bat')
        with open(execution_bat_path, 'w') as f:
            f.write(f'playwright show-trace "{trace_path}"\nexit')

    finally:
        print("Running Finally Page Fixture")
        page.close()
        context.close()
        browser.close()
        playwright.stop()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if run_on == "grid":
        os.environ["SELENIUM_REMOTE_URL"] = "http://127.0.0.1:4444"
        os.environ[
            "SELENIUM_REMOTE_CAPABILITIES"] = "{'mygrid:options':{os:'windows',platformName:'Windows 11',browserName:'chrome',acceptInsecureCerts:true}}"
    config.option.allure_report_dir = os.path.join(RESULTS_DIR, 'Allure_Results')
    config.option.htmlpath = os.path.join(RESULTS_DIR, 'HTML_Results', 'BasicReport.html')


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    print("pytest_runtest_makereport after")
    rep = outcome.get_result()
    if rep.when == "call":
        item.rep_call = rep
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get('page')
        if page and iteration_dir:
            timestamp = datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
            screenshot_dir = os.path.join(iteration_dir, "failure-screenshot")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"failure-screenshot_{timestamp}.png")
            page.screenshot(path=screenshot_path)
            allure.attach.file(screenshot_path, name=f"failure-screenshot_{timestamp}",
                               attachment_type=allure.attachment_type.PNG)


@pytest.fixture(scope="session", autouse=True)
def before_after_all():
    attach_batch_files_to_allure()
    write_environment_properties(ALLURE_RESULTS_DIR)
    # from utils.pre_req_test import pre_req_user_setup
    # pre_req_user_setup()
    yield
    if run_on == "grid":
        kill_remote_session()


@pytest.fixture(scope="function", autouse=True)
def before_after_test(request):
    print("before_after_test---before")
    yield
    print("before_after_test---after")
    test_name = f"{request.node.name.split('[')[0]}_TC_{str(request.node.name.split('[')[1][0])}"
    outcome = request.node.rep_call
    if outcome.failed:
        execution_cycles(Execution_results_csv, test_name, "Failed", date_time_of_execution, Execution_Day)
        execution_cycles(execution_cycles_report, test_name, "Failed", date_time_of_execution, Execution_Day)
        gen_execution_history(execution_history, test_name, "Failed", Execution_Day, date_time_of_execution,
                              RESULTS_DIR)
    elif outcome.skipped:
        execution_cycles(Execution_results_csv, test_name, "Skipped", date_time_of_execution, Execution_Day)
        execution_cycles(execution_cycles_report, test_name, "Skipped", date_time_of_execution, Execution_Day)
        gen_execution_history(execution_history, test_name, "Skipped", Execution_Day, date_time_of_execution,
                              RESULTS_DIR)
    elif outcome.passed:
        execution_cycles(Execution_results_csv, test_name, "Passed", date_time_of_execution, Execution_Day)
        execution_cycles(execution_cycles_report, test_name, "Passed", date_time_of_execution, Execution_Day)
        gen_execution_history(execution_history, test_name, "Passed", Execution_Day, date_time_of_execution,
                              RESULTS_DIR)
    print("before_after_test---after end")


def write_file(directory, name_with_extension, content):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, name_with_extension)
    with open(file_path, 'w') as f:
        f.write(content)


def attach_batch_files_to_allure():
    write_file(RESULTS_DIR, "allure_single_file.bat", "allure generate --single-file Allure_Results\nexit")
    write_file(RESULTS_DIR, "allure_serve.bat", "allure serve Allure_Results")


def get_environment_config(file_path="config.json"):
    try:
        data = read_json(file_path)
        run_only_on = data.get("Run_only_on", "")
        if run_only_on in data.get("environments", {}):
            environment_values = data["environments"][run_only_on]
            print(f"Environment: {run_only_on}")
            return environment_values, run_only_on
        else:
            print(f"Invalid Run_only_on value specified or environment not found: {run_only_on}")
            return None

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return None


def read_json(filename):
    with open(filename, "r") as file:
        try:
            json_data = json.load(file)
            return json_data
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error: Invalid JSON format in file '{filename}': {e}")


def write_environment_properties(results_dir):
    env_config_path = get_file_location('env_config.json')
    environment, run_only_on = get_environment_config(env_config_path)
    content = (
        f"ENVIRONMENT = {run_only_on}\n"
        f"URL: {environment.get('URL')}\n"
        f"BOX2: {environment.get('BOX2')}\n"
        f"BOX3: {environment.get('BOX3')}\n"
        f"BOX4: {environment.get('BOX4')}\n"
        f"CPU: {environment.get('CPU')}\n"
        f"OBS: {environment.get('OBS')}\n"
    )
    write_file(os.path.join(results_dir), "environment.properties", content)


def get_file_location(filename):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    for root, dirs, files in os.walk(root_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            return file_path

    print(f'{RED}File "{filename}" not found in directory "{root_dir}".{RESET}')
    return None


def get_folder_location(folder_name):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    for root, dirs, files in os.walk(root_dir):
        if folder_name in dirs:
            folder_path = os.path.join(root, folder_name)
            return folder_path

    print(f'{RED}Folder "{folder_name}" not found in directory "{root_dir}".{RESET}')
    return None


def execution_cycles(csv_path, test_name, status, time, date):
    rows = []
    file_exist = os.path.isfile(csv_path)
    time = time.replace('-', ':')
    if file_exist:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)

    if not file_exist or rows[0] != ['Test_Name', 'Last_Status', 'Iterations', 'Execution_Time',
                                     'Execution_Dime']:
        rows.insert(0, ['Test_Name', 'Last_Status', 'Iterations', 'Execution_Time', 'Execution_Dime'])

    updated = False
    for row in rows[1:]:
        if row[0] == test_name:
            row[1] = status
            execution_count = int(row[2]) + 1
            row[2] = str(execution_count)
            row[3] = time
            row[4] = date

            updated = True
            break
    if not updated:
        rows.append([test_name, status, '1', time, date])

    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)


import time


def gen_execution_history(csv_path, test_name, status, date, exec_time, result_folder):
    rows = []
    file_exist = os.path.isfile(csv_path)
    exec_time = exec_time.replace('-',':')
    if file_exist:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)

    if not file_exist or rows[0] != ['Test_Name', 'Status', 'Type', 'Iterations', 'Date', 'Time', 'Result_Folder']:
        rows.insert(0, ['Test_Name', 'Status', 'Type', 'Iterations', 'Date', 'Time', 'Result_Folder'])

    execution_count = 1
    for row in rows[1:]:
        if row[0] == test_name:
            execution_count = execution_count + 1
    rerun = "Normal"
    for row in rows[1:]:
        if row[0] == test_name and row[4] == date and row[5] == exec_time and row[6] == result_folder:
            rerun = "Rerun"
            break
    rows.append([test_name, status, rerun, str(execution_count), date, exec_time, result_folder])

    retry_count = 0
    while retry_count < 5:
        try:
            with open(csv_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            file.close()
            break
        except PermissionError:
            retry_count += 1
            time.sleep(1)  # wait for 1 second before retrying
    else:
        print("Failed to write to file after 5 retries")


def kill_remote_session():
    from selenium import webdriver
    drivers = []
    try:
        for _ in range(2):
            driver = webdriver.Remote(
                command_executor="http://127.0.0.1:4444",
                options=webdriver.ChromeOptions()
            )
            drivers.append(driver)
            print("Started a remote Chrome session.")
        yield
    finally:
        for driver in drivers:
            driver.quit()
            print("Killed a remote Chrome session.")
