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
If firefox version > 46: (marionette does not support right click on element)
    wget https://github.com/mozilla/geckodriver/releases/download/v0.11.1/geckodriver-v0.11.1-linux64.tar.gz
    tar -zxvf geckodriver-v0.11.1-linux64.tar.gz
    sudo mv geckodriver /usr/bin
Or:
    Download firefox binary of version you want
    wget https://ftp.mozilla.org/pub/firefox/releases/44.0/linux-x86_64/en-US/firefox-44.0.tar.bz2
    tar -xjvf firefox-44.0.tar.bz2
    Point to the Binary when creating the driver
    

killall -e firefox to when testing to ensure clean up
"""
import time
import traceback

from selenium import webdriver
#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from pyvirtualdisplay import Display

class AppWebDriver(object):
    def __init__(self, prefix):
        self.instance_prefix = prefix
        self.display = Display(visible=0, size=(1280, 960))
        self.display.start()
        #binary = FirefoxBinary('firefox/firefox')
        #firefox = DesiredCapabilities.FIREFOX
        #firefox['marionette'] = False
        #self.driver = webdriver.Firefox(firefox_binary=binary, capabilities = firefox)          
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()

    def end_session(self):
        self.driver.get("https://{}.service-now.com/logout.do".format(self.instance_prefix))
        self.driver.delete_all_cookies()
        try:
            self.driver.quit()
        except:
            print "Failed to quit webdriver."
        self.display.stop()

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
        
    def create_table(self, table_name, app_prefix, app_name = '', new_module = False):
        success = True
        log = "Custom table created successfully."
        try:
            # Create custom table
            self.driver.get("https://{}.service-now.com/nav_to.do?uri=%2Ftable_columns.do".format(self.instance_prefix))
            self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
            # Fill in table name
            table_name_present = expected_conditions.presence_of_element_located((By.ID, 'sysparm_tablelabel'))
            WebDriverWait(self.driver, 5).until(table_name_present, "Could not find table name input.")
            table_name_input = self.driver.find_element_by_id("sysparm_tablelabel")
            table_name_input.send_keys(table_name)
            # Select extends table
            extends_dropdown = self.driver.find_element_by_xpath("//select[@id='sysparm_extends']/option[@value='task']")
            extends_dropdown.click()
            # Enter table number prefix
            number_prefix_present = expected_conditions.presence_of_element_located((By.ID, 'sysparm_number_prefix'))
            WebDriverWait(self.driver, 10).until(number_prefix_present, "Could not find number prefix input.")
            number_prefix_input = self.driver.find_element_by_id('sysparm_number_prefix')            
            number_prefix_input.send_keys(app_prefix)
            if app_name:
                # Fill in app name field
                app_name_input = self.driver.find_element_by_id('sysparm_app_name')
                app_name_input.clear()
                app_name_input.send_keys(app_name)
            else:
                # Uncheck new app checkbox
                new_app_checkbox = self.driver.find_element_by_id('sysparm_new_application')
                new_app_checkbox.click()
            if not new_module:
                # Uncheck new module checkbox
                new_module_checkbox = self.driver.find_element_by_id('sysparm_new_module')                
                new_module_checkbox.click()
            create_button = self.driver.find_element_by_name('create')
            create_button.click()
            # Wait for and accept confirmation dialogue
            WebDriverWait(self.driver, 10).until(expected_conditions.alert_is_present(), "Timed out waiting for create dialogue.")
            alert = self.driver.switch_to_alert()
            alert.accept()
            #TODO: Check if app prefix conflict warning exists?
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
            content_present = expected_conditions.presence_of_element_located((By.CLASS_NAME, 'home_select_content'))
            WebDriverWait(self.driver, 5).until(content_present)
            renderers_select = Select(self.driver.find_elements_by_class_name('home_select_content')[0])
            renderers_select.select_by_visible_text('Reports')
            # Wait for Reports options to populate 
            time.sleep(60)            
            content_present = expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "option[value='{}']".format(app_name)))
            WebDriverWait(self.driver, 10).until(content_present, "Could not find {} in Reports options.".format(app_name))            
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
    
    # Open the additional actions menu and select the 'Configure'-> menu
    def open_configure_menu(self, table_name, menu):
            self.driver.get("https://{}.service-now.com/{}.do".format(self.instance_prefix, table_name))        
            # Open 'Configure'
            menu_icon = self.driver.find_element_by_class_name('icon-menu')
            menu_icon.click()
            configure_menu = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = 'Configure']")
            actions = ActionChains(self.driver)
            actions.move_to_element(configure_menu)
            actions.perform()
            # Open the 'Configure' sub menu
            menu_option = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = '{}']".format(menu))
            menu_option.click()
            time.sleep(2) # wait for select options to populate        
        
    # Helper function to update the 'Selected' column with the given configuration    
    def update_selected_configuration(self, configuration, new_fields):
            available_select = Select(self.driver.find_element_by_id('select_0'))   
            # Remove all 'Selected' fields
            selected_select = Select(self.driver.find_element_by_id('select_1'))
            remove_selected_button = self.driver.find_element_by_xpath("//a[contains(@class, 'icon-chevron-left')]")       
            for selected in selected_select.options:
                selected.click()
                remove_selected_button.click()
            available_select.deselect_all()
            # Add 'Selected' fields specified in configuration
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
                    if new_fields[add_to_selected] == 'Reference':
                        reference_select = Select(self.driver.find_element_by_id('refTable'))
                        reference_select.select_by_visible_text(new_fields['References'][add_to_selected])
                    # Add new field to Selected
                    add_field_button = self.driver.find_element_by_id('addButton')
                    add_field_button.click()
                    selected_select = Select(self.driver.find_element_by_id('select_1'))
                    selected_select.deselect_all()
                    selected_select.select_by_visible_text(add_to_selected)

            save_button = self.driver.find_element_by_id('sysverb_save')
            save_button.click()
            
            time.sleep(5)
            # Wait for save dialogue to complete
            #menu_page = expected_conditions.presence_of_element_located((By.ID, 'sysparm_button_close'))
            #WebDriverWait(self.driver, 10).until(menu_page)
            
    def configure_form_layout(self, table_name, section_name, configuration, new_fields):
        success = True
        log = "Form Layout for {} {} configured successfully.".format(table_name, section_name)
        try:
            self.open_configure_menu(table_name, 'Form Layout')
            section_select = Select(self.driver.find_element_by_id('sysparm_section'))
            
            # Check if section already exists
            if section_name in [option.text for option in section_select.options]:
                section_select.select_by_visible_text(section_name)
            else:
                # Create new section
                section_select.select_by_visible_text('New...')
                section_prompt_present = expected_conditions.presence_of_element_located((By.ID, 'glide_prompt_answer'))
                WebDriverWait(self.driver, 5).until(section_prompt_present, "Could not find new section prompt.")                
                section_caption_input = self.driver.find_element_by_id('glide_prompt_answer')
                section_caption_input.send_keys(section_name)
                section_ok_button = self.driver.find_element_by_id('ok_button')
                section_ok_button.click()
            time.sleep(2) # wait for selected options to update
                
            # Add new Selected fields
            self.update_selected_configuration(configuration, new_fields)
            
        except Exception, e:
            success = False
            log = traceback.format_exc(e)       
        
        return success, log

    def configure_related_lists(self, table_name, configuration):
        success = True
        log = "Related Lists for {} configured successfully.".format(table_name)
        try:
            self.open_configure_menu(table_name, 'Related Lists')
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

    # Helper function to right click and open a label menu
    def open_label_menu(self, table_name, label, menu):
            self.driver.get("https://{}.service-now.com/{}.do".format(self.instance_prefix, table_name))
            label_span = self.driver.find_element_by_xpath("//span[contains(@class, 'label-text') and text() = '{}']".format(label))
            actions = ActionChains(self.driver)
            actions.context_click(label_span)
            actions.perform()
            menu_option = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = '{}']".format(menu))
            menu_option.click()
        
    def configure_label_choices(self, table_name, label, configuration):
        success = True
        log = "{} choices for {} configured successfully.".format(label, table_name)
        try:
            self.open_label_menu(table_name, label, 'Configure Choices')
            new_option_input = self.driver.find_element_by_id('newOption')
            add_item_button = self.driver.find_element_by_id('addButton')
            for add_to_selected in configuration:
                new_option_input.clear()
                new_option_input.send_keys(add_to_selected)
                add_item_button.click()
            save_button = self.driver.find_element_by_id('sysverb_save')
            save_button.click()
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log
        
    def configure_list_layout(self, table_name, configuration, new_fields):    
        success = True
        log = "List layout for {} configured successfully.".format(table_name)
        try:
            self.driver.get("https://{}.service-now.com/{}.do".format(self.instance_prefix, table_name))
            number_column = self.driver.find_element_by_xpath("//a[text() = 'Number']")
            actions = ActionChains(self.driver)
            actions.context_click(number_column)
            actions.perform()
            configure_menu = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = 'Configure']")
            actions = ActionChains(self.driver)            
            actions.move_to_element(configure_menu)
            actions.perform()
            list_layout_menu_option = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = 'List Layout']")
            list_layout_menu_option.click()
            # Add new Selected fields
            self.update_selected_configuration(configuration, new_fields)
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log

    def get_visual_task_board_url(self, table_name, state_variables):  
        success = True
        log = "Visual Task Board for {} configured successfully.".format(table_name)
        try:
            self.driver.get("https://{}.service-now.com/{}.do".format(self.instance_prefix, table_name))
            number_column = self.driver.find_element_by_xpath("//a[text() = 'State']")
            actions = ActionChains(self.driver)
            actions.context_click(number_column)
            actions.perform()
            show_menu_option = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = 'Show Visual Task Board']")        
            show_menu_option.click()
            url = self.driver.current_url.lstrip("https://{}.service-now.com".format(self.instance_prefix))
            state_variables['task_board_url'] = url
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
    app.end_session()