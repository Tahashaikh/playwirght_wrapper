import os
import json
import random
import socket
import string

import pandas as pd
import pytest

from conftest import PROJECT_ROOT

BOLD = '\033[1m'
GREEN = '\033[92m'
RED = '\033[91m'
ORANGE = '\033[38;5;208m'
RESET = '\033[0m'
CYAN = '\033[96m'


def get_root_path_join(*sub_paths):
    return os.path.join(PROJECT_ROOT, *sub_paths)


def get_system_ip():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        print("Error:", e)
        return None


def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


def generate_random_cnic():
    five = str(random.randint(10000, 99999))
    seven = str(random.randint(1000000, 9999999))
    one = str(random.randint(0, 9))
    random_cnic = f"{five}-{seven}-{one}"
    return random_cnic


def generate_random_number(minimum, maximum):
    return random.randint(minimum, maximum)


def read_values_from_csv(path):
    df = pd.read_csv(path)
    print(df.index)
    if df.empty or df.isnull().all().all():
        data = {col: [None] for col in df.columns}
        data['skip'] = [True]
        df = pd.DataFrame(data)
    else:
        df['skip'] = False
    df.index += 1
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'count'}, inplace=True)
    return df.values.tolist()


# read_values_from_csv("E:\\ALL_PROJECTS\\Playwright_R2_Automation\\R2-Automation\\system_generated_scripts\\TLR_OBC_IBC_UC2_OBC_LO_C\\test_TLR_OBC_IBC_UC2_OBC_LO_C_S1.csv")