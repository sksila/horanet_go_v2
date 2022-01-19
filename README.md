[![pipeline status](http://gitlab.horanet.com/horanet/horanet_collectivity/badges/dev-10.0/pipeline.svg)](http://gitlab.horanet.com/horanet/horanet_collectivity/commits/dev-10.0)
[![coverage report](http://gitlab.horanet.com/horanet/horanet_collectivity/badges/dev-10.0/coverage.svg)](http://gitlab.horanet.com/horanet/horanet_collectivity/commits/dev-10.0)

## Install prerequisites (Debian/Ubuntu):

This [script](https://gitlab.horanet.com/horanet/scripts/blob/master/install-odoo.sh) will:
- install PostgreSQL (if you want) and create postgres odoo user
- install wkhtmltopdf
- install PhantomJS
- install node and less
- install pip
- create a virtualenv for odoo
- clone odoo sources where you want to

## Install Python dependencies (Debian/Ubuntu):

`(sudo) pip install -r ./requirements.txt`

## Add a module on an existing odoo installation:

`odoo -c config.ini -d db_name -i module_name`

## Update a module:

`odoo -c config.ini -d db_name -u module_name`

## To enable UI testing, install python dependencies

`(sudo) pip install -r ./requirements/python-dev.txt`

`odoo -c config.ini -d db_name --test-enable`

## Use coverage reports

Generate code coverage reports : [Tutorial](http://gitlab.horanet.com/horanet/horanet_collectivity/wikis/tutoriel-:-utiliser-coverage)

## Use flake8 reports

Launch on commit :

`flake8 --install-hook git`

`git config --bool flake8.strict true`

`git config --bool flake8.lazy true`

Generate flake8 reports : [Tutorial](http://gitlab.horanet.com/horanet/horanet_collectivity/wikis/tutoriel-:-utiliser-flake8)

