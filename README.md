Pywikibot-SDC [![Build Status](https://travis-ci.org/lokal-profil/pywikibot-sdc.svg?branch=master)](https://travis-ci.org/lokal-profil/pywikibot-sdc)[![codecov.io Code Coverage](https://img.shields.io/codecov/c/github/lokal-profil/pywikibot-sdc.svg)](https://codecov.io/gh/lokal-profil/pywikibot-sdc)
=======

A library and command line application for the upload of Structured Data to
[Wikimedia Commons](https://commons.wikimedia.org) by making use of [Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot)
internals.

The library is geared towards supporting all features of Structured Data,
meaning all data types, *prominent* flags, multiple values per property,
multiple qualifiers per value etc. The library is however largely limited to
uploading new data, changing already existing statements is therefore not
currently supported.

This is primarily intended as a stop-gap measure until proper support is
implemented in Pywikibot [T223820](https://phabricator.wikimedia.org/T223820).

Heavily inspired by the following hack by Abbe98:
<https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python>


## To install

You can install `pywikibot-sdc` via `pip` using:
`pip install git+https://github.com/lokal-profil/pywikibot-sdc.git`

If it is your first time running Pywikibot you will also have to [set up a
`user-config.py` file](https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation#Configure_Pywikibot).

## Usage as a command line application

After installation Pywikibot-SDC can be used by simply calling `pywikibotsdc PATH`
from the command line. `PATH` is the path to a JSON file containing a
dictionary of file names (with or without the *File:*-prefix) and the associated
structured data to upload for each (in the format described [below](#sdc-in-data-format)).

For convenience if only a single file is updated the filename can be passed via
the `-f` flag and the JSON file should then only contain a single entry of the
[SDC in-data](#sdc-in-data-format).

To upload data to a file that already contains some structured data add the
`--strategy` argument to the call using one of the [named merge strategies](#merge-strategies).

Use the `-h` flag to see a full list of arguments. Note that the
[global Pywikibot arguments](https://www.mediawiki.org/wiki/Manual:Pywikibot/Global_Options)
are also supported.

## Usage as a library

In its most simple form call `sdc_upload.upload_single_sdc_data(file_page, sdc_data)`
with a `pywikibot.FilePage` object (or just the filename as a string) of a
newly uploaded file and the associated structured data to upload (in the format
described [below](#sdc-in-data-format)).

To upload data to a file that already contains some structured data add the
`strategy` argument to the call using one of the [named merge strategies](#merge-strategies).

While the command line application is limited to Wikimedia Commons (and Beta
Commons) the library should work for any MediaWiki instance.

## Merge strategies
There are five allowed strategies for merging the provided data with any
pre-existing data.
*   `None` (default): Only upload the data if no prior data exists.
*   `"New"`: Only upload the data if there is no prior data for any of the
        claims to be added. I.e. drop all data if any of the proposed Pids or
        caption languages are already present.
*   `"Add"`: Only upload those parts of the data for which there are no
        prior claims. I.e. drop any statements where the Pid or caption language
        is already present.
*   `"Blind"` (not generally recommended): Upload the data without regards to
        what is already there. May overwrite pre-existing captions and add
        duplicate statements.
*   `"Nuke"` (not generally recommended): Delete all prior data before
        uploading the new data. This should probably only be used if you
        uploaded the original data then spotted that it was wrong. Even then
        it's probably worth checking that the file hasn't been edited since
        the original upload.

## SDC in-data format

### Main structure

The in-data is expected as a json-like dictionary entry where the main keys are
`edit_summary`, `caption` and the *Pid*s of any claims that are added. All keys are optional.

Short example:
```json
{
    "edit_summary": "Uploading SDC data for newly uploaded image",
    "caption": {
        "en": "The Lund underground in moonlight.",
        "sv": "Lunds tunnelbana i månsken."
    },
    "P170": "Q123",
    "P180": "57"
}
```

For a more extensive example, suited for test-upload to [Beta Commons](https://commons.wikimedia.beta.wmflabs.org/),
see [docs/SDC_beta_commons_demo.json](docs/SDC_beta_commons_demo.json).

#### edit_summary

The `edit_summary` field is a simple text field used to provide an edit summary
when the data is uploaded. You can use `{count}` in the string to include the
number of statements added. This field is overridden if an edit_summary is passed
directly to `upload_single_sdc_data()`. If no edit summary is provided the
default one below is used:

`'Added {count} structured data statement(s) #pwbsdc'`

#### caption

The `caption` field takes the form of a simple dictionary where the keys are the
[language codes](https://www.wikidata.org/wiki/Help:Wikimedia_language_codes/lists/all)
and the values are plain text strings. This data is used to set the *caption*
(*label* in Wikibase lingo) of the file.

#### Pid claims

Pid/Property claims can be provided in up to three formats depending on the data
type of the property and if any qualifiers are provided.

The *simple claim format* can be used for any data type which can be provided as
a simple string and where the claim has no qualifiers or a *prominent* flag
(see *complex claim format* below).

```python
"Pid": "<string_value>"
```

The *complex claim format* can be used for any data type and additionally supports
qualifiers and and marking the claim as *prominent*.
```python
"Pid": {
    "_": <value>,
    "prominent": <bool>,
    "qualifier Pid_1": <qualifier_claim>,
    … more qualifiers
}
```

The format of `<value>` will depend on the data type. See the [Data type formats](#data-type-formats)
section below.

`prominent` is provided with a boolean value. If the key is not provided the *False*
is assumed. Setting the key to `True` sets the *prominent* flag on the claim
(*preferred* rank in Wikibase lingo).

The qualifier `<qualifier_claim>` supports the same three formats as the main claim
with the difference that the *complex claim format* does not support qualifiers
or the *prominent* flag and that the `<value>` can be provided either directly or
under the `_` key.

The *list claim format* can be used to supply multiple claims for the same Pid.
Both the simple and the complex claim formats are supported.
```python
"Pid": [
    "<string_value>",
    {
        "_": <value>,
        "prominent": <bool>
    }
]
```

Note that even when the `<value>` is numeric it must be provided as a string.

Any keys provided other than the ones described above (on the main level or
inside claims) are ignored.

### Data type formats

How a value is interpreted is based on the Property for which it is provided, the
expected data type is loaded from the underlying Wikibase installation itself.

This tool does not do any data validation so if you pass it rubbish which sort of
looks right you'll hopefully get complaints from Pywikibot or the MediaWiki API.

Wikibase supports [two special value types](https://www.mediawiki.org/wiki/Wikibase/DataModel/Primer#unknown),
"no value" and "unknown value" which can be used independently of the data type
of the property. To use one of these set the `<value>` to `_no_value_` or
`_some_value_`.

#### Simple string values

Many data types simply consist of a string value. This includes:
external identifiers, urls, math notation, musical notation and strings.

Examples:
*   String: `"Some text"`
*   Url: `"https://commons.wikimedia.org"`
*   Math: `"E = m c^2"`
*   External identifier: `"123-345"`
*   Musical notation: `"\drums {cb hh hh hc sn sn hh hh cb}"`

Additionally [items](#items), [Commons media](#commons-media), [tabular data](#tabular-data-and-geo-shapes),
[geo shapes](#tabular-data-and-geo-shapes), [dates](#point-in-time--date),
[monolingual texts](#monolingual-text), [quantities](#quantity) and [coordinates](#coordinates).
can be supplied as simple strings here. The assumptions made for this convenience
are described in the relevant sections below.

Note that *Musical notation* requires `pywikibot >= 5.5.0` and thus `python >= 3.5`.

#### Items

For this data types the [Qid](https://www.wikidata.org/wiki/Wikidata:Glossary#QID)
of the item is supplied as a simple string. The site on which the item is expected
is determined by the Wikibase installation. So on e.g. when adding structured data
to [Beta Commons](https://commons.wikimedia.beta.wmflabs.org/) the Qid is expected
on [Beta Wikidata](https://wikidata.beta.wmflabs.org/wiki/).

Example: `"Q42"`

#### Commons media

For this data type the page name is supplied as a simple string. The "File:" namespace
prefix of the page name is optional. The data page will always be expected to live
Wikimedia Commons, independently on which wiki your are writing structured data to.

Example values: `"File:Exempel_WIKI.jpg"` or `"Exempel_WIKI.jpg"`.

#### Tabular data and Geo shapes

For these two data types the page name is supplied as a simple string. The "Data:"
namespace prefix of the page name must be included. The site on which the pages must
live is determined by the Wikibase installation.

Note e.g. that for statements added to Beta Commons the Data pages are still expected
to live on "normal" Wikimedia Commons.

Example values: `"Data:DateI18n.tab"` or `"Data:Sweden.map"`.

#### Point in time / Date

A date can be provided either using an ISO_8601 string or a timestamp string. In
either case the largest precision that will be used is that of a day (due to Wikidata's
settings) so "2020-12-31" and "2020-12-31T23:59:59Z" will result in the same output.

Example values:
*   Fully qualified date: `"2020-12-31"` or `"2020-12-31T23:59:59Z"`
*   Year and month only: `"2020-12"`
*   Year only: `"2020"`

#### Monolingual text

Monolingual text requires the value be supplied either as a dictionary with the
keys `text` (a plain text string) and `lang` is the [language code](https://www.wikidata.org/wiki/Help:Monolingual_text_languages).

Example values:
```json
{
    "text": "Spider",
    "lang": "en"
}
```
```json
{
    "text": "Hämppi",
    "lang": "fit"
}
```

Or as a plain string in the format `text@lang` e.g. `"Spider@en"` or
`"Hämppi@fit"`. In this format the text cannot contain an `@` sign.

#### Quantity

Quantities can either be supplied with or without units. If no unit is to be used
then the value must be supplied as a plain string using "." as a decimal sign.

Example: `"123.4"`

If the quantity comes with a unit then it must be provided either as a dictionary
with the `amount` and `unit` keys or as a plain string in the format `amount@unit`.
The value of `unit` should be the Qid corresponding to the unit on the used
Wikibase installation.

Example (using [kg](https://www.wikidata.org/wiki/Q11570) as the unit):
```json
{
    "amount": "123.4",
    "unit": "Q11570"
}
```
or
`"123.4@Q11570"`.

#### Coordinates

Coordinates are supplied as as either a dictionary with `lat` and `lon` keys or
as a plain string in the format `lat_value@lat,lon_value@lon` or
`lon_value@lon,lat_value@lat`. The longitude and latitude values are provided as
strings in decimal format using "." as a decimal sign.
Example:
```json
{
    "lat": "55.708333",
    "lon": "13.199167"
}
```
or either `"55.708333@lat,13.199167@lon"` or `"13.199167@lon,55.708333@lat"`.

Note that the number of significant figures provided is used to determine the
precision of the coordinate. So `{"lat": "55.7", "lon": "13.2"}` will be interpreted
differently from `{"lat": "55.70", "lon": "13.2"}`.
