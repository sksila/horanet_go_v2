from io import BytesIO
import base64
# 1 : imports of python lib
import logging
import os
import shutil
import tempfile
import zipfile

# 2 :  imports of odoo
from odoo import models, api, fields, exceptions, _
_logger = logging.getLogger(__name__)


class ImportDataSynchronization(models.TransientModel):
    """Wizard for data importation from an other system."""

    # region Private attributes
    _name = 'horanet.tpa.wizard.import'
    _description = "Import data synchronization"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    conserve_uploaded_file = fields.Boolean(string="Conserve uploaded file", default=False,
                                            help="Uploaded archive content is save on the server in a temporary"
                                                 " directory, if set to true, the folder will be conserved after the"
                                                 " import, otherwise it will be regarding of the"
                                                 " import result. (consult the log for the path)")
    import_method = fields.Selection(string="Choose import method", selection=[('orm', "Using ORM")], default='orm')
    track_history = fields.Boolean(string="Track history during import", default=False)
    datafile = fields.Binary(string="Compressed file containing data")
    datafile_file_name = fields.Char(string="Hidden file name")
    is_up_to_date = fields.Boolean(string="Create synchronized", default=True)
    delete_all_before_import = fields.Boolean(string="Delete all previous synchronization records", default=False)

    # endregion

    @api.multi
    def run_import(self):
        """Import partners informations from zip folder.

        :return: True if complete
        """
        # test value coherence
        if not self.datafile and self.delete_all_before_import:
            return self._delete_all_previous_external_id()
        if not self.datafile:
            raise exceptions.Warning(_("The data file is mandatory"))

        _logger.info("Start Import, this operation take time")
        _logger.info("Data file conversion and extraction")
        temp_dir = tempfile.mkdtemp(prefix='odoo_horanet_tmp_')
        try:
            _logger.warning("Creating folder..." + str(temp_dir))
            test = BytesIO(base64.decodestring(self.datafile))
            pyzip = zipfile.ZipFile(test)
            pyzip.extractall(temp_dir)
            _logger.info("Data file conversion and extraction, DONE")

            required_data = dict()
            required_data['tpa_synchronization_status.csv'] = ['partner_ext_id', 'tpa_name', 'external_id']
            required_data['partner_synchro.csv'] = ['partner_ext_id']

            dictionary_file = self._check_and_get_data_file(required_data, temp_dir)

            self._start_sql_import(dictionary_file)
            _logger.info("Congratulation Import done")
        finally:
            if not self.conserve_uploaded_file:
                shutil.rmtree(temp_dir)
        return True

    @api.multi
    def _start_sql_import(self, dictionary_file):
        """Private method to copy partners from CSV file to Odoo system.

        :param dictionary_file: CSV file of datas
        :return: nothing
        """
        _logger.info("Start SQL Import")
        cr = self.env.cr

        # if self.delete_all_before_import:
        #     self._delete_all_previous_external_id()
        # else:
        #     _logger.info('Deletion of previous external id record ignored')

        _logger.info("Get partner data")
        data_synchro = self._get_data_csv(dictionary_file['tpa_synchronization_status.csv'])

        self = self.with_context({'tracking_disable': not self.track_history})

        # Expecting list_data_city : ('name', 'code', 'zip_ids', 'country_state_id')
        _logger.info("Start external id import, " + str(len(data_synchro)) + " records")

        # partner ID
        _logger.info('Get partner technical ID')
        list_partner_extid = list(set([x['partner_ext_id'] for x in data_synchro]))
        list_partner_extid_rec = self.env['ir.model.data'].search_read(
            [('model', '=', 'res.partner'), ('name', 'in', list_partner_extid)], ['res_id', 'name'])

        list_partner_id = {c['name']: c['res_id'] for c in list_partner_extid_rec if c['res_id'] != 0}

        res_partner = self.env['res.partner'].sudo()

        _logger.info("Start Importing data with ORM (%s records)" % (str(len(list_partner_id))))

        if self.import_method == 'orm':
            loop_number = 0
            list_partner_rec = res_partner.search([('id', 'in', list_partner_id.values())])
            dict_partner_by_id = {c.id: c for c in list_partner_rec}
            dict_partner_by_ext_id = {k: dict_partner_by_id[v] for (k, v) in list_partner_id.items()}
            for synchro in data_synchro:
                loop_number += 1
                if loop_number % 100 == 0:
                    _logger.info("Creating synchronization record %s of %s" % (loop_number, str(len(data_synchro))))
                partner = dict_partner_by_ext_id[synchro['partner_ext_id']]
                synch_rec = partner.get_or_create_tpa_synchro_partner(synchro['tpa_name'], synchro['external_id'])
                synch_rec.write({'last_message_export': synchro['message'] or '',
                                 'last_sync_date': fields.Datetime.now() if self.is_up_to_date else False})

        data_partners = self._get_data_csv(dictionary_file['partner_synchro.csv'])
        list_partner_extid = list(set([x['partner_ext_id'] for x in data_partners]))
        list_partner_extid_rec = self.env['ir.model.data'].search_read(
            [('model', '=', 'res.partner'), ('name', 'in', list_partner_extid)], ['res_id', 'name'])

        dict_partnerid_by_extid = {c['name']: c['res_id'] for c in list_partner_extid_rec if c['res_id'] != 0}

        _logger.info("Start updating partner synchronization flag, " + str(len(data_partners)) + " records")
        loop_number = 0
        for data_partner in data_partners:
            loop_number += 1
            if loop_number % 100 == 0:
                _logger.info("Updating partner %s of %s" % (loop_number, str(len(data_partners))))
            partner_id = dict_partnerid_by_extid[data_partner.pop('partner_ext_id')]
            cr.execute("UPDATE res_partner SET " + ", ".join(
                [str(k) + '=' + str(v) for (k, v) in data_partner.items() if v]) + " WHERE id=" + str(partner_id))

        cr.commit()

    def _delete_all_previous_synchro_record(self):
        """Private method to delete all previous synchronization records.

        :return: nothing
        """
        cr = self.env.cr
        _logger.info("Delete all previous external id")
        cr.execute(
            "delete from ir_model_data where module = '" + str(
                self.module_name) + "' and model = 'res.partner'")
        cr.commit()
        _logger.info("Delete complete")

    def _check_and_get_data_file(self, required_data, folder_path):
        """Private method to check datas from CSV file.

        :param required_data: List of required data for Odoo system
        :param folder_path: Folder path
        :return: nothing
        """
        _logger.info("Scanning file content")
        list_file = dict()
        for file_name, data_label in required_data.items():
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):

                raise exceptions.Warning(_("File " + file_name + " not found"))
            header_fields = []
            with open(file_path, "r") as fp:
                header_fields = fp.readline().rstrip().split(";")
            for label in data_label:
                if label not in header_fields:
                    raise exceptions.Warning(_(
                        "Missing " + label + " in header of file " + file_name + "\n" + "file path : " + file_path))
            list_file[file_name] = file_path
        _logger.info("File content OK")
        return list_file

    def _get_data_csv(self, file_path):
        """Private method to get CSV file.

        :param file_path: File path
        :return: List of data
        """
        with open(file_path, 'r') as f:
            data_file = [tuple(line.rstrip().split(";")) for line in f.read().splitlines()]
        header = data_file.pop(0)
        data = []
        for partner in data_file:
            tmp = {}
            for label in header:
                idx = header.index(label)
                tmp[label] = partner[idx]
            data.append(tmp)
        return data


# endregion

pass
