import os.path
import re
from contextlib import nullcontext

import allure
import json
from playwright.sync_api import Page

_ok_button1 = "#OkButton"
_slip_print_ok_button = "(//button[@id='OkButton'])[2]"
_voucher_number_dropdown1 = '#VoucherNumberDropDown-VoucherNumberDropDown'
_voucher_number_dropdown2 = '#VoucherNumberDropDown1-VoucherNumberDropDown'
_voucher_number_dropdown3 = '#VoucherNumberDropDown-GenericDropDown'
_reference_number_dropdown1 = '#ReferenceNumberDropDown-ReferenceNumberDropDown'
_reference_number_dropdown2 = '#ReferenceNumberDropDown1-ReferenceNumberDropDown'
_advice_number_dropdown1 = '#AdvicesNumberDropDown-AdvicesNumbersDropDown'
_advice_number_dropdown2 = '#AdvicesNumberDropDown1-AdvicesNumbersDropDown'
_reference_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover'] span"
_voucher_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover']"
_advice_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover']"
_Ref_NO = "(//div[@class='el-row']/div/div/div[@class='el-form-item__content'])[1]"
_Ref_NO2 = "(//div[@class='el-row']/div/div/div[@class='el-form-item__content'])[2]"
_Ref_No1 = "//p[contains(text(), 'Inter Branch PAY CASH Ref.No.')]"
_Ref_No2 = "//p[contains(text(), 'Inter Branch RECEIVE DEPOSIT Ref.No.')]"
_Inw_no = "//p[contains(text(), 'INW N')]"
_Req_no = "//p[contains(text(), 'Request N')]"
_Bill_no = "//p[contains(text(), 'Bill N')]"
_Bill_no2 = "(//*[contains(normalize-space(.), 'Bill N')])[last()]"
_Doc_no = "//p[contains(text(), 'Doc N')]"
_doc_bill = "//p[contains(text(), 'Document Bill')]"
_doc_bill2 = "(//*[contains(normalize-space(.), 'Document Bill')])[last()]"
_adv_pay_no = "(//*[contains(normalize-space(.), 'Advance Payment NO. ')])[last()]"
_adv_pay_no2 = "(//*[contains(normalize-space(.), 'Advance Payment N')])[last()]"
_contract_no = "(//*[contains(normalize-space(.), 'Contract N')])[last()]"
_Doc_num = "(//*[contains(normalize-space(.), 'Doc N')])[last()]"
_Vou_num = "(//*[contains(normalize-space(.), 'Voucher')])[last()]"
_Loan_no = "(//*[contains(normalize-space(.), 'Loan')])[last()]"
_IFDBC_num = "(//*[contains(normalize-space(.), 'IFDBC')])[last()]"
_LC_num = "(//*[contains(normalize-space(.), 'Swift')])[last()]"


def find_project_root(start_path, marker_files=None):
    if marker_files is None:
        marker_files = ['conftest.py', '.gitignore']

    current_path = start_path

    while current_path != os.path.dirname(current_path):
        if any(os.path.exists(os.path.join(current_path, marker)) for marker in marker_files):
            return current_path
        current_path = os.path.dirname(current_path)
    return None


