import pandas as pd
import random
import socket
from database.Queries import *
from database.database_connection import *
from utils.utils import *
from conftest import *

test_data = read_json(get_file_location('test_data.json'))
current_branch_code = test_data['branch_code']
username = test_data['username']
authorizer = test_data['authorizer']
password = test_data['password']


# def update_system_ip(Enable=False):
#     if Enable:
#         current_system_ip = get_system_ip()
#         execute_query(int(current_branch_code), Queries.update_user_system_ip,
#                       values=(current_system_ip, current_branch_code, username))
#     else:
#         execute_query(int(current_branch_code), Queries.update_user_system_ip,
#                      values=("null", current_branch_code, username))


def first_test_data():
    data = []
    for i in range(20):
        row = {'username': f'standard_user{i}',
               'password': f'secret_sauce{i}'
               }
        data.append(row)
    return pd.DataFrame(data)


def Second_test_data():
    data = []
    for i in range(20):
        row = {'username1': f'standard_user{i}',
               'password': f'secret_sauce{i}'}
        data.append(row)
    return pd.DataFrame()


def third_test_data():
    data = []
    for i in range(20):
        row = {'username': f'standard_user{i}',
               'password': f'secret_sauce{i}'}
        data.append(row)
    return pd.DataFrame(data)