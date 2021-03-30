# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

"""Utilities for managing GeoNode base models
"""

# Standard Modules
import os
import logging
from dateutil.parser import isoparse
from datetime import datetime, timedelta

# Django functionality
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage as storage

# Geonode functionality
from guardian.shortcuts import get_perms, remove_perm, assign_perm

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Link, Configuration
from geonode.geoserver.helpers import ogc_server_settings
from geonode.maps.models import Map
from geonode.services.models import Service

logger = logging.getLogger('geonode.base.utils')

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']

# embrapa #
from datetime import datetime
from geonode.base.models import Embrapa_Data_Quality_Statement, Embrapa_Authors
from django.db.models.functions import (ExtractDay, ExtractMonth, ExtractYear, ExtractHour, ExtractMinute, ExtractSecond)
import requests

from django.http import HttpResponse
from django.db import connection

class AuthorObjects:
    def __init__(self, nome, afiliacao, autoria):
        self.nome = nome
        self.afiliacao = afiliacao
        self.autoria = autoria


def db_table_exists(table_name):

    print("Nome da tabela:")
    print(table_name)
    if table_name in connection.introspection.table_names():
        return table_name in connection.introspection.table_names()
    else:
        return None

def authors_objects_api():

    try:
        autores_endpoint = 'https://www.ainfo-h.cnptia.embrapa.br/ws/rest/listaAutores'

        #autores_endpoint = 'https://embrapa-geoinfo-api-mock.herokuapp.com/ws/rest/listaAutores'

        response = requests.get(autores_endpoint)

        data = response.json()
    except Exception as error:
        return []

    autores_afiliacao = [i for i in range(len(data))]
    autores_autoria = [i for i in range(len(data))]
    autores_nome = [i for i in range(len(data))]

    for i in range(len(data)):
        autores_afiliacao[i] = data[i]["afiliacao"]
        autores_autoria[i] = data[i]["autoria"]
        autores_nome[i] = data[i]["nome"]

    objects_author = []

    for i in range(len(data)):
        objects_author.append(AuthorObjects(autores_nome[i], autores_afiliacao[i], autores_autoria[i]))

    return objects_author

def choice_authors():

    try:

        autores_endpoint = 'https://www.ainfo-h.cnptia.embrapa.br/ws/rest/listaAutores'

        #autores_endpoint = 'https://embrapa-geoinfo-api-mock.herokuapp.com/ws/rest/listaAutores'

        #autores_endpoint = 'http://www.ainfo-h.cnptia.embrapa.br/ws/rest/listaAutoriaByAutoria?autoria={0}'.format(settings.FILTRO_AUTOR)

        response = requests.get(autores_endpoint)

        data = response.json()
    except Exception as error:
        return []

    base_embrapa_authors_exists = db_table_exists("base_embrapa_authors")
    if base_embrapa_authors_exists:
        autores_database = Embrapa_Authors.objects.values_list('name', flat=True).order_by('name')
    else:
        autores_database = ['']

    autores_range_database = [i for i in range(len(autores_database))]

    autores_total_range = len(autores_range_database) + len(data)

    autores_nome = [i for i in range(autores_total_range)]
    autores_afiliacao = [i for i in range(autores_total_range)]
    autores_autoria = [i for i in range(autores_total_range)]

    j = 0

    for i in range(len(data)):
        autores_afiliacao[j] = data[i]["afiliacao"]
        autores_autoria[j] = data[i]["autoria"]
        autores_nome[j] = data[i]["nome"]
        j = j + 1

    for i in range(len(autores_database)):
        autores_nome[j] = autores_database[i]
        j = j + 1

    autores_nome = list(dict.fromkeys(autores_nome))

    autores_nome_tuples = list(zip(autores_nome,autores_nome))

    return autores_nome_tuples

