from lxml import etree
from odoo import _
from odoo.http import request


def xml_from_string(xmlstr):
    """Returns an lxml.etree._ElementTree object from a string containing a valid XML document."""
    try:
        return etree.XML(str(xmlstr).strip())
    except etree.XMLSyntaxError:
        return None


def xml_from_file(filepath):
    """Returns an lxml.etree._ElementTree object from a file containing a valid XML document."""
    try:
        return etree.parse(filepath)
    except etree.XMLSyntaxError:
        return None


def xsd_from_string(xsdstr):
    """Returns an lxml.etree.XMLSchema object from a string containing a valid XML document."""
    try:
        xml = etree.XML(str(xsdstr).strip())
        return etree.XMLSchema(xml)
    except etree.XMLSyntaxError:
        return None


def xsd_from_file(filepath):
    """Returns an lxml.etree.XMLSchema object from a file containing a valid XML document."""
    try:
        # print "filepath : ",filepath
        xml = etree.parse(filepath)
        return etree.XMLSchema(xml)
    except etree.XMLSyntaxError:
        return None


def validate(xml, xsd):
    """
    Receives an lxml.etree._ElementTree object and an lxml.etree.XMLSchema object.

    Returns True or False respectively as the XSD validation of the XML succeeds or fails.
    """
    return xsd.validate(xml)


def validate_from_strings(xmlstr, xsdstr):
    """
    Receives a string containing a valid XML document and another string containing a valid XSD document.

    Validates the first according to the latter returning True or False
    respectively as the validation succeeds or fails.
    """
    xml = xml_from_string(xmlstr)
    xsd = xsd_from_string(xsdstr)
    return validate(xml, xsd)


def validate_from_element(xml, xsdfilepath):
    xsd = xsd_from_file(xsdfilepath)
    return validate(xml, xsd)


def validate_from_files(xmlfilepath, xsdfilepath):
    """
    Receives a string with a file path to a valid XML document and a string with a file path to a valid XSD document.

    Validates the first according to the latter returning True or False respectively as the validation
    succeeds or fails.
    """
    xml = xml_from_file(xmlfilepath)
    xsd = xsd_from_file(xsdfilepath)
    return validate_with_errors(xml, xsd)


def validate_xml_string_from_xsd_file(xmlstr, xsdfilepath):
    """
    Validates a string containing an XML document as the first parameter with an XSD document.

    The XSD document is contained in the file path passed as the second parameter.
    """
    xml = xml_from_string(xmlstr)
    xsd = xsd_from_file(xsdfilepath)
    return validate(xml, xsd)


def validate_with_errors(xml, xsd):
    """Returns a tuple with a boolean product of the XSD validation and the error log object."""
    validation = xsd.validate(xml)
    return (validation, xsd.error_log,)


def xsd_error_as_simple_string(error):
    """
    Returns a string based on an XSD error object.

    Format : LINE:COLUMN:LEVEL_NAME:DOMAIN_NAME:TYPE_NAME:MESSAGE.
    """
    parts = [
        error.line,
        error.column,
        error.level_name,
        error.domain_name,
        error.type_name,
        error.message
    ]
    return ':'.join([str(item) for item in parts])


def xsd_error_log_as_simple_strings(error_log):
    """Returns a list of strings representing all the errors of an XSD error log object."""
    return [xsd_error_as_simple_string(e) for e in error_log]


def form_validate_nat_jur_cat_tiers(data, is_company):
    """Add errors and the associated message in the dictionary if there is something wrong for a front account.

    This method is used to check the natJur and catTiers informations in the partner front template.

    :param data: data of the form
    :param is_company: if the data is for a company or a normal partner
    :return: error and associated message
    """
    error = dict()
    error_message = []
    nat_jur_id = data.get('nat_jur_id')
    cat_tiers_id = data.get('cat_tiers_id')

    required_nat_jur = request.env['collectivity.config.settings'].get_required_nat_jur()
    required_cat_tiers = request.env['collectivity.config.settings'].get_required_cat_tiers()

    if is_company and required_nat_jur and not nat_jur_id:
        error['nat_jur_id'] = 'error'
        error_message.append(_("The Natjur is required"))

    if is_company and required_cat_tiers and not cat_tiers_id:
        error['cat_tiers_id'] = 'error'
        error_message.append(_("The CatTiers is required"))

    return error, error_message
