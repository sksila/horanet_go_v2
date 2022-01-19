import base64
import json

import magic
from odoo.addons.portal.controllers.portal import CustomerPortal as website_account

from odoo import _, http
from odoo.http import request

# Taken from https://www.sitepoint.com/web-foundations/mime-types-complete-list/
VALID_MIME_TYPES = [
    'image/bmp',
    'image/x-windows-bmp',
    'image/x-ms-bmp',
    'image/jpeg',
    'image/pjpeg',
    'image/png',
    'application/pdf',
]

MEGABYTE = 1024 * 1024  # Equal to 1 Megabyte
MAX_FILE_SIZE_IN_MEGABYTES = 10


class WebsitePortalDocuments(website_account):
    @http.route()
    def home(self, **kw):
        """Add documents to main home page."""
        response = super(WebsitePortalDocuments, self).home(**kw)
        user = request.env.user

        documents = request.env['ir.attachment']

        document_count = documents.search_count([
            ('user_id', '=', user.id), ('parent_doc_id', '=', False)
        ])

        response.qcontext.update({
            'document_count': document_count,
        })
        return response

    def _get_attachment_types(self):
        """Search and return all records of ir.attachment.type.

        :return: ir.attachment.type recordset
        """
        # TODO: remove sudo calls when we'll have good access/record rules
        attachment_type_obj = request.env['ir.attachment.type'].sudo()
        return attachment_type_obj.search([])

    def _get_attachment_type(self, technical_name):
        """Search and return one record of ir.attachment.type.

        :param str technical_name: technical_name of the record to search for
        :return: ir.attachment.type record
        """
        # TODO: remove sudo calls when we'll have good access/record rules
        attachment_type_obj = request.env['ir.attachment.type'].sudo()

        return attachment_type_obj.search(
            [('technical_name', '=', technical_name)]
        )

    def _redirect_my_documents(self):
        return request.redirect('/my/documents')

    def _validate_form(self, document_type, files, custom_values):
        """Check the values of form inputs.

        :param document_type: technical_name of ir.attachment.type
        :param files: list of files received
        :param recipient: res.partner attached to the ir.attachment
        :param recipients: list of res.partner available to the current user
        :return: form errors that will be displayed to the user
        :rtype: {}
        """
        errors = {}
        self.extra_validation(custom_values)

        types_names = [attach['technical_name'] for attach in self._get_attachment_types()]

        if document_type not in types_names:
            errors['err_doc_type'] = _('The document type {type} is not valid.').format(type=document_type)
        if not files:
            errors['err_no_doc'] = _('No document was provided.')

        errors_docs = {}
        for i, current_file in enumerate(files):
            key = 'err_doc_{}'.format(i)

            mimetype = magic.from_buffer(current_file.read(1024), mime=True)
            if mimetype == 'application/x-empty':
                if len(files) > 1:
                    break  # if a user forgot to fill additional files inputs
                else:
                    errors_docs[key] = _('A file must be provided.')
                    break

            if mimetype not in VALID_MIME_TYPES:
                errors_docs[key] = _(
                    "The type '{mimetype}' of {filename} isn't valid."
                ).format(mimetype=mimetype, filename=current_file.filename)
            else:
                # As document_src is not a real file, we need to position the cursor
                # from the beggining (0) to the end (2) of the file like object and
                # get the current byte position which is the length of the file
                current_file.stream.seek(0, 2)
                size = current_file.stream.tell()
                current_file.stream.seek(0)  # Reset the position to the beginning of the file
                if size > MAX_FILE_SIZE_IN_MEGABYTES * MEGABYTE:
                    errors_docs[key] = _('The file {filename} is too big.').format(filename=current_file.filename)

        if errors_docs:
            errors['errors_docs'] = errors_docs

        errors.update(self.extra_validation(custom_values))

        return errors

    def extra_validation(self, values):
        """Use this method if you want to implement your own validation logic on existing fields or new fields.

        :param values: custom input values
        :return: input errors that will be displayed to the user
        :rtype: {}
        """
        errors = {}
        return errors

    def custom_attachment_values(self, custom_values):
        """Use this method if you want to add custom values to an ir.attachment.

        :param values: custom input values
        :return: values that will be written on ir.attachment object
        :rtype: {}
        """
        values = {}

        return values

    @http.route(['/my/documents'], type='http', auth='user', methods=['GET'], website=True)
    def get_documents(self, date_begin=None, date_end=None):
        """Display all ir.attachment owned by the current user."""
        template_name = 'partner_documents.documents'
        context = self._prepare_portal_layout_values()

        domain = [('user_id', '=', request.env.user.id)]
        archive_groups = self._get_archive_groups('ir.attachment', domain)

        docs = request.env.user.get_documents(date_begin=date_begin, date_end=date_end)

        context.update({
            'documents': docs,
            'archive_groups': archive_groups,
            'date': date_begin,
        })

        return request.render(template_name, context)

    @http.route(['/my/documents/list'], type='http', auth='user', methods=['GET'], website=True)
    def get_documents_list(self, date_begin=None, date_end=None, _=False):
        """Display all ir.attachment owned by the current user."""
        docs = request.env.user.get_documents(status=['to_check', 'valid'], date_begin=date_begin, date_end=date_end)

        # dict_docs = dict(zip(docs.mapped('id'), docs.mapped('name')))
        list_docs = [{'document_type': doc.document_type_id.id,
                      'id': doc.id,
                      'name': doc.name,
                      'child_names': [child.datas_fname for child in doc.child_ids],
                      'datas_fname': doc.datas_fname} for doc in docs.sorted('id')]

        return json.dumps(list_docs)

    @http.route(['/my/documents/<int:parent_doc_id>'], type='http', auth='user', methods=['GET'], website=True)
    def get_document(self, parent_doc_id):
        """Display a page that list files attached to the current document.

        Only in case this document has more than one file attached to it

        :param parent_doc_id: id of the ir.attachment to list files
        """
        template_name = 'partner_documents.document'

        document = request.env.user.get_documents(document_id=parent_doc_id)
        context = {'document': document}

        return request.render(template_name, context)

    @http.route(['/my/documents/add',
                 '/my/documents/update/<int:document_id>'],
                type='http', auth='user', methods=['GET', 'POST'], website=True)
    def add_document(self, redirect=None, document_type=None, document_id=None, modal_call=None, **kw):
        """Display a form that allow current user to send documents.

        The user is able to select himself or its related partners as the
        partner attached to the ir.attachment and the type of the document he
        wants to create

        :param redirect: where to redirect the user
        :param document_type: value used to select the document_type select input
        :param partner_id: id of res.partner to select on the recipient select input
        """
        template_name = 'partner_documents.add_document'

        if document_type:
            document_types = self._get_attachment_type(document_type)
        else:
            document_types = self._get_attachment_types()

        context = {
            'partner': request.env.user.partner_id,
            'document_types': document_types,
            'valid_mime_types': VALID_MIME_TYPES,
            'max_file_size': MAX_FILE_SIZE_IN_MEGABYTES,
            'document_type': document_type,
            'redirect': redirect
        }

        # Si on est en mise à jour, on force le type de document
        document = None
        if document_id:
            document = request.env['ir.attachment'].sudo().browse(document_id)
            context.update({
                'document_types': [document.document_type_id],
                'document_type': document.document_type_id.technical_name,
                'document_id': document_id
            })

        context.update(kw)

        if request.httprequest.method == 'POST':
            uploaded_files = request.httprequest.files.getlist('uploaded_files')

            context.update({
                'document_type': document_type,
                'uploaded_files': uploaded_files,
            })

            errors = self._validate_form(document_type, uploaded_files, kw)

            if errors:
                context.update(errors)
                return request.render(template_name, context)

            attachment_type = self._get_attachment_type(document_type)

            self.create_or_update_attachments(uploaded_files, attachment_type, document, kw)

            if redirect:
                return request.redirect(redirect)

            if not modal_call:
                return self._redirect_my_documents()

        return request.render(template_name, context)

    def create_or_update_attachments(self, uploaded_files, attachment_type, document, extra_values):
        """Create an ir.attachment object.

        :param uploaded_files: file like objects that will be saved
        :param attachment_type: type of the ir.attachment to use
        :param extra_values: custom input values
        """
        attachment_obj = request.env['ir.attachment'].sudo()
        attachment = None
        attachment_childs = []
        for uploaded_file in uploaded_files:
            try:
                # BytesIO object
                data = uploaded_file.stream.getvalue()
            except AttributeError:
                # File object
                data = uploaded_file.stream.read()
                uploaded_file.stream.close()

            user = request.env.user

            # TODO: WE NEED TO CHECK THAT THE UPLOADED FILE HAS THE RIGHT
            #       EXTENSION CORRESPONDING TO ITS MIMETYPE
            values = {
                'document_type_id': attachment_type.id,
                'datas': base64.encodestring(data),
                'datas_fname': uploaded_file.filename,
                'mimetype': uploaded_file.mimetype,
                'user_id': user.id,
                'partner_id': user.partner_id.id
            }

            values.update(self.custom_attachment_values(extra_values))

            if attachment:
                values = {
                    'datas': base64.encodebytes(data),
                    'datas_fname': uploaded_file.filename,
                    'mimetype': uploaded_file.mimetype,
                }
                attachment_childs.append(attachment_obj.create(values))
            else:
                if document:
                    document.child_ids.unlink()
                    values.update({'status': 'to_check'})
                    document.write(values)
                    attachment = document
                else:
                    attachment = attachment_obj.create(values)

        if attachment_childs:
            attachment.child_ids = [(6, 0, [r.id for r in attachment_childs])]
            attachment.child_ids.set_child_ids_parent_values()

    @http.route(['/my/documents/delete'], type='http', auth='user', methods=['POST'], website=True)
    def delete_document(self, **kw):
        """Delete the ir.attachment record."""
        parent_doc_id = kw.get('parent_doc_id')

        request.env.user.delete_document(parent_doc_id)

        return self._redirect_my_documents()

    @http.route(['/my/documents/preview/<int:parent_doc_id>'], type='http', auth='user', methods=['GET'], website=True)
    def preview_document(self, parent_doc_id):
        """Display the selected document in a new TabError.

        :param parent_doc_id: the id of the ir.attachment to display its data
        """
        document = request.env.user.get_documents(document_id=parent_doc_id)

        if not document or not document.mimetype:
            return self._redirect_my_documents()

        return request.make_response(
            base64.b64decode(document.datas), [
                ('Content-Type', document.mimetype),
            ]
        )