def choice_data_quality_statement():

    try:
        data_quality_statement_endpoint = 'https://www.ainfo-h.cnptia.embrapa.br/ws/rest/tituloByTitulo?titulo={0}'.format(settings.FILTRO_DATA)

        #data_quality_statement_endpoint = 'https://embrapa-geoinfo-api-mock.herokuapp.com/data-quality-statement'

        response = requests.get(data_quality_statement_endpoint)

        data = response.json()
    except Exception as error:
        return []

    base_embrapa_data_quality_statement_exists = db_table_exists("base_embrapa_data_quality_statement")
    if base_embrapa_data_quality_statement_exists:
        data_quality_statement_content_database = Embrapa_Data_Quality_Statement.objects.values_list('name', flat=True).order_by('name')
    else:
        data_quality_statement_content_database = ['']

    data_quality_statement_range_api = [i for i in range(len(data))]

    data_quality_statement_range_database = [i for i in range(len(data_quality_statement_content_database))]

    data_quality_statement_total_range = len(data_quality_statement_range_api) + len(data_quality_statement_range_database)

    data_quality_statement_content_reference = [i for i in range(data_quality_statement_total_range)]

    j = 0

    for i in range(len(data)):
        data_quality_statement_content_reference[j] = data[i]["referenciaBibliografica"]
        j = j + 1

    for i in range(len(data_quality_statement_content_database)):
        data_quality_statement_content_reference[j] = data_quality_statement_content_database[i]
        j = j + 1

    data_quality_statement_content_reference = list(dict.fromkeys(data_quality_statement_content_reference))

    data_quality_statement_content_reference_tuples = list(zip(data_quality_statement_content_reference,data_quality_statement_content_reference))

    return data_quality_statement_content_reference_tuples

    #return data_quality_statement_content_reference

def choice_purpose_list():
    embrapaunity = settings.EMBRAPA_UNITY_DEFAULT
    result = choice_purpose()
    return result

def savetext(text):
    f = open("/usr/src/geonode/geonode/log_utils.txt", "a+")
    f.write(str(text))
    f.close()

def choice_purpose(val):
    #savetext("DEF choice_purpose VALUE : {}".format(str(val)))
    #savetext()

    if val == "":
        val = 0

    if int(val) > 0:
        if os.path.exists("/usr/src/geonode/geonode/log_unidade.txt"):
            os.remove("/usr/src/geonode/geonode/log_unidade.txt")
        f = open("/usr/src/geonode/geonode/log_unidade.txt", "a+")
        f.write(str(val))
        f.close()
    elif val == 0:
        if os.path.exists("/usr/src/geonode/geonode/log_unidade.txt"):
            f = open("/usr/src/geonode/geonode/log_unidade.txt", "r")
            val = f.read()
            f.close()

    current_year = get_only_year()

    if val == 0 or val == "0":
        val = 96

    unity_id = val
    
    if unity_id == 0:
        unity_id = settings.EMBRAPA_UNITY_DEFAULT

    if settings.ACAO_GERENCIAL_API:
        try:
            #savetext('UTILS - Codigo unidade : {} - {}'.format(unity_id, str(datetime.now())))
            acao_gerencial_endpoint = 'https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/lista/acoesgerenciais/poridunidadeembrapaano/{0}/{1}'.format(unity_id, current_year)
            response = requests.get(acao_gerencial_endpoint)
            data = response.json()
        except Exception as error:
            savetext("UTILS - choice_purpose erro 1")
            savetext(error)
            return []

        data_acao_gerencial = data["acaoGerencial"]
        embrapa_acao_gerencial = [i for i in range(len(data_acao_gerencial))]

        for i in range(len(data_acao_gerencial)):
            embrapa_acao_gerencial[i] = data_acao_gerencial[i]["acaoGerencialId"] + ' - ' + data_acao_gerencial[i]["titulo"]

        return embrapa_acao_gerencial
    else :
        # Chamada para projeto
        try:
            projeto_endpoint = 'https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/projeto/lista/poridunidadeembrapa?id_unidadeembrapa={0}'.format(unity_id)
            response = requests.get(projeto_endpoint)
            data = response.json()
        except Exception as error:
            savetext("choice_purpose erro 2")
            savetext(error)        
            return []
        
        data_projeto_id_titulo = data["projeto"]
        embrapa_projeto = [i for i in range(len(data_projeto_id_titulo))]

        if type(data_projeto_id_titulo) is dict:
            embrapa_projeto = ['1']
            embrapa_projeto[0] = data_projeto_id_titulo["id"] + ' - ' + data_projeto_id_titulo["titulo"]
        elif type(data_projeto_id_titulo) is list:
            for i in range(len(data_projeto_id_titulo)):
                embrapa_projeto[i] = data_projeto_id_titulo[i]["id"] + ' - ' + data_projeto_id_titulo[i]["titulo"]
        #savetext("choice_purpose lista:")
        #savetext(str(embrapa_projeto))
        return embrapa_projeto

    return []


