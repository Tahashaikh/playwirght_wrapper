# from functools import wraps
# from playwright.sync_api import Page, TimeoutError
#
#
# def handle_popup(func):
#     @wraps(func)
#     def wrapper(page: Page, *args, **kwargs):
#         def check_popup():
#             try:
#                 popup_button = page.locator(".modal-body")
#                 if popup_button.is_visible(timeout=5000):
#                     print("Pop-up detected.")
#                     message = popup_button.text_content().lower()
#                     valid_messages = ["this is a small modal. it has very less cont2ent",
#                                       "transaction cancelled",
#                                       "transaction stopped"]
#                     if message == valid_messages:
#                         print(f"Pop-up message: {message}")
#                         page.locator("#closeSmallModal").click()
#                     else:
#                         raise Exception(f"Unexpected pop-up message: {message} is not equal to {valid_messages}")
#                 else:
#                     print("No pop-up detected.")
#             except TimeoutError:
#                 print("Timeout occurred while checking for pop-up.")
#             except Exception as e:
#                 print(f"An error occurred: {e}")
#                 raise e
#
#         check_popup()
#         result = func(page, *args, **kwargs)
#         check_popup()
#
#         return result
#
#     return wrapper


from functools import wraps
from playwright.sync_api import Page, TimeoutError


def handle_popup(func):
    @wraps(func)
    def wrapper(page: Page, *args, **kwargs):
        def check_popup():
            try:
                popup_button = page.locator(".el-message-box__message")
                if popup_button.is_visible(timeout=5000):
                    message = popup_button.text_content().strip()
                    valid_messages = [
                        "Sign-on is Successful  Last Sign-on date is",
                        "transaction cancelled",
                        "transaction stopped"
                    ]
                    for valid_message in valid_messages:
                        if valid_message in message:
                            print(f"Pop-up message matched: {valid_message}")
                            page.locator("button[class='el-button el-button--primary']").click()
                            break
                    else:
                        raise Exception(f"Unexpected pop-up message: '{message}' did not match any "
                                        f"valid messages {valid_messages}.")
                else:
                    pass
            except TimeoutError:
                print("Timeout occurred while checking for pop-up.")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

        check_popup()
        result = func(page, *args, **kwargs)
        check_popup()

        return result

    return wrapper


def handle_popups(page: Page):
    page.wait_for_timeout(2000)
    popup_button = page.locator(".el-message-box__message")
    if popup_button.is_visible():
        message = popup_button.text_content().strip().lower()
        valid_messages = [
            "NO record Found",
            "No record found."
        ]
        for valid_message in valid_messages:
            if valid_message.strip().lower() in message.lower():
                # print(f"Pop-up message matched: {valid_message}")
                # page.locator("button[class='el-button el-button--primary']").click(
                if page.get_by_role('button', name='Ok').is_visible():
                    page.get_by_role('button', name='Ok').click()
                elif page.get_by_role('button', name='Yes').is_visible():
                    page.get_by_role('button', name='Yes').click()
                page.wait_for_timeout(2000)