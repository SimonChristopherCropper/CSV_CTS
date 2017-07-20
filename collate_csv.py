"""
------------------------     Collate_CSV    --------------------------

This script collates all the CSV files within a directory tree that
matches a particular mask and puts the data into a single file for
review so errors and inconsistencies can be identified.

Programmed by Simon Cropper 19 July 2017

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
import argparse
import pandas as pd
import os.path
import os

def cli():
    """
    Main Commandline Interface
    """
    parser = argparse.ArgumentParser(
        description='Collate all CSVs in a directory tree that matches a particular file mask')
    parser.add_argument('-c', '--config',
                        help='Path to configuration INI file',
                        default="config.ini")
    args = parser.parse_args()

    # Read in the configuration file
    config = configparser.ConfigParser()
    config.read(args.config)

    # Get program specific data from config file
    collate_config = config['collate_csv']
    working_dir = collate_config['workingdir']
    filemask = collate_config['filemask']
    outputfile = collate_config['outputfile']
    columnlist = collate_config['columnlist'].split(',')

    # Initialize list of files
    file_list = []
    
    # Walk directory tree finding all files
    for root, dirs, files in os.walk(working_dir):
        for filename in files:
            if filename.endswith(filemask):
                file_list.append(os.path.join(root, filename))
    
    # Collate all the data
    df_list = [pd.read_csv(file) for file in file_list]

    # If you got somethingm concatenate and save to CSV
    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        final_df[columnlist].to_csv(os.path.join(working_dir, outputfile), index=False)

if __name__ == '__main__':
    cli()
