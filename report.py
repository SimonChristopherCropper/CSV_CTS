#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
------------------------     CSV_CTS()    --------------------------

This script takes a directory tree of CSV files, consolidates them,
transposes the data into a date series, references a known 'start date'
for each file and synchroises the CSVs based on this date.

The input files have at least an Id column (normally unique to the file),
a date column, and a response column (with values like Yes/No/Missing).

The known 'start date' for each Id is specified in a separate CSV file,
with an additional offset.

Many parameters can be specified in an associated configuration file.
This can specify the location of the input and output, and column names
and values.
By default this file is assumed to be named config.ini in the directory
this is executed in; but can be specified from the command line with -c.

See the "example" folder for an example configuration file and sample
data.

Programmed by Edward Ross 4 February 2017

"""

#***********************************************************************
#***********************     GPLv3 License      ************************
#***********************************************************************
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#***********************************************************************

import configparser
import fnmatch
import argparse
import os
import logging
import datetime

import pandas as pd
import numpy as np

def read_date_ones(path='date_ones.csv', id_col='ID', datecol='Date',
                   date_format='%Y-%m-%d'):
    """Reads the start date file from CSV at path into a Pandas dataframe

    * path: Path to file to read
    * id_col: Name of the column for identifiers
    * datecol: Name of the column for dates
    * date_format: String representing strptime format
    Returns: Data frame indexed on [id_col] with contents from path
    """
    data = pd.read_csv(path,
                       usecols=[id_col, datecol],
                       na_values=[''],
                       parse_dates=[datecol],
                       date_parser=lambda t: pd.Timestamp(datetime.datetime.strptime(t, date_format)),
                       index_col=[id_col]).rename(columns={datecol: 'date_one'})
    return data


def read_datafile(path, id_col='ID', datecol='Date', responsecol='Response',
                  date_format='%d/%m/%Y'):
    """Reads a data from CSV at path into a Pandas dataframe

    * path: Path to file to read
    * id_col: Name of the column for identifiers
    * datecol: Name of the column for dates
    * responsecol: Name of the column for responses (Y/N/M)
    * date_format: String representing strptime format
    Returns: Data frame with contents from path indexed on [id_col, datecol]
    """
    data = pd.read_csv(path,
                       usecols=[id_col, datecol, responsecol],
                       na_values=[''],
                       parse_dates=[datecol],
                       date_parser=lambda t: pd.Timestamp(datetime.datetime.strptime(t, date_format)),
                       index_col=[id_col, datecol])

    # Warn if there is more than one id in a file
    ids = set(data.index.get_level_values(level=id_col))
    if len(ids) > 1:
        logging.warn("File %s contains multiple ids: %s", path, ids)

    # Warn if there are missing dates
    dates = data.index.get_level_values(level=datecol)
    date_range = pd.date_range(start=min(dates), end=max(dates))
    missing_dates = set(date_range) - set(dates)
    if missing_dates:
        logging.warn("File %s is missing dates: %s", path,
                     ', '.join(d.strftime(date_format) for
                         d in sorted(missing_dates)))

    return data

def find_files(directory, filemask):
    """Finds all files one directory below directory matching filemask

    * directory: String representing path to search
    * filemask: String representing pattern to match (e.g. '*.csv)
                See fnmatch for the possibilities
    Returns: A list of path strings matching the filemask.

    Note that directories are never returned
    """
    output_paths = []
    for subdir in os.scandir(directory):
        if subdir.is_dir():
            # Log if there is no matching
            match = False
            for filename in os.scandir(subdir.path):
                if (filename.is_file() and
                    fnmatch.fnmatch(filename.name, filemask)):
                    match = True
                    output_paths.append(filename.path)
            if not match:
                logging.warn("No matching file in directory %s", subdir.name)
    return output_paths

def cli():
    """The command line interface"""
    parser = argparse.ArgumentParser(
        description='Consolidate, transpose and synchroise CSVs')
    parser.add_argument('-c', '--config',
                        help='Path to configuration INI file',
                        default="config.ini")

    args = parser.parse_args()

    # Read in the configuration file
    config = configparser.ConfigParser()
    config.read(args.config)

    outconfig = config['output']
    inconfig = config['input']
    dmconfig = config['datemap']

    # Clear the log and start logging
    with open(outconfig['log'], 'w'):
        pass
    logging.basicConfig(filename=outconfig['log'],level=logging.WARNING,
            format='%(levelname)s: %(message)s')

    # Column names in input files
    response_col = inconfig['response_col']
    id_col = inconfig['id_col']
    date_col = inconfig['date_col']
    # Input file directory, filemask and date format
    inpath = inconfig['path']
    input_filemask = inconfig['filemask']
    date_format = inconfig['date_format']

    response_map = config['responses']
    # B is used for Blank (no value)
    assert 'b' not in response_map.keys()
    assert 'B' not in response_map.values()
    response_map['b'] = 'B'
    responses = response_map.keys()

    # The 'start date' file
    date1_col = dmconfig['date_col']
    date1_offset = int(dmconfig['offset_days'])


    # Read in start date files
    date_map = read_date_ones(dmconfig['path'],
                              dmconfig['id_col'],
                              date1_col,
                              dmconfig['date_format'])
    date_map.index.name = id_col
    # Maximum number of days to report on
    max_days = int(dmconfig['max_days'])

    # Find all of the data files
    data_files = find_files(inpath, input_filemask)

    # Read all of the datafiles into pandas
    data_frames = []
    for data_file in data_files:
        try:
            frame = read_datafile(data_file, id_col,
                                  date_col,
                                  response_col,
                                  date_format)
            data_frames.append(frame)
            # Note the source file for error logging
            frame['source_file'] = data_file
        except (ValueError, KeyError) as e:
            logging.error("In file %s: %s", data_file, e)
    df = pd.concat(data_frames)

    # Mark the blank entries with B
    df = df.fillna('B')

    # Lower case all responses and remove whitespace
    df[response_col] = df[response_col].apply(lambda x: x.lower().strip())

    # Check for invalid Responses
    valid_response = (df[response_col].isin(responses) |
                      df[response_col].isnull())
    if not valid_response.all():
        logging.error("Removing invalid responses: %s",
                      df[~valid_response])
        df = df[valid_response]

    # Rename values to canonical
    df[response_col] = df[response_col].apply(lambda x: response_map[x])

    # Check for duplicate rows
    # Remove any duplicates
    duplicates = df.index.duplicated(False)
    if duplicates.any():
        logging.error("Removing duplicate rows: \n%s", df[duplicates])

        df = df[~duplicates]

    # Calculate the time delta for each id from start_date - date1_offset
    df = df.join(date_map, how='left')

    # Check whether any start dates are missing
    missing_starts = set(df[df['date_one'].isnull()].index.get_level_values(0))
    if missing_starts:
        logging.warn("Missing start dates for ids %s",
                     ', '.join(str(ids) for ids in sorted(missing_starts)))


    df['delta'] = pd.Series(df.index.map(lambda x: x[1]), df.index) - df['date_one']
    df['delta'] = df['delta'] - pd.Timedelta(days=date1_offset)

    # Filter down to days between 0 and max_dates
    df = df[df['delta'] >= pd.Timedelta(days=0)]
    df = df[df['delta'] < pd.Timedelta(days=max_days)]

    # Generate the names for pivoting on
    df['days'] = (
            df['delta']
           .apply(lambda x: x.days + 1))
    df['pivot'] = (
            df['days']
            # 0 pad the numbers to ensure the order of the columns is correct
           .apply(lambda x: 'Day{:0{prec}d}'.format(x, prec=len(str(max_days))))
           )


    # Perform the pivot
    pivot = df.reset_index().pivot(index=id_col,
                                   values=response_col,
                                   columns='pivot')

    # Calculate the first date of response
    first_days = df.groupby(level=0)['days'].min()
    first_days.name = 'First_Response'

    # Calculate the first date of first Yes response
    first_yes = df[df[response_col] == 'Y'].groupby(level=0)['days'].min()
    first_yes.name = 'First_Yes'

    # Calculate the total number of days for which there is a respone
    days = (
        (df.groupby(level=0)['delta'].max() -
         df.groupby(level=0)['delta'].min())
        .apply(lambda x: x.days + 1))
    days.name = 'Total_Period'


    # Calculate the number other values: Number of Y/N/M
    names = config['response_names']
    # Upper case keys (Config INI files keys are always lower case)
    names = {k.upper(): 'Total_%s' % v for k, v in names.items()}
    tally = (
        df
        .groupby(level=0)[response_col]
        .value_counts()
        .rename(columns={response_col : 'count'})
        .reset_index()
        .pivot(values=0, columns=response_col, index=id_col)
        .fillna(0)
        .astype(np.int32)
        .rename(columns=names)
        )

    result = pivot.join(days).join(tally).join(first_days).join(first_yes)


    result.to_csv(outconfig['path'])

if __name__ == '__main__':
    cli()
