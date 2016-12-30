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

from app_creator import AppCreator

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() # if python version < 2.7.9

class PMAppCreator(AppCreator):
    
    def __init__(self, instance_prefix, user, pwd, prev_state = {}):
        auth_pair = user, pwd
        AppCreator.__init__(self, instance_prefix, auth_pair, {}, prev_state)
        
        self.state_map = {
                            1: (self.check_login_credentials,
                                    "Check if the login credentials are valid."),        
                            2: (self.check_for_project_tables,
                                    "Check if the 'Project' & 'Project Task' tables already exists."),
                            3: (self.create_project_tables,
                                    "Create 'Project' & 'Project Task' tables."),
                            4: (self.configure_project_form_layouts,
                                    "Configure 'Project' form layouts."),
                            5: (self.configure_related_lists,
                                    "Configure 'Project' related lists."),
                            6: (self.configure_label_choices,
                                    "Configure 'Portfolio' & 'Project Size' label choices."),
                            7: (self.configure_project_task_form_layout,
                                    "Configure 'Project Task' form layout."),
                            8: (self.configure_list_layout,
                                    "Configure 'Project List' & 'Project Task List' list layout."),
                            9: (self.get_project_task_board_url,
                                    "Get 'Project' task board url."),
                            10: (self.setup_project_app_roles,
                                    "Create project app role and apply to 'Project'."),
                            11: (self.setup_project_group_roles,
                                    "Create 'Project Manager' group roles."),
                            12: (self.create_reports,
                                    "Create various project reports."),                                  
                            13: (self.create_modules,
                                    "Create project modules."),
                            14: (self.create_email_notification_records,
                                    "Create email notifications."),
                            15: (self.create_business_rule_records,
                                    "Create business rules."),
                            16: (self.create_assignment_rules,
                                    "Create 'Project Managers' assignment rule."),
                            17: (self.add_reports,
                                     "Add reports to overview.")                                    
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
        # Create the 'Project' table
        success, log = self.web_driver.create_table('Project',
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
        return self.web_driver.create_table('Project Task',
                                           'PRJTASK',
                                           '')                                                   
                
    def configure_project_form_layouts(self):
        # Configure 'Project' form layout        
        expected_selected = ['|- begin_split -|', 'Number', 'Portfolio', 'Priority',
                             'Configuration item [+]', '|- split -|', 'State', 'Project Size','Assignment group [+]',
                             'Assigned to [+]','|- end_split -|', 'Short description','Description']
        new_fields = { 'Portfolio' : 'Choice', 'Project Size' : 'Choice'}    
        success, log = self.web_driver.configure_form_layout('u_project', 'Project', expected_selected, new_fields)
        
        if not success:
            return success, log
        else:
            self.log(log)
            
        # Configure 'Planning' form layout
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
        success,log = self.web_driver.configure_list_layout('u_project', configuration, {})
        
        if not success:
            return success, log
        else:
            self.log(log)
        
        # Configure u_project_task layout
        configuration = ['Number', 'Short description', 'Priority', 'State', 'Assigned to [+]']
        success, log = self.web_driver.configure_list_layout('u_project_task', configuration, {})
        return success, log      
        
    def get_project_task_board_url(self):
        # Retrieves the taskboard url and stores it in self.state_variables['task_board_url']
        return self.web_driver.get_visual_task_board_url('u_project', self.state_variables)

    def setup_project_app_roles(self):                   
        # Create the custom application role
        url = "https://{}.service-now.com/api/now/table/sys_user_role".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': 'project_manager',
                                    'description': "This role is required to create projects"\
                                                    " in the project management application."
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Update the new application to require the new role
        url = "https://{}.service-now.com/api/now/table/sys_app_application/{}".format(self.instance_prefix,
                                                                                        self.state_variables['app_sys_id'])
        put_data = json.dumps({
                                    'roles': 'project_manager,itil'        
                                })
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
        url = "https://{}.service-now.com/api/now/table/sys_dictionary?sysparm_query="\
                "name%3Du_project%5Einternal_type%3Dcollection&sysparm_limit=1".format(self.instance_prefix)
        project_sys_id, log = self.get_json_response_key('sys_id', url)

        if not project_sys_id:
            return project_sys_id, log
        else:
            self.state_variables['project_sys_id'] = project_sys_id
            self.log(log)

        #Assign project roles
        url = "https://{}.service-now.com/api/now/table/sys_dictionary/{}".format(
                self.instance_prefix, self.state_variables['project_sys_id'])
        put_data = json.dumps({
                                    'write_roles': 'project_manager,itil',
                                    'create_roles': 'project_manager',
                                    'delete_roles': 'project_manager'
                                })
        success, log = self.verify_put_data(url, put_data)
    
        if not success:
            return success, log
        else:
            self.log(log)    
    
        # Assign project_manager role to project create/delete access itil to write
        url = "https://{}.service-now.com/api/now/table/sys_dictionary?sysparm_query="\
                "name%3Du_project_task%5Einternal_type%3Dcollection&sysparm_limit=1".format(self.instance_prefix)
        project_task_sys_id, log = self.get_json_response_key('sys_id', url)

        if not project_task_sys_id:
            return project_task_sys_id, log
        else:
            self.state_variables['project_task_sys_id'] = project_task_sys_id
            self.log(log)          
    
        # Assign project task roles  
        url = "https://{}.service-now.com/api/now/table/sys_dictionary/{}".format(
                    self.instance_prefix, self.state_variables['project_task_sys_id'])
        put_data = json.dumps({
                                    'write_roles': 'project_manager,itil',
                                    'create_roles': 'project_manager,itil',
                                    'delete_roles': 'project_manager,itil'
                                })
        return self.verify_put_data(url, put_data)

    def create_reports(self):
        # Create calendar report for projects
        url = "https://{}.service-now.com/api/now/table/sys_report".format(self.instance_prefix)
        post_data = json.dumps({
                                    'title': "Planned Project Start",
                                    'table': 'u_project',
                                    'type': 'calendar',
                                    'field': 'u_planned_start',
                                    'trend_field': 'u_planned_start'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
        
        # Create calendar report for project tasks
        url = "https://{}.service-now.com/api/now/table/sys_report".format(self.instance_prefix)
        post_data = json.dumps({
                                    'title': "Planned Project Task Start",
                                    'table': 'u_project_task',
                                    'type': 'calendar',
                                    'field': 'u_planned_start_date',
                                    'trend_field': 'u_planned_start_date'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create Overdue Project Task Report
        url = "https://{}.service-now.com/api/now/table/sys_report".format(self.instance_prefix)
        post_data = json.dumps({
                                    'title': "Overdue Project Tasks",
                                    'table': 'u_project_task',
                                    'type': 'list',
                                    'filter': 'u_planned_end_date<javascript:gs.minutesAgoStart(0)^active=true'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Projects by portfolio
        post_data = json.dumps({
                                   'title': 'Projects by Portfolio',
                                   'table': 'u_project',
                                   'field': 'u_portfolio',
                                   'type': 'pie',
                               })
        success, log = self.verify_post_data(url, post_data)
        if not success:
            return success, log
        else:
            self.log(log)

        # Create open projects by project manager
        post_data = json.dumps({
                                   'title': "Open Projects by Project Manager",
                                   'table': 'u_project',
                                   'field': 'assigned_to',
                                   'trend_field': 'state',
                                   'type': 'bar',
                                   'filter': 'active=true^EQ'
                               })
        success, log = self.verify_post_data(url, post_data)
        if not success:
            return success, log
        else:
            self.log(log)

        # Create Open project tasks by project
        post_data = json.dumps({
                                    'title': "Open Project Tasks by Project",
                                    'table': 'u_project_task',
                                    'field': 'parent',
                                    'trend_field': 'state',
                                    'type': 'bar',
                                    'filter': 'active=true^EQ'
                                })
        return self.verify_post_data(url, post_data)
        
    def create_modules(self):
        # Create sys_portal_page for overview model
        url = "https://{}.service-now.com/api/now/table/sys_portal_page".format(self.instance_prefix)
        post_data = json.dumps({
                                   'title': "Project Management Overview",
                                   'selectable': False,
                                   'view': 'project_overview',
                                   'roles': 'admin'
                                })
        page_sys_id, log = self.get_json_response_key('sys_id', url, post_data)

        if not page_sys_id:
            return page_sys_id, log
        else:
            self.state_variables['page_sys_id'] = page_sys_id
            self.log(log)
        
        # Create 'Overview' model
        url = "https://{}.service-now.com/api/now/table/sys_app_module".format(self.instance_prefix)
        post_data = json.dumps({
                                   'title': 'Overview',
                                   'active': True,
                                   'order': '100',
                                   'link_type': 'HOMEPAGE',
                                   'homepage': self.state_variables['page_sys_id'],
                                   'application': 'Project Management'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
           return success, log
        else:
           self.log(log)
           
        # Create 'Taskboard' module
        post_data = json.dumps({
                                    'title': "Taskboard",
                                    'active': True,
                                    'order': '150',
                                    'link_type': 'DIRECT',
                                    'application': 'Project Management',
                                    'roles': 'project_manager',
                                    'query': self.state_variables['task_board_url']
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create 'Create New' module
        post_data = json.dumps({
                                    'title': "Create New",
                                    'active': True,
                                    'order': '200',
                                    'link_type': 'NEW',
                                    'name': 'u_project',
                                    'application': 'Project Management',
                                    'roles':'project_manager'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
           return success, log
        else:
           self.log(log)

        # Create 'My Projects' module
        post_data = json.dumps({
                                    'title': 'My Projects',
                                    'active': True,
                                    'order': '300',
                                    'link_type': 'LIST',
                                    'name': 'u_project',
                                    'application': 'Project Management',
                                    'filter': 'active=true^assigned_to=javascript:getMyAssignments()^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
           
        # Create 'Work in Progress' module
        post_data = json.dumps({
                                    'title': "Work in Progress",
                                    'active': True,
                                    'order': '400',
                                    'link_type': 'LIST',
                                    'name': 'u_project',
                                    'application': 'Project Management',
                                    'filter': 'active=true^state=2^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
           
        # Create 'All' module
        post_data = json.dumps({
                                    'title': "All",
                                    'active': True,
                                    'order': '500',
                                    'link_type': 'LIST',
                                    'name': 'u_project',
                                    'application': 'Project Management'
                                 })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
        
        # Create 'Tasks' separator module
        post_data = json.dumps({
                                    'title': 'Tasks',
                                    'active': True,
                                    'order': '600',
                                    'link_type': 'SEPARATOR',
                                    'application': 'Project Management'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
        
        # Create 'Assigned to me' module
        post_data = json.dumps({
                                    'title': 'Assigned to me',
                                    'active': True,
                                    'order': '700',
                                    'link_type': 'LIST',
                                    'name': 'u_project_task',
                                    'application': 'Project Management',
                                    'filter': 'active=true^assigned_to=javascript:getMyAssignments()^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create 'Work in Progress' module
        post_data = json.dumps({
                                    'title': 'Work in Progress',
                                    'active': True,
                                    'order': '800',
                                    'link_type': 'LIST',
                                    'name': 'u_project_task',
                                    'application': 'Project Management',
                                    'filter': 'active=true^state=2^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
           
        # Create 'All' module
        post_data = json.dumps({
                                    'title': 'All',
                                    'active': True,
                                    'order': '900',
                                    'link_type': 'LIST',
                                    'name': 'u_project_task',
                                    'application': 'Project Management'
                                })
        
        return self.verify_post_data(url, post_data)

    def add_reports(self):
        # Add all created reports to overview page
        return self.web_driver.add_reports('project', ['Project', 'Project Task'], 6) # 6 reports expected   

    def create_email_notification_records(self):
        # Create email notification record for when Project commented
        url = "https://{}.service-now.com/api/now/table/sysevent_email_action".format(self.instance_prefix)
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'send_self': False,
                                    'name': 'Project Commented',
                                    'recipient_fields': "opened_by,assigned_to,watch_list",
                                    'collection': 'u_project',
                                    'condition': 'commentsVALCHANGES^EQ',
                                    'subject': "Project ${number} -- comments added",
                                    'message_html': """<div>Short Description: ${short_description}</div>
                                                       <div>Click here to view Project: ${URI_REF}</div>
                                                       <div><hr/></div>
                                                       <div>Priority: ${priority}</div>
                                                       <div>Comments:</div>
                                                       <div>${comments}</div>
                                                       <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        #Create email notification record for when Project task commented
        post_data = json.dumps({
                                   'sysevent_email_action': 'INSERT_OR_UPDATE',
                                   'action_update': True,
                                   'send_self': False,
                                   'name': 'Project Task Commented',
                                   'recipient_fields': "opened_by,assigned_to,watch_list",
                                   'collection': 'u_project_task',
                                   'condition': 'commentsVALCHANGES^EQ',
                                   'subject': "Project Task ${number} -- comments added",
                                   'message_html': """<div>Short Description: ${short_description}</div>
                                                       <div>Click here to view Project Task: ${URI_REF}</div>
                                                       <div><hr/></div>
                                                       <div>Priority: ${priority}</div>
                                                       <div>Comments:</div>
                                                       <div>${comments}</div>
                                                       <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when Project work noted
        url = "https://{}.service-now.com/api/now/table/sysevent_email_action".format(self.instance_prefix)
        post_data = json.dumps({
                                   'sysevent_email_action': 'INSERT_OR_UPDATE',
                                   'action_update': True,
                                   'send_self': False,
                                   'name': 'Project Work Noted',
                                   'recipient_fields': "assigned_to,work_notes_list",
                                   'collection': 'u_project',
                                   'condition': 'work_notesVALCHANGES^EQ',
                                   'subject': "Project ${number} -- work notes added",
                                   'message_html': """<div>Short Description: ${short_description}</div>
                                                      <div>Click here to view Project: ${URI_REF}</div>
                                                      <div><hr/></div>
                                                      <div>Priority: ${priority}</div>
                                                      <div>Work Notes:</div>
                                                      <div>${work_notes}</div>
                                                      <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when Project task work noted
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'send_self': False,
                                    'name': 'Project Task Work Noted',
                                    'recipient_fields': "assigned_to,work_notes_list",
                                    'collection': 'u_project_task',
                                    'condition': 'work_notesVALCHANGES^EQ',
                                    'subject': "Project Task ${number} -- work notes added",
                                    'message_html': """<div>Short Description: ${short_description}</div>
                                                      <div>Click here to view Project Task: ${URI_REF}</div>
                                                      <div><hr/></div>
                                                      <div>Priority: ${priority}</div>
                                                      <div>Work Notes:</div>
                                                      <div>${work_notes}</div>
                                                      <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when Project closed
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'send_self': False,
                                    'name': "Project Closed",
                                    'recipient_fields': "opened_by,watch_list,parent.assigned_to",
                                    'collection': 'u_project',
                                    'condition': 'activeCHANGESTOfalse^EQ',
                                    'subject': "Project ${number} has been closed",
                                    'message_html': """<div>Your Project ${number} has been closed."""\
                                                    """Please contact the service desk if you have any questions.</div>
                                                    <div>Closed by: ${closed_by}</div>
                                                    <div>&nbsp;</div>
                                                    <div>Short description: ${short_description}</div>
                                                    <div>Click here to view: ${URI_REF}</div>
                                                    <div><hr/></div>
                                                    <div>Comments:</div>
                                                    <div>${comments}</div>
                                                    <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        #Create email notification record for when Project Task closed
        post_data = json.dumps({
                                   'sysevent_email_action': 'INSERT_OR_UPDATE',
                                   'action_update': True,
                                   'send_self': False,
                                   'name': "Project Task Closed",
                                   'recipient_fields': "opened_by,watch_list,parent.assigned_to",
                                   'collection': 'u_project_task',
                                   'condition': 'activeCHANGESTOfalse^EQ',
                                   'subject': "Project Task ${number} has been closed",
                                   'message_html': """<div>Your Project Task${number} has been closed.""" \
                                                   """Please contact the service desk if you have any questions.</div>
                                                   <div>Closed by: ${closed_by}</div>
                                                   <div>&nbsp;</div>
                                                   <div>Short description: ${short_description}</div>
                                                   <div>Click here to view: ${URI_REF}</div>
                                                   <div><hr/></div>
                                                   <div>Comments:</div>
                                                   <div>${comments}</div>
                                                   <div>&nbsp;</div>"""
                                })           
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when project assigned to my group
        post_data = json.dumps({
                                   'sysevent_email_action': 'INSERT_OR_UPDATE',
                                   'action_insert': True,
                                   'action_update': True,
                                   'name': "Project assigned to my group",
                                   'recipient_fields': 'assignment_group',
                                   'collection': 'u_project',
                                   'condition': 'assigned_toISEMPTY^assignment_groupVALCHANGES^EQ',
                                   'subject': "Project ${number} has been assigned to group "\
                                              "${assignment_group}",
                                   'message_html': """<div>Short Description: ${short_description}</div>
                                                       <div>Click here to view Project: ${URI_REF}</div>
                                                       <div><hr/></div>
                                                       <div>Priority: ${priority}</div>
                                                       <div>Comments:</div>
                                                       <div>${comments}</div>
                                                       <div>&nbsp;</div>"""
                               })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when project task assigned to my group
        post_data = json.dumps({
                                   'sysevent_email_action': 'INSERT_OR_UPDATE',
                                   'action_insert': True,
                                   'action_update': True,
                                   'name': "Project Task assigned to my group",
                                   'recipient_fields': 'assignment_group',
                                   'collection': 'u_project_task',
                                   'condition': 'assigned_toISEMPTY^assignment_groupVALCHANGES^EQ',
                                   'subject': "Project Task ${number} has been assigned to group "\
                                              "${assignment_group}",
                                   'message_html': """<div>Short Description: ${short_description}</div>
                                                       <div>Click here to view Project Task: ${URI_REF}</div>
                                                       <div><hr/></div>
                                                       <div>Priority: ${priority}</div>
                                                       <div>Comments:</div>
                                                       <div>${comments}</div>
                                                       <div>&nbsp;</div>"""
                               })
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when Project assigned to me
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'action_insert': True,
                                    'send_self': False,
                                    'name': "Project assigned to me",
                                    'recipient_fields': 'assigned_to',
                                    'collection': 'u_project',
                                    'condition': 'assigned_toVALCHANGES^assigned_toISNOTEMPTY^EQ',
                                    'subject': "Project ${number} has been assigned to you",
                                    'message_html': """<div>Short Description: ${short_description}</div>
                                                        <div>Click here to view Project: ${URI_REF}</div>
                                                        <div><hr /></div>
                                                        <div>Priority: ${priority}</div>
                                                        <div>Comments:</div>
                                                        <div>${comments}</div>
                                                        <div>&nbsp;</div>"""
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)

        # Create email notification record for when Project Task assigned to me
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'action_insert': True,
                                    'send_self': False,
                                    'name': "Project Task assigned to me",
                                    'recipient_fields': 'assigned_to',
                                    'collection': 'u_project_task',
                                    'condition': 'assigned_toVALCHANGES^assigned_toISNOTEMPTY^EQ',
                                    'subject': "Project Task ${number} has been assigned to you",
                                    'message_html': """<div>Short Description: ${short_description}</div>
                                                        <div>Click here to view Project Task: ${URI_REF}</div>
                                                        <div><hr /></div>
                                                        <div>Priority: ${priority}</div>
                                                        <div>Comments:</div>
                                                        <div>${comments}</div>
                                                        <div>&nbsp;</div>"""
                                })
        return self.verify_post_data(url, post_data)
        
    def create_business_rule_records(self):
        # Require preceding task
        url = "https://{}.service-now.com/api/now/table/sys_script".format(self.instance_prefix)
        post_data = json.dumps({
                                   'sys_script_action': 'INSERT_OR_UPDATE',
                                   'action_update': True,
                                   'abort_action': True,
                                   'add_message': True,
                                   'when': 'before',
                                   'name': 'Preceding Task Enforcement',
                                   'collection': 'u_project_task',
                                   'filter_condition': 'stateVALCHANGES^u_preceding_task.active=true^u_preceding_taskISNOTEMPTY',
                                   'message': """<p>There is a dependency entered on the completion of task ${current.u_preceding_task}</p>
                                                <p>Until the preceding task is completed, work on the current task should not begin.</p>
                                                """
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        # Set work start to current date when state moves to work in progress and start date is empty for project
        post_data = json.dumps({
                                    'sys_script_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'when': 'before',
                                    'name': 'Project - Set Work Start',
                                    'collection': 'u_project',
                                    'filter_condition': 'stateCHANGESTO2^EQ',
                                    'template': 'work_start=javascript:gs.nowDateTime();^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)

        # Set work end to current date when state moves to closed complete for project
        post_data = json.dumps({
                                    'sys_script_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'when': 'before',
                                    'name': 'Project - Set Work End',
                                    'collection': 'u_project',
                                    'filter_condition': 'activeCHANGESTOfalse^EQ',
                                    'template': 'work_end=javascript:gs.nowDateTime();^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)

        #Set work start to current date when state moves to work in progress and start date is empty for project task.
        post_data = json.dumps({
                                    'sys_script_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'when': 'before',
                                    'name': 'Project Task- Set Work Start',
                                    'collection': 'u_project_task',
                                    'filter_condition': 'stateCHANGESTO2^EQ',
                                    'template': 'work_start=javascript:gs.nowDateTime();^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)

        #Set work end to current date when state moves to closed complete for project task
        post_data = json.dumps({
                                   'sys_script_action': 'INSERT_OR_UPDATE',
                                   'action_update': True,
                                   'when': 'before',
                                   'name': 'Project Task- Set Work End',
                                   'collection': 'u_project_task',
                                   'filter_condition': 'activeCHANGESTOfalse^EQ',
                                   'template': 'work_end=javascript:gs.nowDateTime();^EQ'
                                })
        return self.verify_post_data(url, post_data)
        
    def create_assignment_rules(self):
        # Create default assignment for all records on new table, new group
        url = "https://{}.service-now.com/api/now/table/sysrule_assignment".format(self.instance_prefix)
        post_data = json.dumps({
                                    'active': True,
                                    'name': "Project Assignment",
                                    'table': "u_project",
                                    'group': "Project Managers"
                                })
        return self.verify_post_data(url, post_data)        