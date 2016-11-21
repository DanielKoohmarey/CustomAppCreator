# -*- coding: utf-8 -*-
"""
Created on Sat Nov 19 16:25:00 2016

@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

Dependencies: 
    sudo pip install requests
"""
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 13:51:07 2016

@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

Dependencies: 
    sudo pip install requests
"""
import json
import requests
import sys
import os
import time

from app_creator import AppCreator

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() # if python version < 2.7.9

class PMAppCreator(AppCreator):
    
    def __init__(self, instance_prefix, user, pwd, prev_state = {}):
        auth_pair = user, pwd
        AppCreator.__init__(self, instance_prefix, auth_pair, {}, prev_state)
        
        self.state_map = {
                            1: (self.check_for_project_tables,
                                    "Check if the project app table already exists."),
                            2: (self.create_project_tables,
                                    "Create 'Project' & 'Project Task' tables."),
                            3: (self.configure_project_form_layouts,
                                    "Configure 'Project' form layouts."),
                            4: (self.configure_related_lists,
                                     "Configure 'Project' related lists."),
                            5: (self.configure_label_choices,
                                     "Configure 'Portfolio' & 'Project Size' label choices."),
                            6: (self.configure_project_task_form_layout,
                                     "Configure 'Project Task' form layout."),
                            7: (self.configure_list_layout,
                                     "Configure 'Project List' & 'Project Task List' list layout."),
                            8: (self.setup_project_app_roles,
                                    "Create project app role and apply to 'Project'."),
                            9: (self.setup_project_group_roles,
                                    "Create 'Project Manager' group roles."),                                     
                                   
                                     
                         }      
                
    def check_for_project_tables(self):
        success, log = self.check_for_table('Project')        
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Check if 'Project Task' table exists
        return self.check_for_table('Project Task')

    def create_project_tables(self):
        # Log in
        success, log = self.web_driver.login(self.auth_pair[0], self.auth_pair[1])
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create the 'Project' table
        success, log = self.web_driver.create_custom_table(self.auth_pair[0], 
                                                   self.auth_pair[1], 
                                                   'Project',
                                                   'PRJ',
                                                   'Project Management')
                                                   
        if not success:
            return success, log
        else:
            self.log(log)
        # Save the 'Project' app sys id                                                
        url = "https://{}.service-now.com/api/now/table/sys_app_application?" \
                "sysparm_query=titleSTARTSWITH{}&sysparm_limit=1".format(self.instance_prefix,
                                                                        'Project Management')
        app_sys_id, log = self.get_json_response_key('sys_id', url)
        
        if not app_sys_id:
            return app_sys_id, log
        else:
            self.state_variables['app_sys_id'] = app_sys_id
            self.log(log)            
        # Create the 'Project Task' table
        return self.web_driver.create_custom_table(self.auth_pair[0], 
                                                   self.auth_pair[1], 
                                                   self.app_name,
                                                   'Project Task',
                                                   'PRJTASK',
                                                   '',
                                                   False)                                                   
                
    def configure_project_form_layouts(self):
        # Configure x form layout        
        expected_selected = ['|- begin_split -|', 'Number', 'Portfolio', 'Priority',
                             'Configuration item [+]', '|- split -|', 'Assignment group [+]', 'Assigned to [+]',
                            'State', 'Project Size','|- end_split -|', 'Short description','Description']
        new_fields = { 'Portfolio' : 'Choice', 'Project Size' : 'Choice'}    
        success, log = self.web_driver.configure_form_layout('u_project', 'Project', expected_selected, new_fields)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Configure y form layout
        expected_selected = ['|- begin_split -|', 'Planned Start', 'Planned End', 'Estimated Cost', '|- split -|',
                             'Work start', 'Work end', 'Actual Cost', '|- end_split -|']
        new_fields = { 'Planned Start' : 'Date/Time', 'Planned End' : 'Date/Time', 'Estimated Cost' : 'Price',
                       'Actual Cost': 'Price',} 
        success, log = self.web_driver.configure_form_layout('u_project', 'Planning', expected_selected, new_fields)
       
        if not success:
            return success, log
        else:
            self.log(log)
        # Configure 'Notes' form layout
        expected_selected = ['|- begin_split -|', 'Watch list', '|- split -|', 'Work notes list', '|- end_split -|',
                           'Work notes', 'Additional comments', 'Activities (filtered)']
        new_fields = {}
        success, log = self.web_driver.configure_form_layout('u_project', 'Notes', expected_selected, new_fields)
        return success, log
    
    def configure_related_lists(self):
        configuration = ['Project Task->Parent']
        return self.web_driver.configure_related_lists('u_project', configuration)

    def configure_label_choices(self):
        # Confgure 'Portfolio' label
        configuration = ['IT', 'HR', 'Facilities', 'Finance', 'Accounting', 'R&D', 'Marketing', 'Sales']
        success, log = self.web_driver.configure_label_choices('u_project', 'Portfolio', configuration)
        
        if not success:
            return success, log
        else:
            self.log(log)        
        # Configure 'Project Size' label
        configuration = ['Extra Small', 'Small', 'Medium', 'Large', 'Extra Large']
        success, log = self.web_driver.configure_label_choices('u_project','Project Size', configuration)
        return success, log

    def configure_project_task_form_layout(self):
        expected_selected = ['|- begin_split -|', 'Number', 'Parent [+]', 'Preceding Task', 'Priority',
                            'Planned Start Date', 'Planned End Date', '|- split -|', 'State', 'Assignment group [+]',
                            'Assigned to [+]', 'Configuration item [+]', 'Work start', 'Work end', '|- end_split -|',
                            'Short description', 'Work notes', 'Additional comments', 'Activities (filtered)']
        new_fields = { 'Preceding Task' : 'Reference', 'References' : { 'Preceding Task' : 'Project Task' }, 
                          'Planned Start Date' : 'Date/Time', 'Planned End Date' : 'Date/Time' }  
        return self.web_driver.configure_form_layout('u_project_task', 'Project Task', expected_selected, new_fields)

    def configure_list_layout(self):
        # Configure u_project_list list layout
        configuration = ['Number', 'Short description', 'Portfolio', 'Priority', 'State', 'Assigned to [+]']
        success,log = self.web_driver.configure_list_layout('u_project_list', configuration, {})
        
        if not success:
            return success, log
        else:
            self.log(log)   
        # Configure u_project_task layout
        configuration = ['Number', 'Short description', 'Priority', 'State', 'Assigned to [+]']
        success, log = self.web_driver.configure_list_layout('u_project_task_list', configuration, {})
        return success, log      
        
    def get_project_taskboard_url(self):
        # Retrieves the taskboard url and stores it in self.state['task_board_url']
        return self.web_driver.get_visual_task_board_url('u_project_list', self.state)

    def setup_project_app_roles(self):                   
        # Create the custom application role
        url = "https://{}.service-now.com/api/now/table/sys_user_role".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': 'project_manager',
                                    'description': "This role is required to create projects"\
                                                    "in the project management application."
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Update the new application to require the new role
        url = "https://{}.service-now.com/api/now/table/sys_app_application/{}".format(self.instance_prefix,
                                                                                        self.state_variables['app_sys_id'])
        put_data = "{{'roles':'project_manager,itil'}}"
        return self.verify_put_data(url, put_data)
                
    def setup_project_group_roles(self):
       # Create the group record
       url = "https://{}.service-now.com/api/now/table/sys_user_group".format(self.instance_prefix)
       post_data = json.dumps({
           'name': 'Project Managers',
           'description': "This group contains project managers."
       })
       success, log = self.verify_post_data(url, post_data)
    
       if not success:
           return success, log
       else:
           self.log(log)
       # Assign custom role to group
       url = "https://{}.service-now.com/api/now/table/sys_group_has_role".format(self.instance_prefix)
       post_data = json.dumps({
           'group': 'Project Managers',
           'role': 'project_manager'
       })
       success, log = self.verify_post_data(url, post_data)
    
       if not success:
           return success, log
       else:
           self.log(log)
    
    
       #Assign project_manager and itil roles to project task create/write access
       #GET project dictionary record sys ID
       url = "https://{}.service-now.com/api/now/table/sys_dictionary?sysparm_query=name%3Du_project%5Einternal_type%3Dcollection&sysparm_limit=1".format(
           self.instance_prefix)
       project_sys_id = self.get_data(url)
    
    
       url = "https://{}.service-now.com/api/now/table/sys_dictionary/{}".format(
           self.instance_prefix, self.state_variables['project_sys_id'])
       put_data = "{{'write_roles':'project_manager,itil','create_roles':'project_manager','delete_roles':'project_manager'}}"
       return self.verify_put_data(url, put_data)
    
    
       #Assign project_manager role to project create/delete access itil to write
       #GET project task dictionary record sys ID
       url = "https://{}.service-now.com/api/now/table/sys_dictionary?sysparm_query=name%3Du_project_task%5Einternal_type%3Dcollection&sysparm_limit=1{}".format(
           self.instance_prefix)
       project_task_sys_id = self.get_data(url)
    
    
    
    
       url = "https://{}.service-now.com/api/now/table/sys_dictionary/{}".format(
           self.instance_prefix, self.state_variables['project_sys_id'])
       put_data = "{{'write_roles':'project_manager,itil','create_roles':'project_manager,itil','delete_roles':'project_manager,itil'}}"
       return self.verify_put_data(url, put_data)
       #Create homepage named Overview, and link homepage module
      