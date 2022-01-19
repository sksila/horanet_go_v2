# coding: utf-8

import os

import odoo
from odoo.tests import common

if any([odoo.tools.config['test_enable'], odoo.tools.config['test_file']]):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError as ex:
        raise ex

TIMEOUT = 3


@common.post_install(True)
class TestListDocuments(common.HttpCase):
    user_name = 'John Doe'
    user_login = 'john'

    def setUp(self):
        super(TestListDocuments, self).setUp()

        self.driver = webdriver.PhantomJS(
            service_log_path='/tmp/ghostdriver.log',
            service_args=['--cookies-file=/tmp/cookies.txt']
        )
        self.driver.implicitly_wait(TIMEOUT)
        self.driver.set_window_size(1280, 1024)

        self.server_url = self.env['ir.config_parameter'] \
            .get_param('web.base.url')

        with self.registry.cursor() as test_cursor:
            env = self.env(test_cursor)

            self.user = env['res.users'].create({
                'name': self.user_name,
                'login': self.user_login,
                'password': self.user_login,
                'action_id': env.ref('website.action_website_homepage').id,
                'groups_id': [(6, 0, [env.ref('base.group_portal').id])]
            })

    def tearDown(self):
        super(TestListDocuments, self).tearDown()
        self.driver.quit()

    def test_document_scenario(self):
        # John wants to see its documents so he goes on odoo
        self.driver.get(self.server_url)

        # He clicks on Sign in link
        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Sign in'))
        )
        self.driver.find_element_by_link_text('Sign in').click()

        # He enters his credentials to log in
        self.driver.find_element_by_id('login').send_keys(self.user_login)
        self.driver.find_element_by_id('password').send_keys(self.user_login)

        # He clicks on the login button
        self.driver.find_element_by_xpath('//button[text()="Log in"]').click()

        # John is logged in, he clicks on his name in the menu
        self.driver.find_element_by_link_text('John Doe').click()

        # John clicks on My Account link
        self.driver.find_element_by_link_text('My Account').click()

        # John clicks on Documents link
        self.driver.find_element_by_link_text('Documents').click()

        # He notices that he hasn't any document yet
        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Add a document'))
        )
        self.assertIn("You don't have any documents.", self.driver.page_source)

        # He decides to add a document so he clicks on the corresponding button
        self.driver.find_element_by_link_text('Add a document').click()

        # He selects a file from his computer
        self.driver.find_element_by_name('uploaded_files').send_keys(
            os.path.join(
                os.path.dirname(__file__),
                '../static/description/icon.png'
            )
        )

        # Everything looks good so he decides to send the document
        self.driver.find_element_by_xpath('//button[text()="Send"]').click()

        # As the upload was a success, John's redirected to documents page
        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Add a document'))
        )
        self.assertEqual(
            self.server_url + '/my/documents',
            self.driver.current_url)

        # He notices that the previous message disappeared and now there
        # is a one line with its document marked as 'To check'
        rows = self.driver.find_elements_by_xpath('//table/tbody/tr')
        self.assertEqual(1, len(rows))
        self.assertIn('To check', rows[0].text)

        # Back office agent rejects john's document
        with self.registry.cursor() as test_cursor:
            env = self.env(test_cursor)
            env['ir.attachment'].search([('user_id', '=', self.user.id)]).write({'status': 'rejected'})

        # John wants to see if his document has been validated, so he refreshes the page
        self.driver.refresh()

        # He notices that his document has been rejected
        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Add a document'))
        )

        rows = self.driver.find_elements_by_xpath('//table/tbody/tr')
        self.assertEqual(1, len(rows))
        self.assertIn('Rejected', rows[0].text)

        # He notices that there is an Edit button on his document's line
        self.assertIn('Edit', rows[0].text)

        # He clicks on Edit button
        self.driver.find_element_by_link_text('Edit').click()

        # He selects a file from his computer (the same file...)
        self.driver.find_element_by_name('uploaded_files').send_keys(
            os.path.join(
                os.path.dirname(__file__),
                '../static/description/icon.png'
            )
        )

        # Everything looks good so he decides to send the document again
        self.driver.find_element_by_xpath('//button[text()="Send"]').click()

        # As the upload was a success, John's redirected to documents page
        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Add a document'))
        )
        self.assertEqual(
            self.server_url + '/my/documents',
            self.driver.current_url)

        # He notices that his document is marked as 'To check' again
        rows = self.driver.find_elements_by_xpath('//table/tbody/tr')
        self.assertEqual(1, len(rows))
        self.assertIn('To check', rows[0].text)

        # He notices that the Edit button has disappeared
        self.assertNotIn('Edit', rows[0].text)
