#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Support functionality to allow upload of Structured Data.

Internally used data format and merge strategies described in README.md.
"""
from __future__ import unicode_literals

import json
from builtins import dict

import pywikibot

import pywikibotsdc.common as common
from pywikibotsdc.sdc_exception import SdcException

# Wikibase has hardcoded Commons as the only allowed site for media files
# T90492. Pywikibot gets cranky if it's initialised straight away though.
_COMMONS_MEDIA_FILE_SITE = None  # pywikibot.Site('commons', 'commons')
DEFAULT_EDIT_SUMMARY = \
    'Added {count} structured data statement(s) #pwbsdc'
STRATEGIES = ('new', 'blind', 'squeeze', 'nuke')


def _get_commons():
    """Return cached pywikibot.Site('commons', 'commons')."""
    global _COMMONS_MEDIA_FILE_SITE
    if not _COMMONS_MEDIA_FILE_SITE:
        _COMMONS_MEDIA_FILE_SITE = pywikibot.Site('commons', 'commons')
    return _COMMONS_MEDIA_FILE_SITE


def _submit_data(target_site, payload):
    """
    Submit the Structured Data for upload.

    @param target_site: pywikibot.Site where data is uploaded.
    @param payload: request formatted for the MediaWiki Action API
    @raises: pywikibot.data.api.APIError
    """
    request = target_site._simple_request(**payload)
    request.submit()


def upload_single_sdc_data(file_page, sdc_data, target_site=None,
                           strategy=None, summary=None):
    """
    Upload the Structured Data corresponding to the recently uploaded file.

    @param file_page: pywikibot.FilePage object (or the file name as a string)
        corresponding to the media file to which Structured Data should be
        attached. If a file name is provided the target_site parameter must
        also be supplied unless the file lives on Wikimedia Commons).
    @param sdc_data: internally formatted Structured Data in json format
    @param target_site: pywikibot.Site where the file_page is found (if only a
        file name was supplied). Defaults to Wikimedia Commons.
    @param strategy: Strategy used for merging uploaded data with pre-existing
        data. Allowed values are None (default), "New" and "Blind".
    @param summary: edit summary If not provided one is looked for in the
        sdc_data, if none is found there then a default summary is used.
    @return: Number of added statements
    @raises: ValueError, SdcException
    """
    # support either file_name+Site or file_page as input
    if isinstance(file_page, pywikibot.FilePage):
        if target_site and target_site != file_page.site:
            raise ValueError(
                'target_site should not be provided when file_page is a '
                'FilePage object.')
        target_site = file_page.site
    else:
        target_site = target_site or _get_commons()
        file_page = pywikibot.FilePage(target_site, file_page)

    media_identifier = 'M{}'.format(file_page.pageid)

    # check if there is Structured Data already and resolve what to do
    # raise SdcException if merge is not possible
    skipped = merge_strategy(media_identifier, target_site, sdc_data, strategy)
    if skipped:
        pywikibot.log(
            '{0} - Conflict with existing values. Dropping the following '
            'properties and caption languages{}.'.format(
                file_page.title(),
                ', '.join([', '.join(v) for v in skipped.values()])))

    # Translate from internal sdc data format to that expected by MediaWiki.
    try:
        sdc_payload = format_sdc_payload(target_site, sdc_data)
    except Exception as error:
        raise SdcException(
            'error', error, 'Formatting SDC data failed: {0}'.format(error)
        )

    # upload sdc data
    summary = summary or sdc_data.get('edit_summary', DEFAULT_EDIT_SUMMARY)
    num_statements = (len(sdc_payload.get('labels', []))
                      + len(sdc_payload.get('claims', [])))
    payload = {
        'action': 'wbeditentity',
        'format': u'json',
        'id': media_identifier,
        'data': json.dumps(sdc_payload, separators=(',', ':')),
        'token': target_site.tokens['csrf'],
        'summary': summary.format(count=num_statements),
        'bot': target_site.has_right('bot')
    }
    if strategy and strategy.lower() == 'nuke':
        payload['clear'] = 1

    try:
        _submit_data(target_site, payload)
    except pywikibot.data.api.APIError as error:
        raise SdcException(
            'error', error, 'Uploading SDC data failed: {0}'.format(error)
        )
    return num_statements


def _get_existing_structured_data(media_identifier, target_site):
    """
    Return pre-existing Structured Data, if any.

    This treats an file where no Structured Data has ever existed the same as
    one where all statements and captions have been removed.

    @param media_identifier: Mid of the file
    @param target_site: pywikibot.Site object to which file should be uploaded
    @return The Structured Data of the file or None if no data was ever present
        or if the data has since been removed.
    """
    request = target_site._simple_request(
        action='wbgetentities', ids=media_identifier)
    raw = request.submit()
    data = raw.get('entities').get(media_identifier)
    if ('missing' not in data.keys()
            and (data.get('labels') or data.get('statements'))):
        return data


def merge_strategy(media_identifier, target_site, sdc_data, strategy):
    """
    Check if the file already holds Structured Data, if so resolve what to do.

    @param media_identifier: Mid of the file
    @param target_site: pywikibot.Site object to which file should be uploaded
    @param sdc_data: internally formatted Structured Data in json format
    @param strategy: Strategy used for merging uploaded data with pre-existing
        data. Allowed values are None, "New", "Blind", "Squeeze" and "Nuke".
    @return: dict of pids and caption languages removed from sdc_data due to
        conflicts.
    @raises: ValueError, SdcException
    """
    prior_data = _get_existing_structured_data(media_identifier, target_site)
    if not prior_data:
        # even unknown strategies should pass if there is no prior data
        return

    if not strategy:
        raise SdcException(
            'warning', 'pre-existing sdc-data',
            ('Found pre-existing SDC data, no new data will be added. '
             'Found data: {}'.format(prior_data))
        )
    elif strategy.lower() in ('new', 'squeeze'):
        pre_pids = prior_data['statements'].keys()
        pre_langs = prior_data['labels'].keys()
        new_langs = sdc_data.get('caption', {}).keys()

        if strategy.lower() == 'squeeze':
            pid_clash = set(pre_pids).intersection(sdc_data.keys())
            lang_clash = set(pre_langs).intersection(new_langs)
            for pid in pid_clash:
                sdc_data.pop(pid, None)
            for lang in lang_clash:
                sdc_data['caption'].pop(lang, None)
            if (not any(is_prop_key(key) for key in sdc_data.keys())
                    and not sdc_data.get('caption')):
                # warn if not data left to upload
                raise SdcException(
                    'warning', 'all conflicting pre-existing sdc-data',
                    ('Found pre-existing SDC data, no new non-conflicting '
                     'data could be added. Found data: {}'.format(
                         prior_data))
                )
            elif pid_clash or lang_clash:
                return {'pids': pid_clash, 'langs': lang_clash}
        elif (not set(pre_pids).isdisjoint(sdc_data.keys())
                or not set(pre_langs).isdisjoint(new_langs)):
            raise SdcException(
                'warning', 'conflicting pre-existing sdc-data',
                ('Found pre-existing SDC data, no new data will be added. '
                 'Found data: {}'.format(prior_data))
            )
    elif strategy.lower() not in STRATEGIES:
        raise ValueError(
            'The `strategy` parameter must be None, "{0}" or "{1}" '
            'but "{2}" was provided'.format(
                '", "'.join([s.capitalize() for s in STRATEGIES[:-1]]),
                STRATEGIES[-1].capitalize(),
                strategy))
    # pass if strategy is "Blind" or "Nuke"


def format_sdc_payload(target_site, data):
    """
    Translate from internal sdc data format to that expected by MediaWiki.

    This takes no responsibility for validating the passed in sdc data.

    @param target_site: pywikibot.Site object to which file was uploaded
    @param data: internally formatted sdc data.
    @return: dict formated sdc data payload
    @raises: ValueError
    """
    allowed_non_property_keys = ('caption', 'summary')
    payload = dict()

    if data.get('caption'):
        payload['labels'] = dict()
        for k, v in data['caption'].items():
            payload['labels'][k] = {'language': k, 'value': v}

    if set(data.keys()) - set(allowed_non_property_keys):
        prop_data = {key: data[key] for key in data.keys() if is_prop_key(key)}
        if prop_data:
            payload['claims'] = []
        for prop, value in prop_data.items():
            if isinstance(value, list):
                for v in value:
                    claim = make_claim(v, prop, target_site)
                    payload['claims'].append(claim.toJSON())
            else:
                claim = make_claim(value, prop, target_site)
                payload['claims'].append(claim.toJSON())

    # raise error if no recognisable sdc data is found
    if not payload:
        raise ValueError(
            'The provided sdc data contains no recognised labels: {}'.format(
                ', '.join(data.keys())))

    return payload


def make_claim(value, prop, target_site):
    """
    Create a pywikibot Claim representation of the internally formatted value.

    @param value: str|dict The internally formatted claim value
    @param prop: str Property of the claim
    @param target_site: pywikibot.Site to which Structured Data is uploaded
    @return: pywikibot.Claim
    @raises: ValueError
    """
    repo = target_site.data_repository()
    claim = pywikibot.Claim(repo, prop)
    if common.is_str(value):
        claim.setTarget(format_claim_value(claim, value))
    elif isinstance(value, dict):
        set_complex_claim_value(value, claim)
    else:
        raise ValueError(
            'Incorrectly formatted property value: {}'.format(value))
    return claim


def set_complex_claim_value(value, claim):
    """
    Populate a claim provided in the complex claim format.

    A complex claim is either one with a multi-part data type, or with the
    prominent flag or with qualifiers.

    @param value: str|dict The internally formatted claim value
    @param claim: pywikibot.Claim for which value is being set
    @return: pywikibot.Claim
    """
    # more complex data types or values with e.g. qualifiers
    claim.setTarget(format_claim_value(claim, value['_']))

    # set prominent flag
    if value.get('prominent'):
        claim.setRank('preferred')

    # add qualifiers
    qual_prop_data = {key: value[key] for key in value.keys()
                      if is_prop_key(key)}
    for qual_prop, qual_value in qual_prop_data.items():
        if isinstance(qual_value, list):
            for q_v in qual_value:
                claim.addQualifier(
                    format_qualifier_claim_value(
                        q_v, qual_prop, claim))
        else:
            claim.addQualifier(
                format_qualifier_claim_value(
                    qual_value, qual_prop, claim))
    return claim


def format_qualifier_claim_value(value, prop, claim):
    """
    Populate a more complex claim.

    A complex claim is either one with a multi-part data type, or with the
    prominent flag or with qualifiers.

    @param value: str|dict The internally formatted qualifier value
    @param prop: str Property of qualifier
    @param claim: pywikibot.Claim to which qualifier is being added
    @return: pywikibot.Claim
    @raises: ValueError
    """
    if common.is_str(value) or isinstance(value, dict):
        # support using exactly the same format as for complex claims
        if isinstance(value, dict) and '_' in value:
            value = value.get('_')

        qual_claim = pywikibot.Claim(claim.repo, prop)
        qual_claim.setTarget(
            format_claim_value(qual_claim, value))
        return qual_claim
    else:
        raise ValueError(
            'Incorrectly formatted qualifier: {}'.format(value))


def format_claim_value(claim, value):
    """
    Reformat the internal claim as the relevant pywikibot object.

    @param claim: pywikibot.Claim to which value should be added
    @param value: str|dict encoding the value to be added
    @return: pywikibot representation of the claim value
    """
    repo = claim.repo
    if claim.type == 'wikibase-item':
        return pywikibot.ItemPage(repo, value)
    elif claim.type == 'commonsMedia':
        return pywikibot.FilePage(_get_commons(), value)
    elif claim.type == 'geo-shape':
        return pywikibot.WbGeoShape(
            pywikibot.Page(repo.geo_shape_repository(), value))
    elif claim.type == 'tabular-data':
        return pywikibot.WbTabularData(
            pywikibot.Page(repo.tabular_data_repository(), value))
    elif claim.type == 'monolingualtext':
        return pywikibot.WbMonolingualText(
            value.get('text'), value.get('lang'))
    elif claim.type == 'globe-coordinate':
        # set precision to the least precise of the values
        precision = max(
            coord_precision(value.get('lat')),
            coord_precision(value.get('lon')))
        return pywikibot.Coordinate(
            float(value.get('lat')),
            float(value.get('lon')),
            precision=precision)
    elif claim.type == 'quantity':
        if isinstance(value, dict):
            return pywikibot.WbQuantity(
                value.get('amount'),
                pywikibot.ItemPage(repo, value.get('unit')),
                site=repo)
        else:
            return pywikibot.WbQuantity(value, site=repo)
    elif claim.type == 'time':
        # note that Wikidata only supports precision down to day
        # as a result pywikibot.WbTime.fromTimestr will produce an incompatible
        # result for a fully qualified timestamp/timestr
        return iso_to_wbtime(value)

    # simple strings
    return value


def is_prop_key(key):
    """
    Check that a key is a valid property reference.

    @param key: key to test
    @return: if key is a valid property reference
    """
    return (
        common.is_str(key)
        and len(key) > 1
        and key[0] == 'P'
        and common.is_pos_int(key[1:]))


# copied from wikidataStuff.helpers.iso_to_wbtime
def iso_to_wbtime(date):
    """
    Convert ISO date string into WbTime object.

    Given an ISO date object (1922-09-17Z or 2014-07-11T08:14:46Z)
    this returns the equivalent WbTime object.

    Note that the time part is discarded as Wikidata doesn't support precision
    below a day.

    @param item: An ISO date string
    @type item: basestring
    @return: The converted result
    @rtype: pywikibot.WbTime
    """
    date = date[:len('YYYY-MM-DD')].split('-')
    if len(date) == 3 and all(common.is_int(x) for x in date):
        # 1921-09-17Z or 2014-07-11T08:14:46Z
        d = int(date[2])
        if d == 0:
            d = None
        m = int(date[1])
        if m == 0:
            m = None
        return pywikibot.WbTime(
            year=int(date[0]),
            month=m,
            day=d)
    elif len(date) == 1 and common.is_int(date[0][:len('YYYY')]):
        # 1921Z
        return pywikibot.WbTime(year=int(date[0][:len('YYYY')]))
    elif (len(date) == 2
            and all(common.is_int(x) for x in (date[0], date[1][:len('MM')]))):
        # 1921-09Z
        m = int(date[1][:len('MM')])
        if m == 0:
            m = None
        return pywikibot.WbTime(
            year=int(date[0]),
            month=m)

    # once here all interpretations have failed
    raise ValueError(
        'An invalid ISO-date string received: {}'.format(date))


def coord_precision(digits):
    """
    Guestimate the precision of a number based on the significant figures.

    This will assume the largest possible error in the case of integers.

    Requires that the number be given as a string (since sig. figs. may
    otherwise have been removed.)

    @param digits: the number to guestimate the precision from
    @type digits: str
    @return: precision
    @rtype: int
    """
    # @todo consider adding a is_number check
    if not common.is_str(digits):
        raise ValueError('coordinate must be provided as a string')
    integral, _, fractional = digits.partition(".")
    if fractional:
        return pow(10, -len(fractional))
    elif int(integral) == 0:
        return 1
    else:
        to_the = len(integral) - len(integral.rstrip('0'))
        # maximum imprecision allowed by Wikibase is 10
        return min(10, pow(10, to_the))
