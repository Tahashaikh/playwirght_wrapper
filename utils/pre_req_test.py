import allure

from database.Queries import Queries
from database.database_connection import execute_query
from database.database_operations import update_system_ip
from conftest import get_file_location, read_json

test_data = read_json(get_file_location('test_data.json'))
current_branch_code = test_data['branch_code']
username = test_data['username']
authorizer = test_data['authorizer']
password = test_data['password']


def pre_req_user_setup(branch):
    # users = [{'VDQATST8': '3::2X=H/H8', 'VDQATST7': '3::2X=H/H8', 'VDQATST6': '3::2X=H/H8', 'VDQATST5': '3::2X=H/H8',
    #           'VDQATST1': '3::2X=H/H8', 'VDQATST2': '3::2X=H/H8',
    #           'VDQATST3': '3::2X=H/H8', 'VDQATST4': '3::2X=H/H8',
    #           'TSTING': 'HAAGB=H/Q*'}]
    # authorizer = [
    #     {'VDQAAUTH8': 'G::2X=H/F8', 'VDQAAUTH7': 'G::2X=H/F8', 'VDQAAUTH6': 'G::2X=H/F8', 'VDQAAUTH5': 'G::2X=H/F8',
    #      'VDQAAUTH1': 'G::2X=H/F8', 'VDQAAUTH2': 'G::2X=H/F8',
    #      'VDQAAUTH3': 'G::2X=H/F8', 'VDQAAUTH4': 'G::2X=H/F8',
    #      'TSTAUTH': 'OAAGB=H/W*'}]
    users = [{'TSTING': 'HAAGB=H/Q*','VDQATST1': '3::2X=H/H8','TSTING1': 'HAAGB=H/Q*'}]
    authorizer = [{'TSTAUTH1': 'OAAGB=H/W*','VDQAAUTH1': 'G::2X=H/F8','TSTAUTH1': 'OAAGB=H/W*'}]
    for name in users:
        for user, password in name.items():
            result = execute_query(branch, Queries.check_user_exists,
                                   values=(user.upper(), branch))
            check = result[0].get('USER_ID')
            if check == 0 or check == '0':
                execute_query(branch, Queries.user_insertion,
                              values=(branch, user.upper(), password))
            execute_query(branch, Queries.assign_rights_to_users,
                          values=(user.upper(), branch, user.upper(), branch))
            execute_query(branch, Queries.update_user_limit, values=(user.upper(), branch))
    for name in authorizer:
        for user, password in name.items():
            result = execute_query(branch, Queries.check_user_exists,
                                   values=(user.upper(), branch))
            check = result[0].get('USER_ID')
            if check == 0 or check == '0':
                execute_query(branch, Queries.auth_user_insertion,
                              values=(branch, user.upper(), password))
            execute_query(branch, Queries.assign_rights_to_users,
                          values=(user.upper(), branch, user.upper(), branch))
            execute_query(branch, Queries.update_auth_limit, values=(user.upper(), branch))
    execute_query(branch, Queries.update_password, values=("HAAGB=H/Q*", "TSTING"))
    execute_query(branch, Queries.update_password, values=("HAAGB=H/Q*", "TSTING1"))
    execute_query(branch, Queries.update_password, values=("3::2X=H/H8", "VDQATST1"))
    execute_query(branch, Queries.update_password, values=("G::2X=H/F8", "VDQAAUTH1"))
    execute_query(branch, Queries.update_password, values=("OAAGB=H/W*", "TSTAUTH1"))
    execute_query(branch, Queries.update_password, values=("OAAGB=H/W*", "TSTAUTH"))
    update_system_ip(Enable=True)


def pre_req_user_check(brn_cd, user):
    result = execute_query(brn_cd, Queries.check_user_exists,
                           values=(user.upper(), brn_cd))
    check = result[0].get('USER_ID')
    if check == 0 or check == '0':
        execute_query(brn_cd, Queries.user_insertion,
                      values=(brn_cd, user.upper(), password))
    execute_query(brn_cd, Queries.assign_rights_to_users,
                  values=(user.upper(), brn_cd, user.upper(), brn_cd))


def update_user_cert_dates(branch, user):
    execute_query(int(branch), Queries.update_user_dates,
                  values=(int(branch), user.upper()))
    execute_query(int(branch), Queries.assign_rights_to_users,
                  values=(user.upper(), branch, user.upper(), branch))


def branch_setup(branch):
    cpu_date = execute_query(int('1999'), Queries.Fetch_Brn_Date,int('1999'))
    brn_date = execute_query(int(branch), Queries.Fetch_Brn_Date,int(branch))
    if cpu_date[0]['REAL_DATE'] != brn_date[0]['REAL_DATE']:
         execute_query(int(branch), Queries.update_target_branch_date, values=(cpu_date[0]['REAL_DATE'], branch))

def user_setups(branch, user):
    pre_req_user_check(branch, user)
    pre_req_user_setup(branch)
    update_user_cert_dates(branch, user)
    branch_setup(branch)

