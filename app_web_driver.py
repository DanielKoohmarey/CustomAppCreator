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
import urllib2

from selenium import webdriver
#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display

class AppWebDriver(object):
    def __init__(self, prefix, auth):
        self.instance_prefix = prefix
        self.auth_pair = auth
        self.display = Display(visible=0, size=(1280, 960))
        self.display.start()
        #binary = FirefoxBinary('/home/ubuntu/firefox/firefox')
        #firefox = DesiredCapabilities.FIREFOX
        #firefox['marionette'] = False
        #self.driver = webdriver.Firefox(firefox_binary=binary, capabilities = firefox)
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()
        self.logged_in = False
        self.missing_fields = []
        self.login()

    def login(self):
        try:        
            login_url = "https://{}.service-now.com/login.do".format(self.instance_prefix)
            self.driver.get(login_url)
            user_input = self.driver.find_element_by_name('user_name')
            user_input.send_keys(self.auth_pair[0])
            pass_input = self.driver.find_element_by_name('user_password')
            pass_input.send_keys(self.auth_pair[1])
            submit_button = self.driver.find_element_by_name('not_important')
            submit_button.click()
            time.sleep(5)
            if self.driver.current_url != login_url:
                self.logged_in = True
        except Exception, e:
            print "Failed to login to {}\n{}".format(self.instance_prefix, e)

    def end_session(self):
        self.driver.get("https://{}.service-now.com/logout.do".format(self.instance_prefix))
        self.driver.delete_all_cookies()
        try:
            self.driver.quit()
        except:
            print "Failed to quit webdriver."
        self.display.stop()
        
    def create_table(self, table_name, app_prefix, app_name = '', new_module = False):
        success = True
        log = "{} table created successfully.".format(table_name)
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
            time.sleep(2) # wait for the table to be created for subsequent REST calls
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log

    def add_reports(self, overview_name, report_options, expected, skip = 0, retry = True):
        success = True
        log = "Added {} reports successfully.".format(expected)
        try:          
            self.driver.get("https://{}.service-now.com/home.do?sysparm_view={}_overview".format(self.instance_prefix, overview_name))
            # Open add content popup
            add_content_button = self.driver.find_element_by_xpath("//button[text()='Add content']")
            add_content_button.click()
            reports_option_present = expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "option[value='Reports']"))
            WebDriverWait(self.driver, 10).until(reports_option_present, "Could not find Reports option.")
            renderers_select = Select(self.driver.find_elements_by_class_name('home_select_content')[0])
            renderers_select.select_by_visible_text('Reports')
            # Wait for Reports options to populate
            if retry:
                try:
                    report_option_present = expected_conditions.presence_of_element_located((By.XPATH,
                                        "//*[contains(@class,'home_select_content')][2]/option[@value='{}']".format(report_options[0])))
                    WebDriverWait(self.driver, 10).until(report_option_present, 
                                        "Could not find '{}' in Reports options.".format(report_options[0]))
                except TimeoutException:
                    # Retry if we can't find the element
                    print "Could not find '{}' in Reports options, retrying.".format(report_options[0])
                    return self.add_reports(overview_name, report_options, expected, skip, False)
            else:
                report_option_present = expected_conditions.presence_of_element_located((By.XPATH,
                                    "//*[contains(@class,'home_select_content')][2]/option[@value='{}']".format(report_options[0])))
                WebDriverWait(self.driver, 10).until(report_option_present, 
                                    "Could not find '{}' in Reports options.".format(report_options[0]))
            # Add reports from all report options specified
            report_select = Select(self.driver.find_elements_by_class_name('home_select_content')[1])
            dropzone = 'dropzone1'           
            for report_option in report_options:         
                report_select.select_by_visible_text(report_option)
                time.sleep(5) # wait for report options to load
                # Add available content to grid
                content_select = Select(self.driver.find_elements_by_class_name('home_select_content')[2])
                for content in content_select.options[skip:]:
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
            time.sleep(2) # wait for menu to fully appear for move_to_element
            configure_menu = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = 'Configure']")
            actions = ActionChains(self.driver)
            actions.move_to_element(configure_menu)
            actions.perform()
            # Open the 'Configure' sub menu
            menu_option = self.driver.find_element_by_xpath("//div[contains(@class, 'context_item') and text() = '{}']".format(menu))
            menu_option.click()
            time.sleep(2) # wait for 'Selected' options to populate        
        
    # Helper function to update the 'Selected' column with the given configuration    
    def update_selected_configuration(self, configuration, new_fields):
            available_select_exists = expected_conditions.presence_of_element_located((By.ID, 'select_0'))
            WebDriverWait(self.driver, 20).until(available_select_exists)
            time.sleep(2) # wait for 'Selected' options to populate 
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
                    available_select.deselect_all()                  
                elif add_to_selected in available_options:
                    available_select.select_by_visible_text(add_to_selected)
                    add_available_button.click()
                    available_select.deselect_all()
                else:
                    # Create new field
                    if add_to_selected not in new_fields:
                        print "WARNING! Missing form layout field: {}".format(add_to_selected)
                        self.missing_fields.append(add_to_selected)
                        continue                 
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
            
            # Wait for save dialogue to complete
            try:
                close_save_button_exists = expected_conditions.presence_of_element_located((By.ID, 'sysparm_button_close'))
                WebDriverWait(self.driver, 10).until(close_save_button_exists)
            except TimeoutException:
                pass
            
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
                new_section_present = expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "option[value='.new']"))
                WebDriverWait(self.driver, 5).until(new_section_present, "Could not find 'New..' section option.")  
                section_select.select_by_visible_text('New...')
                section_prompt_present = expected_conditions.presence_of_element_located((By.ID, 'glide_prompt_answer'))
                WebDriverWait(self.driver, 5).until(section_prompt_present, "Could not find new section prompt.")                
                section_caption_input = self.driver.find_element_by_id('glide_prompt_answer')
                section_caption_input.send_keys(section_name)
                section_ok_button = self.driver.find_element_by_id('ok_button')
                section_ok_button.click()
                
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
            # Remove all 'Selected' fields
            selected_select = Select(self.driver.find_element_by_id('select_1'))
            remove_selected_button = self.driver.find_element_by_xpath("//a[contains(@class, 'icon-chevron-left')]")       
            for selected in selected_select.options:
                selected.click()
                remove_selected_button.click()
            # Add configuration fields to 'Selected'
            available_select = Select(self.driver.find_element_by_id('select_0'))       
            available_select.deselect_all()
            add_available_button = self.driver.find_element_by_class_name('icon-chevron-right')
            for add_to_selected in configuration:
                available_select.select_by_visible_text(add_to_selected)
                add_available_button.click()
                available_select.deselect_all()
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
            self.driver.get("https://{0}.service-now.com/nav_to.do?uri=%2Fslushbucket.do%3Fsysparm_view%3D%26sysparm_referring_url%3D"\
                            "{1}_list.do%26sysparm_form%3Dlist%26sysparm_user_list%3Dfalse%26sysparm_list%3D"\
                            "{1}%26sysparm_collection%3D".format(self.instance_prefix, table_name))
            self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
            # Add new Selected fields
            self.update_selected_configuration(configuration, new_fields)
        except Exception, e:
            success = False
            log = traceback.format_exc(e)
        
        return success, log

    def get_visual_task_board_url(self, table_name, state_variables):  
        success = True
        log = "Retrieved visual task board url for {} successfully.".format(table_name)
        try:
            self.driver.get("https://{0}.service-now.com/nav_to.do?uri=%2F$vtb_get.do%3F"\
                            "sysparm_action%3Dboard_show%26sysparm_field%3Dstate%26sysparm_table%3D"\
                            "{1}%26sysparm_query%3Dactive%253Dtrue".format(self.instance_prefix, table_name))
            self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
            vtb_present = expected_conditions.presence_of_element_located((By.CLASS_NAME, "vtb-navbar"))
            WebDriverWait(self.driver, 20).until(vtb_present, "Could not load visual taskbar.")
            task_board_url = self.driver.current_url.replace("https://{}.service-now.com/nav_to.do?uri=%2F".format(self.instance_prefix), '')
            task_board_url = urllib2.unquote(urllib2.unquote(task_board_url)) # url is double encoded
            state_variables['task_board_url'] = task_board_url
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
    app = AppWebDriver(instance_prefix, (user, pwd))
    print "Web driver started successfully"
    if app.logged_in:
        print "Logged in successfully"
    app.end_session()
    print "Ended session successfully"
