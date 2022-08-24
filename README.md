# *surveychecks* - evaluating survey data

## What is *surveychecks*?

Surveychecks lets you compare and evaluate a survey data set, either real or computer generated, with the programing template used to set up the survey.

## Central survey evaluation components

* Check whether all survey variables are in the data set and vice versa.
* Evaluate whether the predifined value ranges of each variable are met.
* Assess if all filter conditions were set correctly.

## Quickstart

1. Clone the respository
    >git clone
2. Prepare the programing template for surveychecks *(see: docs/preparing_syntax.md)*
3. Initiate the class
   >catiCheck = surveychecks(pdDataframe, pathToProgramingTemplate)
4. Run variable check
   >catiCheck.varcheck()
5. Run range checks
   >catiCheck.rangeCheck()
   >catiCheck.rangeCheck(filterMissVal = int, checkType = 'missing')
6. Run filter checks
   >catiCheck.filterCheck()
   >catiCheck.filterCheck(filterMissVal = int, checkType = 'missing')

## Notes

This package is still in early development and subject to changes. Documentation will be updated soon.
