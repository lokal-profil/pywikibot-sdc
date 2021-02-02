#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for helpers.py."""
from __future__ import unicode_literals

import unittest
from copy import deepcopy

import mock

import pywikibot

from pywikibotsdc.sdc_exception import SdcException
from pywikibotsdc.sdc_support import (
    _get_existing_structured_data,
    coord_precision,
    is_prop_key,
    iso_to_wbtime,
    merge_strategy
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
        self.set_mock_response_data(data)
        result = _get_existing_structured_data(self.mid, self.mock_site)
        self.assertEquals(result, data)

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
        self.assertEquals(result, data)

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
        self.assertEquals(result, data)


class TestMergeStrategy(unittest.TestCase):
    """Test the merge_strategy method."""

    def setUp(self):
        self.mid = 'M123'
        self.mock_site = mock.MagicMock()

        self.base_sdc = {
            "caption": {
                "en": "Foo",
                "sv": "Bar",
            },
            "P123": "Q456",
        }

        patcher = mock.patch(
            'pywikibotsdc.sdc_support._get_existing_structured_data')
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
        for strategy in (None, 'new', 'blind', 'squeeze', 'foo'):
            input_data = deepcopy(self.base_sdc)
            r = merge_strategy(
                self.mid, self.mock_site, input_data, strategy)
            self.assertIsNone(r)
            self.assertEquals(input_data, self.base_sdc)

    def test_merge_strategy_unknown_strategy_some_data_raises(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        with self.assertRaises(ValueError) as ve:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'foo')
        self.assertTrue(
            str(ve.exception).startswith('The `strategy` parameter'))
        self.assertTrue('foo' in str(ve.exception))

    def test_merge_strategy_none_strategy_some_non_conflicting_data(self):
        self.set_mock_response_data(captions={'fr': 'hello'})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, None)
        self.assertEquals(se.exception.data, 'pre-existing sdc-data')

    def test_merge_strategy_new_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'New')
        self.assertEquals(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_new_strategy_some_conflicting_label_data(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertEquals(
            se.exception.data, 'conflicting pre-existing sdc-data')

    def test_merge_strategy_new_strategy_some_conflicting_claim_data(self):
        self.set_mock_response_data(claims={'P123': [{}]})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertEquals(
            se.exception.data, 'conflicting pre-existing sdc-data')

    def test_merge_strategy_blind_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Blind')
        self.assertEquals(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_blind_strategy_some_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'sv': 'hello'}, claims={'P123': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Blind')
        self.assertEquals(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_squeeze_strategy_some_non_conflicting_data(self):
        input_data = deepcopy(self.base_sdc)
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        r = merge_strategy(self.mid, self.mock_site, input_data, 'Squeeze')
        self.assertEquals(input_data, self.base_sdc)
        self.assertIsNone(r)

    def test_merge_strategy_squeeze_strategy_some_conflicting_data(self):
        expected_data = deepcopy(self.base_sdc)
        expected_data['caption'].pop('sv')
        expected_data.pop('P123')
        self.set_mock_response_data(
            captions={'sv': 'hello', 'fr': 'hi'}, claims={'P123': [{}]})
        r = merge_strategy(self.mid, self.mock_site, self.base_sdc, 'Squeeze')
        self.assertEquals(self.base_sdc, expected_data)
        self.assertEquals(r, {'pids': {'P123'}, 'langs': {'sv'}})

    def test_merge_strategy_squeeze_strategy_all_conflicting_data(self):
        self.set_mock_response_data(
            captions={'sv': 'hello', 'en': 'hi'}, claims={'P123': [{}]})
        with self.assertRaises(SdcException) as se:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'Squeeze')
        self.assertEquals(
            se.exception.data, 'all conflicting pre-existing sdc-data')
