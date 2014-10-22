from __future__ import absolute_import

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from documents.statistics import get_statistics as documents_statistics
from ocr.statistics import get_statistics as ocr_statistics
from permissions.models import Permission

from .api import diagnostics, tools
from .conf.settings import DISABLE_HOME_VIEW


def home(request):
    if DISABLE_HOME_VIEW:
        return HttpResponseRedirect(reverse('document_list_recent'))
    else:
        return render_to_response('home.html', {},
        context_instance=RequestContext(request))


def maintenance_menu(request):
    user_tools = {}
    for namespace, values in tools.items():
        user_tools[namespace] = {
            'title': values['title']
            }
        user_tools[namespace].setdefault('links', [])
        for link in values['links']:
            try:
                permissions = link.get('permissions', [])
                Permission.objects.check_permissions(request.user, permissions)
                user_tools[namespace]['links'].append(link)
            except PermissionDenied:
                pass

    return render_to_response('tools.html', {
        'blocks': user_tools,
        'title': _(u'maintenance menu')
    },
    context_instance=RequestContext(request))


def statistics(request):
    if request.user.is_superuser or request.user.is_staff:
        blocks = []
        blocks.append(documents_statistics())
        blocks.append(ocr_statistics())

        return render_to_response('statistics.html', {
            'blocks': blocks,
            'title': _(u'Statistics')
        },
        context_instance=RequestContext(request))
    else:
        raise PermissionDenied


def diagnostics_view(request):
    return render_to_response('diagnostics.html', {
        'blocks': diagnostics,
        'title': _(u'Diagnostics')
    },
    context_instance=RequestContext(request))
