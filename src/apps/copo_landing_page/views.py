import common.schemas.utils.data_utils as d_utils

from common.utils.logger import Logger
from datetime import datetime, timezone
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
import json
from src.apps.copo_core.models import UserDetails, banner_view

l = Logger()


def index(request):
    banner = banner_view.objects.all()
    if len(banner) > 0:
        context = {'user': request.user, "banner": banner[0]}
    else:
        context = {'user': request.user}
    return render(request, 'index_new.html', context)


def cookie_response(request):
    cookie_consent_dict = dict()
    cookie_response = request.POST.get('cookie_response', None)

    user_id = str(request.user.id)
    user_device = request.user_agent.device.family
    user_browser = f'{request.user_agent.browser.family} version { request.user_agent.browser.version_string}'
    user_operating_system = request.user_agent.os.family

    if (user_device == 'Other'):
        if request.user_agent.is_pc:
            user_device = 'desktop'
        elif request.user_agent.is_tablet:
            user_device = 'tablet'
        elif request.user_agent.is_mobile:
            user_device = 'mobile'
        else:
            user_device = 'unknown'

    cookie_consent_dict['user_browser'] = user_browser
    cookie_consent_dict['user_device'] = user_device
    cookie_consent_dict['user_operating_system'] = user_operating_system
    cookie_consent_dict['cookie_response'] = d_utils.convertStringToBoolean(
        cookie_response)
    cookie_consent_dict['cookie_response_date_created'] = datetime.now(
        timezone.utc).replace(microsecond=0).isoformat()

    try:
        user_details = UserDetails.objects.get(pk=user_id)

        if user_details.repo_manager is None:
            user_details.repo_manager = list()

        if user_details.repo_submitter is None:
            user_details.repo_submitter = list()

        if user_details.cookie_consent_log is None:
            user_details.cookie_consent_log = list()

        user_details.cookie_consent_log.append(
            json.dumps(cookie_consent_dict, default=dict))
        user_details.save()

        response = HttpResponse(json.dumps({'resp': 'user details updated'}))
    except Exception as e:
        l.exception(e)
        response = HttpResponseBadRequest(json.dumps({'resp': 'Error'}))

    return response
