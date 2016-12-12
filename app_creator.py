# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 13:51:07 2016

@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

Dependencies: 
    sudo pip install requests
"""
import pickle
import requests
import time
import app_web_driver

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() # if python version < 2.7.9

class AppCreator(object):
    json_headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
    
    def __init__(self, instance_prefix, auth_pair, run_variables, prev_state = {}):
        self.instance_prefix = instance_prefix 
        self.auth_pair = auth_pair
        self.run_variables = run_variables
        self.web_driver = app_web_driver.AppWebDriver(instance_prefix, auth_pair)
        self.state_variables = prev_state
        if not self.state_variables:
            self.state_variables['state'] = 1
        self.logged = []
        self.state_map = {}

    def log(self, message, indent = True):
        # Indent subsequent messages from the same state
        if indent and self.logged and self.logged[-1][0] == self.state_variables['state']:
                message = '\t'+message
        self.logged.append((self.state_variables['state'],message))
        print message
 
    def get_progress_string(self, state_started = False):
        completion_state = float(len(self.state_map))
        progress = round(((self.state_variables['state']-state_started)/completion_state)*100)
        progress_string = "Step {} of {} ({}%) ".format(self.state_variables['state'],completion_state,
                                                        progress)
        return progress_string
                                                            
    def get_json_response_key(self, key, url, post_data = ""):
        return_value = None
        path = url.split(".service-now.com")[1]
        log = "Could not parse {} in json response from {}.".format(key, path)
        
        if post_data:
            response = requests.post(url, auth=self.auth_pair,
                                     headers=self.json_headers, data=post_data)
        else:
            response = requests.get(url, auth=self.auth_pair, 
                                    headers=self.json_headers)
        json_response = {}
        try:
            if response.status_code == 200:
                json_response = response.json()['result'][0]
            elif response.status_code == 201:
                json_response = response.json()['result']
            else:
                log = "Unsuccessful response code from {}: {}.".format(path, response.status_code)
        except:
            log = "Error parsing result field in json response from {}".format(path)
    
        if key in json_response:
            return_value = json_response[key]
            log = "Parsed {} in json response from {}.".format(key, path)
            
        return return_value, log

    def verify_post_data(self, url, post_data):
        success = False
        path = url.split(".service-now.com")[1]
        log = "POST {} response did not have status code 201.".format(path)
        
        response = requests.post(url, auth=self.auth_pair, headers=self.json_headers, data=post_data)
        if response.status_code == 201:
            success = True
            log = "POST {} response had status code 201 (expected).".format(path)
        else:
            log = "POST {} response had status code {}, expected 201.".format(path, response.status_code)
            
        return success, log
        
    def verify_put_data(self, url, post_data):
        success = False
        path = url.split(".service-now.com")[1]
        log = "PUT {} response did not have status code 200.".format(path)
        
        response = requests.put(url, auth=self.auth_pair, headers=self.json_headers, data=post_data)
        if response.status_code == 200:
            success = True
            log = "PUT {} response had status code 200.".format(path)
        else:
            log = "PUT {} response had status code {}, expected 200.".format(response.status_code, path)
            
        return success, log
            
    def check_login_credentials(self):
        success = self.web_driver.logged_in
        log = "Logged in to {} successfully.".format(self.instance_prefix)
        if not success:
            log = "Failed to login to {}, invalid credentials.".format(self.instance_prefix)
        return success, log
            
    def check_for_table(self, table_name):
        success = False
        log = "The {} table already exists.".format(table_name)
        url = "https://{}.service-now.com/api/now/table/sys_dictionary?"\
                "sysparm_query=name%3D{}&sysparm_limit=1".format(self.instance_prefix, table_name)
        response = requests.get(url, auth=self.auth_pair, headers=self.json_headers)
        if response.status_code == 200:
            if not response.json()['result']:
                success = True
                log = "The {} table does not exist.".format(table_name)
        elif response.status_code == 401:
            log = "Invalid username/password, could not authenticate request."
        else:
            log = "GET query for table name did not have status code 200."
        
        return success, log 
            
    def run(self):
        self.log("Starting run from step {}...".format(self.state_variables['state']))
        start_time = time.time()
        
        while(self.state_variables['state'] <= len(self.state_map)):
            state_func, state_desc = self.state_map[self.state_variables['state']]
                        
            self.log("{} STARTED: {}".format(self.get_progress_string(True), state_desc), False)
            success, log = state_func()
  
            if success:
                self.log(log)
                self.log("{} SUCCESS: Completed step successfully.".format(self.get_progress_string()), False)
            else:
                self.log("{} FAILURE: {}".format(self.get_progress_string(True), log), False)
                self.log("Ending run prematurely...", False)
                self.save_state()
                break
           
            self.state_variables['state'] += 1
                
        time_elapsed = time.time() - start_time
        self.log("Run completed in {}min {}s.".format(str(time_elapsed // 60).split('.')[0],
                                                    str(time_elapsed % 60).split('.')[0]))                                                    
           
    def save_state(self):
        backup_state = open('{}_backup_state.pkl'.format(self.instance_prefix), 'wb')
        pickle.dump(self.state_variables, backup_state)
        backup_state.close()
        self.log("State variables saved in {}_backup_state.pkl.".format(self.instance_prefix), False)
        
    def get_html_results(self):
        td_style = 'padding:10px;text-align:left;border: 1px solid #ddd;'
        td_head_style = 'background-color:#00aeef;color:white;'        
        # Run variable report
        row_highlight = 'background-color:#ffffff'  
        if self.run_variables:
            html = "<h3>Run Variables</h3>"
            html += "<table style='border-collapse:collapse;'><thead><tr><td style="\
                    "'{0}{1}'><b>Variable</b></td><td style='{0}{1}'><b>Value</b>"\
                    "</td></tr></thead><tbody>".format(td_style, td_head_style)
            for key,value in self.run_variables.items():
                html += "<tr><td style='{0}{1}'>{2}</td><td style='{0}{1}'>{3}</td></tr>".format(
                            td_style, row_highlight, key, value)
                if row_highlight == 'background-color:#ffffff':
                    row_highlight = 'background-color:#f2f2f2'
                else:
                    row_highlight = 'background-color:#ffffff'            
            html += "</tbody></table>"
        # State variable report
        row_highlight = 'background-color:#ffffff'                
        html += "<h3>State Variables</h3>"
        html += "<table style='border-collapse:collapse;'><thead><tr><td style="\
                "'{0}{1}'><b>Variable</b></td><td style='{0}{1}'><b>Value</b>"\
                "</td></tr></thead><tbody>".format(td_style, td_head_style)
        for key,value in self.state_variables.items():
            if key == 'state':
                continue
            html += "<tr><td style='{0}{1}'>{2}</td><td style='{0}{1}'>{3}</td></tr>".format(
                        td_style, row_highlight, key, value)
            if row_highlight == 'background-color:#ffffff':
                row_highlight = 'background-color:#f2f2f2'
            else:
                row_highlight = 'background-color:#ffffff'            
        html += "</tbody></table>"
        # Log report
        row_highlight = 'background-color:#ffffff'        
        html += "<h3>Log</h3>"
        html += "<table style='border-collapse:collapse;'><thead><tr><td style="\
                "'{0}{1}'><b>Step</b></td><td style='{0}{1}'><b>Description</b>"\
                "</td></tr></thead><tbody>".format(td_style, td_head_style)
        prev_state = 0
        for state, description in self.logged:
            if 'SUCCESS:' in description:
                html += "<tr><td style='{0}background-color:#00FF7F;'>{2}.</td><td style="\
                        "'{0}{1}'>{3}</td></tr>".format(td_style, row_highlight, state, description)
            elif 'FAILURE:' in description:
                html += "<tr><td style='{0}background-color:#FF6347;'>{2}.</td><td style="\
                        "'{0}{1}'>{3}</td></tr>".format(td_style, row_highlight, state, description)                
            elif state == prev_state:
                # Add indentation to multiple steps under the same state
                html += "<tr><td style='{0}{1}'>{2}.</td><td style="\
                        "'{0}{1}'><span style='padding-left:15px;'>{3}"\
                        "</span></td></tr>".format(td_style, row_highlight, state, description.lstrip('\t'))
            else:
                html += "<tr><td style='{0}{1}'>{2}.</td><td style="\
                        "'{0}{1}'>{3}</td></tr>".format(
                            td_style, row_highlight, state, description)
            if row_highlight == 'background-color:#ffffff':
                row_highlight = 'background-color:#f2f2f2'
            else:
                row_highlight = 'background-color:#ffffff'
            prev_state = state
        html += "</tbody></table>"
        
        return html