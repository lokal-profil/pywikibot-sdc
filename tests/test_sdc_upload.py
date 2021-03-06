#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for sdc_upload.py."""
from __future__ import unicode_literals

import unittest
from copy import deepcopy

import mock

import pywikibot

from pywikibotsdc.sdc_exception import SdcException
from pywikibotsdc.sdc_upload import (
    _get_existing_structured_data,
    coord_precision,
    format_claim_value,
    format_sdc_payload,
    is_prop_key,
    iso_to_wbtime,
    merge_strategy,
    upload_single_sdc_data
)


class TestIsPropKey(unittest.TestCase):
    """Test the is_prop_key method."""

    def test_is_prop_key_empty_fail(self):
        self.assertFalse(is_prop_key(''))

    def test_is_prop_key_short_pid(self):
        self.assertTrue(is_prop_key('P1'))

    def test_is_prop_key_long_pid(self):
        self.assertTrue(is_prop_key('P968434'))

    def test_is_prop_key_qid_fail(self):
        self.assertFalse(is_prop_key('Q42'))

    def test_is_prop_key_p_fail(self):
        self.assertFalse(is_prop_key('P'))

    def test_is_prop_key_int_fail(self):
        self.assertFalse(is_prop_key('42'))


class TestIsoToWbtime(unittest.TestCase):
    """Test the iso_to_wbtime method."""

    def test_iso_to_wbtime_empty_raises(self):
        with self.assertRaises(ValueError):
            iso_to_wbtime('')

    def test_iso_to_wbtime_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            iso_to_wbtime('late 1980s')

    def test_iso_to_wbtime_date_and_time(self):
        date = '2014-07-11T08:14:46Z'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_date_and_timezone(self):
        date = '2014-07-11Z'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_date(self):
        date = '2014-07-11'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_and_timezone(self):
        date = '2014Z'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year(self):
        date = '2014'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_month_and_timezone(self):
        date = '2014-07Z'
        expected = pywikibot.WbTime(year=2014, month=7)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_month(self):
        date = '2014-07'
        expected = pywikibot.WbTime(year=2014, month=7)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_month_zero_day(self):
        date = '2014-07-00'
        expected = pywikibot.WbTime(year=2014, month=7)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_zero_month_zero_day(self):
        date = '2014-00-00'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_zero_month(self):
        date = '2014-00'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)


class TestCoordPrecision(unittest.TestCase):
    """Test the coord_precision method."""

    def test_coord_precision_empty_raises(self):
        with self.assertRaises(ValueError):
            coord_precision('')

    def test_coord_precision_float_raises(self):
        with self.assertRaises(ValueError):
            coord_precision(0.200)

    def test_coord_precision_dms_raises(self):
        with self.assertRaises(ValueError):
            coord_precision("15°10'15''")

    def test_coord_precision_zero(self):
        self.assertEqual(coord_precision('0'), 1)

    def test_coord_precision_decimal_zero(self):
        self.assertEqual(coord_precision('0.0'), 0.1)

    def test_coord_precision_one(self):
        self.assertEqual(coord_precision('1'), 1)

    def test_coord_precision_decimal_one(self):
        self.assertEqual(coord_precision('1.0'), 0.1)

    def test_coord_precision_padded_one(self):
        self.assertEqual(coord_precision('01'), 1)

    def test_coord_precision_ten(self):
        self.assertEqual(coord_precision('20'), 10)

    def test_coord_precision_hundred_hits_max(self):
        self.assertEqual(coord_precision('300'), 10)

    def test_coord_precision_hundred_respects_last_digit(self):
        self.assertEqual(coord_precision('301'), 1)

    def test_coord_precision_no_integer_part(self):
        self.assertEqual(coord_precision('0.2'), 0.1)

    def test_coord_precision_no_integer_part_explicit_sig_fig(self):
        self.assertEqual(coord_precision('0.200'), 0.001)

    def test_coord_precision_long_digit(self):
        self.assertEqual(coord_precision('12.34456'), 0.00001)


