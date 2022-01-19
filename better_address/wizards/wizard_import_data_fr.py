from io import StringIO
import base64
# 1 : imports of python lib
import logging
import os
import tempfile
import zipfile

# 2 :  imports from odoo
from odoo import models, api, fields
from ..config import config

logger = logging.getLogger(__name__)


class ImportAdresseDataFr(models.TransientModel):
    """Class of import french address methods."""

    # region Private attributes
    _name = 'horanet.location.wizard.import.fr'
    _description = 'Import data location fr'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    state_import = fields.Selection(
        string="Creation state",
        selection=config.STATES_LIST,
        default='confirmed',
        help='Validation state in witch the new records will be created')
    multi_transaction = fields.Boolean(
        string='Multi transaction',
        default=False,
        help='True : a commit will be executed every chunks\n'
             'False : The creation of all records will be transactionned'
             ' (no commit during import)')
    create_externalid = fields.Boolean(
        string="Create external id",
        default=False,
        help='If disabled, it will not be possible to insert Partner via import,'
             ' but the database size and the import time will be reduced by 50% ! '
             ' (And the performance of the system will be improved due '
             'to the database size reduction)')
    conserve_uploaded_file = fields.Boolean(
        string="Conserve uploaded file",
        default=False,
        help='Uploaded archive content is save on the server in a temporary'
             ' directory, if set to true, the folder will be conserved after the'
             ' import, otherwise it will be regarding of the'
             ' import result. (consult the log for the path)')
    module_name = fields.Char(string="Module name for external id", default='better_address')
    chunk_size = fields.Integer(string="Chunk size for street data", default=100000)
    datafile = fields.Binary(string="Compressed file containing data", attachment=True)
    datafile_file_name = fields.Char(string='hidden file name')
    delete_all_before_import = fields.Boolean(string='Delete all data before import', default=False, required=True)
    selected_states = fields.Many2many(
        string="Selected states",
        comodel_name='res.country.state',
        domain=[('country_id.code', '=', 'FR')],
    )

    # endregion

    # region Actions
    @api.multi
    def run_import(self):
        """Main method of import process. Read data from the .csv file and import them."""
        # test value cohérence
        self.env.cr.execute('SHOW server_version_num')
        psql_version = int(self.env.cr.fetchall()[0][0])
        if psql_version < 90500:
            raise Warning("This wizard must be used on a PSQL cluster version >= 9.5")
        if not isinstance(self.chunk_size, int) or self.chunk_size < 1:
            raise Warning("The chunk size value is incorrect")
        if not self.state_import:
            raise Warning("The creation state is incorrect")
        if not self.datafile:
            raise Warning("The data file is mandatory")
        logger.warning("Start Import, this operation take time")
        logger.info("Data file conversion and extraction")
        temp_dir = tempfile.mkdtemp(prefix='odoo_horanet_tmp_')
        try:
            logger.warning('création du dossier :' + str(temp_dir))
            test = StringIO(base64.decodebytes(self.datafile))
            pyzip = zipfile.ZipFile(test)
            pyzip.extractall(temp_dir)
            logger.info('Data file conversion and extraction, DONE')

            required_data = dict()
            required_data['city.csv'] = ['name', 'code', 'zip_ids', 'country_state_id', 'country_id']
            # required_data['zip.csv'] = ['name']
            required_data['street.csv'] = ['name', 'code', 'city_code']
            required_data['street_number.csv'] = ['name']
            dictionary_file = self._check_and_get_data_file(required_data, temp_dir)

            self._start_sql_import(dictionary_file)
            logger.info("Congratulation Import done")
        finally:
            if self.conserve_uploaded_file:
                os.removedirs(temp_dir)
        return True

    # endregion

    # region Model methods
    @api.multi
    def _start_sql_import(self, dictionary_file):
        """Method to import by sql.

        :param dictionary_file: the file with all the data
        """
        logger.info("Start SQL Import")
        cr = self.env.cr

        if self.delete_all_before_import:
            self._delete_all_location_record()
        else:
            logger.warning("Deletion of previous location record ignored")

        logger.info("Get City data")
        dict_data_city = self._get_data_city(file_path=dictionary_file['city.csv'], states_filter=self.selected_states)
        if not dict_data_city:
            logger.warning("Not city data to import")
            return
        list_city_id = self._upsert_city(list_data_city=dict_data_city)
        # data_city[1] -> city code
        if self.create_externalid:
            list_tuple_name_id = list(zip(
                ['city_' + data_city['code'] for data_city in dict_data_city],
                [city_id[0] for city_id in list_city_id]
            ))
            self._create_external_id(list_tuple_name_id, 'res.city')
        # data_city[2] -> zip codes
        dico_city_id_by_code = dict(list(zip([x['code'] for x in dict_data_city], [x[0] for x in list_city_id])))

        logger.info("Extract ZIP data")
        list_zip = set(sum([city['zip_ids'].split(',') for city in dict_data_city], []))
        # self._get_data_zip(dictionary_file['zip.csv'])
        list_zip_id = self._upsert_zip(list_zip)
        if self.create_externalid:
            list_tuple_name_id = list(zip(
                ['zip_' + zip_data for zip_data in list_zip],
                [zip_id[0] for zip_id in list_zip_id]
            ))
            self._create_external_id(list_tuple_name_id, 'res.zip')
        dico_zip_id_by_name = dict(list(zip([x for x in list_zip], [x[0] for x in list_zip_id])))
        logger.info("Generating CITY<->ZIP data")
        # Attention, certaines villes n'ont pas de ZIP code !?
        list_rel = sum(
            [
                [
                    (dico_zip_id_by_name[y], dico_city_id_by_code[x['code']])
                    for y in x['zip_ids'].split(',') if y != ''
                ]
                for x in dict_data_city
            ], [])
        self._upsert_zip_city_rel(list_rel)

        if self.multi_transaction:
            logger.info("commit")
            cr.commit()

        logger.info("Get Street data")
        # Expecting list_data_zip :('name','code','city_code')
        street_imported = 0
        for data_street in self._get_data_street_in_chunks(dictionary_file['street.csv'], lines=self.chunk_size):
            # filtre les rues par rapport au villes précédemment importé
            # 0->name 1->code 2->city_code
            data_street = [
                (tuple_street[:2] + (dico_city_id_by_code[tuple_street[2]],))
                for tuple_street in data_street if tuple_street[2] in dico_city_id_by_code
            ]
            if not data_street:
                continue

            list_street_id = self._upsert_street(data_street)
            if self.create_externalid:
                list_tuple_name_by_id = list(zip(
                    ['street_' + str(street[2]) + str(street[1]) for street in data_street],
                    [street_id[0] for street_id in list_street_id]
                ))
                self._create_external_id(list_tuple_name_by_id, 'res.street')
            if self.multi_transaction:
                logger.info("commit")
                cr.commit()
            street_imported += len(data_street)
            logger.info("{nb_street_inserted} street inserted ".format(nb_street_inserted=str(street_imported)))

        logger.info("Get Street_Number data")
        data_street_number = self._get_data_street_number(dictionary_file['street_number.csv'])
        list_street_number_id = self._upsert_street_number(data_street_number)
        if self.create_externalid:
            list_tuple_name_id = list(zip(
                ['number_' + street_number[0].replace(" ", "_") for street_number in data_street_number],
                [street_number_id[0] for street_number_id in list_street_number_id]
            ))
            self._create_external_id(list_tuple_name_id, 'street.number')

        cr.commit()
        logger.info("SQL Import DONE")

    # region CITY
    def _get_data_city(self, file_path, states_filter):
        """Return a dictionary with all the header informations of a city contained in a file.

        :param file_path: file path
        :param states_filter: res.country.state recordset, used to filter city to import by states
        :return: a list of dictionary of the file
        """
        with open(file_path, "r") as f:
            data_file = [tuple(line.rstrip().split(";")) for line in f.read().splitlines()]
        header = data_file.pop(0)
        idx_name = header.index('name')
        idx_code = header.index('code')
        idx_zip_ids = header.index('zip_ids')
        ref_country = header.index('country_id')
        idx_country_state_id = header.index('country_state_id')
        # Expecting list_data_city : ('name', 'code', 'zip_ids', 'country_state_id','country_id')

        # Get state id and filter state if parameter selected_state is set
        domain_search_state = [('model', '=', 'res.country.state')]
        if states_filter:
            domain_search_state.append(('res_id', 'in', states_filter.ids))
        id_states = self.env['ir.model.data'].search_read(domain_search_state, ['res_id', 'name', 'complete_name'])
        dictionary_state_id = dict((k['name'], k['res_id']) for k in id_states)

        # Resolve country id
        id_countries = self.env['ir.model.data'].search_read([('model', '=', 'res.country')],
                                                             ['res_id', 'complete_name'])
        dictionary_country_id = dict((k['complete_name'], k['res_id']) for k in id_countries)

        data_city = [{'name': x[idx_name],
                      'code': x[idx_code],
                      'zip_ids': x[idx_zip_ids],
                      'country_state_id': dictionary_state_id[x[idx_country_state_id]],
                      'country_id': dictionary_country_id.get(x[ref_country], False),
                      } for x in data_file if x[idx_country_state_id] in dictionary_state_id]
        return data_city

    @api.multi
    def _upsert_city(self, list_data_city):
        """Method to insert/update cities in the database.

        :type list_data_city: list(dict)
        :param: list_data_city: contains all the external ids name

        :return: id of inserted or updated cities
        :rtype: list(tuple(int,))
        """
        cr = self.env.cr
        # Expecting list_data_city : ('name', 'code', 'zip_ids', 'country_state_id')
        logger.info("Start City import, {nb_cities} records".format(nb_cities=str(len(list_data_city))))
        # id_france = self.pool['res.country'].search(cr, 1, [('code', '=', 'FR')], limit=1)[0]
        log_access_columns, log_access_values = self._get_sql_log_access_column_and_value()

        # Création de la requête
        insert_value = ','.join(
            cr.mogrify(
                query="({log_access_values}, '{state_import}', %s, %s, %s, %s)".format(
                    log_access_values=log_access_values,
                    state_import=str(self.state_import)),
                vars=(str(city['country_state_id']), city['name'], city['code'], str(city['country_id'])))
            for city in list_data_city)

        # Exécution
        cr.execute("""
            INSERT INTO res_city ({log_access_columns}, state, country_state_id, name, code, country_id)
            VALUES {insert_value}
            ON CONFLICT ON CONSTRAINT res_city_unicity_on_code
            DO UPDATE
                SET name = EXCLUDED.name, write_date = CURRENT_TIMESTAMP
            RETURNING id""".format(log_access_columns=log_access_columns, insert_value=insert_value))
        logger.info("City import Done")
        result = cr.fetchall()
        return result

    # endregion

    # region ZIP
    @api.multi
    def _upsert_zip(self, list_data_zip):
        """Insert/update zip records from a data list.

        :param list_data_zip: contains all the external ids name
        :return: id of inserted or updated zip
        :rtype: list(tuple(int,))
        """
        cr = self.env.cr
        # Expecting list_data_zip :('name')
        logger.info("Start ZIP import, {nb_street} records".format(nb_street=str(len(list_data_zip))))

        log_access_columns, log_access_values = self._get_sql_log_access_column_and_value()

        insert_values = ','.join(
            cr.mogrify(
                query="({log_access_values}, %s, %s)".format(log_access_values=log_access_values),
                vars=(str(self.state_import), data_zip))
            for data_zip in list_data_zip)

        cr.execute("""
            INSERT INTO res_zip ({log_access_columns}, state, name)
            VALUES {insert_values}
            ON CONFLICT ON CONSTRAINT res_zip_unicity_code
            DO UPDATE
                SET name = EXCLUDED.name, write_date = CURRENT_TIMESTAMP
            RETURNING id""".format(
            log_access_columns=log_access_columns,
            insert_values=insert_values))
        logger.info("ZIP import Done")
        result = cr.fetchall()
        return result

    # endregion

    # region CIT_ZIP_REL
    @api.multi
    def _upsert_zip_city_rel(self, list_data_zip_city):
        """Method to create/update relations between zip and cities.

        :type list_data_zip_city: list(int, int)
        :param list_data_zip_city: contains all the external ids name -> list(id_zip (int), id_city (int))
        :return: nothing
        """
        cr = self.env.cr
        logger.info("Start ZIP_CITY_rel import, {nb_import} records".format(nb_import=str(len(list_data_zip_city))))

        insert_value = ','.join([
            "({zip_id}, {city_id})".format(
                zip_id=str(x[0]),
                city_id=str(x[1]))
            for x in list_data_zip_city])

        cr.execute("""
            INSERT INTO res_city_res_zip_rel(res_zip_id, res_city_id)
            VALUES {insert_value}
            ON CONFLICT ON CONSTRAINT res_city_res_zip_rel_res_zip_id_res_city_id_key
            DO NOTHING""".format(
            insert_value=insert_value))
        logger.info("ZIP_CITY_rel import Done")
        return

    # endregion

    # region STREET
    @staticmethod
    def _get_data_street_in_chunks(file_path, lines=1024):
        """Get header informations in a file containing streets.

        :param: file_path: file path
        """
        with open(file_path, "r") as f:
            header = tuple(f.readline().rstrip().split(";"))
            idx_name = header.index('name')
            idx_code = header.index('code')
            idx_city_code = header.index('city_code')
            while True:
                data_file = [tuple(f.readline().rstrip().split(";")) for i in range(lines)]
                if not data_file or len(data_file[0]) < 2:
                    break
                data_file = [(x[idx_name], x[idx_code], x[idx_city_code]) for x in data_file if len(x) > 2]
                yield data_file

    @api.multi
    def _upsert_street(self, list_data_street):
        """Upsert street in the database.

        :type list_data_street: list
        :param list_data_street: data tuple -> (<street_name>(str), <street_code>(str), <city_id>(int))
        :return: id of inserted or updated street
        :rtype: list(tuple(int,))
        """
        cr = self.env.cr

        if list_data_street:
            logger.info("Start Street import, {nb_street} records".format(nb_street=str(len(list_data_street))))
            log_access_columns, log_access_values = self._get_sql_log_access_column_and_value()

            static_query = "({log_access_values}, %s, %s, %s, '{state_import}')".format(
                log_access_values=log_access_values,
                state_import=str(self.state_import))
            insert_value = ','.join(
                cr.mogrify(
                    query=static_query,
                    vars=(data_street[0], data_street[1], str(data_street[2])))
                for data_street in list_data_street)

            cr.execute("""
                INSERT INTO res_street({log_access_columns}, name, code, city_id, state)
                VALUES {insert_value}
                ON CONFLICT ON CONSTRAINT res_street_unicity_on_code
                DO UPDATE
                    SET name = EXCLUDED.name, city_id = EXCLUDED.city_id, write_date = CURRENT_TIMESTAMP
                RETURNING id""".format(
                log_access_columns=log_access_columns,
                insert_value=insert_value))

            logger.info("Street import Done")
            result = cr.fetchall()
            return result

    # endregion

    # region STREET NUMBER
    @staticmethod
    def _get_data_street_number(file_path):
        """Get header informations in a file of a street number.

        :param: file_path: file path
        :return: return the header named 'name' of the file
        """
        with open(file_path, "r") as f:
            data_file = [tuple(line.rstrip().split(";")) for line in f.read().splitlines()]
        header = data_file.pop(0)
        idx_name = header.index('name')
        return [(x[idx_name],) for x in data_file]

    @api.multi
    def _upsert_street_number(self, list_data_street_number):
        """Insert street numbers in the database.

        :type list_data_street_number: list(str)
        :param list_data_street_number: list of street number name -> list(<street_number_name>(str))
        :return: id of inserted or updated street_number
        :rtype: list(tuple(int,))
        """
        cr = self.env.cr
        logger.info("Start Street_Number import, {nb_records} records".format(
            nb_records=str(len(list_data_street_number))))
        if list_data_street_number:
            log_access_columns, log_access_values = self._get_sql_log_access_column_and_value()

            # Création de la requête
            insert_value = ','.join(
                cr.mogrify(
                    query="({log_access_values}, %s)".format(log_access_values=log_access_values),
                    vars=(data_street_number[0],))
                for data_street_number in list_data_street_number)

            # Exécution
            cr.execute("""
                INSERT INTO res_street_number({log_access_columns}, name)
                VALUES {insert_value}
                ON CONFLICT ON CONSTRAINT res_street_number_unicity_on_number
                DO UPDATE
                    SET write_date = CURRENT_TIMESTAMP
                RETURNING id""".format(
                log_access_columns=log_access_columns,
                insert_value=insert_value))

            logger.info("Street_Number import Done")
            return cr.fetchall()
        else:
            return None

    # endregion

    # region UTILS
    @api.multi
    def _delete_all_location_record(self):
        """Delete all location records in the database."""
        cr = self.env.cr
        logger.info("Delete all location records")
        cr.execute("DELETE FROM ir_model_data WHERE module = {module_name} AND model IN"
                   " ('res.zip','res.street','res.city','res.street.number')".format(module_name=str(self.module_name)))
        cr.commit()
        cr.execute("DELETE from res_zip")
        cr.execute("DELETE from res_city")
        cr.execute("DELETE from res_street")
        cr.execute("DELETE from res_street_number")
        cr.commit()
        logger.info("Deletion complete")

    @staticmethod
    def _check_and_get_data_file(required_data, folder_path):
        """Read the file and check if all header are here.

        :param required_data : required data
        :param folder_path : folder path
        :return: dictionary containing headers
        """
        logger.info('Scanning file content')
        list_file = dict()
        for file_name, data_label in required_data.iteritems():
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                raise Exception('Fichier ' + file_name + ' not found')

            with open(file_path, "r") as fp:
                header_fields = fp.readline().rstrip().split(";")
            for label in data_label:
                if label not in header_fields:
                    raise Exception(
                        'Missing ' + label + ' in header of file ' + file_name + '\n' + 'file path : ' + file_path)
            list_file[file_name] = file_path
        logger.info('File content OK')
        return list_file

    @api.multi
    def _create_external_id(self, list_tuple_name_id, model):
        """Generate external ids based on timestamp and model.

        :param list_tuple_name_id: contains all the external ids name
        :param model: name of the model to import in
        :return:
        """
        cr = self.env.cr
        logger.info("Create External ID, {nb_external_id} records".format(nb_external_id=str(len(list_tuple_name_id))))

        log_access_columns, log_access_values = self._get_sql_log_access_column_and_value()

        insert_value = ','.join(
            cr.mogrify(
                query="({log_access_values}, {date_init}, {date_update}, {noupdate}, %s, %s, %s, %s)".format(
                    log_access_values=log_access_values,
                    date_init='CURRENT_TIMESTAMP',
                    date_update='CURRENT_TIMESTAMP',
                    noupdate='TRUE'),
                vars=(str(self.module_name), model, tuple_name_id[0], str(tuple_name_id[1])))
            for tuple_name_id in list_tuple_name_id)

        cr.execute("""
                INSERT INTO ir_model_data
                    ({log_access_columns}, date_init, date_update, noupdate, module, model, name, res_id)
                VALUES {insert_values}
                ON CONFLICT (module, name)
                DO UPDATE
                    SET res_id = EXCLUDED.res_id, write_date = CURRENT_TIMESTAMP""".format(
            log_access_columns=log_access_columns,
            insert_values=insert_value)
        )

        logger.info("Create External ID, Done")

    @api.model
    def _get_sql_log_access_column_and_value(self):
        """Construct the default log access column field/value to insert in SQL requests.

        :return: column names, default values
        :rtype: tuple(str, str)
        """
        return (
            'create_uid, create_date, write_uid, write_date',
            str(self.env.uid) + ', CURRENT_TIMESTAMP, ' + str(self.env.uid) + ', CURRENT_TIMESTAMP'
        )
    # endregion
    # endregion
