# This is the Comment template used to add details in test scenario script.

"""
Script Name: <Your Script Name>
Description: <A brief description of what the script does>
FSM Name: <FSM Name>
Test Case: <Test Case>
Flow: <Positive or Negative>


Author: <Your Name>
Created Date: <Date when the script was created>
Last Modified Date: <Date of the last modification>
Version: <Version>

Dependencies: <List any dependencies>
Execution: <Instructions on how to execute the script, if necessary>

Change Log:
    - <Date>: <Description of changes made>
"""
# Recording Commands
[Normal]
playwright codegen <Url>

[In case of Http error]
playwright codegen --ignore-https-errors https://xyz/
playwright codegen --ignore-https-errors https://xyz/
playwright codegen --ignore-https-errors https://qa.xyz-xyz.org/






# How to set up Playwright on your local computer

[Step 1]
**Install all the software, such as Nodejs, Python, PyCharm, and Git Bash.**

[Step 2]
**After the installation, open PyCharm and create a new project in a virtual environment.**

[Step 3]
**Open the terminal, take a new session for the command prompt, and run the following commands:**

* set HTTPS_PROXY=http://127.0.0.1:8080
* set HTTP_PROXY=http://127.0.0.1:8080
* set https-proxy=http://127.0.0.1:8080
* set http-proxy=http://127.0.0.1:8080   

* pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
* pip config set global.strict-ssl false
* pip config set global.https-proxy http://127.0.0.1:8080
* pip config set global.proxy http://127.0.0.1:8080

[Step 4]
* Now install Playwright.
* pip install pytest-playwright
* python -m pip install --upgrade pip
* playwright install.
* pip install -r requirements.txt 

**Note: If you face any errors while installing, whitelist the URLs.**

[Step 5]
**After the installation of Playwright, run this command to record the scenario:**
* playwright codegen <URL>.

# Selenium Grid Integration
* java -jar selenium-server-4.15.0.jar hub
* java -jar selenium-server-4.15.0.jar node --hub http://127.0.0.1:4444/
* **Before running below commands Run Upper 4 command in step-3**
* java -jar selenium-server-4.15.0.jar node --hub http://127.0.0.1:4444 --selenium-manager true -I "chrome"
* java -jar selenium-server-4.15.0.jar node --hub http://127.0.0.1:4444 --selenium-manager true
* java -jar selenium-server-4.15.0.jar node --hub http://127.0.0.1:4444 --selenium-manager true  --session-timeout 300 -I "chrome"
* os.environ["SELENIUM_REMOTE_URL"] = "http://127.0.0.1:4444"