class TestGetExistingStructuredData(unittest.TestCase):
    """
    Test the _get_existing_structured_data method.

    Testing focuses on determining if any data is present based on a handful of
    real responses.
    """

    def setUp(self):
        self.mid = 'M102303'
        # specing as a pywikibot.Site object makes overriding _simple_request
        # needlessly convoluted
        self.mock_site = mock.MagicMock()

    def set_mock_response_data(self, sdc):
        """Set the mock response of the API call."""
        data = {
            'entities': {
                self.mid: sdc
            },
            'success': 1
        }
        self.mock_site._simple_request.return_value.submit.return_value = data

    def test_get_existing_structured_data_never_existed_none(self):
        data = {'id': 'M102303', 'missing': ''}
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertIsNone(result)

    def test_get_existing_structured_data_data_deleted_none(self):
        data = {
            'pageid': 102303, 'ns': 6,
            'title': 'File:John Hamilton-Buchanan, Vanity Fair, 1910-09-07.jpg',  # noqa
            'lastrevid': 229666, 'modified': '2021-01-30T21:48:18Z',
            'type': 'mediainfo', 'id': 'M102303', 'labels': {},
            'descriptions': {}, 'statements': []}
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertIsNone(result)

    def test_get_existing_structured_data_has_caption(self):
        data = {
            'pageid': 102303, 'ns': 6,
            'title': 'File:John Hamilton-Buchanan, Vanity Fair, 1910-09-07.jpg',  # noqa
            'lastrevid': 229665, 'modified': '2021-01-30T21:47:25Z',
            'type': 'mediainfo', 'id': 'M102303',
            'labels': {'en': {'language': 'en', 'value': 'hello'}},
            'descriptions': {}, 'statements': []}
        expected = data.copy()
        expected['statements'] = {}
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertEqual(result, expected)

    def test_get_existing_structured_data_has_statement(self):
        data = {
            'pageid': 102303, 'ns': 6,
            'title': 'File:John Hamilton-Buchanan, Vanity Fair, 1910-09-07.jpg',  # noqa
            'lastrevid': 229664, 'modified': '2021-01-30T21:46:37Z',
            'type': 'mediainfo', 'id': 'M102303', 'labels': {},
            'descriptions': {},
            'statements': {'P245962': [{'mainsnak': {
                'snaktype': 'value', 'property': 'P245962',
                'hash': 'e5b20128816e43e6720cf8cd9e7a7eaa7bb67b98',
                'datavalue': {
                    'value': {
                        'entity-type': 'item', 'numeric-id': 123,
                        'id': 'Q123'},
                    'type': 'wikibase-entityid'}},
                'type': 'statement',
                'id': 'M102303$0c401e5f-48b3-c80d-b9d6-569fa34b9f51',
                'rank': 'normal'}]}}
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertEqual(result, data)

    def test_get_existing_structured_data_has_caption_and_statement(self):
        data = {
            'pageid': 102303, 'ns': 6,
            'title': 'File:John Hamilton-Buchanan, Vanity Fair, 1910-09-07.jpg',  # noqa
            'lastrevid': 229664, 'modified': '2021-01-30T21:46:37Z',
            'type': 'mediainfo', 'id': 'M102303',
            'labels': {'en': {'language': 'en', 'value': 'hello'}},
            'descriptions': {},
            'statements': {'P245962': [{'mainsnak': {
                'snaktype': 'value', 'property': 'P245962',
                'hash': 'e5b20128816e43e6720cf8cd9e7a7eaa7bb67b98',
                'datavalue': {
                    'value': {
                        'entity-type': 'item', 'numeric-id': 123,
                        'id': 'Q123'},
                    'type': 'wikibase-entityid'}},
                'type': 'statement',
                'id': 'M102303$0c401e5f-48b3-c80d-b9d6-569fa34b9f51',
                'rank': 'normal'}]}}
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertEqual(result, data)


