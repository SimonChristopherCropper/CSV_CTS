------------------------     CSV_CTS()    --------------------------

The main script, report.py takes a directory tree of CSV files,
consolidates them, transposes the data into a date series, references a
known 'start date' for each file and synchroises the CSVs based on this
date. 

It outputs an output file with the results, and a log file with any
issues found while processing files.

Requires Python 3; should run on most major operating systems.

The input files have at least an Id column (normally unique to the file),
a date column, and a response column (with values like Yes/No/Missing).
See the files in subdirectories of example\data for sample inputs.

The known 'start date' for each Id is specified in a separate CSV file,
with an additional offset.

See the file example\date_day1.csv for an example.

Many parameters can be specified in an associated configuration file.
This can specify the location of the input and output, and column names
and values.

By default this file is assumed to be named config.ini in the directory
this is executed in; but can be specified from the command line with -c.
See the file example\config.ini for a full example.

To test the script from the root directory run:
    python3 report.py -c example\config.ini

This library is released under GPLv3 Licence; see licences.

Files:

* report.py - Main reporting script run with Python
* requirements.txt - Python dependencies. Install with 
                         pip install -r requirements.txt
* examples - Example data
* licences - GPLv3 Licence
