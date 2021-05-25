# ecl_tokenizer
Simple tokenizator of Eclipse data decks. Pure Python code with no dependencies.
Pandas and Numpy are required for further data manipulations.

## Detection rules
Eclipse data deck (Eclipse case) is a collection of ASCII files.
Each file has a set of data records, specified by keywords.
Eclipse has several types of keywords. We do not care about those types.
We only split a case by keyword:value pairs.
Empty lines and comments are ignored.
Keyword owns the data that located between that keyword and the next keyword.
If data without keyword is found, exception is raised.

This is not a strict parser, as we do not know all of possible keywords and their syntax,
we reply on simple detection of possible keywords.

We assume that keyword is a command up to 8 chars long, starts with column 0 and could
consist of A-Z, 0-9, + and - symbols. Keyword should be uppercase and start with a letter.

There is special keyword `INCLUDE` which includes other file into current file. When such
keyword is found, it is parsed right away, and parser continues reading current after that.
`INCLUDE` keywords could be nested.

We keep track of parsed files to prevent recursion. We also keep track of missing files that `INCLUDE` keyword refers to.

## Workflow
### Initialization
```
import ecl_tokenizer as et
case = et.EclCase(r"C:\GitHub\opm-tests\model5\0_BASE_MODEL5.DATA")
```
### Show the structure of case
```
>>> case.describe()
+ C:\GitHub\opm-tests\model5\0_BASE_MODEL5.DATA
|-- C:\GitHub\opm-tests\model5\0_BASE_MODEL5.DATA
|-- C:\GitHub\opm-tests\model5\include\test1_20x30x10.grdecl
|-- C:\GitHub\opm-tests\model5\include\permx_model5.grdecl
|-- C:\GitHub\opm-tests\model5\include\pvt_live_oil_dgas.ecl
|-- C:\GitHub\opm-tests\model5\include\rock.inc
|-- C:\GitHub\opm-tests\model5\include\relperm.inc
|-- C:\GitHub\opm-tests\model5\include\summary.inc
|-- C:\GitHub\opm-tests\model5\include\well_vfp.ecl
|-- C:\GitHub\opm-tests\model5\include\flowl_b_vfp.ecl
|-- C:\GitHub\opm-tests\model5\include\flowl_c_vfp.ecl
```
### Look up keywords
```
# Query for keyword presence.
>>> case.has_kwd("DIMENS")
True
# Get list of all instances of given keyword.
>>> case.get_kwds("DIMENS")
[<EclKwd: DIMENS    Section "RUNSPEC  " Parent: "C:\GitHub\opm-tests\model5\0_BASE_MODEL5.DATA" Line_number: "17">
]
```
### Extracting data of keywords
```
# Get raw data of first instance of given keyword.
>>> case.get_kwds("DIMENS")[0].value
[' 20 30 10 /']
# Get combined data from records of all instances of given keyword.
>>> case.get_kwds_data("DIMENS")
[['20', '30', '10']]
```
### Data extraction example
```
>>> import pandas as pd
>>> import numpy as np
# By default, N*M type of records are expanded.
>>> wsp = case.get_kwds_data("WELSPECS")
>>> df1 = pd.DataFrame(wsp)
>>> df1
       0     1   2   3  4      5  6  7     8  9  10 11
0  'B-1H'  'B1'  11   3       OIL        SHUT
1  'B-2H'  'B1'   4   7       OIL        SHUT
2  'B-3H'  'B1'  11  12       OIL        SHUT
3  'C-1H'  'C1'  13  20       OIL        SHUT
4  'C-2H'  'C1'  12  27       OIL        SHUT
5  'F-1H'  'F1'  19   4     WATER        SHUT
6  'F-2H'  'F1'  19  12     WATER        SHUT
7  'G-3H'  'G1'  19  21     WATER        SHUT
8  'G-4H'  'G1'  19  25     WATER        SHUT

# Disable expansion of N*M type of records.
>>> wsp2 = case.get_kwds_data("WELSPECS", expand=False)
>>> df2 = pd.DataFrame(wsp2)
>>> df2
       0     1   2   3   4      5   6   7     8   9   10  11
0  'B-1H'  'B1'  11   3  1*    OIL  1*  1*  SHUT  1*  1*  1*
1  'B-2H'  'B1'   4   7  1*    OIL  1*  1*  SHUT  1*  1*  1*
2  'B-3H'  'B1'  11  12  1*    OIL  1*  1*  SHUT  1*  1*  1*
3  'C-1H'  'C1'  13  20  1*    OIL  1*  1*  SHUT  1*  1*  1*
4  'C-2H'  'C1'  12  27  1*    OIL  1*  1*  SHUT  1*  1*  1*
5  'F-1H'  'F1'  19   4  1*  WATER  1*  1*  SHUT  1*  1*  1*
6  'F-2H'  'F1'  19  12  1*  WATER  1*  1*  SHUT  1*  1*  1*
7  'G-3H'  'G1'  19  21  1*  WATER  1*  1*  SHUT  1*  1*  1*
8  'G-4H'  'G1'  19  25  1*  WATER  1*  1*  SHUT  1*  1*  1*
# By default, all of columns are of string type. See the next section for workaround.
>>> df2.dtypes
0     object
1     object
2     object
3     object
4     object
5     object
6     object
7     object
8     object
9     object
10    object
11    object
dtype: object
```
### Data types
By default, data returned from `case.get_kwds_data("kwd")` is of string type.
To recognize them as numbers, supply the `dtype=float32` argument to `pd.DataFrame` constructor.
(It seems like older versions of pandas do not support integer columns).
```
>>> df2 = pd.DataFrame(wsp2, dtype="float32")
>>> df2
       0     1     2     3   4      5   6   7     8   9   10  11
0  'B-1H'  'B1'  11.0   3.0  1*    OIL  1*  1*  SHUT  1*  1*  1*
1  'B-2H'  'B1'   4.0   7.0  1*    OIL  1*  1*  SHUT  1*  1*  1*
2  'B-3H'  'B1'  11.0  12.0  1*    OIL  1*  1*  SHUT  1*  1*  1*
3  'C-1H'  'C1'  13.0  20.0  1*    OIL  1*  1*  SHUT  1*  1*  1*
4  'C-2H'  'C1'  12.0  27.0  1*    OIL  1*  1*  SHUT  1*  1*  1*
5  'F-1H'  'F1'  19.0   4.0  1*  WATER  1*  1*  SHUT  1*  1*  1*
6  'F-2H'  'F1'  19.0  12.0  1*  WATER  1*  1*  SHUT  1*  1*  1*
7  'G-3H'  'G1'  19.0  21.0  1*  WATER  1*  1*  SHUT  1*  1*  1*
8  'G-4H'  'G1'  19.0  25.0  1*  WATER  1*  1*  SHUT  1*  1*  1*
>>> df2.dtypes
0      object
1      object
2     float32
3     float32
4      object
5      object
6      object
7      object
8      object
9      object
10     object
11     object
dtype: object
```
### Example of PERMX/PORO extraction
```
# Get the model dimensions.
>>> case.get_kwds_data("DIMENS")
[['20', '30', '10']]
# How many PERMX values we should have?
>>> 20*30*10
6000
# Check for presense of PERMX and PORO keywords in this case.
>>> case.has_kwd("PERMX")
True
>>> case.has_kwd("PORO")
True
# Get PERMX data and convert to numpy array of proper type.
>>> permx = case.get_kwds_data("PERMX")
>>> permx_arr = np.array(permx, dtype="float32")
# Number of data records is correct.
>>> permx_arr.shape
(1, 6000)
```
## Usage
You are welcome to use this code in accordance with its license.
Copyrights should be preserved.
The Author is not responsible for any outcome that you experience from this code.
See the license for more details.

## Contributing
All code contains bugs. This code is reached the state where it deserved sharing.
If you find any bug, please contribute via raising tickets or submitting pull requests, as long as you agree with the license terms.