class TestMergeStrategy(unittest.TestCase):
    """Test the merge_strategy method."""

    def setUp(self):
        self.mid = 'M123'
        self.mock_site = mock.MagicMock(spec=pywikibot.Site)

        self.base_sdc = {
            "caption": {
                "en": "Foo",
                "sv": "Bar",
            },
            "P123": "Q456",
        }

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload._get_existing_structured_data')
        self.mock__get_existing_structured_data = patcher.start()
        self.mock__get_existing_structured_data.return_value = None
        self.addCleanup(patcher.stop)

    def set_mock_response_data(self, captions=None, claims=None):
        """Set the mock response of the API call."""
        data = {
            'labels': captions or {},
            'statements': claims or {}
        }
        self.mock__get_existing_structured_data.return_value = data

    def test_merge_strategy_any_strategy_no_data(self):
        # Any strategy, even an unknown one, should pass if no prior data.
        for strategy in (None, 'new', 'blind', 'add', 'nuke', 'foo'):
            input_data = deepcopy(self.base_sdc)
            r = merge_strategy(
                self.mid, self.mock_site, input_data, strategy)
            self.assertIsNone(r, msg=strategy)
            self.assertEqual(input_data, self.base_sdc, msg=strategy)

    def test_merge_strategy_unknown_strategy_some_data_raises(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        with self.assertRaises(ValueError) as ve:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'foo')
        self.assertTrue(
            str(ve.exception).startswith('The `strategy` parameter'))
        self.assertTrue('Foo' in str(ve.exception))

    def test_merge_strategy_none_strategy_some_non_conflicting_data(self):
        self.set_mock_response_data(captions={'fr': 'hello'})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, None)
        self.assertEqual(se.exception.data, 'pre-existing sdc-data')

    def test_merge_strategy_new_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'New')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_new_strategy_some_conflicting_label_data(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertEqual(
            se.exception.data, 'conflicting pre-existing sdc-data')

    def test_merge_strategy_new_strategy_some_conflicting_claim_data(self):
        self.set_mock_response_data(claims={'P123': [{}]})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertEqual(
            se.exception.data, 'conflicting pre-existing sdc-data')

    def test_merge_strategy_blind_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Blind')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_blind_strategy_some_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'sv': 'hello'}, claims={'P123': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Blind')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_add_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Add')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_add_strategy_some_conflicting_data(self):
        expected_data = deepcopy(self.base_sdc)
        expected_data['caption'].pop('sv')
        expected_data.pop('P123')
        self.set_mock_response_data(
            captions={'sv': 'hello', 'fr': 'hi'}, claims={'P123': [{}]})
        r = merge_strategy(self.mid, self.mock_site, self.base_sdc, 'Add')
        self.assertEqual(self.base_sdc, expected_data)
        self.assertEqual(r, {'pids': {'P123'}, 'langs': {'sv'}})

    def test_merge_strategy_add_strategy_all_conflicting_data(self):
        self.set_mock_response_data(
            captions={'sv': 'hello', 'en': 'hi'}, claims={'P123': [{}]})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'Add')
        self.assertEqual(
            se.exception.data, 'all conflicting pre-existing sdc-data')

    def test_merge_strategy_nuke_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Nuke')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_nuke_strategy_some_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'sv': 'hello'}, claims={'P123': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Nuke')
        self.assertEqual(input_data, self.base_sdc)
        self.assertIsNone(r)


