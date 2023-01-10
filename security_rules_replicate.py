#!/usr/bin/env python3
import argparse
import prisma_sase
import yaml
import json
import panapi
from panapi.config import identity,management,security
from time import sleep

def sdk_login_to_controller(filepath):
    with open(filepath) as f:
        client_secret_dict = yaml.safe_load(f)
        client_id = client_secret_dict["client_id"]
        client_secret = client_secret_dict["client_secret"]
        tsg_id_str = client_secret_dict["scope"]
        tsg = tsg_id_str.split(":")[1]
        print(client_id, client_secret, tsg)
     
    sdk = prisma_sase.API(controller="https://sase.paloaltonetworks.com/", ssl_verify=False)
    sdk.set_debug(3) 
    sdk.interactive.login_secret(client_id, client_secret, tsg)
    
    return sdk

def create_security_rule_on_t2(url, payload, T2_secret_filepath):
    sdk = sdk_login_to_controller(T2_secret_filepath)
    
    resp = sdk.rest_call(url=url, data=payload,method="POST")
    sdk.set_debug(3)
    print(resp)
    
def push_security_rules_to_cloud(folder):
    #Building the session handler
    session = panapi.PanApiSession()
    session.authenticate()

    #Push the config and waiting for the job to complete
    print('Pushing the configuration')
    job = management.ConfigVersion(folders=['Mobile Users']).push(session)
    job_complete = False
    while job_complete is False:
        job.read(session)
        if session.response.status_code == 200:
            status = session.response.json()['data'][0]['status_str']
            print('Polling job [{}]: {}'.format(job.id, status))
            if status == 'FIN':
                job_complete = True
            elif status == 'PEND' or status == 'ACT':
                job_complete = False
            else:
                job_complete = True
        else:
            print('API call failure!')
            break
        sleep(5)

def fetch_security_rules_from_tenant(sdk1, folder, position,T2_secret_filepath):
     sdk = sdk1
     
     #Fetch all the security rules
     url = "https://api.sase.paloaltonetworks.com/sse/config/v1/security-rules?"+"position="+position+"&folder="+folder
     print(url)

     resp = sdk.rest_call(url=url, method="GET")
     sdk.set_debug(3)
     print(resp)

     print("RESPONSE IS {}".format(resp.json()))
     response_payload = resp.json()
     data_list = response_payload["data"]
     print("Data List: {}".format(data_list)) 
     
     list_security_rule_fields = [
                "action",
                "application",
                "category",
                "description",
                "destination",
                "destination_hip",
                "disabled",
                "from",
                "log_setting",
                "name",
                "negate_destination",
                "negate_source",
                "profile_setting",
                "service",
                "source",
                "source_hip",
                "source_user",
                "tag",
                "to"
               ]
 
     default = ["any"] 
     for data in data_list:
         print(data)
         
         payload = {
             "name": data["name"]
         }
         for field in list_security_rule_fields:
             if data.get(field) is not None:
                 payload[field] = data[field]
             else:
                 pass
         create_security_rule_on_t2(url, payload, T2_secret_filepath)
     push_security_rules_to_cloud(folder) 


if __name__ == "__main__":

     #Parsing the arguments to the script
     parser = argparse.ArgumentParser(description='Onboarding the LocalUsers, Service Connection and Security Rules.')
     parser.add_argument('-t1', '--T1Secret', help='Input secret file in .yml format for the tenant(T1) from which the security rules have to be replicated.') 
     parser.add_argument('-t2', '--T2Secret', help='Input secret file in .yml format for the tenant(T2) to which the security rules have to be replicated.')
     parser.add_argument('-folder', '--folder', help='Folder from where the Rules have to be read on the tenant T1.')
     parser.add_argument('-p', '--destRulePos', help='Position from where the Rules have to be read from tenant T1 (pre/post)')
     parser.add_argument('-o', '--omitrules', help='Input file containing list of rules to be omitted from creation')

     args = parser.parse_args()
     T1_secret_filepath = args.T1Secret
     T2_secret_filepath = args.T2Secret
     folder = args.folder
     position = args.destRulePos
     if position not in ("pre", "post"):
         print("Enter a valid option pre/post for -l")
         exit()

     #Pass the secret of 'from tenant' to login
     sdk1 = sdk_login_to_controller(T1_secret_filepath)
     
     #Fetch the security rules from tenant t1
     fetch_security_rules_from_tenant(sdk1,folder, position, T2_secret_filepath)
    
    
