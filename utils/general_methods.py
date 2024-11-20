import re
import allure
from playwright.sync_api import Page

# Logout Locators
_logout_button = "#sign-off"
_ok_button = "//span[normalize-space()='OK']"
_modal_message = '.el-message-box__message'
_modal_message1 = '#swal2-html-container'
_modal_yes_button = "//button[normalize-space()='Yes']"
_modal_ok_button = "button[class='el-button el-button--primary']"
_main_menu_button = '#main-menu'
_exit_button = '#ExitButton'
_ok_button1 = "#OkButton"
_slip_print_ok_button = "(//button[@id='OkButton'])[2]"
_voucher_number_dropdown1 = '#VoucherNumberDropDown-VoucherNumberDropDown'
_voucher_number_dropdown2 = '#VoucherNumberDropDown1-VoucherNumberDropDown'
_reference_number_dropdown1 = '#ReferenceNumberDropDown-ReferenceNumberDropDown'
_reference_number_dropdown2 = '#ReferenceNumberDropDown1-ReferenceNumberDropDown'
_advice_number_dropdown1 = '#AdvicesNumberDropDown-AdvicesNumbersDropDown'
_advice_number_dropdown2 = '#AdvicesNumberDropDown1-AdvicesNumbersDropDown'
_reference_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover'] span"
_voucher_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover']"
_advice_number = "div[aria-hidden='false'] li[class='el-select-dropdown__item selected hover']"
_confirmation_textbox = "#ConfirmationTextBox"
_cancellation_text = "(//div[@class='el-col el-col-24 el-col-md-11 el-col-lg-11'])[1]"
_teller_menu_button = "#teller"
_batch_menu_button = "(//button[normalize-space()='Batch'])"
_open_batch_button = "(//button[normalize-space()='Open'])"
_batch_password = "#PasswordTextBox"
_authorize_textbox = '#UserNameTextBox'
_batch_ok_button = "#OkButton"
_authorize_button = "#AuthorizeButton"
_batch_message = ".el-form-item__content"


def getVoucherAndReferenceNumberFromDropdown(page: Page, optional_ok_button: bool = True, advice_number: bool = False):
    with allure.step("----Get Voucher and Reference Number----"):
        if page.is_visible(_reference_number_dropdown1):
            _reference_number_dropdown = _reference_number_dropdown1
        elif page.is_visible(_reference_number_dropdown2):
            _reference_number_dropdown = _reference_number_dropdown2
        page.click(_reference_number_dropdown)
        reference_number = page.inner_text(_reference_number)
        page.press(_reference_number, "Enter")
        print(f"Message: {reference_number}")

        if page.is_visible(_voucher_number_dropdown1):
            _voucher_number_dropdown = _voucher_number_dropdown1
        elif page.is_visible(_voucher_number_dropdown2):
            _voucher_number_dropdown = _voucher_number_dropdown2
        page.click(_voucher_number_dropdown)
        voucher_number = page.inner_text(_voucher_number)
        page.press(_voucher_number, "Enter")
        print(f"Message: {voucher_number}")
        if advice_number:
            if page.is_visible(_advice_number_dropdown1):
                _advice_number_dropdown = _advice_number_dropdown1
            elif page.is_visible(_advice_number_dropdown2):
                _advice_number_dropdown = _advice_number_dropdown2
            page.click(_advice_number_dropdown)
            advice_number = page.inner_text(_advice_number)
            page.press(_advice_number, "Enter")
            print("Message: " + advice_number)
        page.wait_for_timeout(1000)
        page.click(_ok_button)
        if optional_ok_button:
            page.click(_slip_print_ok_button)