class TestUploadSingleSdcData(unittest.TestCase):
    """Test the upload_single_sdc_data method."""

    def setUp(self):
        self.mock_file_page = mock.MagicMock(spec=pywikibot.FilePage)
        self.mock_pwb_touch = self.mock_file_page.touch

        self.base_sdc = {
            "caption": {
                "en": "Foo",
                "sv": "Bar",
            },
            "P123": "Q456",
        }

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.merge_strategy')
        self.mock_merge_strategy = patcher.start()
        self.mock_merge_strategy.return_value = None
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.format_sdc_payload')
        self.mock_format_sdc_payload = patcher.start()
        self.mock_format_sdc_payload.return_value = {}
        self.addCleanup(patcher.stop)

        # mock out anything communicating with live platforms
        patcher = mock.patch(
            'pywikibotsdc.sdc_upload._submit_data')
        self.mock__submit_data = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload._get_commons')
        self.mock__get_commons = patcher.start()
        self.mock__get_commons.return_value = mock.MagicMock(spec=pywikibot.Site)  # noqa:E501
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.get_media_identifier')
        self.mock_get_media_identifier = patcher.start()
        self.mock_get_media_identifier.return_value = 'M123'
        self.addCleanup(patcher.stop)

    def test_upload_single_sdc_data_handle_upload_error(self):
        self.mock__submit_data.side_effect = pywikibot.data.api.APIError('mock error', '')  # noqa:E501
        with self.assertRaises(SdcException) as se:
            upload_single_sdc_data(self.mock_file_page, self.base_sdc)
        self.assertTrue('mock error' in se.exception.log)
        self.mock_pwb_touch.assert_not_called()

    def test_upload_single_sdc_data_handle_sdc_formatting_error(self):
        self.mock_format_sdc_payload.side_effect = ValueError('mock error', '')
        with self.assertRaises(SdcException) as se:
            upload_single_sdc_data(self.mock_file_page, self.base_sdc)
        self.assertTrue('mock error' in se.exception.log)
        self.mock__submit_data.assert_not_called()
        self.mock_pwb_touch.assert_not_called()

    def test_upload_single_sdc_data_any_non_nuke_does_not_trigger_clear(self):
        strategies = (None, 'new', 'blind', 'add', 'foo')
        for strategy in strategies:
            upload_single_sdc_data(
                self.mock_file_page, self.base_sdc, strategy=strategy)
        self.assertEqual(self.mock__submit_data.call_count, len(strategies))
        for num, call in enumerate(self.mock__submit_data.call_args_list):
            payload = call[0][1]
            self.assertEqual(payload.get('clear', 0), 0, msg=strategies[num])

    def test_upload_single_sdc_data_nuke_triggers_clear(self):
        upload_single_sdc_data(
            self.mock_file_page, self.base_sdc, strategy="Nuke")
        self.mock__submit_data.assert_called_once()
        payload = self.mock__submit_data.call_args[0][1]
        self.assertEqual(payload.get('clear', 0), 1)
        self.mock_pwb_touch.assert_not_called()

    def test_upload_single_sdc_data_null_edit_triggers_touch(self):
        upload_single_sdc_data(
            self.mock_file_page, self.base_sdc, null_edit=True)
        self.mock__submit_data.assert_called_once()
        self.mock_pwb_touch.assert_called()

    def test_upload_single_sdc_data_no_null_edit_no_touch(self):
        upload_single_sdc_data(
            self.mock_file_page, self.base_sdc, null_edit=False)
        self.mock__submit_data.assert_called_once()
        self.mock_pwb_touch.assert_not_called()

    def test_upload_single_sdc_data_null_edit_T275981_adds_explanation(self):
        self.mock_pwb_touch.side_effect = pywikibot.i18n.TranslationError('Fo')
        with self.assertRaises(pywikibot.i18n.TranslationError):
            upload_single_sdc_data(
                self.mock_file_page, self.base_sdc, null_edit=True)
        self.mock__submit_data.assert_called_once()
        self.mock_pwb_touch.assert_called()


