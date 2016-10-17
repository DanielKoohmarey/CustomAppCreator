# -*- coding: utf-8 -*-
"""
@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016
"""
import time
import datetime
import gmail_wrapper

from custom_app_creator import CustomAppCreator

def main():
    wrapper = gmail_wrapper.GmailWrapper()    
    current_day = datetime.date.today().day    
    
    while True:
        # Get an unread (unprocessed) automation request
        unread_msg_id = wrapper.get_unread_message_id()
        if unread_msg_id:
            msg_data = wrapper.get_message_data(unread_msg_id)
            msg_body = msg_data['body'].split('\r\n')
            # Check if email is an automation request            
            if not msg_body or msg_body[0] != "Automation Request":
                wrapper.mark_as_read(unread_msg_id)
                continue
            print "{} Parsing email from {}".format(datetime.datetime.now(), msg_data['date'])
            # Parse out run variables
            run_variables = {}
            for line in msg_body[1:]:
                if not line:
                    continue
                variable, value = line.split(': ')
                run_variables[variable] = value.strip()
            # Create the appropriate automation class
            app_creator = None                
                
            if run_variables['Type'] == 'Custom App':
                app_creator = CustomAppCreator(run_variables['Instance Prefix'],
                                               run_variables['User'],
                                                run_variables['Password'],
                                                run_variables['App Name'],
                                                run_variables['App Prefix'])
            
            if not app_creator:
                wrapper.mark_as_read(unread_msg_id)
                continue
            
            app_creator.run()
            app_creator.web_driver.end_session()
            
            # Generate email result report
            success = 'FAILED'
            if app_creator.state_variables['state'] > len(app_creator.state_map):
                success = 'SUCCEEDED'
            subject = "{} creation: {}".format(app_creator.app_name, success)        
            
            html = "<h2>{} {} Automation Report</h2>".format(run_variables['Type'], app_creator.app_name)
            html += app_creator.get_html_results()
            html += "<h4> Automation request received at {}</h4>".format(msg_data['date'])
            plain = "\r\n".join(['{}. {}'.format(step, desc) for step, desc in app_creator.logged])
            
            message = wrapper.create_message(subject, plain, html)
            wrapper.send_message(message)
            
            wrapper.mark_as_read(unread_msg_id)
            
        else:
            print "{} Sleeping 5min before checking email... ".format(datetime.datetime.now())
            time.sleep(300) # check mail every 5 min
            
        if current_day != datetime.date.today().day:
            current_day = datetime.date.today().day
            heartbeat_msg = wrapper.create_message('Gmail Monitor Still Running',
                                                   '{} Script Heartbeat.'.format(datetime.datetime.now()),
                                                   '{} Script Heartbeat.'.format(datetime.datetime.now()),
                                                   'danielkoohmarey@gmail.com')
            wrapper.send_message(heartbeat_msg)


if __name__ == '__main__':
    main()