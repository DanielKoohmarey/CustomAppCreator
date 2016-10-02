# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 13:51:07 2016

@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

TODO: convert prints to log function that stores all logged messages in list, on run send email list somewhere
On crash, run 'ps' command and kill outstand Firefox / Xvfb
"""
import json
import pickle
import requests
import sys
import os
import time
import app_web_driver

class AppCreator(object):
    json_headers = {
                        "Content-Type" : "application/json",
                        "Accept" : "application/json"
                    }
    
    def __init__(self, instance_prefix, user, pwd, app_name, app_prefix, 
                     prev_state):
        self.instance_prefix = instance_prefix 
        self.auth_pair = user,pwd
        self.app_name = app_name
        self.table_name = 'u_'+ app_name.replace(" ","_")
        self.app_prefix = app_prefix
        
        self.web_driver = app_web_driver.AppWebDriver(instance_prefix)
        self.state_variables = prev_state
        if not self.state_variables:
            self.state_variables['state'] = 17
        self.logged = []
        self.state_map = {
                            1: (self.create_custom_table,
                                     "Create the custom app table & retrieve the app sys id."),
                            2: (self.setup_custom_app_role,
                                     "Create custom app role and apply to app."),
                            3: (self.set_custom_group_role,
                                     "Create the group record & assign custom role to group."),
                            4: (self.create_live_feed_group,
                                     "Create the live feed group."),
                            5: (self.create_knowledge_base,
                                     "Create the knowledge base & retrieve the knowledge sys id."),
                            6: (self.create_user_criteria_record,
                                     "Create a user criteria record & retrieve the criteria sys id."),
                            7: (self.create_can_contribute_record,
                                     "Create a can contribute record."),
                            8: (self.create_email_notification_records,
                                     "Create email notification records."),
                            9: (self.create_inbound_email_actions,
                                     "Retrieve the plus sys id & create inbound email actions."),
                            10: (self.create_modules,
                                      "Retrieve the page sys id & create modules."),
                            11: (self.create_reports,
                                      "Create reports."),
                            12: (self.add_reports,
                                      "Add reports to overview."),
                            13: (self.create_assignment_rules,
                                      "Create assignment rules."),                                      
                            14: (self.setup_slas,
                                      "Create SLAs & save P1-P4 sla sys ids & create escalation rule."),
                            15: (self.create_catalog_category,
                                      "Create catalog category & save category sys id."),
                            16: (self.create_record_producer,
                                      "Create record producer & save producer sys id."),
                            17: (self.create_catalog_item,
                                      "Create catalog item & save item sys id.")
                        }

    def log(self, message, indent = True):
        # Indent subsequent messages from the same state
        if indent and self.logged and self.logged[-1][0] == self.state_variables['state']:
                message = '\t'+message
        self.logged.append((self.state_variables['state'],message))
        print message
 
    def get_progress_string(self):
        completion_state = float(len(self.state_map))
        progress_string = "Step {} of {} ({}%) ".format(self.state_variables['state'],completion_state,
                                                        round((self.state_variables['state']/completion_state)*100))
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
    
        if response.status_code == 200:
            json_response = response.json()['result'][0]
        elif response.status_code == 201:
            json_response = response.json()['result']
        else:
            log = "Unsuccessful response code from {}: {}.".format(path, response.status_code)
            json_response = {}
    
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
            log = "POST {} response had status code 201.".format(path)
            
        return success, log
        
    def verify_put_data(self, url, post_data):
        success = False
        path = url.split(".service-now.com")[1]
        log = "PUT {} response did not have status code 200.".format(path)
        
        response = requests.put(url, auth=self.auth_pair, headers=self.json_headers, data=post_data)
        if response.status_code == 200:
            success = True
            log = "PUT {} response had status code 200.".format(path)
            
        return success, log

    def create_custom_table(self):
        # Create the custom table
        success, log = self.web_driver.create_custom_table(self.auth_pair[0], 
                                                   self.auth_pair[1], 
                                                   self.app_name,
                                                   self.app_prefix)
        if not success:
            return success, log
        else:
            self.log(log)
        # Save the created applications sys_id field    
        url = "https://{}.service-now.com/api/now/table/sys_app_application?" \
                "sysparm_query=titleSTARTSWITH{}&sysparm_limit=1".format(
                    self.instance_prefix, self.app_name)
        app_sys_id, log = self.get_json_response_key('sys_id', url)
        
        if app_sys_id:
            self.state_variables['app_sys_id'] = app_sys_id
            
        return app_sys_id, log
                                   
    def setup_custom_app_role(self):
        # Create the custom application role
        url = "https://{}.service-now.com/api/now/table/sys_user_role".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': self.app_name,
                                    'description': "This role is required for access"\
                                                    "to the {} application.".format(self.app_name)
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Update the new application to require the new role
        url = "https://{}.service-now.com/api/now/table/sys_app_application/{}".format(
                self.instance_prefix, self.state_variables['app_sys_id'])
        put_data = "{{'roles':'{}'}}".format(self.app_name)   
        return self.verify_put_data(url, put_data)                              

    def set_custom_group_role(self):
        # Create the group record
        url = "https://{}.service-now.com/api/now/table/sys_user_group".format(self.instance_prefix) 
        post_data = json.dumps({
                                    'name': self.app_name,
                                    'description': "This group contains the fulfillers working "\
                                                    "in the {} application.".format(self.app_name)
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Assign custom role to group
        url = "https://{}.service-now.com/api/now/table/sys_group_has_role".format(self.instance_prefix) 
        post_data = json.dumps({
                                    'group': self.app_name,
                                    'role': self.app_name
                                })
        return self.verify_post_data(url, post_data)
                                 
    def create_live_feed_group(self):
        # Create the live feed group
        url = "https://{}.service-now.com/api/now/table/live_group_profile".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': self.app_name,
                                    'public_group': False,
                                    'visible_group': True,
                                    'short_description': "Discuss and collaborate on topics "\
                                                            "regarding {}".format(self.app_name)
                                })            
        return self.verify_post_data(url, post_data)                       
    
    def create_knowledge_base(self):
        # Create the knowledgebase and save the sys_id
        url = 'https://{}.service-now.com/api/now/table/kb_knowledge_base'.format(instance_prefix)
        post_data = json.dumps({
                                    'description': "Read self-help articles and learn more about {}".format(self.app_name),
                                    'active': True,
                                    'retire_workflow': '3d18ef12c30031000096dfdc64d3aeb6',
                                    'workflow': 'fbe441019f112100d8f8700c267fcf1a',
                                    'title': self.app_name,
                                    'retire_workflow_type': 'INSTANT',
                                    'workflow_type': 'INSTANT'                
                                })
        knowledge_sys_id, log = self.get_json_response_key('sys_id', url, post_data)
        
        if knowledge_sys_id:
            self.state_variables['knowledge_sys_id'] = knowledge_sys_id
            
        return knowledge_sys_id, log

    def create_user_criteria_record(self):
        # Create a user criteria record for the new role and save the sys_id
        url = "https://{}.service-now.com/api/now/table/user_criteria".format(self.instance_prefix)
        post_data = json.dumps({ 
                                    'role': self.app_name,
                                    'name': self.app_name 
                                })
        criteria_sys_id, log = self.get_json_response_key('sys_id', url, post_data)

        if criteria_sys_id:
            self.state_variables['criteria_sys_id'] = criteria_sys_id
            
        return criteria_sys_id, log

    def create_can_contribute_record(self):
        # Create a can contribute record for the custom role on the knowledgebase
        url = "https://{}.service-now.com/api/now/table/kb_uc_can_contribute_mtom".format(self.instance_prefix)
        post_data = json.dumps({
                                    'kb_knowledge_base': self.state_variables['knowledge_sys_id'],
                                    'user_criteria': self.app_name
                                })
        return self.verify_post_data(url, post_data)         

    def create_email_notification_records(self):
        # Create email notification record for when custom app commented
        url = "https://{}.service-now.com/api/now/table/sysevent_email_action".format(self.instance_prefix)
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'send_self': False,
                                    'name': '{} Commented'.format(self.app_name),
                                    'recipient_fields': "opened_by,assigned_to,watch_list",
                                    'collection': self.table_name,
                                    'condition': 'commentsVALCHANGES^EQ',
                                    'subject': "{} ${{number}} -- comments added".format(self.app_name),
                                    'message_html': """<div>Short Description: ${{short_description}}</div>
                                                    <div>Click here to view {}: ${{URI_REF}}</div>
                                                    <div><hr/></div>
                                                    <div>Priority: ${{priority}}</div>
                                                    <div>Comments:</div>
                                                    <div>${{comments}}</div>
                                                    <div>&nbsp;</div>""".format(self.app_name)
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create email notification record for when custom app closed      
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'send_self': False,
                                    'name': "{} Closed".format(self.app_name),
                                    'recipient_fields': "opened_by,watch_list",
                                    'collection': self.table_name,
                                    'condition': 'activeCHANGESTOfalse^EQ',
                                    'subject': "Your {} ${{number}} has been closed".format(self.app_name),
                                    'message_html': """<div>Your {} ${{number}} has been closed."""\
                                                    """Please contact the service desk if you have any questions.</div>
                                                    <div>Closed by: ${{closed_by}}</div>
                                                    <div>&nbsp;</div>
                                                    <div>Short description: ${{short_description}}</div>
                                                    <div>Click here to view: ${{URI_REF}}</div>
                                                    <div><hr/></div>
                                                    <div>Comments:</div>
                                                    <div>${{comments}}</div>
                                                    <div>&nbsp;</div>""".format(self.app_name)
                                })
        success, log = self.verify_post_data(url, post_data)

        if not success:
            return success, log
        else:
            self.log(log)
        # Create email notification record for when custom app assigned to my group
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_insert': True,
                                    'action_update': True,
                                    'name': "{} assigned to my group".format(self.app_name),
                                    'recipient_fields': 'assignment_group',
                                    'collection': self.table_name,
                                    'condition': 'assigned_toISEMPTY^assignment_groupVALCHANGES^EQ',
                                    'subject': "{} ${{number}} has been assigned to group"\
                                                "${{assignment_group}}".format(self.app_name),
                                    'message_html': """<div>Short Description: ${{short_description}}</div>
                                                    <div>Click here to view {}: ${{URI_REF}}</div>
                                                    <div><hr/></div>
                                                    <div>Priority: ${{priority}}</div>
                                                    <div>Comments:</div>
                                                    <div>${{comments}}</div>
                                                    <div>&nbsp;</div>""".format(self.app_name)
                                })

        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create email notification record for when custom app assigned to me
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_update': True,
                                    'action_insert': True,
                                    'send_self': False,                          
                                    'name': "{} assigned to me".format(self.app_name),
                                    'recipient_fields':'assigned_to',
                                    'collection': self.table_name,
                                    'condition': 'assigned_toVALCHANGES^assigned_toISNOTEMPTY^EQ',
                                    'subject': "{} ${{number}} has been assigned to you".format(self.app_name),
                                    'message_html': """<div>Short Description: ${{short_description}}</div>
                                                    <div>Click here to view {}: ${{URI_REF}}</div>
                                                    <div><hr /></div>
                                                    <div>Priority: ${{priority}}</div>
                                                    <div>Comments:</div>
                                                    <div>${{comments}}</div>
                                                    <div>&nbsp;</div>""".format(self.app_name)                          
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create email notification record for when custom app opened for me
        post_data = json.dumps({
                                    'sysevent_email_action': 'INSERT_OR_UPDATE',
                                    'action_insert': True,
                                    'send_self': True,                            
                                    'name': "{} opened for me".format(self.app_name),
                                    'recipient_fields': 'opened_by',
                                    'collection': self.table_name,
                                    'condition': 'active=true^EQ',
                                    'subject': "{} ${{number}} -- opened on your behalf".format(self.app_name),
                                    'message_html': """<div>The service desk has received your request for help"""\
                                                    """ and will respond shortly. If you would like to provide further"""\
                                                    """ information about the issue, you may simply reply to this"""\
                                                    """ email with any updates.</div>
                                                    <div>&nbsp;</div>
                                                    <div>Click here to view: ${{URI_REF}}</div>
                                                    <div><hr /></div>
                                                    <div>Description: ${{short_description}}</div>
                                                    <div>Comments:</div>
                                                    <div>${{comments}}</div>
                                                    <div>&nbsp;</div>""".format(self.app_name)
                                })
        return self.verify_post_data(url, post_data)      
                        
    def create_inbound_email_actions(self):
        # Create subaddress needed for creating new inbound email records
        url = "https://{}.service-now.com/api/now/table/email_plus_address".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': self.app_name,
                                    'plus_address': self.app_prefix
                                })
        plus_sys_id, log = self.get_json_response_key('sys_id', url)
        
        if not plus_sys_id:
            return plus_sys_id, log
        else:
            self.state_variables['plus_sys_id'] = plus_sys_id
            self.log(log)
        # Create custom app inbound email action record 
        url = "https://{}.service-now.com/api/now/table/sysevent_in_email_action".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': "Create {} Record".format(self.app_name),
                                    'type': 'new',
                                    'table': self.table_name,
                                    'active': True,
                                    'stop_processing': True,
                                    'template': 'contact_type=email^short_descriptionDYNAMICb637bd21ef3221002841f'\
                                                '7f775c0fbb6^commentsDYNAMIC367bf121ef3221002841f7f775c0fbe2^EQ',
                                    'plus_address': self.state_variables['plus_sys_id']
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create custom app from Forward record
        post_data = json.dumps({
                                    'name': "Create {} Record (Forwarded)".format(self.app_name),
                                    'type': 'forward',
                                    'table': self.table_name,
                                    'active': True,
                                    'stop_processing': True,
                                    'filter_condition': 'recipientsLIKE{}+{}@service-now.com^EQ'.format(
                                                            self.instance_prefix, self.app_prefix),
                                    'template': 'contact_type=email^short_descriptionDYNAMICb637bd21ef3221002841f7f775c0fbb6'\
                                                '^commentsDYNAMIC367bf121ef3221002841f7f775c0fbe2^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
         # Create custom app from Reply record       
        post_data = json.dumps({
                                    'name': "Update {} Record (Reply)".format(self.app_name),
                                    'type': 'reply',
                                    'table': self.table_name,
                                    'active': 'true',
                                    'stop_processing': 'true',
                                    'template': 'commentsDYNAMIC367bf121ef3221002841f7f775c0fbe2^EQ'
                                })
        return self.verify_post_data(url, post_data)
                         
    def create_modules(self):
        # Create sys_portal_page for overview model
        url = "https://{}.service-now.com/api/now/table/sys_portal_page".format(self.instance_prefix)
        post_data = json.dumps({
                                    'title': "{} Overview".format(self.app_name),
                                    'selectable': False,
                                    'view': '{}_overview'.format(self.app_name),
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
                                    'application': self.app_name
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
                                    'name': self.table_name,
                                    'application': self.app_name
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create 'Open' module
        post_data = json.dumps({
                                    'title': 'Open',
                                    'active': True,
                                    'order': '300',
                                    'link_type': 'LIST',
                                    'name': self.table_name,
                                    'application': self.app_name,                        
                                    'filter': 'active=true^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create 'Open - Unassigned' module
        post_data = json.dumps({
                                    'title': "Open - Unassigned",
                                    'active': True,
                                    'order': '400',
                                    'link_type': 'LIST',
                                    'name': self.table_name,
                                    'application': self.app_name,
                                    'filter': 'active=true^assigned_toISEMPTY^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create 'Assigned to me' module
        post_data = json.dumps({
                                    'title': "Assigned to me",
                                    'active': True,
                                    'order': '500',
                                    'link_type': 'LIST',
                                    'name': self.table_name,
                                    'application': self.app_name,
                                    'filter': 'active=true^assigned_to=javascript:getMyAssignments()^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create 'Closed' module
        post_data = json.dumps({
                                    'title': 'Closed',
                                    'active': True,
                                    'order': '600',
                                    'link_type': 'LIST',
                                    'name': self.table_name,
                                    'application': self.app_name,
                                    'filter': 'active=false'
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
                                    'order':'700',
                                    'link_type': 'LIST',
                                    'name': self.table_name,
                                    'application': self.app_name
                                })
        return self.verify_post_data(url, post_data)

    def create_reports(self):
        # Create My Open Custom App Records report
        url = "https://{}.service-now.com/api/now/table/sys_report".format(self.instance_prefix)
        post_data = json.dumps({
                                    'title': "My Open {} Issues".format(self.app_name),
                                    'table': self.table_name,
                                    'type': 'list',
                                    'filter': 'opened_byDYNAMIC90d1921e5f510100a9ad2572f2b477fe^active=true'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create Open Custom App Records by Assignment report
        post_data = json.dumps({
                                    'title': "Open {} Records by Assignment".format(self.app_name),
                                    'table': self.table_name,
                                    'field': 'assigned_to',
                                    'type': 'bar',
                                    'filter': 'active=true^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create Open Custom app Records by Priority report
        post_data = json.dumps({
                                    'title': "Opened {} this month by Priority".format(self.app_name),
                                    'table': self.table_name,
                                    'field': 'priority',
                                    'type': 'bar',
                                    'filter':'opened_atONThis month@javascript:gs.beginningOfThisMonth()'\
                                                '@javascript:gs.endOfThisMonth()'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create Open Custom app Records by State report
        post_data = json.dumps({ 
                                    'title': 'Open {} Records by State'.format(self.app_name),
                                    'table': self.table_name,
                                    'field': 'state',
                                    'type': 'pie',
                                    'filter': 'active=true^EQ'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
       # Create Open Custom app Records by Escalation report        
        post_data = json.dumps({ 
                                    'title':'Open {} Records by Escalation'.format(self.app_name),
                                    'table': self.table_name,
                                    'field': 'escalation',
                                    'type': 'bar',
                                    'filter': 'active=true^EQ'
                                })
        return self.verify_post_data(url, post_data)

    def add_reports(self):
        # Add all created reports to overview page
        return self.web_driver.add_reports(self.app_name, 5) # 5 reports expected
        
    def create_assignment_rules(self):
        # Create default assignment for all records on new table, new group
        url = "https://{}.service-now.com/api/now/table/sysrule_assignment".format(self.instance_prefix)
        post_data = json.dumps({
                                    'active': True,
                                    'name': "{} Group Assignment".format(self.app_name),
                                    'table': self.table_name,
                                    'group': self.app_name
                                })
        return self.verify_post_data(url, post_data)
        
    def setup_slas(self):
        # Create sysrule_escalate for Custom App Priority 1
        url = "https://{}.service-now.com/api/now/table/sysrule_escalate".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': "{} Priority 1".format(self.app_name),
                                    'table': self.table_name,
                                    'description': "Priority 1 should be solved within eight hours"\
                                                    " on a 24X7 basis (no calendar).",
                                    'condition': 'priority=1^EQ',
                                    'pause_condition': 'active=false^EQ'
                                })
        p1_sla_sys_id, log = self.get_json_response_key('sys_id', url, post_data) 
        
        if not p1_sla_sys_id:
            return p1_sla_sys_id, log
        else:
            self.state_variables['p1_sla_sys_id'] = p1_sla_sys_id
            self.log(log)
        # Create sysrule_escalate for Custom App Priority 2 and save the sla sys_id               
        post_data = json.dumps({
                                    'name': "{} Priority 2".format(self.app_name),
                                    'table': self.table_name,
                                    'description': "Priority 2 should be solved within tweny four hours"\
                                                    " on a 24X7 basis (no calendar).",
                                    'condition': 'priority=2^EQ',
                                    'pause_condition': 'active=false^EQ'
                                })
        p2_sla_sys_id, log = self.get_json_response_key('sys_id', url, post_data) 
        
        if not p2_sla_sys_id:
            return p2_sla_sys_id, log
        else:
            self.state_variables['p2_sla_sys_id'] = p2_sla_sys_id
            self.log(log)
        # Create sysrule_escalate for Custom App Priority 3 and save the sla sys_id
        post_data = json.dumps({
                                    'name': "{} Priority 3".format(self.app_name),
                                    'table': self.table_name,
                                    'description': "Priority 3 should be solved within three business days"\
                                                    " on a 24X7 basis (no calendar).",
                                    'condition': 'priority=3^EQ',
                                    'pause_condition': 'active=false^EQ'
                                })
        p3_sla_sys_id, log = self.get_json_response_key('sys_id', url, post_data) 
        
        if not p3_sla_sys_id:
            return p3_sla_sys_id, log
        else:
            self.state_variables['p3_sla_sys_id'] = p3_sla_sys_id
            self.log(log)
        # Create sysrule_escalate for Custom App Priority 4 and save the sla sys_id        
        post_data = json.dumps({
                                    'name': "{} Priority 4".format(self.app_name),
                                    'table': self.table_name,
                                    'description': "Priority 4 should be solved within five business days on a 24X7 basis (no calendar).",
                                    'condition': 'priority=4^EQ',
                                    'pause_condition': 'active=false^EQ'
                                })
        p4_sla_sys_id, log = self.get_json_response_key('sys_id', url, post_data) 
        
        if not p4_sla_sys_id:
            return p4_sla_sys_id, log
        else:
            self.state_variables['p4_sla_sys_id'] = p4_sla_sys_id
            self.log(log)
        
        # Create sysrule_escalate_interval for Custom App Priority 1 Moderate Escalation
        url = "https://{}.service-now.com/api/now/table/sysrule_escalate_interval".format(instance_prefix)
        post_data = json.dumps({
                                    'escalation': self.state_variables['p1_sla_sys_id'],
                                    'escalation_level': '1',
                                    'wait': '1970-01-01 00:15:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 1 High Escalation          
        post_data = json.dumps({
                                    'escalation': self.state_variables['p1_sla_sys_id'],
                                    'escalation_level': '2',
                                    'wait': '1970-01-01 02:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 1 Overdue Escalation 
        post_data = json.dumps({
                                    'escalation': self.state_variables['p1_sla_sys_id'],
                                    'escalation_level': '3',
                                    'wait': '1970-01-01 02:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 2 Moderate Escalation        
        post_data = json.dumps({
                                    'escalation': self.state_variables['p2_sla_sys_id'],
                                    'escalation_level': '1',
                                    'wait': '1970-01-01 08:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 2 High Escalation
        post_data = json.dumps({
                                    'escalation': self.state_variables['p2_sla_sys_id'],
                                    'escalation_level': '2',
                                    'wait': '1970-01-01 08:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
       
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 2 Overdue Escalation 
        post_data = json.dumps({
                                    'escalation': self.state_variables['p2_sla_sys_id'],
                                    'escalation_level': '3',
                                    'wait': '1970-01-01 08:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
         # Create sysrule_escalate_interval for Custom App Priority 3 Moderate Escalation       
        post_data = json.dumps({
                                    'escalation': self.state_variables['p3_sla_sys_id'],
                                    'escalation_level': '1',
                                    'wait': '1970-01-01 24:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 3 High Escalation        
        post_data = json.dumps({
                                    'escalation': self.state_variables['p3_sla_sys_id'],
                                    'escalation_level': '2',
                                    'wait': '1970-01-01 24:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 3 Overdue Escalation           
        post_data = json.dumps({
                                    'escalation': self.state_variables['p3_sla_sys_id'],
                                    'escalation_level': '3',
                                    'wait': '1970-01-01 24:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 4 Moderate Escalation        
        post_data = json.dumps({
                                    'escalation': self.state_variables['p4_sla_sys_id'],
                                    'escalation_level': '1',
                                    'wait': '1970-01-01 48:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 4 High Escalation
        post_data = json.dumps({
                                    'escalation': self.state_variables['p4_sla_sys_id'],
                                    'escalation_level': '2',
                                    'wait': '1970-01-01 48:00:00'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)
        # Create sysrule_escalate_interval for Custom App Priority 4 Overdue Escalation            
        post_data = json.dumps({
                                    'escalation': self.state_variables['p4_sla_sys_id'],
                                    'escalation_level': '3',
                                    'wait': '1970-01-01 24:00:00'
                                })
        return self.verify_post_data(url, post_data)             

    def create_catalog_category(self):
        # Create catalog category for Custom App Services and save category sys_id
        url = "https://{}.service-now.com/api/now/table/sc_category".format(self.instance_prefix)
        post_data = json.dumps({
                                    'active': True,
                                    'sc_catalog': 'e0d08b13c3330100c8b837659bba8fb4',
                                    'title': "{} Services".format(self.app_name),
                                    'description': "Request goods and services from the {} group.".format(self.app_name)
                                })
        catalog_category_sys_id, log = self.get_json_response_key('sys_id', url, post_data)
        
        if catalog_category_sys_id:
            self.state_variables['catalog_category_sys_id'] = catalog_category_sys_id
            
        return catalog_category_sys_id, log    

    def create_record_producer(self):
        # Create Custom App Record Producer in created catalog category and save record producer sys_id
        url = "https://{}.service-now.com/api/now/table/sc_cat_item_producer".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': "{} Record Producer".format(self.app_name),
                                    'table_name': self.table_name,
                                    'active': True,
                                    'category': self.state_variables['catalog_category_sys_id'],
                                    'short_description': "Get {} help".format(self.app_name),
                                    'description': "Submit an issue or question regarding {} services.".format(self.app_name)
                                })
        record_producer_sys_id, log = self.get_json_response_key('sys_id', url, post_data)
        
        if not record_producer_sys_id:
            return record_producer_sys_id, log
        else:
            self.state_variables['record_producer_sys_id'] = record_producer_sys_id
            self.log(log)

        url = "https://{}.service-now.com/api/now/table/item_option_new".format(instance_prefix)
        # Create short description variable
        post_data = json.dumps({
                                    'map_to_field': True,
                                    'field': 'short_description',
                                    'type': "Single Line Text",
                                    'mandatory': True,
                                    'cat_item': self.state_variables['record_producer_sys_id'],
                                    'question_text': "What is your question or issue?",
                                    'order': '10'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)           
        # Create description variable
        post_data = json.dumps({
                                    'map_to_field': True,
                                    'field': 'additional_comments',
                                    'type': "Multi Line Text",
                                    'mandatory': False,
                                    'cat_item': self.state_variables['record_producer_sys_id'],
                                    'question_text': "Please provide any additional information below:",
                                    'order': '20'
                                })
        return self.verify_post_data(url, post_data)

    def create_catalog_item(self):
        # Create Custom App catalog item in created catalog category
        url = "https://{}.service-now.com/api/now/table/sc_cat_item".format(self.instance_prefix)
        post_data = json.dumps({
                                    'name': "{} Item".format(self.app_name),
                                    'active': True,
                                    'category': self.state_variables['catalog_category_sys_id'],
                                    'delivery_plan': '523da512c611228900811a37c97c2014',
                                    'short_description': "Request item or service from {}".format(self.app_name),
                                    'description': "Submitting this form will begin the standard "\
                                                    "request fulfillment process for a {} item.".format(self.app_name),
                                    'sc_catalogs': 'e0d08b13c3330100c8b837659bba8fb4'
                                })
        catalog_item_sys_id, log = self.get_json_response_key('sys_id', url, post_data)
        
        if catalog_item_sys_id:
            self.state_variables['catalog_item_sys_id'] = catalog_item_sys_id
        
        url = "https://{}.service-now.com/api/now/table/item_option_new".format(instance_prefix)
        # Create short description variable
        post_data = json.dumps({
                                    'map_to_field': True,
                                    'type': "Single Line Text",
                                    'mandatory': True,
                                    'cat_item': self.state_variables['catalog_item_sys_id'],
                                    'question_text': "What item or service are you requesting?",
                                    'order': '10'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        # Create description variable
        post_data = json.dumps({
                                    'map_to_field': True,
                                    'type': "Multi Line Text",
                                    'mandatory': False,
                                    'cat_item': self.state_variables['catalog_item_sys_id'],
                                    'question_text': "Please provide any additional information below:",
                                    'order': '20'
                                })
        return self.verify_post_data(url, post_data)
                        
    def run(self):
        self.log("Starting run from step {}...".format(self.state_variables['state']))
        start_time = time.time()
        
        while(self.state_variables['state'] <= len(self.state_map)):
            state_func, state_desc = self.state_map[self.state_variables['state']]
                        
            self.log("{} STARTED: {}".format(self.get_progress_string(), state_desc))
            success, log = state_func()
  
            if success:
                self.log(log)
                self.log("{} SUCCESS: Completed step successfully.".format(self.get_progress_string()), False)
            else:
                self.log("{} FAILURE: {}".format(self.get_progress_string(), log), False)
                self.log("Ending run prematurely...", False)
                self.save_state()
                break
           
            self.state_variables['state'] += 1
                
        time_elapsed = time.time() - start_time
        self.log("Run completed in {}min {}s.".format(str(time_elapsed // 60).split('.')[0],
                                                    str(time_elapsed % 60).split('.')[0]))                                                    
           
    def save_state(self):
        backup_state = open('backup_state.pkl', 'wb')
        pickle.dump(self.state_variables, backup_state)
        backup_state.close()
        self.log("State variables saved in backup_state.pkl.", False)

if __name__ == '__main__':
        if len(sys.argv) < 6 :
            print "Usage: {} [instance prefix] [user] [password] [app name]"\
                    "[app prefix] (state file)".format(sys.argv[0])

        state_data = {}

        if len(sys.argv) > 6:
            state_path = sys.argv[6]
            if not os.path.isfile(state_path):
                print "Could not find state file: {}".format(state_path)
            else:
                state_file = open(state_path, "wb")
                state_data = pickle.load(state_file)        
        
        app_creator = AppCreator(instance_prefix, user, pwd, app_name, 
                                 app_prefix, state_data)
                                 
        app_creator.run()
        app_creator.web_driver.end_session()