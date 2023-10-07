# WiP

# APITester

An object designed to run various preset and custom API tests.

- [Input Attributes](#input-attributes)
- [Non-Input Attributes](#non-input-attributes)
- [Class Constants](#class-constants)
- [Methods](#methods)
  - [update_fields](#update_fields)
  - [add_issue](#add_issue)
  - [add_result](#add_result)
  - [update_progress_bars](#update_progress_bars)
  - [run_one_api](#run_one_api)
  - [run_one_test](#run_one_test)
  - [run_general_tests](#run_general_tests)
  - [run_one_field](#run_one_field)
  - [run_all_tests](#run_all_tests)
  - [clear_results](#clear_results)
  - [rerun_rests](#rerun_rests)
  - [run_custom_inputs](#run_custom_inputs)
- [`test_fields` Notes](#test_fields_notes)
- [predo/test/undo/final_undo notes](#predotestundofinal_undo-notes)
- [custom_inputs notes](#custom_inputs-notes)
- [custom_tests notes](#custom_tests-notes)

## Input Attributes

- `base_url` (string): Base URL consistent across multiple predo, test, and undo functions.
- `test_fields` (list): List of dictionaries specifying which fields should be tested. For detailed information on the structure, refer to the notes section.
- `predo` (dict): Info needed to run an API before the API to be tested.
- `test` (dict): Info needed to run the API that is to be tested.
- `undo` (dict): Info needed to run an API after the API to be tested.
- `custom_inputs` (list): Array of objects to input custom combinations of data with expected results for bespoke testing.
- `custom_tests` (list): Array of objects containing information needed to run custom input tests.
- `matching_fields` (list): Array of arrays with values that should match one another.
- `delete_value` (string): Value to be used in the header or body of an API request when an indirect reference is made, but the value cannot be found.
- `print_status` (bool): Print status (passed/fail) of each API request.
- `print_json` (bool): Print JSON result of each API request.
- `print_progress` (bool): Print progress bar when steps are updated.
- `display_refresh` (bool): For progress bar, refresh the print display instead of printing to a new line.
- `min_print_wait` (float): Amount of time between progress prints.

### Input Attributes with No Inputs

- `tests_summary` (dict): Counts of passed tests and total tests for each field.
- `log` (dict): A log of the previously run predo, test, undo that for each of the three API requests.
- `results` (list): List of results of tests.
- `current_result` (dict): Object containing all the results that are currently being processed; resets at the end of each full test.
- `tests_summary_by_field` (list): List of dict of counts of passed tests and total tests for each field.
- `failed_predo` (list): List of failed predo requests.
- `failed_test` (list): List of failed test requests.
- `failed_undo` (list): List of failed undo requests.
- `l1_progress_bar` (dict): Object to store info on progress bar for highest level view of tests.
- `l2_progress_bar` (dict): Object to store info on progress bar for next level of hierarchy of tests.
- `l3_progress_bar` (dict): Object to store info on progress bar for next level of hierarchy of tests.

## Non-Input Attributes

- `total_predo_issues` (integer): Running count of failed attempts at predo.
- `total_test_issues` (integer): Running count of unexpected results.
- `total_undo_issues` (integer): Running count of failed attempts at undo.

## Class Constants

- `_general_test_field` (string): Name to put in 'field' attribute for output for non-field specific tests.
- `_log_init` (dict): Initial value for log.
- `_l1_init` (dict): Initial value for l1_progress_bar.
- `_l2_init` (dict): Initial value for l2_progress_bar.
- `_l3_init` (dict): Initial value for l3_progress_bar.

## Methods

### `update_fields`

Updates a field of an object within APITester, including any fields that should match such changes.

### `add_issue`

Adds an issue count to various counters as needed.

### `add_result`

Adds results to the result attribute of the object.

### `update_progress_bars`

Updates progress bar and prints all active progress bars.

### `run_one_api`

Runs one API (predo, test, undo).

### `run_one_test`

Runs the predo, test, and undo and logs the results.

### `run_general_tests`

Runs all standard general tests.

### `run_one_field`

Runs all standard field-specific tests for one specific field.

### `run_all_tests`

Runs general tests, all field tests, custom tests then synthesizes results.

### `clear_results`

Clears/resets pertinent variables; likely used before running all tests.

### `rerun_rests`

Reruns tests, clearing results and other pertinent fields, then runs all tests.

### `run_custom_inputs`

Runs all tests specified by the custom_inputs attribute.

## `test_fields` Notes

The structure of `test_fields` should be as follows:
- `test_field` (string): Name of the field being tested.
- `test_type` (string): Data type of field.
- `field_parameters` (dict): Contains various parameters to be used in tests done on the field.
