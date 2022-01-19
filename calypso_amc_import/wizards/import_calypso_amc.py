# coding: utf-8

import base64

from odoo import api, fields, models, registry


class ImportCalypsoAMCWizard(models.TransientModel):
    _name = 'partner.contact.identification.wizard.import.calypso.amc'

    imported_file = fields.Binary()

    @api.multi
    def action_import_mediums_and_tags(self):
        self.ensure_one()

        lines = base64.b64decode(self.imported_file).split('\n')

        # We don't care about the head line
        if 'Calypso-DEC' in lines[0]:
            del lines[0]

        card_type = self.env.ref('partner_contact_identification.demo_medium_type_card')

        mapping_calypso_csn = self.env.ref('calypso_amc_import.mapping_calypso_csn')
        mapping_calypso_fiscality = self.env.ref('calypso_amc_import.mapping_calypso_fiscality')
        mapping_calypso_work_and_social = self.env.ref('calypso_amc_import.mapping_calypso_work_and_social')
        mapping_calypso_health = self.env.ref('calypso_amc_import.mapping_calypso_health')
        mapping_calypso_transport = self.env.ref('calypso_amc_import.mapping_calypso_transport')
        mapping_calypso_civil_state = self.env.ref('calypso_amc_import.mapping_calypso_civil_state')
        mapping_calypso_relation_with_elected_officials = self.env.ref('calypso_amc_import.mapping_calypso_relation_with_elected_officials') # noqa
        mapping_calypso_sport_recreation_childhood = self.env.ref('calypso_amc_import.mapping_calypso_sport_recreation_childhood') # noqa
        mapping_calypso_economy = self.env.ref('calypso_amc_import.mapping_calypso_economy')
        mapping_calypso_police = self.env.ref('calypso_amc_import.mapping_calypso_police')
        mapping_calypso_citizens_relations = self.env.ref('calypso_amc_import.mapping_calypso_citizens_relations') # noqa
        mapping_calypso_agents_services = self.env.ref('calypso_amc_import.mapping_calypso_agents_services')
        mapping_calypso_studients_facilities = self.env.ref('calypso_amc_import.mapping_calypso_studients_facilities') # noqa
        mapping_calypso_business_fidelity = self.env.ref('calypso_amc_import.mapping_calypso_business_fidelity') # noqa

        tags = []
        for line in lines:
            columns = line.split(',')

            if not columns[0]:
                continue

            tags.append({
                'csn': hex(int(columns[0])).split('0x')[1].upper(),
                'fiscality': columns[2],
                'work_social': columns[3],
                'health': columns[4],
                'transport': columns[5],
                'civil_state': columns[6],
                'relation_elected': columns[7],
                'sport': columns[8],
                'economy': columns[9],
                'police': columns[10],
                'citizens_relations': columns[11],
                'agents_services': columns[12],
                'studients_facilities': columns[13],
                'business_fidelity': columns[14]
            })

        with registry(self.env.cr.dbname).cursor() as cursor:
            cursor.execute(
                'PREPARE insert_medium AS \
                 INSERT INTO partner_contact_identification_medium (type_id, active) VALUES ($1, True) RETURNING id;')
            cursor.execute(
                'PREPARE search_csn_tag AS \
                 SELECT id FROM partner_contact_identification_tag WHERE number = $1 AND mapping_id = $2;')
            cursor.execute(
                'PREPARE insert_tags AS \
                 INSERT INTO partner_contact_identification_tag (number, mapping_id, medium_id, active) \
                 VALUES \
                 ($2, $3, $1, True), \
                 ($4, $5, $1, True), \
                 ($6, $7, $1, True), \
                 ($8, $9, $1, True), \
                 ($10, $11, $1, True), \
                 ($12, $13, $1, True), \
                 ($14, $15, $1, True), \
                 ($16, $17, $1, True), \
                 ($18, $19, $1, True), \
                 ($20, $21, $1, True), \
                 ($22, $23, $1, True), \
                 ($24, $25, $1, True), \
                 ($26, $27, $1, True), \
                 ($28, $29, $1, True);'
            )

            for tag in tags:
                cursor.execute('EXECUTE insert_medium (%s)', params=[card_type.id])
                medium_id = cursor.fetchone()[0]
                cursor.execute('EXECUTE search_csn_tag (%s, %s)', params=(tag.get('csn'), mapping_calypso_csn.id))

                tag_id = cursor.fetchone()
                if tag_id:
                    cursor.execute('DELETE FROM partner_contact_identification_medium WHERE id = %s;', params=[medium_id]) # noqa
                    continue

                cursor.execute(
                    'EXECUTE insert_tags (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', # noqa
                    params=(
                        medium_id,
                        tag.get('csn'), mapping_calypso_csn.id,
                        tag.get('fiscality'), mapping_calypso_fiscality.id,
                        tag.get('work_social'), mapping_calypso_work_and_social.id,
                        tag.get('health'), mapping_calypso_health.id,
                        tag.get('transport'), mapping_calypso_transport.id,
                        tag.get('civil_state'), mapping_calypso_civil_state.id,
                        tag.get('relation_elected'), mapping_calypso_relation_with_elected_officials.id,
                        tag.get('sport'), mapping_calypso_sport_recreation_childhood.id,
                        tag.get('economy'), mapping_calypso_economy.id,
                        tag.get('police'), mapping_calypso_police.id,
                        tag.get('citizens_relations'), mapping_calypso_citizens_relations.id,
                        tag.get('agents_services'), mapping_calypso_agents_services.id,
                        tag.get('studients_facilities'), mapping_calypso_studients_facilities.id,
                        tag.get('business_fidelity'), mapping_calypso_business_fidelity.id
                    )
                )
