#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Entry point for uploading Structured Data to Commons."""
from __future__ import unicode_literals

import argparse
import json
from builtins import open
from pathlib import Path

import pywikibot

import pywikibotsdc.sdc_upload as sdc_upload
from pywikibotsdc.sdc_exception import SdcException


def _load_file(filename):
    """
    Open and read a JSON file containing Structured Data.

    @param filename: the file to open
    """
    with open(filename, 'r') as f:
        return json.load(f)


def _load_site(use_beta):
    """
    Load the pywikibot.Site object of target Commons site.

    @param use_beta: use Beta Commons rather than Wikimedia Commons
    """
    if use_beta:
        return pywikibot.Site('beta', 'commons')
    else:
        return pywikibot.Site('commons', 'commons')


def handle_args(argv=None):
    """
    Parse and handle command line arguments.

    Also parses any global pywikibot arguments:
    https://www.mediawiki.org/wiki/Manual:Pywikibot/Global_Options

    @param argv: arguments to parse. Defaults to sys.argv[1:].
    @return: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description='Upload Structured Data to Commons.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Also supports any global pywikibot arguments (other than -help). '
            'Most importantly:\n'
            '  -simulate             don\'t write to database\n'
            '  -dir:PATH             path to directory in which to look for '
            'user-config.py')
    )
    parser.add_argument(
        'data', action='store', metavar='PATH', type=Path,
        help='path to file containing Structured Data in json format')
    parser.add_argument(
        '--strategy', action='store', choices=sdc_upload.STRATEGIES,
        help='merge strategy to use')
    parser.add_argument(
        '--summary', action='store',
        help='edit summary to use instead of default')
    parser.add_argument(
        '-n', '--null_edit', action='store_true',
        help='perform a null_edit to the file page after uploading the data')
    parser.add_argument(
        '-f', '--filename', action='store',
        help=('Commons filename to which Structured Data corresponds '
              '(only used when data covers a single file and the filename is '
              'omitted from the file)'))
    parser.add_argument(
        '-b', '--beta', action='store_true',
        help='upload to Beta Commons rather than Wikimedia Commons')

    # first pass args to argparse, then to pywikibot
    # while more work than parser.parse_args(pywikibot.handle_args(argv))
    # it gives argparse control of -help
    args, unknown_args = parser.parse_known_args(argv)
    if unknown_args:
        unknown_args = pywikibot.handle_args(unknown_args)
        if unknown_args:
            parser.error(
                'unrecognized arguments: {}'.format(' '.join(unknown_args)))

    return args


def main():
    """Run main process."""
    args = handle_args()
    sdc_data = _load_file(args.data)
    site = _load_site(args.beta)

    # run
    if args.filename:
        try:
            num = sdc_upload.upload_single_sdc_data(
                args.filename, sdc_data, target_site=site,
                strategy=args.strategy, summary=args.summary,
                null_edit=args.null_edit)
        except SdcException as se:
            pywikibot.output('{0} - {1}'.format(args.filename, se.log))
        else:
            pywikibot.output(
                '{0} - Successfully uploaded with {1} statements'.format(
                    args.filename, num))
    else:
        total = {'files': 0, 'num': 0}
        for filename, data in sdc_data.items():
            try:
                num = sdc_upload.upload_single_sdc_data(
                    filename, data, target_site=site, strategy=args.strategy,
                    summary=args.summary, null_edit=args.null_edit)
            except SdcException as se:
                pywikibot.output('{0} - {1}'.format(filename, se.log))
            else:
                total['files'] += 1
                total['num'] += num
                pywikibot.output(
                    '{0} - Successfully uploaded with {1} statements'.format(
                        filename, num))
        pywikibot.output(
            'Successfully uploaded {num} statements to {files} files'.format(
                **total))


if __name__ == "__main__":
    main()
