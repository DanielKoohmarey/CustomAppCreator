# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 13:51:07 2016

@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2016

Dependencies: 
    sudo pip install selenium
    sudo apt-get install firefox
    
Notes:
If firefox version > 46:    
   wget https://github.com/mozilla/geckodriver/releases/download/v0.11.1/geckodriver-v0.11.1-linux64.tar.gz
   tar -zxvf geckodriver-v0.11.1-linux64.tar.gz
   sudo mv geckodriver /usr/bin
Or:
    sudo apt-get purge firefox
    sudo add-apt-repository ppa:ubuntu-mozilla-daily/ppa
    apt-cache show firefox | grep Version
    sudo apt-get install firefox=45.0.2+build1-0ubuntu1
    sudo apt-mark hold firefox
    
    To upgrade:
    
    sudo apt-mark unhold firefox
    sudo apt-get upgrade    
"""
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from pyvirtualdisplay import Display

class AppWebDriver(object):
    def __init__(self, prefix):
        self.instance_prefix = prefix
        #self.display = Display(visible=0, size=(1280, 960))
        #self.display.start()        
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()

    def end_session(self):
        self.driver.get("https://{}.service-now.com/logout.do".format(self.instance_prefix))
        self.driver.delete_all_cookies()
        try:
            self.driver.quit()
        except:
            print "Failed to quit webdriver."
        #self.display.stop()
        
    def wait_for_element(self, element_id, max_wait):
        wait = 0
        element = None
        while wait < max_wait:
            elements = self.driver.find_elements_by_id(element_id)
            if elements:
                element = elements[0]
                break
            else:
                wait += 1
                time.sleep(1)
        return element

    def login(self, user, pwd):
        success = True
        log = "Logged in successfully."
        try:        
            self.driver.get("https://{}.service-now.com/login.do".format(self.instance_prefix))
            user_input = self.driver.find_element_by_name('user_name')
            user_input.send_keys(user)
            pass_input = self.driver.find_element_by_name('user_password')
            pass_input.send_keys(pwd)
            submit_button = self.driver.find_element_by_name('not_important')
            submit_button.click()        
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log
        
    def create_custom_table(self, table_name, app_prefix, app_name = '', new_app = True, new_module = True):
        success = True
        log = "Custom table created successfully."
        try:
            # Create custom table
            self.driver.get("https://{}.service-now.com/nav_to.do?uri=%2Ftable_columns.do".format(self.instance_prefix))
            self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
            table_name_input = self.driver.find_element_by_name("sysparm_tablelabel")
            table_name_input.send_keys(table_name)
            extends_dropdown = self.driver.find_element_by_xpath("//select[@id='sysparm_extends']/option[@value='task']")
            extends_dropdown.click()
            number_prefix_input = self.wait_for_element('sysparm_number_prefix', 10)
            number_prefix_input.send_keys(app_prefix)
            if app_name:
                # Fill in app name field
                app_name_input = self.driver.find_element_by_name('sysparm_app_name')
                app_name_input.clear()
                app_name_input.send_keys()
            if not new_app:
                # Uncheck new app checkbox
                new_app_checkbox = self.driver.find_element_by_name('sysparm_new_application')
                new_app_checkbox.click()
            if not new_module:
                # Uncheck new module checkbox
                new_module_checkbox = self.driver.find_element_by_name('sysparm_new_module')                
                new_module_checkbox.click()
            create_button = self.driver.find_element_by_name('create')
            create_button.click()
            # Wait for and accept confirmation dialogue
            WebDriverWait(self.driver, 10).until(expected_conditions.alert_is_present(), "Timed out waiting for create dialogue.")
            alert = self.driver.switch_to_alert()
            alert.accept()
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log

    def add_reports(self, app_name, expected):
        success = True
        log = "Added {} reports successfully.".format(expected)
        try:
            self.driver.get("https://{}.service-now.com/home.do?sysparm_view={}_overview".format(self.instance_prefix, app_name))
            # Open add content popup
            add_content_button = self.driver.find_element_by_xpath("//button[text()='Add content']")
            add_content_button.click()
            renderers_select = Select(self.driver.find_elements_by_class_name('home_select_content')[0])
            renderers_select.select_by_visible_text('Reports')
            time.sleep(10) # wait for reports column to populate
            report_select = Select(self.driver.find_elements_by_class_name('home_select_content')[1])
            report_select.select_by_visible_text(app_name)
            # Add available content to grid
            content_select = Select(self.driver.find_elements_by_class_name('home_select_content')[2])
            dropzone = 'dropzone1'
            for content in content_select.options[1:]:
                content.click()
                add_button = self.driver.find_element_by_xpath("//*[@id='{}']/a".format(dropzone))
                add_button.click()
                if dropzone == 'dropzone1':
                    dropzone = 'dropzone2'
                else:
                    dropzone = 'dropzone1'
                time.sleep(2) # allow report to be added before adding the next one
            close_popup = self.driver.find_element_by_css_selector('a.icon-cross-circle:nth-child(1)')
            close_popup.click()
            # Verify correct number of reports added 
            reports_added = len(self.driver.find_elements_by_class_name('report_content'))
            if  reports_added != expected:
                success = False
                log = "{} of {} reports added.".format(reports_added, expected)
        
        except Exception, e:
            success = False
            log = traceback.format_exc(e)       
        
        return success, log
        
    def open_configuration_menu(self, table_name, menu):
            self.driver.get("https://{}.service-now.com/{}.do".format(self.instance_prefix, table_name))        
            # Open Configuration->menu
            menu_button = self.driver.find_element_by_class_name('icon-menu')
            menu_button.click()
            configure_menu = self.driver.find_element_by_xpath("//div[contains(@class, context_item) and text() = 'Configure']")
            actions = ActionChains(self.driver)
            actions.move_to_element(configure_menu)
            actions.perform()
            form_layout = self.driver.find_element_by_xpath("//div[contains(@class, context_item) and text() = '{}']".format(menu))
            form_layout.click()
            time.sleep(2) # wait for select options to populate        
        
    def configure_form_layout(self, table_name, section_name, configuration, new_fields):
        success = True
        log = "Form Layout for {} configured successfully.".format(table_name)
        try:
            self.open_configuration_menu(table_name, 'Form Layout')
            section_select = Select(self.driver.find_element_by_id('sysparm_section'))
            if section_name in [option.text for option in section_select.options]:
                section_select.select_by_visible_text(section_name)
                time.sleep(2) # wait for selected options to update
                # Remove all Selected fields
                selected_select = Select(self.driver.find_element_by_id('select_1'))
                remove_selected_button = self.driver.find_element_by_xpath("//a[contains(@class, 'icon-chevron-left')]")          
                for selected in selected_select.options:
                    selected.click()
                    remove_selected_button.click()
            else:
                # Create new section
                section_select.select_by_visible_text('New...')
                time.sleep(2) # wait for section prompt
                section_caption_input = self.driver.find_element_by_id('glide_prompt_answer')
                section_caption_input.send_keys(section_name)
                section_ok_button = self.driver.find_element_by_id('ok_button')
                section_ok_button.click()
                time.sleep(2) # wait for selected options to update
                
            # Add new Selected fields
            available_select = Select(self.driver.find_element_by_id('select_0'))
            add_available_button = self.driver.find_element_by_class_name('icon-chevron-right')
            for add_to_selected in configuration:
                available_options = [option.text for option in available_select.options]
                if available_options.count(add_to_selected) > 1:
                    # Only select first option if multiple matches exist
                    available_select.select_by_visible_text(add_to_selected)
                    first_option = available_select.first_selected_option
                    available_select.deselect_all()
                    first_option.click()
                    add_available_button.click()
                    available_select.deselect_by_visible_text(add_to_selected)                    
                elif add_to_selected in available_options:
                    available_select.select_by_visible_text(add_to_selected)
                    add_available_button.click()
                    available_select.deselect_by_visible_text(add_to_selected)
                else:
                    # Create new field
                    if add_to_selected not in new_fields:
                        return False, "Missing form layout field: {}".format(add_to_selected)                   
                    new_field_name_input = self.driver.find_element_by_id('newOption')            
                    new_field_name_input.send_keys(add_to_selected)
                    new_field_type_select = Select(self.driver.find_element_by_id('newType'))
                    new_field_type_select.select_by_visible_text(new_fields[add_to_selected])
                    # Add new field to Selected
                    add_field_button = self.driver.find_element_by_id('addButton')
                    add_field_button.click()
                    selected_select = Select(self.driver.find_element_by_id('select_1'))
                    selected_select.deselect_all()
                    selected_select.select_by_visible_text(add_to_selected)
            
            save_button = self.driver.find_element_by_id('sysverb_save')
            save_button.click()
            
        except Exception, e:
            success = False
            log = traceback.format_exc(e)       
        
        return success, log

    def configure_related_lists(self, table_name, configuration):
        success = True
        log = "Related Lists for {} configured successfully.".format(table_name)
        try:
            self.open_configuration_menu(table_name, 'Related Lists')
            available_select = Select(self.driver.find_element_by_id('select_0'))
            add_available_button = self.driver.find_element_by_class_name('icon-chevron-right')
            for add_to_selected in configuration:
                available_select.select_by_visible_text(add_to_selected)
                add_available_button.click()
                available_select.deselect_by_visible_text(add_to_selected)
            save_button = self.driver.find_element_by_id('sysverb_save')
            save_button.click()
        except Exception, e:
            success = False
            log = traceback.format_exc(e)       
        
        return success, log
if __name__ == '__main__':
    user = 'admin'
    pwd = 'admin'
    instance_prefix = 'dkoohsc5'
    app_prefix = ''
    app_name = ''    
    app = AppWebDriver(instance_prefix)
    app.login(user, pwd)
    #app.create_custom_table(app_name, app_prefix)
    #app.add_reports(app_name, 4)
    #expected_selected = ['|- begin_split -|', 'Number', 'Portfolio', 'Priority',
    #                     'Configuration item [+]', '|- split -|', 'Assignment group [+]', 'Assigned to [+]',
    #                    'State', 'Project Size','|- end_split -|', 'Short description','Description']
    #new_fields = { 'Portfolio' : 'Choice', 'Project Size' : 'Choice'}    
    #expected_selected = ['|- begin_split -|', 'Planned Start', 'Planned End', 'Estimated Cost', '|- split -|',
    #                     'Actual Start', 'Actual End', 'Actual Cost', '|- end_split -|']
    #new_fields = { 'Planned Start' : 'Date/Time', 'Planned End' : 'Date/Time', 'Estimated Cost' : 'Price',
    #              'Actual Start' : 'Date/Time', 'Actual End' : 'Date/Time', 'Actual Cost': 'Price',} 
    #expected_selected = ['|- begin_split -|', 'Watch list', '|- split -|', 'Work notes list', '|- end_split -|',
    #                   'Work notes', 'Additional comments', 'Activities (filtered)']
    #new_fields = {}
    #print app.configure_form_layout('u_project', 'Notes', expected_selected, new_fields)
    configuration = ['Project Task->Parent']
    print app.configure_related_lists('u_project',configuration)