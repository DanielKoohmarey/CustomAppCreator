# -*- coding: utf-8 -*-
"""
@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

Note:
    Run screen -S server, then python gmail_monitor.py
    To detach screen, ctrl+a+d
    To resume, screen -r server
    To view screens, screen -ls
    To exit once attached, type exit
"""
import time
import datetime
import gmail_wrapper
import traceback

from email.utils import parsedate_tz, mktime_tz
from custom_app_creator import CustomAppCreator
from pm_app_creator import PMAppCreator

def main():
    wrapper = gmail_wrapper.GmailWrapper()    
  
    while True:
        # Get an unread (unprocessed) automation request
        unread_msg_id = wrapper.get_unread_message_id()
        if unread_msg_id:
            msg_data = wrapper.get_message_data(unread_msg_id)
            msg_body = msg_data['body'].split('\n')
            msg_body = [elem.rstrip('\r') for elem in msg_body]
            # Check if email is an automation request
            if not msg_body or msg_body[0] != "Automation Request":
                wrapper.mark_as_read(unread_msg_id)
                continue
            # Process emails a minimum of 4 hours later
            timezone_time = parsedate_tz(msg_data['date'])
            epoch_time = mktime_tz(timezone_time)
            received_time = datetime.datetime.utcfromtimestamp(epoch_time)
            if ((datetime.datetime.now() - received_time).total_seconds() // 3600) < 4:
                continue
            formatted_time = received_time.strftime("%m-%d-%y %I:%M:%S %p")
            current_time = datetime.datetime.now().strftime("%m-%d-%y %I:%M:%S %p")
            print "{} Parsing email from {}".format(current_time, formatted_time)
            # Parse out run variables
            run_variables = {}
            for line in msg_body[1:]:
                if not line or ':' not in line:
                    continue
                variable, value = line.split(':')
                run_variables[variable] = value.strip()
            # Create the appropriate automation class
            app_creator = None                
                
            if run_variables['Type'] == 'Custom App':
                app_creator = CustomAppCreator(run_variables['Instance Prefix'],
                                               run_variables['User'],
                                                run_variables['Password'],
                                                run_variables['App Name'],
                                                run_variables['App Prefix'])
                                                
            elif run_variables['Type'] == 'Project Management App':
                app_creator = PMAppCreator(run_variables['Instance Prefix'],
                                           run_variables['User'],
                                            run_variables['Password'])
            
            if not app_creator:
                wrapper.mark_as_read(unread_msg_id)
                continue
            
            app_creator.run()
            app_creator.web_driver.end_session()
            
            # Generate email result report
            success = 'FAILED'
            if app_creator.state_variables['state'] > len(app_creator.state_map):
                success = 'SUCCEEDED'
            subject = "{} {}: {}".format(run_variables['Instance Prefix'], run_variables['Type'], success)        
            
            html = "<h2>{} {} Automation Report</h2>".format(app_creator.instance_prefix, run_variables['Type'])
            html += app_creator.get_html_results()
            html += "<h4> Automation request received at {}</h4>".format(formatted_time)
            plain = "\r\n".join(['{}. {}'.format(step, desc) for step, desc in app_creator.logged])
            
            message = wrapper.create_message(subject, plain, html)
            wrapper.send_message(message)
            
            wrapper.mark_as_read(unread_msg_id)
            
        else:
            print "{} Sleeping 5min before checking email... ".format(datetime.datetime.now())
            time.sleep(300) # check mail every 5 min


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception, e:
        wrapper = gmail_wrapper.GmailWrapper()
        crash_string = traceback.format_exc(e)
        print crash_string
        crash_msg = wrapper.create_message('Gmail Monitor Crashed', crash_string, crash_string)
        wrapper.send_message(crash_msg)