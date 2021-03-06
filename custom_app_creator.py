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
import pickle
import requests
import sys
import os
import getpass

from app_creator import AppCreator

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() # if python version < 2.7.9

class CustomAppCreator(AppCreator):
    
    def __init__(self, instance_prefix, user, pwd, app_name, app_prefix, 
                     prev_state = {}):
        self.app_name = app_name
        self.app_prefix = app_prefix                         
        self.table_name = 'u_'+ app_name.replace(" ","_").lower()
        auth_pair = user, pwd
        run_variables = {}
        run_variables['app_name'] = app_name
        run_variables['app_prefix'] = app_prefix
        run_variables['table_name'] = self.table_name
        AppCreator.__init__(self, instance_prefix, auth_pair, run_variables, 
                                prev_state)
                                
        self.state_map = {
                            1: (self.check_login_credentials,
                                    "Check if the login credentials are valid."),
                            2: (self.check_for_custom_table,
                                    "Check if the custom app table already exists."),
                            3: (self.create_custom_table,
                                    "Create the custom app table & retrieve the app sys id."),
                            4: (self.setup_custom_app_role,
                                    "Create custom app role and apply to app."),
                            5: (self.set_role_permissions,
                                    "Add delete role to custom role."),                                     
                            6: (self.set_custom_group_role,
                                    "Create the group record & assign custom role to group."),
                            7: (self.create_live_feed_group,
                                    "Create the live feed group."),
                            8: (self.create_knowledge_base,
                                    "Create the knowledge base & retrieve the knowledge sys id."),
                            9: (self.create_user_criteria_record,
                                    "Create a user criteria record & retrieve the criteria sys id."),
                            10: (self.create_can_contribute_record,
                                     "Create a can contribute record."),
                            11: (self.create_email_notification_records,
                                     "Create email notification records."),
                            12: (self.create_inbound_email_actions,
                                     "Retrieve the plus sys id & create inbound email actions."),
                            13: (self.create_modules,
                                     "Retrieve the page sys id & create modules."),
                            14: (self.create_reports,
                                     "Create reports."),
                            15: (self.create_assignment_rules,
                                     "Create assignment rules."),                                      
                            16: (self.setup_slas,
                                     "Create SLAs & save P1-P4 sla sys ids & create escalation rule."),
                            17: (self.create_catalog_category,
                                     "Create catalog category & save category sys id."),
                            18: (self.create_record_producer,
                                     "Create record producer & save producer sys id."),
                            19: (self.create_catalog_item,
                                     "Create catalog item & save item sys id."),
                            20: (self.add_reports,
                                     "Add reports to overview."),
                        }                                           
                        
    def check_for_custom_table(self):                             
        return self.check_for_table(self.table_name)               
                             
    def create_custom_table(self):
        # Create the custom table
        success, log = self.web_driver.create_table(self.app_name,
                                                    self.app_prefix,
                                                   self.app_name)
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
                                    'description': "This role is required for access "\
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
        put_data = json.dumps({
                                    'roles': self.app_name        
                                })        
        return self.verify_put_data(url, put_data)                              

    def set_role_permissions(self):
        # Get table dictionary record sys id
        url = "https://{}.service-now.com/api/now/table/sys_dictionary?sysparm_query="\
                "name%3D{}%5Einternal_type%3Dcollection&sysparm_limit=1".format(self.instance_prefix, self.table_name)
        role_sys_id, log = self.get_json_response_key('sys_id', url)

        if not role_sys_id:
            return role_sys_id, log
        else:
            self.state_variables['role_sys_id'] = role_sys_id
            self.log(log) 
        
        url = "https://{}.service-now.com/api/now/table/sys_dictionary/{}".format(self.instance_prefix,
                                                                                    self.state_variables['role_sys_id'])
        put_data = json.dumps({
                                    'delete_roles': self.app_name        
                                })
        return self.verify_put_data(url, put_data)

    def set_custom_group_role(self):
        # Check if the group record already exists
        url = "https://{}.service-now.com/api/now/table/sys_user_group?"\
                "sysparm_query=nameSTARTSWITH{}&sysparm_limit=1".format(self.instance_prefix, self.app_name)       
        response = requests.get(url, auth=self.auth_pair, headers=self.json_headers)
        if response.status_code == 200:
            if response.json()['result']:
                return True, "The {} group already exists, skipping creation.".format(self.app_name)
        
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
        url = 'https://{}.service-now.com/api/now/table/kb_knowledge_base'.format(self.instance_prefix)
        post_data = json.dumps({
                                    'description': "Read self-help articles and learn more about {}".format(self.app_name),
                                    'active': False,
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
                                    'subject': "{} ${{number}} has been assigned to group "\
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
        plus_sys_id, log = self.get_json_response_key('sys_id', url, post_data)
        
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
                                    'order': '95',
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
                                    'field': '',
                                    'type': 'list',
                                    'filter': 'opened_byDYNAMIC90d1921e5f510100a9ad2572f2b477fe^active=true',
                                    'user': 'GLOBAL'
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
                                    'filter': 'active=true^EQ',
                                    'user': 'GLOBAL'
                                })
        success, log = self.verify_post_data(url, post_data)
        
        if not success:
            return success, log
        else:
            self.log(log)

        # Create Open Custom app Records by Priority report
        post_data = json.dumps({
                                    'title': "Opened {} Records this month by Priority".format(self.app_name),
                                    'table': self.table_name,
                                    'field': 'priority',
                                    'type': 'bar',
                                    'filter':'opened_atONThis month@javascript:gs.beginningOfThisMonth()'\
                                                '@javascript:gs.endOfThisMonth()',
                                    'user': 'GLOBAL'
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
                                    'filter': 'active=true^EQ',
                                    'user': 'GLOBAL'
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
                                    'filter': 'active=true^EQ',
                                    'user': 'GLOBAL'
                                })
        return self.verify_post_data(url, post_data)

    def add_reports(self):
        # Add all created reports to overview page
        return self.web_driver.add_reports(self.app_name, [self.app_name], 4, 1) # 4 reports expected, skip the 1st one
        
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
        url = "https://{}.service-now.com/api/now/table/sysrule_escalate_interval".format(self.instance_prefix)
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

        # Create short description variable            
        url = "https://{}.service-now.com/api/now/table/item_option_new".format(self.instance_prefix)
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
        
        url = "https://{}.service-now.com/api/now/table/item_option_new".format(self.instance_prefix)
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
        