def choice_unity():
    try:
        response = requests.get('https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/unidades/lista/todas')
        savetext('Response: ' + str(response))

        data = response.json()
        savetext('len(data): ' + str(len(data)))

        data_ids = data["unidadesEmbrapa"]
        savetext('Tamanho data_ids: ' + str(len(data_ids)))
    except Exception as error:
        savetext("Erro choice_unity: ")
        savetext(error)
        return []
    
    embrapa_only_ids = [i for i in range(len(data_ids))]
    savetext('Tamanho embrapa_only_ids: ' + str(len(embrapa_only_ids)))

    embrapa_only_names = [i for i in range(len(data_ids))]
    savetext('Tamanho embrapa_only_names: ' + str(len(embrapa_only_names)))

    embrapa_ids_names = [i for i in range(len(data_ids))]
    savetext('Tamanho embrapa_ids_names: ' + str(len(embrapa_ids_names)))
    
    for i in range(len(data_ids)):
        embrapa_only_ids[i] = data_ids[i]["id"]
        embrapa_only_names[i] = data_ids[i]["nome"]

    for i in range(len(data_ids)):
        embrapa_ids_names[i] = embrapa_only_ids[i] + ' - ' + embrapa_only_names[i]

    savetext('Tamanho embrapa_ids_names: ' + str(len(embrapa_ids_names)))

    return embrapa_ids_names

def get_last_update():
    data_banco = Embrapa_Last_Updated.objects.annotate(
        day=ExtractDay('last_updated'),
        month=ExtractMonth('last_updated'),
        year=ExtractYear('last_updated'),
        hour=ExtractHour('last_updated'),
        minute=ExtractMinute('last_updated'),
        second=ExtractSecond('last_updated'),).values(
        'day', 'month', 'year', 'hour', 'minute', 'second'
    ).get()
    print(data_banco)
    day = data_banco["day"]
    month = data_banco["month"]
    year = data_banco["year"]
    hour = data_banco["hour"]
    minute = data_banco["minute"]
    second = data_banco["second"]

    result_in_seconds_from_database = day * 86400 + month * 2592000 + year * 31104000 + hour * 3600 + minute * 60 + second

    print("resultado do banco em segundos:")
    print(result_in_seconds_from_database)
    date_current = datetime.now()

    format_date = str(date_current)

    format_year = format_date[0:4]
    format_year = int(format_year)

    format_month = format_date[5:7]
    format_month = int(format_month)

    format_day = format_date[8:10]
    format_day = int(format_day)

    format_hour = format_date[11:13]
    format_hour = int(format_hour)

    format_minute = format_date[14:16]
    format_minute = int(format_minute)

    format_second = format_date[17:19]
    format_second = int(format_second)

    result_all_in_seconds_current = format_day * 86400 + format_month * 2592000 + format_year * 31104000 + format_hour * 3600 + format_minute * 60 + format_second

    print(result_all_in_seconds_current)

    return [result_all_in_seconds_current, result_in_seconds_from_database]


def get_only_year():

    time = datetime.now()

    format_time = str(time)

    format_time = format_time[0:4]

    return format_time