class TestFormatSdcPayload(unittest.TestCase):
    """Test the format_sdc_payload method."""

    def setUp(self):
        self.mock_site = mock.MagicMock(spec=pywikibot.Site)

        self.base_sdc = {
            "caption": {
                "en": "Foo",
                "sv": "Bar",
            },
        }

        # mock out anything communicating with live platforms
        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.is_prop_key')
        self.mock_is_prop_key = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.make_claim')
        self.mock_make_claim = patcher.start()
        self.addCleanup(patcher.stop)

    def test_format_sdc_payload_error_on_no_data(self):
        with self.assertRaises(ValueError):
            format_sdc_payload(self.mock_site, {})

    def test_format_sdc_payload_error_on_just_unknown(self):
        self.mock_is_prop_key.return_value = False
        with self.assertRaises(ValueError) as ve:
            format_sdc_payload(self.mock_site, {'bar': 'foo'})
        self.assertTrue('bar' in str(ve.exception))
        self.mock_make_claim.assert_not_called()

    def test_format_sdc_payload_error_on_just_summary(self):
        with self.assertRaises(ValueError) as ve:
            format_sdc_payload(self.mock_site, {'summary': 'foo'})
        self.assertTrue('summary' in str(ve.exception))
        self.mock_is_prop_key.assert_not_called()
        self.mock_make_claim.assert_not_called()

    def test_format_sdc_payload_quick_return_on_just_caption(self):
        expected_data = {
            'labels': {
                'en': {'language': 'en', 'value': 'Foo'},
                'sv': {'language': 'sv', 'value': 'Bar'}
            }
        }
        data = format_sdc_payload(self.mock_site, self.base_sdc)
        self.mock_is_prop_key.assert_not_called()
        self.mock_make_claim.assert_not_called()
        self.assertEqual(data, expected_data)