if __name__ == '__main__':
    state_data = {}  

    if(len(sys.argv) == 2 and sys.argv[1] == 'interactive'):  
        instance_prefix = raw_input("Enter Instance Prefix:\n").strip()
        user = raw_input("Enter User:\n").strip()
        password = getpass.getpass("Enter Password:\n")
        app_name = raw_input("Enter App Name:\n").strip()
        app_prefix = raw_input("Enter App Prefix:\n").strip()
        
        print "Running Custom App Creator with the following settings:\n"\
                "Instance Prefix: {0}\nUser: {1}\nPass: {2}\nApp Name: {3}\n"\
                "App Prefix: {4}".format(instance_prefix, user, "*"*len(password),
                                    app_name, app_prefix)  
        
        app_creator = CustomAppCreator(instance_prefix, user, password, app_name, 
                                       app_prefix, state_data)                            
        app_creator.run()
        app_creator.web_driver.end_session()
        
    elif len(sys.argv) > 5:
        if len(sys.argv) > 6:
            state_path = sys.argv[6]
            if not os.path.isfile(state_path):
                print "Could not find state file: {}".format(state_path)
            else:
                state_file = open(state_path, "wb")
                state_data = pickle.load(state_file)        
    
        print "Running Custom App Creator with the following settings:\n"\
                "Instance Prefix: {0}\nUser: {1}\nPass: {2}\nApp Name: {3}\n"\
                "App Prefix: {4}".format(sys.argv[1], sys.argv[2], "*"*len(sys.argv[3]),
                                    sys.argv[4], sys.argv[5])    
        
        app_creator = CustomAppCreator(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], 
                                 sys.argv[5], state_data)
                                 
        app_creator.run()
        app_creator.web_driver.end_session()
        
    else:
        print "Usage:\n{0} interactive \n{0} [instance prefix] [user] [password] [app name]"\
                "[app prefix] (state file)".format(sys.argv[0])