def get_voucher_ref_detail(page: Page, **kwargs):
    resdic = {}

    if page.is_visible(_adv_pay_no):
        adv_no = page.inner_text(_adv_pay_no)
        if adv_no == 'Exposure Transfer' or 'SBP Cheque Outward':
            print(adv_no)
        else:
            adv_no = re.findall(r'\d+', adv_no)
            adv_no = adv_no[0] + ("/" + adv_no[1] if len(adv_no) > 1 and adv_no[1] else '')
            resdic['Adv_NO'] = f"{adv_no}"
            print(f"Message: {adv_no}")


    if page.is_visible(_Ref_No1):
        reference_number = page.inner_text(_Ref_No1)
        reference_number = reference_number.split(":")[1]
        resdic['Refno'] = f"{reference_number}"
        print(f"Message: {reference_number}")

    if page.is_visible(_Ref_No2):
        reference_number = page.inner_text(_Ref_No2)
        reference_number = reference_number.split(":")[1]
        resdic['Refno'] = f"{reference_number}"
        print(f"Message: {reference_number}")

    else:
        if page.is_visible(_reference_number_dropdown1) and page.is_enabled(_reference_number_dropdown1):
            _reference_number_dropdown = _reference_number_dropdown1
            page.click(_reference_number_dropdown)
            reference_number = page.inner_text(_reference_number)
            resdic['Refno'] = f"{reference_number}"
            page.press(_reference_number, "Enter")
            print(f"Message: {reference_number}")
        elif page.is_visible(_reference_number_dropdown2) and page.is_enabled(_reference_number_dropdown2):
            _reference_number_dropdown = _reference_number_dropdown2
            page.click(_reference_number_dropdown)
            reference_number = page.inner_text(_reference_number)
            resdic['Refno'] = f"{reference_number}"
            page.press(_reference_number, "Enter")
            print(f"Message: {reference_number}")

        if page.is_visible(_voucher_number_dropdown1) and page.is_enabled(_voucher_number_dropdown1):
            _voucher_number_dropdown = _voucher_number_dropdown1
            page.click(_voucher_number_dropdown)
            voucher_number = page.inner_text(_voucher_number)
            resdic['vouchernum'] = f"{voucher_number}"
            page.press(_voucher_number, "Enter")
            print(f"Message: {voucher_number}")
        elif page.is_visible(_voucher_number_dropdown2) and page.is_enabled(_voucher_number_dropdown2):
            _voucher_number_dropdown = _voucher_number_dropdown2
            page.click(_voucher_number_dropdown)
            voucher_number = page.inner_text(_voucher_number)
            resdic['vouchernum'] = f"{voucher_number}"
            page.press(_voucher_number, "Enter")
            print(f"Message: {voucher_number}")
        elif page.is_visible(_voucher_number_dropdown3) and page.is_enabled(_voucher_number_dropdown3):
            _voucher_number_dropdown = _voucher_number_dropdown3
            page.click(_voucher_number_dropdown)
            voucher_number = page.inner_text(_voucher_number)
            resdic['vouchernum'] = f"{voucher_number}"
            page.press(_voucher_number, "Enter")
            print(f"Message: {voucher_number}")

    page.wait_for_timeout(2000)

    selectors = [
        (_Ref_NO, 'Ref_No'),
        (_Ref_NO2, 'Ref_No2'),
        (_Vou_num, 'Vou_No'),
        (_IFDBC_num, 'IFDBC_NUM'),
        (_Inw_no, 'Inw_No'),
        (_Doc_no, 'Doc_No'),
        # (_Req_no, 'Ref_No'),
        (_Req_no, 'Request_No'),
        (_Loan_no, 'Loan_no'),
        (_Bill_no, 'Bill_No'),
        (_Bill_no2, 'Bill_No'),
        (_Doc_num, 'Doc_No'),
        (_adv_pay_no2, 'Advance_Pay_num'),
        (_contract_no, 'Contract_No'),
        (_doc_bill, 'Document_Bill'),
        (_doc_bill2, 'Document_Bill'),
        (_LC_num, 'LC_num')

    ]

    for selector, key in selectors:
        try:
            if page.is_visible(selector):
                text = page.inner_text(selector)
                base_key = "Screen_value"
                screen_key = base_key
                counter = 0
                # Find a unique key name
                while screen_key in resdic:
                    counter += 1
                    screen_key = f"{base_key}{counter}"
                # Store the raw text value
                numbers = re.findall(r'\d+', text)
                if len(numbers) >= 2:
                    resdic[screen_key] = text
                    resdic[key] = f"{numbers[0]}/{numbers[1]}"
                elif len(numbers) == 1:
                    resdic[screen_key] = text
                    resdic[key] = numbers[0]
                else:
                    raise ValueError(f"Unexpected number of digits found for {selector}: {numbers}")
                print(f"Message: {text}")
        except Exception as e:
            print(f"Error processing {selector}: {str(e)}")

    print(resdic)
    return resdic


def add_voucher_records(usecase_key, **kwargs):
    project_root = find_project_root(os.path.abspath(__file__))
    file_path = os.path.join(project_root, 'voucher_data.json')

    if not os.path.exists(project_root):
        os.makedirs(file_path)
    if not usecase_key:
        raise ValueError("usecase_name is required")
    else:
        usecase_key = usecase_key.replace("test_", "").replace(".py", "")

    data = {}

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                if file.read(1):
                    file.seek(0)
                    data = json.load(file)
                else:
                    data = {}
        except json.JSONDecodeError:
            print("Error: Json file is corrupted.")
            data = {}
    else:
        data = {}

    if usecase_key not in data:
        data[usecase_key] = []

    voucher_record = {}

    for key, value in kwargs.items():
        voucher_record[key] = value if value is not None and value != '' else None

    data[usecase_key].insert(0, voucher_record)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_values_from_json(usecase_key, **kwargs):
    project_root = find_project_root(os.path.abspath(__file__))
    file_path = os.path.join(project_root, 'voucher_data.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if usecase_key in data:
                value = data[usecase_key]
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    json_values = value[0]
                    kwargs.update(json_values)
                return kwargs
            else:
                print(f"Key '{usecase_key}' not found in the JSON data.")
                return None
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON.")
        return None


def check_key_in_json(usecase_key):
    project_root = find_project_root(os.path.abspath(__file__))
    file_path = os.path.join(project_root, 'voucher_data.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if usecase_key in data:
            return True
        else:
            return False
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file '{file_path}'")


def remove_voucher_records(usecase_key):
    project_root = find_project_root(os.path.abspath(__file__))
    file_path = os.path.join(project_root, 'voucher_data.json')
    if not usecase_key:
        raise ValueError("usecase_name is required")
    else:
        usecase_key = usecase_key.replace("test_", "").replace(".py", "")

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if usecase_key in data:
            items = data[usecase_key]

            if isinstance(items, list):
                if len(items) == 1:
                    removed_items = data.pop(usecase_key)
                    with open(file_path, 'w') as file:
                        json.dump(data, file, indent=4)
                        print(f"Removed key '{usecase_key}' with its subset: removed items: '{removed_items}'")
                elif len(items) > 1:
                    removed_items = items.pop(0)
                    with open(file_path, 'w') as file:
                        json.dump(data, file, indent=4)
                        print(f"Removed first subset: '{removed_items}'")
                return True
            else:
                print(f"Key '{usecase_key}' not found or its value is not in list.")

        else:
            print(f"The '{usecase_key}' not found in JSON.")
            return False

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file '{file_path}'")
