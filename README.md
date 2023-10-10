# APITester

An object designed to run various preset and custom API tests.

## In this README

- [Overview](#overview)
- [Tests](#tests)
  - [General](#general-tests)
  - [Field Specific](#field-specific-tests)
  - [Custom](#custom-tests)
    - [Custom Inputs](#custom-inputs)
    - [Custom Tests](#custom-tests)
- [Implementation](#implementation)
  - [Pre-instantiation](#pre-instantiation)
  - [Instantiation](#instantiation)
  - [Running Tests](#running-tests)
  - [Viewing Results](#viewing-results)
- [Class Attributes and Methods](#class-attributes-and-methods)
  - [Input Attributes](#input-attributes)
  - [Non-Input Attributes](#non-input-attributes)
  - [Class Constants](#class-constants)
  - [Commonly Used Methods](#commonly-used-methods)
    - [run_all_tests](#run_all_tests)
    - [rerun_rests](#rerun_rests)
  - [Other Methods](#other-methods)
- [Utils Functions](#utils-functions)

## Overview

The APITester object takes users inputs about what types of tests should be run, runs the tests, then stores the results in a number of formats as different attributes. Each API request has an *api_input*  (object with a url, header, and body), an expected outcome (success of failure), and then a place to store the specific response for further review.

Each test consists of up to three different API requests-- a predo, test, and undo as described below:
- Predo: **Optional** API request made before test is done that enables a test to be done without causing any unnecessary changes to the database; this can be either to grab an original value for patch test, create a new document for a delete test (so that current documents are not deleted), etc.
- Test: **Required** API request that is being tested
- Undo: **Optional** API request made after test is done to return database back to former state; this can be a delete request to remove a document created in the test, a patch request to revert a document back to its original values, etc.
These different tests can pass information to one another so that changes made in one request can be used to influence API calls of subsequent calls (call order is Predo --> Test --> Undo)

The output is a dataframe that is aggregated into easier to digest views that describe the success rates of all the APIs and easily direct the user to any APIs that failed despite expected success or succeeded despite expected failure. After correcting and validation on the server's APIs, the tests can be ran again to validate the changes made.

## Tests
General tests are ran, independent of any input/payload sent with the API. Field specific tests are then ran to ensure that inputs that should work do work and inputs that should not work do not work. Custom tests are then ran in two different formats: the first being inputs and expected results that are input by the user at instantiation, the second being more complex functions with an expected structure that the object will use to run tests. 

### General Tests
Not specific to input

#### General
Make sure that a base case works to ensure that future test failures (expected or unexpected) don't stem from an unnacceptable base case

- **Acceptable base case**: ensure that user input base case works

#### Access
If authorization via token is required, make sure that when improper token is included, the API request fails

- **No token**: exclude token
- **'None'/null for token**: include token, but a None/null value for the token
- **Shortened token**: remove one character from end of token
- **Lengthened token**: increase token by one character

#### URL ID
If an ID is provided as part of the URL, make sure that when improper IDs are provided, the API request fails

For each ID that is a part of the URL:
- **Exclude ID**: exclude ID from url
- **Lengthen ID**: increase base case ID by one character
- **Shorten ID**: decrease base case ID by one character

### Field-Specific Tests
These tests are ran for each field that is included in the test_fields input parameter, each field potentially being put through different tests depending on the aassociated input parameters (e.g., test_type (string, integer, etc.), field_parameters (min, max, etc.), etc.)

#### General

   - **(non-api) Field either not required or is in test_input**: tests that a given field is either not a required input or, if it is a required input, make sure that the field is included in the input
   - **(non-api) Field type acceptable**: tests that the "test_type" parameter is included in the list of acceptable values `['string', 'integer', 'float', 'boolean', 'array', 'date', 'password', 'password_confirmation', 'email', 'original_password', 'dict']`
   - **Acceptable input**: tests that base case input works
   - **Null value**: tests that null value (None) makes the api fail
   - **No value (deleted)**: for fields that are required or have no default values, tests that api will fail if field value is deleted/not included
   - **Delete value**: when delete_field_test is included in the *test* input parameters, this will make sure that when the *delete* value is included, the api runs and successfully deletes the value for that field in the server database; the *delete_value* is a parameter supplied when initializing the object and should align with a keyword definied and used in your APIs to delete a field in the database.

#### Min (min in field_parameters)
These tests are run for any field with a *min* value in *field_parameters*; *min_inc* can also be provided as a boolean value in *field_parameters* to declare whether min is inclusive (*min_inc* = True; min value is accepted) or exclusive (*min_inc* = False; min value is NOT accepted). *min_inc* has a default value of True (inclusive)

   - **below boundary**: tests that a value below the min is rejected
   - **at boundary**: tests that a value equal to the min is either accepted (*min_inc* = True or is excluded) or rejected (*min_inc* = False)
   - **above boundary**: tests that a value above the min is accepted

#### Max (max in field_parameters)
These tests are run for any field with a *max* value in *field_parameters*; *max_inc* can also be provided as a boolean value in *field_parameters* to declare whether max is inclusive (*max_inc* = True; max value is accepted) or exclusive (*max_inc* = False; max value is NOT accepted). *max_inc* has a default value of True (inclusive)

   - **above boundary**: tests that a value above the max is rejected
   - **at boundary**: tests that a value equal to the max is either accepted (*max_inc* = True or is excluded) or rejected (*max_inc* = False)
   - **below boundary**: tests that a value below the max is accepted

#### Email (test_type = 'email')
These tests are run for any field with a test_type 'email'

   - **Correct email form (loop through different combos of components)**: tests to ensure that only an email address with all of the five following components can be accepted: ['before', '@', 'after', '.', 'end'] --> before@after.end by sending every combo of those five pieces (in that same order) as test values, expecting all but the combination of all five elements to fail
   - **Email already in database (if existing_email in field_parameters)**: if *existing_email* is provided in *field_parameters*, will send a request with that existing email address to test that it fails when the duplicate value is provided; *existing_email* should be an email address that is known to be in the database for a given field (recommended to make a dummy entry with a dummy email address for this test)

#### Matching values (field in self.matching_fields)
Tests that two fields that should match each others' values (e.g., email confirmation, password confirmation) matches; is ran only if the parameter *matching_fields* is provided, a list of lists of fields that should match one another (e.g., `matching_fields = [['password', 'password_confirmation'], ['email', 'email_confirmation']]`)

   - **Make matching values different**: tests if the api rejects the request when two different values are provided for matching values

#### Password (test_type = 'password')
Tests that an input field meets various requirements as dictated by the optional fields in *field_parameters* (length, upper_case, lower_case, number, special_character)

   - **Min length of password (if min_length in field parameters)**: tests a password for a minimum length by looping through lengths from 0 to length + 2 and making sure that all passwords below the specified length are rejected
   - **Max length of password (if min_length in field parameters)**: tests a password for a maximum length by looping through lengths from max_length - 1 to max_length + 1 and making sure that all passwords above the specified length are rejected
   - **Upper case in password (if upper_case in field parameters)**: tests that a lowercase version of the acceptable password is rejected
   - **Lower case in password (if lower_case in field parameters)**: tests that an uppercase version of the acceptable password is rejected
   - **Number in password (if number in field parameters)**: removes numbers in password and if minimum length is required replicates remaining password, then tests to make sure the numberless password is rejected
   - **Special Character in password (if special_character in field parameters)**: removes special characters in password and if minimum length is required replicates remaining password, then tests to make sure the special character-less password is rejected

#### Non-array
Any field that has a data type that is NOT array might be subject to these tests

   - Array of possible inputs (array in field_parameters): if a field is NOT an array *field_type* but has an array of possible values (input as *array* in *field_parameters*); *excluded* must be included as a parameter in *field_parameters* for these tests to run and should be a value that should not be accepted by the api
     - **Test each value in possible inputs array**: test that each value in the input accetpable values *array* is accepted
     - **Test random value outside of possible array**: test that the *excluded* parameter is rejected
   - **Wrong datatypes (multiple)**: for all *test_type* excluding 'string', 'password', 'email', and 'original_password', runs through specified preset data type test values (string: 'a', integer: 1, float: 1.1, boolean: True) and makes sure input is only accepted when the correct data type is accepted

#### Array
These tests are run if a *field_type* of 'array' is provided for a given field

   - **Empty array**: tests that an empty array is rejected
   - **Wrong datatypes (multiple)**: for all *array_type* excluding 'string' and 'array', sends a single value array of each of the data types to test that only the proper array_type is accepted (*array_type* is a parameter of the *test_field* that can be included; this test will only run if an *array_type* is included)
   - Duplicate (if duplicate is True in field_parameters): 
   - **Duplicate array values**: ran only if *duplicates* is included in *field_parameters*; will send request with an array of a duplicated known successful value (from base case) and will test whether it fails when expected (*duplicates* = False) or succeed (*duplicates* = True)
   - **Array of possible inputs (array in field_parameters)**: if an array has an array of possible values (input as *array* in *field_parameters*); *excluded* must be included as a parameter in *field_parameters* for these tests to run and should be a value that should not be accepted by the api
     - **Each value individually from possible inputs array**: sends a single value array of each of the possible values to test whether the request is successful
     - **Single value outside of possible array**: sends a single value array of the *excluded* value to test whether the request fails
     - **Random sample of values in possible inputs array**: runs a test of 5 arrays of random sizes (between 1 and length of possible array) to test whether requests are successful
     - **Single value outside of possible array with random sample of values in possible inputs array**: uses random arrays in 'Random sample...' test and tacks on the *excluded* value at the start of the arrays to test whether requests are rejected
     - **All values in possible inputs array**: sends the entire possible values array to test whether request is successful
     - **Single value outside of possible array with all values in possible inputs array**: sends the entire possible values array with the *excluded* value added to the end of the array to test whether request is rejected


### Custom Tests

#### Custom Inputs
A list of known inputs can be tested by use of the *custom_inputs* parameter. The *custom_inputs* parameter is an array of dict with the form below used that uses the same internal methods to run tests (including using test url/function and running any predo or undo requests), but using any combination of input custom header, body, and url_ids:
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

#### Custom Tests
A list of custom tests that follow the structure as outlined below can be provided. These tests will be run by the APITester object and the results will be included along with the other standard/built-in tests.

The custom_tests is input as an array of dict with the form below that are used to run custom tests. Here is the structure of those dict:
```
{
  function (function): the custom function to be run by the APITester object. It must have
      the following characteristics:
      Inputs:
          standard_inputs (dict, argument 1): the 'inputs' dict that is the second attribute
              in the 'custom_tests' dict as described below
          obj (object, argument 2): 'self' will be passed to the function to allow for
              attributes and methods of the APITester objected to be accessed and ran
      Internal Processes:
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
              obj.add_issue(obj.total_custom_test_issues)
      Outputs: 
          out (list): list of objects with same form as 'result_template' function; it is
              suggestested that the 'result_template' function is integrated into the custom
              function to enable uniform output; alternatively, the function can output an
              empty array results can be directly added using obj.add_result method
  inputs (dict): any input needed to run the process; these should be explicit values, not
      dependent on other parts of the APITester (can use 'obj' input to access other parts of
      the APITester); part of the custom function should be processesing this all-in-one dict
      input into component parts for easy use within the function
  meta_data (dict): information about the function with the following form:
      total_tests (integer): number of tests that are to be run as a part of the process; 
          this number will feed a progress bar to show progress in the test
}
```

## Implementation 

There is a little bit of setup work to be done before instantiating the object, mainly in setting up the *test_fields* parameter. The instantiation process is straightforward and allows for a fair amount of customization of how the tests are run and how their results are displayed. Results can be viewed with several automatically created dataframes with varying amounts of granularity

### Pre-instantiation

****To be updated****

### Instantiation

****To be updated****

### Running Tests

****To be updated****

### Viewing Results

****To be updated****

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
        'min_length' (int): min length of acceptable string (password)
        'max_length' (int): max length of acceptable string (password)
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

## Utils Functions
****To be updated****
