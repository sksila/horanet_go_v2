###
#
#   This file is part of odoo-addons.
#
#   odoo-addons is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   odoo-addons is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##

{
    'name': 'Fields masks',
    'version': '10.0.17.2.8',
    'summary': "Placez des masques de saisie sur vos formulaires",
    'author': 'Aristobulo Meneses',
    'website': 'https://menecio.github.io',
    'category': 'web',
    'depends': [
        # --- Odoo --- #
        'web',
        # --- External --- #

        # --- Horanet --- #
    ],
    'data': ['views/assets.xml', ],
    'application': False,
    'auto_install': False,
    # permet d'installer automatiquement le module si toutes ses dépendances sont installés
    # -default value set is False
    # -If false, the dependent modules are not installed if not installed prior to the dependent module.
    # -If True, all corresponding dependent modules are installed at the time of installing this module.
    'installable': True
}
