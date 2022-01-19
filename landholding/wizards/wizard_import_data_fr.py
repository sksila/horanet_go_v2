# -*- coding: utf-8 -*-

import StringIO
import base64
# 1 : imports of python lib
import logging
import os
import tempfile
import zipfile

# 2 :  imports of openerp
from odoo import models, api, fields, exceptions
from ..config import config

_logger = logging.getLogger(__name__)


class ResetAndImportDataFr(models.TransientModel):
    """Class of import methods."""

    # region Private attributes
    _name = 'landholding.wizard.import.fr'
    _description = 'Import data landholding fr'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    multi_transaction = fields.Boolean(string='Multi transaction', default=False,
                                       help='True : a commit will be executed every chunks\n'
                                            'False : The creation of all records will be transactionned'
                                            ' (no commit during import)')
    conserve_uploaded_file = fields.Boolean(string='Conserve uploaded file', default=False,
                                            help='Uploaded archive content is saved on the server in a temporary'
                                                 ' directory, if set to true, the folder will be conserved after the'
                                                 ' import, otherwise it will be regarding of the'
                                                 ' import result. (consult the log for the path)')
    chunk_size = fields.Integer(string='Chunk size for street data', default=100000)
    datafile = fields.Binary(string='Compressed file containing data')
    datafile_file_name = fields.Char(string='hidden file name')
    delete_all_before_import = fields.Boolean(string='Delete all data before import', default=True, required=True)

    # endregion

    @api.multi
    def run_import(self):
        """
        Read data from the files and import them.

        Main method of import process.
        - Create temporary directory
        - Unzip file in temporary directory
        - Check if subfolders contain all required files (see config file)
        - Insert data
        """
        # test value cohérence
        if not isinstance(self.chunk_size, (int, long)) or self.chunk_size < 1:
            raise exceptions.Warning('The chunk size value is incorrect')
        if not self.datafile:
            raise exceptions.Warning('The data file is mandatory')

        _logger.warning('Start Import, this operation take time')
        _logger.info('Data file conversion and extraction')
        temp_dir = tempfile.mkdtemp(prefix='odoo_horanet_tmp_')
        try:
            _logger.warning(u'Création du dossier :' + str(temp_dir))
            test = StringIO.StringIO(base64.decodestring(self.datafile))
            pyzip = zipfile.ZipFile(test)
            pyzip.extractall(temp_dir)
            _logger.info('Data file conversion and extraction, DONE')

            # Check if subfolders contain all required files (see config file)
            dictionary_file = self._check_and_get_data_files(temp_dir)

            # Validate and insert data
            self._start_sql_import(dictionary_file)
            _logger.info('Congratulation : Import done')
        finally:
            if self.conserve_uploaded_file:
                os.removedirs(temp_dir)
        return True

    # region UTILS
    @api.multi
    def _delete_all_landholding_records(self):
        """Delete all landholding records in the database."""
        cr = self.env.cr

        _logger.info("")
        _logger.info('Start deletion')
        _logger.info("==============")

        for model_name, file_type in config.FILE_MODEL_FILE_TYPE.iteritems():
            _logger.info('Delete all records from ' + model_name + " model")
            cr.execute("DELETE from " + model_name.replace('.', '_'))
        cr.commit()

        _logger.info('Delete complete')

    def _check_and_get_data_files(self, folder_path):
        """Check if subfolders contain all required files (see config file).

        :param folder_path : folder path
        :return: dictionary containing files to upload
        """
        _logger.info("")
        _logger.info('Scanning file content')
        _logger.info("=====================")
        list_subdirs = os.listdir(folder_path)

        list_files = dict()
        for subfolder in list_subdirs:
            # logger.info(subfolder)
            subfolder_path = os.path.join(folder_path, subfolder)
            list_subfolder_files = os.listdir(subfolder_path)

            # Vérifier que tous fichiers recherchés sont présents dans le sous dossier
            for file_type in config.FILE_TYPES:
                file_found = False
                for file_name in list_subfolder_files:
                    if file_type in file_name:
                        file_found = True
                        file_path = os.path.join(subfolder_path, file_name)
                        list_files[subfolder + "/" + file_type] = file_path

                if not file_found:
                    raise Exception(
                        'Missing ' + file_type + ' file in folder ' + subfolder + '\n' +
                        'folder path : ' + subfolder_path)
        _logger.info("Scan completed OK")

        _logger.info("")
        _logger.info("Files found")
        _logger.info("===========")
        for fileName, filePath in list_files.iteritems():
            _logger.info(fileName + "  :  " + filePath)

        return list_files

    @api.multi
    def _start_sql_import(self, dictionary_files):
        """
        Import by sql.

        For each file in dictionary_files:
        - Get data
        - Validate data according to its model (see config file)
        - Insert data

        :param dictionary_files: the files with all the data
        """
        if self.delete_all_before_import:
            self._delete_all_landholding_records()
        else:
            _logger.warning('Deletion of previous location record ignored')

        _logger.info("")
        _logger.info('Start SQL Import')
        _logger.info("================\n")

        for model_name in config.FILE_MODELS:
            _logger.info('Get ' + model_name + ' data')
            _logger.info('-----------------------------------------------------------------------------------------')
            file_type = config.FILE_MODEL_FILE_TYPE[model_name]
            for fileName, filePath in dictionary_files.iteritems():
                if file_type in fileName:
                    _logger.info("Traitement du fichier :  " + filePath)
                    list_data_to_insert = self._get_data(model_name, filePath)
                    self._insert_data(model_name, list_data_to_insert)

            _logger.info('End of ' + model_name + ' data import\n')

        _logger.warning('SQL Import DONE\n')

    # endregion
    # region ZIP
    def _get_data(self, model_name, file_path):
        """
        Get the data from a file and validate them.

        - Get data according to data positions of model_name (see config file)
        - Validate data according to model (see validate_data function in each model)

        :param model_name: odoo model name
        :param file_path: file path
        :return: list of dictionnaries containing values to insert
        """
        file_type = config.FILE_MODEL_FILE_TYPE[model_name]
        data_positions = config.REQUIRED_DATA[model_name]

        if not file_type:
            raise Exception('The file type for ' + model_name + 'model is not configured')

        with open(file_path, "r") as f:
            data_file = [line.rstrip() for line in f.read().splitlines()]

        data_file.pop(0)  # Delete direction 's head record
        data_file.pop(0)  # Delete communal record

        # Pour chaque ligne
        # logger.info(data_positions)
        last_data_line = ()
        list_data_to_insert = list()
        for line in data_file:
            data_line = list()
            pos_article = config.FILE_ARTICLE_POSITION[file_type]
            if pos_article:
                num_article = line[config.FILE_ARTICLE_POSITION[file_type][0] - 1:
                                   config.FILE_ARTICLE_POSITION[file_type][0] - 1 +
                                   config.FILE_ARTICLE_POSITION[file_type][1]]
            else:
                num_article = '00'

            # On parcourt la liste de tuples des positions
            for data_position in data_positions:
                # Si le numéro d'article correspond
                if num_article in data_position[1]:
                    # On ajoute le nom et la valeur de la donnée
                    data_line.append(data_position[0])
                    data_line.append(line[data_position[2] - 1:data_position[2] - 1 + data_position[3]].rstrip())

            if data_line:
                if last_data_line and last_data_line[1] == data_line[1]:
                    # Dans le cas où un modèle est décrit dans plusieurs articles sur plusieurs lignes,
                    # on concatène la ligne courante avec la précédente en lui enlevant son identifiant unique
                    last_data_line.pop(0)  # nom data unique_id
                    last_data_line.pop(0)  # valeur data unique_id
                    data_line = data_line + last_data_line
                else:
                    if last_data_line:
                        # Ajout de l'enregistrement précédent
                        new_record_dict = dict(zip(last_data_line[0::2], last_data_line[1::2]))
                        list_data_to_insert.append(new_record_dict)

                last_data_line = data_line

        # Ajout du dernier enregistrement
        if last_data_line:
            new_record_dict = dict(zip(last_data_line[0::2], last_data_line[1::2]))
            list_data_to_insert.append(new_record_dict)

        _logger.info("Le fichier contient " + str(len(list_data_to_insert)) + " lignes.")

        model = self.env[model_name].sudo()

        # On appelle la fonction validate_data du modèle si elle existe
        try:
            list_data_to_insert = model.validate_data(list_data_to_insert)
        except AttributeError:
            pass

        return list_data_to_insert

    @api.multi
    def _insert_data(self, model_name, list_data_to_insert):
        """Insert in the model table data contained in a list of dictionnaries.

        Constructs a single request to insert all data contained in list_data_to_insert

        :param model_name: oddo model name
        :param list_data_to_insert: list of dictionnaries containing values to insert
        :return: none
        """
        #  Contrôle de présence de données à insérer
        if not list_data_to_insert:
            _logger.warning('There is no data to insert in ' + model_name)
            return

        # Récupération du nom de la table correspondant au modèle
        model_table = model_name.replace('.', '_')

        cr = self.env.cr

        static_values = "CURRENT_TIMESTAMP, " + str(self.env.uid) + " ," + str(
            self.env.uid) + " ,CURRENT_TIMESTAMP"

        # Récupération des noms de champs
        # !!! On considère que tous les dictionnaires ont les mêmes données dans le même ordre !!!
        dynamic_names = ', '.join(list_data_to_insert[0].keys())

        # Récupération des valeurs
        tuples_values_to_insert = [tuple(x.values()) for x in list_data_to_insert]

        # Création de la requête
        insert_values = ','.join(cr.mogrify("(" + static_values + ", %s" * len(x) + ")", x)
                                 for x in tuples_values_to_insert)

        # Exécution
        cr.execute(
            'INSERT INTO  ' + model_table + '(create_date, create_uid, write_uid, write_date, ' +
            dynamic_names + ') VALUES' + insert_values + ' RETURNING id')
        cr.commit()

    # endregion

    pass
