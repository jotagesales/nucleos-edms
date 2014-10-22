from __future__ import absolute_import

import logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.utils.translation import ugettext_lazy as _
#from django.db.models.signals import post_save
#from django.dispatch import receiver

from documents.models import Document, DocumentVersion
from navigation.api import register_links
from django_gpg.runtime import gpg
from django_gpg.exceptions import GPGDecryptionError
from acls.api import class_permissions

from .models import DocumentVersionSignature
from .permissions import (
    PERMISSION_DOCUMENT_VERIFY,
    PERMISSION_SIGNATURE_UPLOAD,
    PERMISSION_SIGNATURE_DOWNLOAD
)

logger = logging.getLogger(__name__)


def has_embedded_signature(context):
    return DocumentVersionSignature.objects.has_embedded_signature(context['object'])


def doesnt_have_detached_signature(context):
    return DocumentVersionSignature.objects.has_detached_signature(context['object']) == False


def document_pre_open_hook(descriptor, instance):
    if DocumentVersionSignature.objects.has_embedded_signature(instance.document):
        # If it has an embedded signature decrypt
        try:
            result = gpg.decrypt_file(descriptor, close_descriptor=False)
            # gpg return a string, turn it into a file like object
        except GPGDecryptionError:
            # At least return the original raw content
            descriptor.seek(0)
            return descriptor
        else:
            descriptor.close()
            return StringIO(result.data)
    else:
        # It no embedded signature pass along
        # Doing this single DB lookup avoids trying to decrypt non signed
        # files always, which could result in slow down for big non signed
        # files
        #descriptor.seek(0)
        return descriptor

    #try:
    #    result = gpg.decrypt_file(descriptor, close_descriptor=False)
    #    # gpg return a string, turn it into a file like object
    #except GPGDecryptionError:
    #    # At least return the original raw content
    #    descriptor.seek(0)
    #    return descriptor
    #else:
    #    descriptor.close()
    #    return StringIO(result.data)


def document_post_save_hook(instance):
    if not instance.pk:
        document_signature, created = DocumentVersionSignature.objects.get_or_create(
            document_version=instance.latest_version,
        )
        #DocumentVersionSignature.objects.update_signed_state(instance.document)

#@receiver(post_save, dispatch_uid='check_document_signature_state', sender=DocumentVersion)
#def check_document_signature_state(sender, instance, **kwargs):
#    if kwargs.get('created', False):
#        DocumentVersionSignature.objects.signature_state(instance.document)

document_signature_upload = {'text': _(u'upload signature'), 'view': 'document_signature_upload', 'args': 'object.pk', 'famfam': 'pencil_add', 'permissions': [PERMISSION_SIGNATURE_UPLOAD], 'conditional_disable': has_embedded_signature}
document_signature_download = {'text': _(u'download signature'), 'view': 'document_signature_download', 'args': 'object.pk', 'famfam': 'disk', 'permissions': [PERMISSION_SIGNATURE_DOWNLOAD], 'conditional_disable': doesnt_have_detached_signature}
document_verify = {'text': _(u'signatures'), 'view': 'document_verify', 'args': 'object.pk', 'famfam': 'text_signature', 'permissions': [PERMISSION_DOCUMENT_VERIFY]}

register_links(Document, [document_verify], menu_name='form_header')
register_links(['document_verify', 'document_signature_upload', 'document_signature_download'], [document_signature_upload, document_signature_download], menu_name='sidebar')

DocumentVersion.register_pre_open_hook(1, document_pre_open_hook)
DocumentVersion.register_post_save_hook(1, document_post_save_hook)

class_permissions(Document, [
    PERMISSION_DOCUMENT_VERIFY,
    PERMISSION_SIGNATURE_UPLOAD,
    PERMISSION_SIGNATURE_DOWNLOAD
])