def delete_orphaned_thumbs():
    """
    Deletes orphaned thumbnails.
    """
    if isinstance(storage, FileSystemStorage):
        documents_path = os.path.join(settings.MEDIA_ROOT, 'thumbs')
    else:
        documents_path = os.path.join(settings.STATIC_ROOT, 'thumbs')
    if os.path.exists(documents_path):
        for filename in os.listdir(documents_path):
            fn = os.path.join(documents_path, filename)
            model = filename.split('-')[0]
            uuid = filename.replace(model, '').replace('-thumb.png', '')[1:]
            if ResourceBase.objects.filter(uuid=uuid).count() == 0:
                print('Removing orphan thumb %s' % fn)
                logger.debug('Removing orphan thumb %s' % fn)
                try:
                    os.remove(fn)
                except OSError:
                    print('Could not delete file %s' % fn)
                    logger.error('Could not delete file %s' % fn)


def remove_duplicate_links(resource):
    """
    Makes a scan of Links related to the resource and removes the duplicates.
    It also regenerates the Legend link in case this is missing for some reason.
    """
    for _n in _names:
        _links = Link.objects.filter(resource__id=resource.id, name=_n)
        _cnt = _links.count()
        while _cnt > 1:
            _links.last().delete()
            _cnt -= 1

    if isinstance(resource, Layer):
        # fixup Legend links
        layer = resource
        legend_url_template = \
            ogc_server_settings.PUBLIC_LOCATION + \
            'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
            '{alternate}&STYLE={style_name}' + \
            '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'
        if layer.default_style and not layer.get_legend_url(style_name=layer.default_style.name):
            Link.objects.update_or_create(
                resource=layer.resourcebase_ptr,
                name='Legend',
                extension='png',
                url=legend_url_template.format(
                    alternate=layer.alternate,
                    style_name=layer.default_style.name),
                mime='image/png',
                link_type='image')


def configuration_session_cache(session):
    CONFIG_CACHE_TIMEOUT_SEC = 60

    _config = session.get('config')
    _now = datetime.utcnow()
    _dt = isoparse(_config.get('expiration')) if _config else _now
    if _config is None or _dt < _now:
        config = Configuration.load()
        _dt = _now + timedelta(seconds=CONFIG_CACHE_TIMEOUT_SEC)
        cached_config = {
            'configuration': {},
            'expiration': _dt.isoformat()
        }

        for field_name in ['read_only', 'maintenance']:
            cached_config['configuration'][field_name] = getattr(config, field_name)

        session['config'] = cached_config


class OwnerRightsRequestViewUtils:

    @staticmethod
    def get_message_recipients():
        User = get_user_model()
        allowed_users = User.objects.none()
        if OwnerRightsRequestViewUtils.is_admin_publish_mode():
            allowed_users |= User.objects.filter(is_superuser=True)
        return allowed_users

    @staticmethod
    def get_resource(resource_base):
        if resource_base.polymorphic_ctype.name == 'layer':
            return Layer.objects.get(pk=resource_base.pk)
        elif resource_base.polymorphic_ctype.name == 'document':
            return Document.objects.get(pk=resource_base.pk)
        elif resource_base.polymorphic_ctype.name == 'map':
            return Map.objects.get(pk=resource_base.pk)
        else:
            return Service.objects.get(pk=resource_base.pk)

    @staticmethod
    def is_admin_publish_mode():
        return settings.ADMIN_MODERATE_UPLOADS


class ManageResourceOwnerPermissions:
    def __init__(self, resource):
        self.resource = resource

    def set_owner_permissions_according_to_workflow(self):
        if self.resource.is_approved and OwnerRightsRequestViewUtils.is_admin_publish_mode():
            self._disable_owner_write_permissions()
        else:
            self._restore_owner_permissions()

    def _disable_owner_write_permissions(self):

        for perm in get_perms(self.resource.owner, self.resource.get_self_resource()):
            remove_perm(perm, self.resource.owner, self.resource.get_self_resource())

        for perm in get_perms(self.resource.owner, self.resource):
            remove_perm(perm, self.resource.owner, self.resource)

        for perm in self.resource.BASE_PERMISSIONS.get('read') + self.resource.BASE_PERMISSIONS.get('download'):
            assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

    def _restore_owner_permissions(self):

        for perm_list in self.resource.BASE_PERMISSIONS.values():
            for perm in perm_list:
                assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

        for perm_list in self.resource.PERMISSIONS.values():
            for perm in perm_list:
                assign_perm(perm, self.resource.owner, self.resource)
