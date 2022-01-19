import base64
from io import BytesIO
import logging
import os

from odoo import _, tools, modules

# TODO Should be replaced by Pillow
from PIL import Image

_logger = logging.getLogger(__name__)


def get_base64_img_avatar_from_file(file_storage):
    u"""
    Essaie de transformer un fichier quelconque en une string image base 64.

    Si l'image est trop grande, plusieurs mécanismes des réduction de taille et de changement de format sont
    appliqués, la limite est 200ko

    :param file_storage: werkzeug filestorage
    :return: Une string à utiliser comme source d'un tag HTML img
    """
    try:
        Image.open(file_storage).verify()
        image_pil = Image.open(file_storage)
        image_64_bytes = tools.image_resize_image_big(base64.b64encode(tools.image_save_for_web(image_pil)))
        bytes_io = BytesIO(base64.b64decode(image_64_bytes))
        bytes_io.seek(0, os.SEEK_END)
        if bytes_io.tell() > (200 * 1024):
            _logger.debug("The image is too big (" + str(bytes_io.tell() / 1024) + "ko > 200ko)")
            image_64_bytes = tools.image_resize_image(base64.b64encode(bytes_io.getvalue()), filetype='png')
            bytes_io = BytesIO(base64.b64decode(image_64_bytes))
            image_pil = Image.open(bytes_io)
            bytes_io.seek(0, os.SEEK_END)
            if bytes_io.tell() > (200 * 1024):
                _logger.debug("The image is still too big after conversion to PNG and crop to 1024x1024")
                image_pil = Image.open(bytes_io)
                bytes_io = BytesIO()
                non_transparent = Image.new('RGB', (1024, 1024), (255, 255, 255, 255))
                non_transparent.paste(image_pil, mask=image_pil.split()[3])
                non_transparent.save(bytes_io, 'JPEG', quality=70)
                image_64_bytes = tools.image_resize_image(base64.b64encode(bytes_io.getvalue()), (800, 800),
                                                          avoid_if_small=True)
                bytes_io = BytesIO(base64.b64decode(image_64_bytes))
                image_pil = Image.open(bytes_io)
                bytes_io.seek(0, os.SEEK_END)
                if bytes_io.tell() > (200 * 1024):
                    _logger.debug(
                        "The image is still too big after conversion to JPEG and crop to 800x800")

        return "data:{0};base64,{1}".format(Image.MIME[image_pil.format], image_64_bytes.decode("utf-8")), []
    except Exception as e:
        _logger.debug(str(e))
        return None, _("The image file used for avatar is invalid. Accepted formats are jpeg, jpg and png")


def get_default_partner_image(partner):
    """Return the default user image with random color."""
    if not partner.image:
        with open(modules.get_module_resource('base', 'static/src/img', 'avatar.png'), 'rb') as f:
            image_raw = BytesIO(f.read())
        # colorize user avatars
        image_bytes = tools.image_colorize(image_raw.getvalue())
        image_base64_bytes = tools.image_resize_image(base64.b64encode(image_bytes), size=(180, 180))
        image_pil = Image.open(BytesIO(base64.b64decode(image_base64_bytes)))
    else:
        image_pil = Image.open(BytesIO(base64.b64decode(partner.image)))
        image_base64_bytes = partner.image

    return "data:{0};base64,{1}".format(Image.MIME[image_pil.format], image_base64_bytes.decode("utf-8"))
