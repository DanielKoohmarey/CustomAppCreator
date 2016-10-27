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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from pyvirtualdisplay import Display

class AppWebDriver(object):
    def __init__(self, prefix):
        self.instance_prefix = prefix
        self.display = Display(visible=0, size=(1280, 960))
        self.display.start()        
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
            self.driver.get("https://{}.service-now.com/login.do".format(self.instance_prefix))
            user_input = self.driver.find_element_by_name('user_name')
            user_input.send_keys(user)
            pass_input = self.driver.find_element_by_name('user_password')
            pass_input.send_keys(pwd)
            submit_button = self.driver.find_element_by_name('not_important')
            submit_button.click()        

    def create_custom_table(self, user, pwd, app_name, app_prefix):
        success = True
        log = "Custom table created successfully."
        try:
            # Login to instance
            self.login(user, pwd)
            # Create custom table
            self.driver.get("https://{}.service-now.com/nav_to.do?uri=%2Ftable_columns.do".format(self.instance_prefix))
            self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
            table_name_input = self.driver.find_element_by_name("sysparm_tablelabel")
            table_name_input.send_keys(app_name)
            extends_dropdown = self.driver.find_element_by_xpath("//select[@id='sysparm_extends']/option[@value='task']")
            extends_dropdown.click()
            number_prefix_input = self.wait_for_element('sysparm_number_prefix', 10)
            number_prefix_input.send_keys(app_prefix)
            new_module_checkbox = self.driver.find_element_by_name('sysparm_new_module')
            if new_module_checkbox.get_attribute('checked') == 'true':
                new_module_checkbox.click()
            create_button = self.driver.find_element_by_name('create')
            create_button.click()
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
        
if __name__ == '__main__':
    user = ''
    pwd = ''
    app_prefix = ''
    app_name = ''    
    app = AppWebDriver('')
    app.create_custom_table(user, pwd, app_name, app_prefix)
    app.add_reports(app_name, 4)