#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""
      DISCLAIMER:

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
   WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
   WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
   PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
   OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
   DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
   GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.
   """

"""
    Description
     This script uses Selenium WebDriver to churn through a list of groups
     and set them as "Collaborative Inboxes"

    Setup
     - Install Chrome
     - You might need to install setuptools:
        https://pypi.python.org/pypi/setuptools
     - Read this:
        http://code.google.com/p/selenium/wiki/ChromeDriver
     - Download ChromeDriver:
        http://chromedriver.storage.googleapis.com/index.html
     - Setup Python-Selenium:
        "easy_install selenium"
     - Create a simple line-separated list of group email addresses.
     - Run the script
        "python bulk_collab_inbox.py --admin admin@mydomain.com
           --password s3cret --list mylist.txt"
"""

__author__ = 'richieforeman@google.com (Richie Foreman)'

from argparse import ArgumentParser

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time

DEFAULT_CHROMEDRIVER_HOST = "http://127.0.0.1:9515"
LOGIN_URL = "https://accounts.google.com/ServiceLogin"

class CustomDriver(webdriver.Remote):

    _DEFAULT_WAIT = 10

    def wait_for_elem_(self, by, value):
        '''
        Wait for an element to appear, or throw an exception
        after a reasonable amount of time.
        '''
        condition = EC.presence_of_element_located((by, value))
        return WebDriverWait(self, self._DEFAULT_WAIT).until(
            method=condition,
            message="could not find element on page")

    def google_login(self, username, password):
        '''
        Blindly attempt a Google login.

        This method assumes the login worked, and returns void.
        '''
        self.get(LOGIN_URL)

        email_field = self.find_element_by_id("Email")
        password_field = self.find_element_by_id("Passwd")
        submit_button = self.find_element_by_id("signIn")

        email_field.send_keys(username)
        password_field.send_keys(password)

        submit_button.click()


def main(args):
    # read a list of groups.
    groups = open(args.list, 'r').read().split("\n")

    print "Loading Selenium Remote Chrome Driver..."
    driver = CustomDriver(
        command_executor=args.driver,
        desired_capabilities=webdriver.DesiredCapabilities.CHROME)

    print "Logging in to Google..."
    driver.google_login(username=args.admin,
                        password=args.password)

    for group in groups:
        print "Adjusting settings for group (%s).." % group
        group_name, domain = group.split("@")

        driver.get("https://groups.google.com/a/%s/forum/"
                   "#!groupsettings/%s/advanced" % (domain, group_name))

        # this is the XPath of the group type dropdown.
        # this will probably break soon.
        dropdown = driver.wait_for_elem_(
            by=By.XPATH,
            value="/html/body/div[6]/div[5]/div[3]/div/div/div/div/div[1]/div"
                  "/div/div/div/div[3]/div[2]/div[2]/div")
        dropdown.click()

        # assuming that this is the only clicked dropdown element.
        elements = driver.find_elements(By.CLASS_NAME,
                                        value="gux-combo-item")

        # currently collaborative inbox is found on the third array index.
        # this will probably break within a month
        element = [e for e in elements if e.text == "Collaborative inbox"][0]
        element.click()

        # apply the collaborative inbox setting.
        probably_the_reset_button = driver.wait_for_elem_(
            by=By.XPATH,
            value="/html/body/div[6]/div[5]/div[3]/div/div/div/div/div[1]/div"
                  "/div/div/div/div[3]/div[7]/div/div/div[2]/span")
        probably_the_reset_button.click()

        # click the dialog box confirmation.
        maybe_the_dialog_box_confirm = driver.wait_for_elem_(
            by=By.XPATH,
            value="/html/body/div[8]/div/div/div[2]/div/div[1]"
                  "/div/div/div[2]/div[1]")
        maybe_the_dialog_box_confirm.click()

        # wait for the ajax request to finish
        time.sleep(2)

        # BEWARE
        # these next few lines very cheaply verify the actions we just took...
        # load the tag page.
        driver.get("https://groups.google.com/a/%s/forum/"
                   "#!groupsettings/%s/tags" % (domain, group_name))

        # The link does not refresh the page, wait for it to async load.
        time.sleep(2)

        print "Validating results for group (%s)..." % group

        element = driver.find_element(by=By.TAG_NAME, value="body")

        if "Tag Suggestions" in str(element.text):
            print "%s - Collaborative Inbox [OK]" % group
        else:
            print "%s - *** Collaborative Inbox [FAILED] ***" % group

        time.sleep(2)

    print "Quitting remote browser..."
    driver.quit()
    print "Done!"

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--admin")
    parser.add_argument("--password")
    parser.add_argument("--list")
    parser.add_argument("--driver", default=DEFAULT_CHROMEDRIVER_HOST)

    main(parser.parse_args())
