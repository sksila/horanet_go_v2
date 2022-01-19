# coding: utf-8

import odoo
from odoo.tests import common

if any([odoo.tools.config['test_enable'], odoo.tools.config['test_file']]):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select, WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError as ex:
        raise ex

TIMEOUT = 10


@common.post_install(True)
class TestUserChangePersonalInformations(common.HttpCase):
    user_name = 'John Doe'
    user_login = 'john'

    def setUp(self):
        super(TestUserChangePersonalInformations, self).setUp()

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
                'groups_id': [(6, 0, [
                    env.ref('base.group_portal').id,
                    env.ref('horanet_go.group_horanet_go_citizen').id])]
            })

            # On créer des données d'adresse
            state = env['res.country.state'].create({'name': 'test01',
                                                     'code': 'test001',
                                                     'country_id': env.ref('base.fr').id})
            city = env['res.city'].create({'name': 'ville-test',
                                           'state': 'confirmed',
                                           'country_state_id': state.id
                                           })
            env['res.zip'].create({'name': 'test1', 'state': 'confirmed', 'city_ids': [(6, 0, [city.id])]})

    def tearDown(self):
        super(TestUserChangePersonalInformations, self).tearDown()

        self.driver.quit()

    def test_01_user_change_personal_informations(self):
        # John wants to see its personal informations so he goes on odoo
        self.driver.get(self.server_url)

        # He clicks on Sign in link
        self.driver.find_element_by_xpath('//a[@href="/web/login"]').click()

        # He enters his credentials to log in
        self.driver.find_element_by_id('login').send_keys(self.user_login)
        self.driver.find_element_by_id('password').send_keys(self.user_login)

        # He clicks on the login button
        self.driver.find_element_by_xpath('//form[@class="oe_login_form"]//button[@type="submit"]').click()
        # time.sleep(10)

        # John is logged in, he clicks on his name in the menu
        self.driver.find_element_by_link_text('John Doe').click()

        # John clicks on My Account link
        self.driver.find_element_by_xpath('//li/a[@role="menuitem" and @href="/my/home"]').click()

        # John clicks on Change button
        self.driver.find_element_by_xpath('//h3[@class="page-header"]/a[@href="/my/account"]').click()

        # He decides to fill the missing ones
        title_input = Select(self.driver.find_element_by_name('title'))
        title_input.select_by_visible_text(title_input.options[1].text)

        self.driver.find_element_by_name('email').send_keys('john@doe.com')
        self.driver.find_element_by_name('phone').send_keys('0102030405')

        country_input = Select(self.driver.find_element_by_name('country_id'))
        country_input.select_by_visible_text('France')

        # He fills the address fields
        self.driver.find_element_by_name('zipcode').send_keys('test1')

        city_input = Select(self.driver.find_element_by_name('city_id'))
        city_input.select_by_visible_text('VILLE-TEST')

        self.driver.find_element_by_name('street_number').send_keys('56')

        self.driver.find_element_by_name('create_new_street').click()
        self.driver.find_element_by_name('new_street').send_keys('Some street')

        # After filling form, he submit it to validate its informations
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()

        WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//li/a[@role="menuitem" and @href="/my/home"]'))
        )

        # He notice that he is redirected to it's account page
        self.assertEqual(
            self.server_url + '/my/home',
            self.driver.current_url
        )
