# WiP

# APITester

An object designed to run various preset and custom API tests.

- [Class Attributes and Methods](#class-attributes-and-methods)
  - [Input Attributes](#input-attributes)
  - [Non-Input Attributes](#non-input-attributes)
  - [Class Constants](#class-constants)
  - [Commonly Used Methods](#commonly-used-methods)
    - [run_all_tests](#run_all_tests)
    - [rerun_rests](#rerun_rests)
  - [Other Methods](#other-methods)

---
## Class Attributes and Methods

### Input Attributes
#### `base_url` (string)
 Base URL consistent across multiple predo, test, and undo functions.
#### `test_fields` (list)
 List of dictionaries specifying which fields should be tested.

 Should be omitted if there is not a body json submit as part of the API (will still run general, non-field-specific tests)
 
 The structure of test_fields should be as follows:
 ```
  {
    'test_field' (string): name of the field being tested
    'test_type' (string): data type of field (can be one of the following: 'string', 'integer', 'float', 'boolean', 'array', 'date', 'password', 'email', 'original_password'; 'original_password' included so as to avoid scrutiny of other password criteria since scrutiny might change since original password was created)
    'field_parameters' (dict): contains various parameters to be used in tests done on the field. The following are valid values and circumstances in which they can be used:
        'min' (integer): minimum value possible (integer/float fields/array_type)
        'min_inc' (bool): inclusive minimum bound; def=True (integer/float fields/array_type)
        'min' (integer): maximum value possible (integer/float fields/array_type)
        'min_inc' (bool): inclusive maximum bound; def=True (integer/float fields/array_type)
        'array' (list): list of possible values (string/int/float fields/array_type)
        'duplicates' (bool): can contain duplicate values (list)
        'length' (int): min length of acceptable string (password)
        'upper_case' (bool): string should contain an upper case (password)
        'lower_case' (bool): string should contain a lower case (password)
        'number' (bool): string should contain a number (password)
        'special_character' (bool): string should contain a special character
    'required' (bool): whether the field is required
    'default' (bool): whether the fields has a default value in the data schema
    'deletable' (bool): whether the field can be deleted
    'acceptable_input' (dict): acceptable baseline 'json' for body of API request
    'array_type' (string): data type of values in array ('string', 'integer', 'float', 'boolean', 'date'); default is None (for non-array test_type)
    }
```
  
#### `predo`* (dict)
 Info needed to run an API before the API to be tested.
#### `test`* (dict)
 Info needed to run the API that is to be tested.
#### `undo`* (dict)
 Info needed to run an API after the API to be tested.

#### *`predo`/ `test` / `undo` / `final_undo` notes:
 The focus of the object is on a test API, but space is provided to run other APIs that allow the database to not accumulate/be depleted of objects. A 'predo' API will be done before the test is run-- this can be helpful if testing a delete function so that an document can be created before running the delete test to then be deleted. An 'undo' API will be done after the test is run-- this can be helpful to either delete documents created by the test or revert documents to their original value. Either way, specific test documents should be used for these APIs so as to not make unwanted changes to your database. The general form of these tests should be as follows: 
 ```
 {
  function (requests function): type of API call to be used (e.g., requests.get,
      requests.post, requests.patch, etc.)
  url (string): API specific url that will be added to the base url,
  header* (dict): all the keys with explicit values or referenced values from the log of
      APIs that are run (self.log); see below for further notes 
  body* (dict): all the keys with explicit values or referenced values from the log of
      APIs that are run (self.log); see below for further notes
  url_ids* (list): all the url_ids with explicit values or referenced values from the
      log of APIs that are run (self.log); see below for further notes
  on_success (bool): (predo and undo only) whether the predo or undo request should be
      made only if the previous test was successful (True) or regardless (False)
  delete_field_test (bool): (test only) whether to run a test to see if fields can be
      deleted with the input delete_value
  final_undo (bool): (test only) whether to run a test with a known success once more 
      time at the end of all the tests for a field (e.g. testing user delete, predo
      would create function, but then if the last test fails, will be left with a
      user-- final_undo runs the delete test one more time with a known success input)
  }
```
 for header, body, and url_ids, values can either be explicit inputs (e.g., 'application/json' for 'Content-Type' in headers) or referenced values from the log. Referenced values from the log will have the following form:
 ```
 {
  referenced_value (bool): flag to run referenced value calc; should be True 
  sources (string): either 'predo', 'test', or 'redo' depending on which request
      gives the needed information
  component (string): either 'body', 'header', or 'response' (possibly 'url_id')
  location (string): directory of value to be found (use "." to get to nested layers
      and [<ind>] to get the <ind> index of an array within an object
  }
```
 \<field> is also something that can be used as a key in header or body or as a location in any of the three inputs; \<field> will be replaced with the current test field some example inputs are as follows, each of the three coming from different tests:
 
1. `'header': {'token': {'referenced_value': True, 'source': 'test', 'component': 'body', 'location': '_id'}}`

2. `'body': {'<field>': {'referenced_value': True, 'source': 'predo', 'component': 'body', 'location': '<field>'}}`

3. `'url_ids': [{'referenced_value': True, 'source': 'predo', 'component': 'body', 'location': '_id'}]`

locations can be nested values as explained in the location description above

#### `custom_inputs` (list)
 Array of objects to input custom combinations of data with expected results for bespoke testing.

 custom_inputs is an array of dict with the form below used that uses the same internal methods to run tests (including using test url/function and running any predo or undo requests), but using any combination of input custom header, body, and url_ids:
 ```
{
  test_expected_api_result (bool): REQUIRED whether the api is expected to be successful
  field (string): field that the test is associated with
  test_name (string): name of the test that is being run
  error (string): error message to be recorded should there be an unexpected result
  test_header (dict): header that you would like to test (omit to maintain test
      attribute's standard header value)
  test_body(dict): body that you would like to test (omit to maintain test attribute's
      standard body value)
  test_url_ids (list): url_ids that you would like to test (omit to maintain test
      attribute's standard url_ids value)
}
```
                    
#### `custom_tests` (list)
 Array of objects containing information needed to run custom input tests.

 the custom_tests is an array of dict with the form below that are used to run custom tests. Here is the structure of those dict:
 ```
{
function (function): the customer function to be run by the APITester object. It must have
    the following characteristics:
  {
    Inputs:
   {
        standard_inputs (dict, argument 1): the 'inputs' dict that is the second attribute
            in the 'custom_tests' dict as described below
        obj (object, argument 2): 'self' will be passed to the function to allow for
            attributes and methods of the APITester objected to be accessed and ran
   }
    Internal Processes:
   {
        If progress through progress bars is desirable, use the l3_progress_bar object and 
            update_progress_bars method to update the progress bar. If you choose to do this,
            make sure the following are inluded somewhere in each custom function:
                # at the start of the code vv
                obj.l3_progress_bar['active'] = True
                obj.l3_progress_bar['progress_bar'].steps = <number of expected steps>
                obj.l3_progress_bar['current_step'] = -1 # will restart progress on the bar
                ...
                # after each iteration if multiple steps are being run vv
                obj.update_progress_bar(value_update={'l3': <index of step that was just complete>})
        Update total errors as they occur by including the following line of code whenever an 
            issue occurs:
            running obj.add_issue(obj.total_custom_test_issues)
    }
    Outputs:
    {
        out (list): list of objects with same form as 'result_template' function; it is
            suggestested that the 'result_template' function is integrated into the custom
            function to enable uniform output; alternatively, the function can output an
            empty array results can be directly added using obj.add_result method
    }
inputs (dict): any input needed to run the process; these should be explicit values, not
    dependent on other parts of the APITester (can use 'obj' input to access other parts of
    the APITester); part of the custom function should be processesing this all-in-one dict
    input into component parts for easy use within the function
meta_data (dict): information about the function with the following form:
    total_tests (integer): number of tests that are to be run as a part of the process; 
        this number will feed a progress bar to show progress in the test
```

#### `matching_fields` (list)
 Array of arrays with values that should match one another.
#### `delete_value` (string)
 Value to be used in the header or body of an API request when an indirect reference is made, but the value cannot be found.

 this situation usually occurs when reverting a document back to its original value through an undo API request, but the original value did not contain the attribute that was edited so it needs to be flagged for deletion; this delete_value can also be a flag to make a patch API remove an optional value for the document
 
#### `print_status` (bool)
 Print status (passed/fail) of each API request.
#### `print_json` (bool)
 Print JSON result of each API request.
#### `print_progress` (bool)
 Print progress bar when steps are updated.
#### `display_refresh` (bool)
 For progress bar, refresh the print display instead of printing to a new line.
#### `min_print_wait` (float)
 Amount of time between progress prints.

---
### Input Attributes with No Inputs

#### `tests_summary` (dict)
 Counts of passed tests and total tests for each field.
#### `log` (dict)
 A log of the previously run predo, test, undo that for each of the three API requests.
#### `results` (list)
 List of results of tests.
#### `current_result` (dict)
 Object containing all the results that are currently being processed; resets at the end of each full test.
#### `tests_summary_by_field` (list)
 List of dict of counts of passed tests and total tests for each field.
#### `failed_predo` (list)
 List of failed predo requests.
#### `failed_test` (list)
 List of failed test requests.
#### `failed_undo` (list)
 List of failed undo requests.
#### `l1_progress_bar` (dict)
 Object to store info on progress bar for highest level view of tests.
#### `l2_progress_bar` (dict)
 Object to store info on progress bar for next level of hierarchy of tests.
#### `l3_progress_bar` (dict)
 Object to store info on progress bar for next level of hierarchy of tests.

---
### Non-Input Attributes

#### `total_predo_issues` (integer)
 Running count of failed attempts at predo.
#### `total_test_issues` (integer)
 Running count of unexpected results.
#### `total_undo_issues` (integer)
 Running count of failed attempts at undo.

---
### Class Constants

#### `_general_test_field` (string)
 Name to put in 'field' attribute for output for non-field specific tests.
#### `_log_init` (dict)
 Initial value for log.
#### `_l1_init` (dict)
 Initial value for l1_progress_bar.
#### `_l2_init` (dict)
 Initial value for l2_progress_bar.
#### `_l3_init` (dict)
 Initial value for l3_progress_bar.

---
### Commonly Used Methods

#### `run_all_tests`
Runs general tests, all field tests, custom tests then synthesizes results.

#### `rerun_rests`
Reruns tests, clearing results and other pertinent fields, then runs all tests.

---
### Other Methods
These methods are generally used internally with other methods

#### `update_fields`
Updates a field of an object within APITester, including any fields that should match such changes.

#### `add_issue`
Adds an issue count to various counters as needed.

#### `add_result`
Adds results to the result attribute of the object.

#### `update_progress_bars`
Updates progress bar and prints all active progress bars.

#### `run_one_api`
Runs one API (predo, test, undo).

#### `run_one_test`
Runs the predo, test, and undo and logs the results.

#### `run_general_tests`
Runs all standard general tests.

#### `run_one_field`
Runs all standard field-specific tests for one specific field.

#### `clear_results`
Clears/resets pertinent variables; likely used before running all tests.

#### `run_custom_inputs`
Runs all tests specified by the custom_inputs attribute.