class TestFormatClaimValue(unittest.TestCase):
    """Test the format_claim_value method."""

    def setUp(self):
        # Actually fully mocking a site object is a sisyphean task, so point it
        # to a site where we can at least not do any harm
        self.mock_site = pywikibot.Site('beta', 'wikidata')
        self.mock_commons = pywikibot.Site('beta', 'commons')

        self.mock_claim = mock.MagicMock(spec=pywikibot.Claim)
        type(self.mock_claim).repo = mock.PropertyMock(
            return_value=self.mock_site)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload._get_commons')
        self.mock__get_commons = patcher.start()
        self.mock__get_commons.return_value = self.mock_commons
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.iso_to_wbtime')
        self.mock_iso_to_wbtime = patcher.start()
        self.mock_iso_to_wbtime.return_value = 'iso_to_wbtime return value'
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'pywikibotsdc.sdc_upload.coord_precision')
        self.mock_coord_precision = patcher.start()
        self.mock_coord_precision.return_value = 0.1
        self.addCleanup(patcher.stop)

    def set_claim_type(self, val):
        type(self.mock_claim).type = mock.PropertyMock(return_value=val)

    def test_format_claim_value_item(self):
        self.set_claim_type('wikibase-item')
        expected_data = pywikibot.ItemPage(self.mock_site, 'Q123')

        data = format_claim_value(self.mock_claim, 'Q123')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_filepage_w_namespace(self):
        self.set_claim_type('commonsMedia')
        expected_data = pywikibot.FilePage(self.mock_commons, 'File:Foo.jpg')

        data = format_claim_value(self.mock_claim, 'File:Foo.jpg')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_filepage_wo_namespace(self):
        self.set_claim_type('commonsMedia')
        expected_data = pywikibot.FilePage(self.mock_commons, 'File:Foo.jpg')

        data = format_claim_value(self.mock_claim, 'Foo.jpg')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_monolingual(self):
        self.set_claim_type('monolingualtext')
        expected_data = pywikibot.WbMonolingualText('Foo', 'sv')

        data = format_claim_value(
            self.mock_claim, {'text': 'Foo', 'lang': 'sv'})
        self.assertEqual(data, expected_data)

    def test_format_claim_value_monolingual_oneliner(self):
        self.set_claim_type('monolingualtext')
        expected_data = pywikibot.WbMonolingualText('Foo', 'sv')

        data = format_claim_value(self.mock_claim, 'Foo@sv')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_unitless_quantity(self):
        self.set_claim_type('quantity')
        expected_data = pywikibot.WbQuantity(12.34, site=self.mock_site)

        data = format_claim_value(self.mock_claim, '12.34')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_unitfull_quantity(self):
        self.set_claim_type('quantity')
        unit = pywikibot.ItemPage(self.mock_site, 'Q123')
        expected_data = pywikibot.WbQuantity(12.34, unit, site=self.mock_site)

        data = format_claim_value(
            self.mock_claim, {'amount': '12.34', 'unit': 'Q123'})
        self.assertEqual(data, expected_data)

    def test_format_claim_value_unitfull_quantity_oneliner(self):
        self.set_claim_type('quantity')
        unit = pywikibot.ItemPage(self.mock_site, 'Q123')
        expected_data = pywikibot.WbQuantity(12.34, unit, site=self.mock_site)

        data = format_claim_value(self.mock_claim, '12.34@Q123')
        self.assertEqual(data, expected_data)

    def test_format_claim_value_time(self):
        self.set_claim_type('time')
        expected_data = 'iso_to_wbtime return value'

        data = format_claim_value(self.mock_claim, '2021-03-02')
        self.assertEqual(data, expected_data)
        self.mock_iso_to_wbtime.assert_called_once_with('2021-03-02')

    def test_format_claim_value_coord(self):
        self.set_claim_type('globe-coordinate')
        expected_data = pywikibot.Coordinate(55.7, 13.19, precision=0.1)

        data = format_claim_value(
            self.mock_claim, {'lat': '55.70', 'lon': '13.19'})
        self.assertEqual(data, expected_data)
        self.assertEqual(self.mock_coord_precision.call_count, 2)

    def test_format_claim_value_coord_use_lesser_precision(self):
        self.set_claim_type('globe-coordinate')
        expected_data = pywikibot.Coordinate(55.7, 13.19, precision=1)

        self.mock_coord_precision.side_effect = [0.1, 1]
        data = format_claim_value(
            self.mock_claim, {'lat': '55.70', 'lon': '13.19'})
        self.assertEqual(data, expected_data)

        # ensure order of precisions are irrelevant
        self.mock_coord_precision.side_effect = [1, 0.1]
        data = format_claim_value(
            self.mock_claim, {'lat': '55.70', 'lon': '13.19'})
        self.assertEqual(data, expected_data)

    def test_format_claim_value_coord_oneliner_lat_first(self):
        self.set_claim_type('globe-coordinate')
        expected_data = pywikibot.Coordinate(55.7, 13.19, precision=0.1)

        data = format_claim_value(self.mock_claim, '55.70@lat,13.19@lon')
        self.assertEqual(data, expected_data)
        self.assertEqual(self.mock_coord_precision.call_count, 2)

    def test_format_claim_value_coord_oneliner_lon_first(self):
        self.set_claim_type('globe-coordinate')
        expected_data = pywikibot.Coordinate(55.7, 13.19, precision=0.1)

        data = format_claim_value(self.mock_claim, '13.19@lon,55.70@lat')
        self.assertEqual(data, expected_data)
        self.assertEqual(self.mock_coord_precision.call_count, 2)

    def test_format_claim_value_coord_oneliner_allow_space(self):
        self.set_claim_type('globe-coordinate')
        expected_data = pywikibot.Coordinate(55.7, 13.19, precision=0.1)

        data = format_claim_value(self.mock_claim, '55.70@lat, 13.19@lon')
        self.assertEqual(data, expected_data)
        self.assertEqual(self.mock_coord_precision.call_count, 2)

    def test_format_claim_value_strings(self):
        string_types = ('string', 'url', 'math', 'external-id',
                        'musical-notation', 'unknown')
        for st in string_types:
            self.set_claim_type('st')
            expected_data = 'foobar'

            data = format_claim_value(self.mock_claim, 'foobar')
            self.assertEqual(data, expected_data)
