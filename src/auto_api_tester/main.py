## TO DO -----------------------------------------------------------------------

## create process for trying different query parameters (attribute of APITester object,
##      array of objects with parameter name, allowable values, etc.)

## -----------------------------------------------------------------------------

import re
import copy
import json
import time
import random
import requests
import itertools
import IPython.display as disp

from timer_bar import TimerBar

## -----------------------------------------------------------------------------

from .utils import change_date, test_boundary, check_field, update_field_value, get_field_value, create_test_field, update_url_id, find_vals, find_hb_vals,find_ids_vals, result_template

## -----------------------------------------------------------------------------

class APITester():
    '''
    An object to be used to run various preset and custom API tests
    -- input attributes --
    base_url (string): base url consistent across mutliple predo, test, and undo functions
    test_fields (list): list of dictionaries specifying which fields should be tested; see below
        for more information on what structure should look like; should be omitted if there is not
        a body json submit as part of the API (will still run general, non-field-specific tests)
    predo (dict): info needed to run an API done before the API to be tested (see notes below);
        can be omitted if there is no need for a predo
    test (dict): info needed to run API that is to be tested (see notes below); can be omitted if
        there is no need for a predo
    undo (dict): info needed to run an API done after the API to be tested (see notes below); can
        be omitted if there is no need for a predo
    custom_inputs (list): array of objects to input custom combinations of data with and expected
        result for bespoke testing (see notes below)
    custom_tests (list): array of objects containing information needed to run custom input tests
        (see notes below)
    matching_fields (list): array of arrays while values that should match one another (e.g., password +
        password confirmation, if one changes the other should change too to make sure API works)
    delete_value (string): value to be used in header or body of api request when an indirect reference
        is made, but the value cannot be found; this situation usually occurs when reverting a
        document back to its original value through an undo API request, but the original value
        did not contain the attribute that was edited so it needs to be flagged for deletion; this
        delete_value can also be a flag to make a patch API remove an optional value for the document
    print_status (bool): print status (passed/fail) of each API request
    print_json (bool): print json result of each API request
    print_progress (bool): print progress bar when steps are updated
    display_refresh (bool): for progress bar, refresh the print display instead of printing to new line
    min_print_wait (float): amount of time between progress prints; will wait until that time has passed
        to print a new line

    -- input attributes that should have no inputs* --
    * these are objects and arrays that will carry over from one instance of an object to the next
        unless they are setup to be input variables that have default/blank values if not provided;
        please do not provide values for these attributes
    tests_summary (dict): counts of passed tests and total tests for each field
    log (dict): a log of the previously run predo, test, undo that for each of the three api
        requests should contain body, header, url_ids, url, expected_result, api_result,
        field_index, and test_index
    results (list): list of results of tests with form dictated by result_template function
    current_result (dict): object containing all the results that are currently being processed;
        resets at the end of each full test, but is handy in case there is an error in one part
        of the test, you can still see the result_template of what you have so far
    tests_summary_by_field (list): list of dict of counts of passed tests and total tests for each field
    failed_predo (list): list of failed predo requests, in the results form
    failed_test (list): list of failed test requests, in the results form
    failed_undo (list): list of failed undo requests, in the results form
    l1_progress_bar (dict): object to store info on progress bar to show progress through three 
        steps of highest level view of tests-- general tests, field tests, and custom tests; it
        has the following form:
        name (string): name of progress bar (shouldn't change from "l1")
        active (bool): whether the progress bar should be printed
        progress_bar (TimerBar): object to contain information about progress
        current_step (integer): current step in the process
    l2_progress_bar (dict): object to store info on progress bar to show progress through next 
        level of hierarchy of tests (e.g, progress through each of fields for field tests, etc.)
        it will have the same form as l1_progress_bar explained above with name of "l2"; when
        starting a fresh l3 process, the 'steps' attribute of the TimerBar object should be
        updated to the total number of anticipated steps of the l3 process and the suffix should
        be updated through the TimerBar's 'suffix_update(<suffix string>)' method
    l3_progress_bar (dict): object to store info on progress bar to show progress through next 
        level of hierarchy of tests (e.g, progress through each sub test for a given field for
        field tests, etc.) it will have the same form as l1_progress_bar explained above with
        name of "l3"; when starting a fresh l3 process, the 'steps' attribute of the TimerBar
        object should be updated to the total number of anticipated steps of the l3 process and
        the suffix should be updated through the TimerBar's 'suffix_update(<suffix string>)'
        method

    -- non-input attributes --
    total_predo_issues (integer): running count of failed attempts at predo
    total_test_issues (integer): running count of unexpected results
    total_undo_issues (integer): running count of failed attempts at undo
    

    -- class constants
    _general_test_field (string): name to put in 'field' attribute for output for non-field
        specific tests
    _log_init (dict): initial value for log
    _l1_init (dict): initial value for l1_progress_bar
    _l2_init (dict): initial value for l2_progress_bar
    _l3_init (dict): initial value for l3_progress_bar


    -- methods (see method for inputs, etc.) --
    update_fields: updates a field of an object within APITester, including any fields that should
        match such changes
    add_issue: adds an issue count to various counters as needed
    add_result: adds results to the result attribute of the object
    update_progress_bars: updates progress bar and prints all active progress bars
    run_one_api: runs one api (predo, test, undo)
    run_one_test: runs the predo, test, and undo and logs the results
    run_general_tests: runs all standard general tests
    run_one_field: runs all standard field-specific tests for one specific field
    run_all_tests: runs general tests, all field tests, custom tests then sythesizes results
    clear_results: clears/resets pertinent variables; likely used before running all tests
    rerun_rests: reruns tests, clearing results and other pertinent fields, then runs all tests
    run_custom_inputs: runs all tests specified by the custom_inputs attribute

    test_fields notes:
        The structure of test_fields should be as follows: {
            'test_field' (string): name of the field being tested
            'test_type' (string): data type of field (can be one of the following: 'string',
                'integer', 'float', 'boolean', 'array', 'date', 'password',
                'email', 'original_password'; 'original_password' included so as to avoid scrutiny
                of other password criteria since scrutiny might change since original password was
                created)
            'field_parameters' (dict): contains various parameters to be used in tests
                done on the field. The following are valid values and circumstances in which
                they can be used:
                    'min' (integer): minimum value possible (integer/float fields/array_type)
                    'min_inc' (bool): inclusive minimum bound; def=True (integer/float
                        fields/array_type)
                    'min' (integer): maximum value possible (integer/float fields/array_type)
                    'min_inc' (bool): inclusive maximum bound; def=True
                        (integer/float fields/array_type)
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
            'array_type' (string): data type of values in array ('string', 'integer', 'float',
                'boolean', 'date'); default is None (for non-array test_type)
        }
    
    predo/test/undo/final_undo notes:
        The focus of the object is on a test API, but space is provided to run other APIs that
        allow the database to not accumulate/be depleted of objects. A 'predo' API will be done
        before the test is run-- this can be helpful if testing a delete function so that an
        document can be created before running the delete test to then be deleted. An 'undo' API
        will be done after the test is run-- this can be helpful to either delete documents
        created by the test or revert documents to their original value. Either way, specific
        test documents should be used for these APIs so as to not make unwanted changes to your
        database. The general form of these tests should be as follows: {
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
        *for header, body, and url_ids, values can either be explicit inputs (e.g.,
            'application/json' for 'Content-Type' in headers) or referenced values from the log.
            Referenced values from the log will have the following form:
                referenced_value (bool): flag to run referenced value calc; should be True 
                sources (string): either 'predo', 'test', or 'redo' depending on which request
                    gives the needed information
                component (string): either 'body', 'header', or 'response' (possibly 'url_id')
                location (string): directory of value to be found (use "." to get to nested layers
                    and [<ind>] to get the <ind> index of an array within an object
            <field> is also something that can be used as a key in header or body or as a location
            in any of the three inputs; <field> will be replaced with the current test field
            some example inputs are as follows, each of the three coming from different tests:
            1. 'header': {'token': {'referenced_value': True, 'source': 'test', 'component': 'body', 'location': '_id'}}
            2. 'body': {'<field>': {'referenced_value': True, 'source': 'predo', 'component': 'body', 'location': '<field>'}}
            3. 'url_ids': [{'referenced_value': True, 'source': 'predo', 'component': 'body', 'location': '_id'}]
            locations can be nested values as explained in the location description above

    custom_inputs notes:
        custom_inputs is an array of dict with the form below used that uses the same internal
            methods to run tests (including using test url/function and running any predo or undo requests), but using any
            combination of input custom header, body, and url_ids:
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
        
    
    custom_tests notes:
        the custom_tests is an array of dict with the form below that are used to run custom
        tests. Here is the structure of those dict:
        function (function): the customer function to be run by the APITester object. It must have
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
                    running obj.add_issue(obj.total_custom_test_issues)
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
    '''
    _general_test_field = '**General**'
    _log_init = {'predo': {}, 'test': {}, 'undo': {}}
    _l1_init = {'name': 'l1', 'active': True, 'progress_bar': TimerBar(steps=0, print_after=True), 'current_step': -1, 'suffix': ' {} / {}', 'issues': 0}
    _l2_init = {'name': 'l2', 'active': False, 'progress_bar': TimerBar(steps=0, print_after=True), 'current_step': -1, 'suffix': ' {} / {}', 'issues': 0}
    _l3_init = {'name': 'l3', 'active': False, 'progress_bar': TimerBar(steps=0, print_after=True), 'current_step': -1, 'suffix': ' {} / {} tests', 'issues': 0}

    def __init__(self,
                 base_url,
                 test_fields = None,
                 predo = None,
                 test = None,
                 undo = None,
                 custom_inputs=None,
                 custom_tests = None,
                 matching_fields = None,
                 delete_value = None,
                 print_status = False,
                 print_json = False,
                 print_progress = True,
                 display_refresh = True,
                 min_print_wait = 0.04,
                 tests_summary = None,
                 log = None,
                 results = None,
                 current_result = None,
                 tests_summary_by_field = None,
                 failed_predo = None,
                 failed_test = None,
                 failed_undo = None,
                 l1_progress_bar = None,
                 l2_progress_bar = None,
                 l3_progress_bar = None,
                ):
        
        self.base_url = base_url
        self.test_fields = test_fields if test_fields is not None else []
        self.predo = predo if predo is not None else None
        self.test = test if test is not None else None
        self.undo = undo if undo is not None else None
        self.custom_inputs = custom_inputs if custom_inputs is not None else []
        self.custom_tests = custom_tests if custom_tests is not None else []
        self.matching_fields = matching_fields if matching_fields is not None else []
        self.delete_value = delete_value
        self.print_status = print_status
        self.print_json = print_json
        self.print_progress = print_progress
        self.display_refresh = display_refresh
        self.min_print_wait = min_print_wait

        self.tests_summary = tests_summary if tests_summary is not None else {}
        self.log = log if log is not None else copy.deepcopy(self._log_init)
        self.l1_progress_bar = l1_progress_bar if l1_progress_bar is not None else copy.deepcopy(self._l1_init)
        self.l2_progress_bar = l2_progress_bar if l2_progress_bar is not None else copy.deepcopy(self._l2_init)
        self.l3_progress_bar = l3_progress_bar if l3_progress_bar is not None else copy.deepcopy(self._l3_init)
        
        self.results = results if results is not None else []
        self.current_result = current_result if current_result is not None else {}
        self.tests_summary_by_field = tests_summary_by_field if tests_summary_by_field is not None else []
        
        self.failed_predo = failed_predo if failed_predo is not None else []
        self.failed_test = failed_test if failed_test is not None else []
        self.failed_undo = failed_undo if failed_undo is not None else []

        self.total_predo_issues = 0
        self.total_test_issues = 0
        self.total_undo_issues = 0
        self.total_custom_test_issues = 0

        self.last_print = time.perf_counter()
        return
    
    def update_fields(self, obj, field, new_value=None, delete=False, match_fields=True):
        '''
        updates a field of an object within APITester, including any fields that should match
            such changes
        
        -- inputs --
        obj (dict): object to be updated
        field (string): directory of value to be updated (use "." to get to nested layers and 
                        [<ind>] to get the <ind> index of an array within an object
        new_value (any): new value to be input into object (ommitted if delete=True)
        delete (bool): if True, will delete the attribute specified by field
        match_fields (bool): if True, will run update_fields on fields specified in
                             self.matching fields to match the target field
        
        Notes: uses general update_field function and associated inputs, but adds match_fields
        ability so that if there are any other fields than the one directly being changed that
        should match that change (e.g., password + passwordConfirmation, etc.) that that value
        will be changed as well. Setting match_fields to False will forego that process and only
        change the target value, a feature intended to be used in test to ensure that API fails
        when two values that should be the same are different 

        -- outputs --
        obj (dict): updated object 
        '''
        obj = update_field_value(obj, field, new_value=new_value, delete=delete)
        
        for matches in self.matching_fields:
            if field in matches and match_fields:
                for val in matches:
                    if val != field:
                        obj = update_field_value(obj, val, new_value=new_value, delete=delete)
        return obj

    def add_issue(self, issue_tracker):
        '''
        adds an issue count to various counters as needed

        -- inputs --
        issue_tracker (object): attribute of self that needs to be updated; should be one of the
            following: self.total_predo_issues, self.total_test_issues, self.total_undo_issues,
            self.total_custom_test_issues
        
        -- outputs --
        None
        '''
        if issue_tracker not in [self.total_predo_issues,
                                 self.total_test_issues,
                                 self.total_undo_issues,
                                 self.total_custom_test_issues]:
            raise ValueError('issue_tracker shoudl be one of the following: self.total_predo_issues '\
                ', self.total_test_issues, self.total_undo_issues, self.total_custom_test_issues')

        issue_tracker += 1
        self.l1_progress_bar['issues'] += 1
        self.l2_progress_bar['issues'] += 1
        self.l3_progress_bar['issues'] += 1
        return
    
    def add_result(self, result):
        '''
        adds results to the result attribute of the object
        
        -- inputs --
        result (list or dict): the result(s) to be added, can either be added one at a time with a
            dict input that uses the result_template function to create the proper object or can be
            added multiple at a time using a list input of objects that use the result_template
            function to create the proper object

        -- outputs --
        None
        '''
        if isinstance(result, list):
            self.results.extend(result)
        elif isinstance(result, dict):
            self.results.append(result)

        self.current_result = {}
        return

    def update_progress_bars(self, value_update={}, suffix_update={}, print_progress_override=None):
        '''
        updates progress bar and prints all active progress bars

        -- inputs --
        value_update (dict): object of new values for each of the level's current values; should have
            form below-- if any values are missing, will maintain same value:
            l1 (integer): updated value of l1 current step
            l2 (integer): updated value of l2 current step
            l3 (integer): updated value of l3 current step
        suffix_update (dict): object of suffix updates if applicable; should have form below-- if
            any values are missing, will take maintain previous value:
            l1 (string): suffix update for l1_progress_bar; must contain 2x '{}' to be filled with
                current step and total steps
            l2 (string): suffix update for l2_progress_bar; must contain 2x '{}' to be filled with
                current step and total steps
            l3 (string): suffix update for l3_progress_bar; must contain 2x '{}' to be filled with
                current step and total steps
        print_progress_override (bool): temporarily override self.print_progress

        -- outputs --
        None
        '''
        if print_progress_override:
            original_pp = self.print_progress
            self.print_progress = print_progress_override

        bars = [self.l1_progress_bar, self.l2_progress_bar, self.l3_progress_bar]

        if self.display_refresh and self.print_progress:
            time.sleep(max(0, self.min_print_wait - (time.perf_counter() - self.last_print)))
            disp.clear_output(wait=True)

        for bar in bars:
            if bar['active']:
                bar_name = bar['name']
                # update current step if needed
                if bar_name in value_update:
                    bar['current_step'] = value_update[bar_name]
                # update suffix if needed
                if bar_name in suffix_update:
                    suffix = suffix_update[bar_name]
                    if suffix.count('{}') != 2:
                        raise ValueError(f"suffix_update for {bar_name} does not has {suffix.count('{}')}x'{{}}' not 2x'{{}}'")
                    bar['suffix'] = suffix
                bar['progress_bar'].suffix_update(bar['suffix'].format(bar['current_step']+1, bar['progress_bar'].steps) + f" ({bar['issues']} issues)")
                if self.print_progress:
                    print(bar['progress_bar'].text_at_step(bar['current_step']))
                    self.last_print = time.perf_counter()

        if print_progress_override:
            self.print_progress = original_pp
        return
    
    def run_one_api(self, api, test_field):
        '''
        runs one api (predo, test, undo)
        
        -- inputs --
        api (string): which api object is being tested ('predo', 'test', or 'undo')
        test_field (string): field currently being tested

        -- outputs --
        api_input (dict): inputs for the api request with the following structure:
            url (string): url used to make the call
            header (dict): object sent as header
            body (dict): object sent as body
        success (bool): whether the api call was success (200s response)
        out_json (dict): json of the response of the api (or dict notifying user of server error)
        response (obj): request response object in its entirety
        '''
        
        if api == 'predo':
            api_obj = self.predo
        elif api == 'test':
            api_obj = self.test
        elif api == 'undo':
            api_obj = self.undo
        else:
            raise ValueError(f'api input must be "predo", "test", or "undo"; "{api}" not acceptable')

        input_url_ids = find_ids_vals(api_obj, self.log, test_field)
        input_url = update_url_id(self.base_url+api_obj['url'], input_url_ids)
        input_header = find_hb_vals(api_obj, 'header', self.log, test_field, self.delete_value)
        input_body = find_hb_vals(api_obj, 'body', self.log, test_field, self.delete_value)

        api_input = {
            'url': input_url,
            'header': input_header,
            'body': input_body
            }

        response = api_obj['function'](api_input['url'],headers=api_input['header'],json=api_input['body'])
        success = (response.status_code // 100 == 2)
        server_error =  (response.status_code // 100) % 10 == 5
        url_not_found = response.status_code == 404
        
        if server_error:
            out_json = {'error': 'server error: see server console for more details'}
        elif url_not_found:
            out_json = {'error': f"url error: url not found ({api_input['url']})"}
        else:
            try:
                out_json = response.json()
            except:
                out_json = {'error': f"unknown error: response status code = {response.status_code}"}
        
        if self.print_status:
            if success:
                print(f'{api} request successful')
            else:
                print(f'{api} request failed with status code: {response.status_code}')

        if self.print_json and success:
            pretty_json = json.dumps(out_json, indent=4, sort_keys=True)
            print(pretty_json)
        
        self.log[api] = {
            'url': api_input['url'],
            'header': api_input['header'],
            'body': api_input['body'],
            'response': out_json,
            'url_ids': input_url_ids,
            'api_result': success,
            'field_index': self.l2_progress_bar['current_step'] + 1,
            'test_index': self.l3_progress_bar['current_step'] + 1
        }
        
        return api_input, success, out_json, response
    
    def run_one_test(self, test_name, error, field, test_expected_api_result, test_header=None, test_body=None, test_url_ids=None, test_source='Not Provided'):
        '''
        runs the predo, test, and undo and logs the results

        -- inputs --
        test_name (string): name of the test being conducted
        error (string): error description if expected results not achieved
        field (string): field being tested
        test_expected_api_result (bool): whether the test api is expected to succeed (True) or not
            (False)
        test_header (dict): json object that if provided will be set to test['header'] before
            running test API request
        test_body (dict): json object that if provided will be set to test['body'] before running
            test API request
        test_url_ids (list): array of url_ids that if provided will be set to test['url_ids'] before
            running test API request

        -- outputs --
        expected_result (bool): whether the api produced the expected result (success or failure)
        '''
        first_field = (self.l2_progress_bar['current_step']+1 == 0) if self.l2_progress_bar['active'] else (self.l3_progress_bar['current_step']+1 == 0)
        
        predo_input = None
        predo_status = 'No predo as part of this tester'
        predo_response = None
        predo_json = None
        if self.predo:
            run_predo = False
            if first_field or not self.predo['on_success']:
                run_predo = True
            elif self.predo['on_success'] and 'api_result' in self.log['test']:
                if self.log['test']['api_result']:
                    run_predo = True
            if run_predo:
                predo_input, predo_success, predo_json, predo_response = self.run_one_api('predo', field)
                if predo_success:
                    predo_status = 'predo successful'
                else:
                    self.add_issue(self.total_predo_issues)
                    predo_status = 'predo attemped and failed'
            else:
                if not 'api_result' in self.log['test']:
                    predo_status = f"'api_result' not in self.log['test']"
                else:
                    predo_status = f"last test api request not successful (self.log.test." \
                                   f"api_result={self.log['test']['api_result']})"
        self.current_result= result_template(
            test_expected_api_result,
            test_name,
            field,
            predo_input,
            predo_status,
            predo_response,
            predo_json,
            test_source
        )
        
        test_input = None
        test_status = 'No test as part of this tester'
        test_response = None
        test_json = None
        test_success = False
        if self.test:
            if test_header is not None:
                original_header = self.test['header']
                self.test['header'] = test_header
            if test_body is not None:
                original_body = self.test['body']
                self.test['body'] = test_body
            if test_url_ids is not None:
                original_url_ids = self.test['url_ids']
                self.test['url_ids'] = test_url_ids
            test_input, test_success, test_json, test_response = self.run_one_api('test', field)
            
            # process result for output
            expected_result = (test_expected_api_result == test_success)

            if expected_result:
                test_status = 'expected results achieved'
            else:
                self.add_issue(self.total_test_issues)
                test_status = f'test ran, but expected results not achieve ({test_success} ' \
                                f'occured but expected {test_expected_api_result})'
            if test_header is not None:
                self.test['header'] = original_header
            if test_body is not None:
                self.test['body'] = original_body
            if test_url_ids is not None:
                self.test['url_ids'] = original_url_ids
                
        self.current_result= result_template(
            expected_result,
            test_expected_api_result,
            test_name,
            error,
            field,
            predo_input,
            predo_status,
            predo_response,
            predo_json,
            test_input,
            test_status,
            test_response,
            test_json,
            test_source
        )
        
        # run if undo['on_success'] is false or if the undo was successful
        undo_input = None
        undo_status = 'No undo as part of this tester'
        undo_response = None
        undo_json = None
        if self.undo:
            if (self.undo['on_success'] and test_success) or not self.undo['on_success']:
                undo_input, undo_success, undo_json, undo_response = self.run_one_api('undo', field)
                if undo_success:
                    undo_status = 'undo successful'
                else:
                    self.add_issue(self.total_undo_issues)
                    undo_status = 'undo not successful'
            else:
                undo_status = 'undo not run because test api request was not successful'

        self.current_result= result_template(
            expected_result,
            test_expected_api_result,
            test_name,
            error,
            field,
            predo_input,
            predo_status,
            predo_response,
            predo_json,
            test_input,
            test_status,
            test_response,
            test_json,
            undo_input,
            undo_status,
            undo_response,
            undo_json,
            test_source
        )
        
        self.update_progress_bars({'l3': self.l3_progress_bar['current_step']+1})


        self.add_result(result_template(
            expected_result,
            test_expected_api_result,
            test_name,
            error,
            field,
            predo_input,
            predo_status,
            predo_response,
            predo_json,
            test_input,
            test_status,
            test_response,
            test_json,
            undo_input,
            undo_status,
            undo_response,
            undo_json,
            test_source
        ))
        
        return expected_result
    
    def run_general_tests(self, placeholder='<id>'):
        '''
        runs all standard general tests

        -- inputs --
        placeholder (string): the string in urls that will be replaced by ids

        -- outputs --
        None

        -- test hierarchy --
        I. General
            A. acceptable base case
        II. Access (private)
            A. No token
            B. 'None' for token
            C. Shortened token
            D. Lengthened token
        III. URL IDs
            Loop through all IDs and do following for each focus:
            A. Exclude id of focus
            B. Add something to id of focus
            C. Remove something from id of focus
        '''
        
        test_input = copy.deepcopy(self.test['body']) #find_hb_vals(self.test, 'body', self.log, self._general_test_field)
        test_field = self._general_test_field
        test_header = copy.deepcopy(self.test['header']) #find_hb_vals(self.test, 'header', self.log, self._general_test_field)
        test_url_ids = copy.deepcopy(self.test['url_ids']) #find_ids_vals(self.test, self.log, self._general_test_field)

        # Count expected tests ---------------------------------------------------------------------

        expected_tests = 1 #if any(test_input) else 0 # 1 base test
        expected_tests += 4 if 'X-Auth-Token' in test_header else 0
        expected_tests += len(test_url_ids)*3

        self.l3_progress_bar['progress_bar'].steps = expected_tests
        
        # Define helper functions to run test ------------------------------------------------------

        def lengthen(val):
            return val + 'a'
        def shorten(val):
            return val[-1]

        def run_general_test(test_name,
                              error,
                              test_expected_api_result,
                              new_value='!!not input!!',
                              match_fields=True,
                              test_header=None,
                              test_url_ids=None):
            if new_value == '!!not input!!':
                test_body = test_input
            elif new_value == '!!delete!!':
                test_body = self.update_fields(test_input, test_field, delete=True, match_fields=match_fields)
            else:
                test_body = self.update_fields(test_input, test_field, new_value=new_value, match_fields=match_fields)
            expected_result = self.run_one_test(
                test_name=test_name,
                error=error,
                field=test_field,
                test_expected_api_result=test_expected_api_result,
                test_header=test_header,
                test_body=test_body,
                test_url_ids=test_url_ids,
                test_source=self._general_test_field
            )

            return
        
        # General tests ---------------------------------------------------------------------------

        # IA. test base case
##        if any(test_input):
        run_general_test(test_name='acceptable base case',
                        error='base case not accepted',
                        test_expected_api_result=True)

        # Access tests (private) ------------------------------------------------------------------

##        test_header = copy.deepcopy(self.test['header'])

        if 'X-Auth-Token' in test_header:
            original_token = test_header['X-Auth-Token']
##            original_token = copy.deepcopy(self.test['header']['X-Auth-Token'])
            temp_header = copy.deepcopy(test_header)

            # IIA. no token
            ## TO DO some issue here, things aren't working
            del temp_header['X-Auth-Token']
            run_general_test('no token (delete)',
                             'success despite no token',
                             False,
                             test_header=temp_header)

            # IIB. none value given for token
            temp_header['X-Auth-Token'] = None
            run_general_test('none value for token',
                             'success despite none value for token',
                             False,
                             test_header=temp_header)

            temp_header = copy.deepcopy(test_header)
            # IIC. shortened token
            if isinstance(test_header['X-Auth-Token'], dict):
                temp_header['X-Auth-Token']['function'] = shorten
            else: 
                temp_header['X-Auth-Token'] = original_token[:-1]
            run_general_test('shortened token',
                             'success despite token being partially shortened',
                             False,
                             test_header=temp_header)

            # IID. lengthened token
            if isinstance(test_header['X-Auth-Token'], dict):
                temp_header['X-Auth-Token']['function'] = lengthen
            else: 
                temp_header['X-Auth-Token'] = original_token + 'a'
            run_general_test('lengthened token',
                             'success despite token being lengthened',
                             False,
                             test_header=temp_header)


        # URL IDs tests ---------------------------------------------------------------------------

        if len(test_url_ids) > 0:
            original_additional_url = copy.deepcopy(self.test['url'])
            original_url_ids = test_url_ids

            start_url_obj = {'url': original_additional_url, 'ids': original_url_ids}

            for i, val_i in enumerate(original_url_ids):
                nothing = copy.deepcopy(start_url_obj)
                too_long = copy.deepcopy(start_url_obj)
                too_short = copy.deepcopy(start_url_obj)
                nothing['ids'] = []

                for j, val_j in enumerate(original_url_ids):
                    if i == j:
                        nothing['url'] = nothing['url'].replace('/'+placeholder, '<gone>', 1)
                        if isinstance(too_long['ids'][j], dict):
                            too_long['ids'][j]['function'] = lengthen
                        else: 
                            too_long['ids'][j] = too_long['ids'][j] + 'a'
                        if isinstance(too_short['ids'][j], dict):
                            too_short['ids'][j]['function'] = shorten
                        else:
                            too_short['ids'][j] = too_short['ids'][j][:-1]
                    else:
                        nothing['url'] = nothing['url'].replace(placeholder, '<still_here>', 1)
                        nothing['ids'].append(val_j)
                nothing['url'] = nothing['url'].replace('<gone>', '')
                nothing['url'] = nothing['url'].replace('<still_here>', placeholder)

                # IIIA. exclude id of focus
                self.test['url'] = nothing['url']
                run_general_test(f'exclude id piece #{i}',
                                 f'success when id piece #{i} excluded',
                                 False,
                                 test_url_ids=nothing['ids'])

                # IIIB. add something to id of focus
                self.test['url'] = too_long['url']
                run_general_test(f'added extra text to id piece #{i}',
                                 f'success when id piece #{i} was elongated',
                                 False,
                                 test_url_ids=too_long['ids'])

                # IIIC. take away piece of current id
                self.test['url'] = too_short['url']
                run_general_test(f'text removed from id piece #{i}',
                                 f'success when id piece #{i} was shortened',
                                 False,
                                 test_url_ids=too_short['ids'])
            
            self.test['url'] = original_additional_url

        ## Process results ------------------------------------------------------------------------
        
        self.tests_summary_by_field.append({
            'field': self._general_test_field,
            'passed_tests': sum([1 for obj in self.results if obj['field'] == test_field and obj['expected_result']]),
            'total_tests': sum([1 for obj in self.results if obj['field'] == test_field]),
            'expected_tests': expected_tests
        })

        return

    def run_one_field(self, index, sample_size=5):
        '''
        runs all standard field-specific tests for one specific field

        -- inputs --
        index (int): index of the field of focus in the test_fields array
        sample_size (int): number of random arrays to test an array datatype that has an array of
            possible values
        
        -- outputs --
        None

        -- test hierarchy
        I. General
            A. (non-api) Field either not required or is in test_input
            B. (non-api) Field type acceptable
            C. Acceptable input
            D. Null value
            E. No value (deleted)
            F. Delete value
        II. Min (min in field_parameters)
            A. below boundary
            B. at boundary
            C. above boundary
        III. Max (max in field_parameters)
            A. above boundary
            B. at boundary
            C. below boundary
        IV. Email (test_type = 'email')
            A. Correct email form (loop through different combos of components)
            B. Email already in database (if existing_email in field_parameters)
        V. Matching values (field in self.matching_fields)
            A. Make matching values different
        VI. Password (test_type = 'password')
            A. Min length of password (if min_length in field parameters)
            B. Max length of password (if max_length in field parameters)
            C. Upper case in password (if upper_case in field parameters)
            D. Lower case in password (if lower_case in field parameters)
            E. Number in password (if number in field parameters)
            F. Special Character in password (if special_character in field parameters)
        VII. Non-array
            A. Array of possible inputs (array in field_parameters)
                1. Test each value in possible inputs array
                2. test random value outside of possible array
            B. Wrong datatypes (multiple)
        VIII. Array
            A. Empty array
            B. Wrong datatypes (multiple)
            C. Duplicate (if duplicate is True in field_parameters)
                1. Duplicate array values
            D. Array of possible inputs (array in field_parameters)
                1. Each value individually from possible inputs array
                2. Single value outside of possible array
                3. Random sample of values in possible inputs array
                4. Single value outside of possible array with random sample of values in possible
                    inputs array
                5. All values in possible inputs array
                6. Single value outside of possible array with all values in possible inputs array 

        '''
        current_field = self.test_fields[index]
        test_field = current_field['test_field']
        test_type = current_field['test_type']
        field_parameters = current_field['field_parameters']
        required = current_field['required']
        default = current_field['default']
        deletable = current_field['deletable']
        array_type = current_field['array_type']
        acceptable_input = current_field['acceptable_input']

        # pull out values from test_acceptable values
        min_val = field_parameters['min'] if 'min' in field_parameters else None
        min_inc = field_parameters['min_inc'] if 'min_inc' in field_parameters else None
        max_val = field_parameters['max'] if 'max' in field_parameters else None
        max_inc = field_parameters['max_inc'] if 'max_inc' in field_parameters else None
        array = field_parameters['array'] if 'array' in field_parameters else None
        excluded = field_parameters['excluded'] if 'excluded' in field_parameters else None
        duplicates = field_parameters['duplicates'] if 'duplicates' in field_parameters else None
        min_length = field_parameters['min_length'] if 'min_length' in field_parameters else None
        max_length = field_parameters['max_length'] if 'max_length' in field_parameters else None
        upper_case = field_parameters['upper_case'] if 'upper_case' in field_parameters else None
        lower_case = field_parameters['lower_case'] if 'lower_case' in field_parameters else None
        number = field_parameters['number'] if 'number' in field_parameters else None
        special_character = field_parameters['special_character'] if 'special_character' in field_parameters else None
        existing_email = field_parameters['existing_email'] if 'existing_email' in field_parameters else None

        dtype_test_values = {
            'string': 'a',
            'integer': 1,
            'float': 1.1,
            'boolean': True
            }

        test_input = copy.deepcopy(acceptable_input)

        # Count expected tests ---------------------------------------------------------------------
        
        expected_tests = 5 # general tests
        expected_tests += 1 if 'delete_field_test' in self.test and self.test['delete_field_test'] else 0
        expected_tests += 3 if min_val else 0 # 3 min tests
        expected_tests += 3 if max_val else 0 # 3 max tests
        expected_tests += 2**5 + 1 if test_type=='email' else 0
        for matching_field_set in self.matching_fields:
            expected_tests += 1 if test_field in matching_field_set else 0
        if test_type == 'password':
            if min_length:
                expected_tests += min_length+2
            expected_tests += 3 if max_length else 0
            expected_tests += 1 if upper_case else 0
            expected_tests += 1 if lower_case else 0
            expected_tests += 1 if number else 0
            expected_tests += 1 if special_character else 0
        if test_type !='array':
            if array:
                expected_tests += len(array) + 1
            if test_type not in ['string', 'password', 'email', 'original_password']:
                for key, value in dtype_test_values.items():
                    if (key != test_type and # don't need to test current test_type
                        not (key=='integer' and test_type=='float')): # integer is acceptable for floats
                        expected_tests += 1
        elif test_type == 'array':
            expected_tests += 1
            if array_type and array_type not in ['array', 'string']:
                for key, value in dtype_test_values.items():
                    if key != array_type:
                        expected_tests += 1
            expected_tests += 1 if duplicates else 0
            if array: # array of possible values
                expected_tests += len(array) + sample_size + 1
                expected_tests += 1 + sample_size + 1
        
        self.l3_progress_bar['progress_bar'].steps = expected_tests
        # Define method specific function to run test ---------------------------------------------

        def run_field_test(test_name,
                              error,
                              test_expected_api_result,
                              new_value='!!not input!!',
                              match_fields=True,
                              test_header=None,
                              test_url_ids=None):
            if new_value == '!!not input!!':
                test_body = test_input
            elif new_value == '!!delete!!':
                test_body = self.update_fields(test_input, test_field, delete=True, match_fields=match_fields)
            else:
                test_body = self.update_fields(test_input, test_field, new_value=new_value, match_fields=match_fields)

            expected_result = self.run_one_test(
                test_name=test_name,
                error=error,
                field=test_field,
                test_expected_api_result=test_expected_api_result,
                test_header=test_header,
                test_body=test_body,
                test_url_ids=test_url_ids,
                test_source='Field Tests'
                                                
            )

            return

        # General field tests ---------------------------------------------------------------------

        # IA. (non-api test) check to make sure test field is input if required
        test_result = not (required and not check_field(test_input, test_field) and not default)
        self.add_result(result_template(
            test_result, False, 'test_field in input', 'test_field not in test_input', test_field, test_source='Field Tests'
            ))
        self.update_progress_bars({'l3': self.l3_progress_bar['current_step']+1})

        # IB. (non-api test) check to make sure test_type is an acceptable value
        test_result =  test_type in ['string', 'integer', 'float', 'boolean', 'array', 'date', 'password', 'password_confirmation', 'email', 'original_password', 'dict']
        self.add_result(result_template(
            test_result, False, 'correct type', f'test_type {test_type} not an acceptable value', test_field, test_source='Field Tests'
            ))
        self.update_progress_bars({'l3': self.l3_progress_bar['current_step']+1})

        # IC. test acceptable input
        run_field_test(test_name='acceptable input',
                       error='base case not accepted',
                       test_expected_api_result=True)

        # ID. test when null value for field
        run_field_test(test_name='null field',
                       error=f'null values accepted for {test_field}',
                       test_expected_api_result=False,
                       new_value=None)
        
        # IE. test when no value for input field
        run_field_test(test_name='no value',
                       error=f'null values accepted for {test_field}',
                       test_expected_api_result=(not required or default),
                       new_value='!!delete!!')
        
        # IF. test if value can be deleted
        if 'delete_field_test' in self.test and self.test['delete_field_test']:
            run_field_test(test_name='delete value',
                           error=f'{test_field} not successfully deleted' if deletable else f'{self.delete_value} accepted as input even thought it shouldn\'t have been accepted',
                           test_expected_api_result=deletable,
                           new_value=self.delete_value)
            
        
        # Min tests -------------------------------------------------------------------------------

        if min_val:
            # IIA. below boundary
            run_field_test('min: below boundary',
                           f'success when lower bound breached',
                           False,
                           new_value=test_boundary(min_val, -1, test_type)) # min_val - 1 if test_type != 'array' else [min_val - 1])

            # IIB. at boundary
            temp_success = True
            if min_inc is not None:
                temp_success = min_inc                
            run_field_test('min: on boundary',
                           'failure when on min bound (expected success)' if temp_success else 'success when on min bound (expected failure)',
                           temp_success,
                           new_value=test_boundary(min_val, 0, test_type)) #min_val if test_type != 'array' else [min_val])

            # IIC. above boundary (within limits)
            run_field_test('min: above boundary',
                           f'failure when lower bound upheld',
                           True,
                           new_value=test_boundary(min_val, 1, test_type)) #min_val + 1  if test_type != 'array' else [min_val + 1])

        # Max tests -------------------------------------------------------------------------------

        if max_val: 
            # IIIA. above boundary
            run_field_test('max: above boundary',
                           f'success when upper bound breached',
                           False,
                           new_value=test_boundary(max_val, 1, test_type)) #max_val + 1 if test_type != 'array' else [max_val + 1])

            # IIIB. at boundary
            temp_success = True
            if max_inc is not None:
                temp_success = max_inc
            run_field_test('min: on boundary',
                           'failure when on max bound (expected success)' if temp_success else 'success when on max bound (expected failure)',
                           temp_success,
                           new_value=test_boundary(max_val, 0, test_type))#max_val if test_type != 'array' else [max_val])

            # IIIC. below boundary (within limits)
            run_field_test('max: below boundary',
                           f'failure when upper bound upheld',
                           True,
                           new_value=test_boundary(max_val, -1, test_type))#max_val - 1 if test_type != 'array' else [max_val - 1])

        # Email tests -----------------------------------------------------------------------------

        if test_type == 'email':
            email_pieces = ['before', '@', 'after', '.', 'end']
            scenarios = list(itertools.product([True, False], repeat=5))
            # IVA. correct email form
            for scenario in scenarios:
                temp_email = ''.join([email_pieces[i] if val else '' for i, val in enumerate(scenario)])            
                email_success = all(scenario)
                run_field_test('valid email',
                               'failed email when expecting success' if email_success else f'success email when expected failure ({temp_email})',
                               email_success,
                               new_value=temp_email)

            # IVB. existing email
            if existing_email:
                run_field_test('email already in database',
                               f'success despite using a duplicate email address ({existing_email})',
                               False,
                               new_value=existing_email)

        # Match fields tests ----------------------------------------------------------------------

        # VA make matching values different
        for matching_field_set in self.matching_fields:
            if test_field in matching_field_set:
                current_val = acceptable_input[test_field]

                if array:
                    if test_type == 'array':
                        updated_val = [array[0]] if current_val != [array[0]] else [array[1]]
                    else:
                        current_val_index = array.index(current_val)
                        updated_val_index = 0 if current_val_index != 0 else 1
                        updated_val = array[updated_val_index]
                elif test_type == 'array' and len(current_val) > 1:
                    updated_val = [current_val[0]]
                elif test_type == 'boolean' or array_type == 'boolean':
                    updated_val = not current_val
                    if array_type == 'boolean':
                        updated_val = [updated_val]
                elif test_type in ['password', 'original_password']:
                    updated_val = current_val + 'a'
                elif test_type == 'date' or array_type == 'date':
                    updated_val = '1/1/2000' 
                    if array_type == 'date':
                        updated_val = [updated_val]
                    # TO DO make this more dynamic (not worth effort right now)
                elif test_type == 'email' or array_type == 'email':
                    current_val = 'a' + current_val
                    if  array_type == 'email':
                        current_val = [current_val]
                elif min_val or max_val:
                    if test_type == 'array':
                        current_val = current_val[0]

                    dist_to_min = None if min_val is None else current_val - min_val
                    dist_to_max = None if max_val is None else current_val - max_val
                    if dist_to_min is None or dist_to_min > 1:
                        updated_val = current_val - 1
                    elif dist_to_max is None or dist_to_max > 1:
                        updated_val = current_val + 1
                    elif dist_to_min and dist_to_min <= 1 and test_type == 'float':
                        updated_val = current_val - dist_to_min/2
                    elif dist_to_max and dist_to_max <= 1 and test_type == 'float':
                        updated_val = current_val + dist_to_max/2
                    else:
                        raise ValueError(f'matching fields test is impossible for {test_field} given the min and max constraints')
                    
                    if test_type == 'array':
                        current_val = [current_val]
                        updated_val = [updated_val]
                else:
                    if test_type == 'array':
                        current_val = current_val[0]
                    updated_val = current_val + dtype_test_values[test_type]
                    if test_type == 'array':
                        current_val = [current_val]
                        updated_val = [updated_val]
                
                run_field_test('Different matching values',
                               f'Success despite different matching values for {test_field} ({matching_field_set})',
                               False,
                               new_value=updated_val,
                               match_fields=False)

        # Password tests --------------------------------------------------------------------------

        if test_type == 'password':
            acceptable_password = acceptable_input[test_field]

            if min_length:
                # VIA. password minimum length
                for i in range(min_length+2):
                    temp_password = acceptable_password[:i]
                    min_length_success = (i >= min_length)
                    run_field_test('password min length',
                                   f'failed min password when expecting success (length = {i})' if min_length_success else f'success min password when expected failure (length = {i})',
                                   min_length_success,
                                   new_value=temp_password)
                    
            if max_length:
                # VIB. password minimum length
                for i in range(max_length-1, max_length+2):
                    temp_password = acceptable_password[:i]
                    if len(temp_password) < i:
                        while len(temp_password) < i:
                            temp_password += temp_password[:i - len(temp_password)]
                    max_length_success = (i <= max_length)
                    run_field_test('password length',
                                   f'failed max password when expecting success (length = {i})' if max_length_success else f'success max password when expected failure (length = {i})',
                                   max_length_success,
                                   new_value=temp_password)
            
            if upper_case:
                # VIC. uppercase required
                run_field_test('password upper case required',
                               'Success when expected failure',
                               False,
                               new_value=acceptable_password.lower())
            
            if lower_case:
                # VID. lowercase required
                run_field_test('password lower case required',
                               'Success when expected failure',
                               False,
                               new_value=acceptable_password.upper())
            
            if number:
                # VIE. number required
                temp_password = re.sub(r'\d', '', acceptable_password)
                # make sure that password is proper length if needed
                if min_length is not None and len(temp_password) < min_length:
                    while len(temp_password) < min_length:
                        temp_password += temp_password[:min_length - len(temp_password)]
                if max_length is not None and len(temp_password) > max_length:
                    temp_password = temp_password[:max_length]
                run_field_test('password number required',
                               'Success when expected failure',
                               False,
                               new_value=temp_password)
            
            if special_character:
                # VIF. special character required
                temp_password = re.sub(r'[^a-zA-Z0-9]' ,'', acceptable_password)
                if min_length is not None and len(temp_password) < min_length:
                    while len(temp_password) < min_length:
                        temp_password += temp_password[:min_length - len(temp_password)]
                if max_length is not None and len(temp_password) > max_length:
                    temp_password = temp_password[:max_length]
                run_field_test('password special character required',
                               'Success when expected failure',
                               False,
                               new_value=temp_password)

        # Non-array tests -------------------------------------------------------------------------

        if test_type !='array':
            if array: # array of possible values
                if array and excluded is None or excluded in array:
                    raise ValueError("if 'array' is included in field_parameters, 'excluded' must " \
                                     "be inclueded as well and should not be in 'array'")

                for val in array:
                    # VIIA1. test all values
                    run_field_test('single values w/array of options (test all values)',
                                   f'failed for input value: {val}',
                                   True,
                                   new_value=val)
                    dummy = val
                # VIIA2. test  value outside of possible array (match datatype)
                run_field_test('single values with/array of options, value outside of array',
                               'Success when using value outside of value in possible array',
                               False,
                               new_value=excluded)

            if test_type not in ['string', 'password', 'email', 'original_password']:
                for key, value in dtype_test_values.items():
                    if (key != test_type and # don't need to test current test_type
                        not (key=='integer' and test_type=='float')): # integer is acceptable for floats
                        # VIIB. wrong data type
                        run_field_test('Wrong data type',
                                       f'type success when expected failure ({key} worked for {test_type})',
                                       False,
                                       new_value=value)

        # Array tests -----------------------------------------------------------------------------

        elif test_type == 'array':

            # VIIIA. empty array
            run_field_test('empty array',
                           'empty array accepted as input',
                           False,
                           new_value=[])

            if array_type and array_type not in ['array', 'string']:
                # VIIIB. array with wrong data type
                for key, value in dtype_test_values.items():
                    if key != array_type:
                        run_field_test('array wrong data type',
                                       f'type success when expected failure ({key} worked for {test_type})',
                                       False,
                                       new_value=[value])
            
            if duplicates is not None:
                # VIIIC1. duplicate array values
                acceptable_value = get_field_value(acceptable_input, test_field)[0]
                run_field_test('duplicate array values',
                               f'type success when duplicate values present',
                               duplicates,
                               new_value=[acceptable_value, acceptable_value])
            
            if array: # array of possible values
                if array and excluded is None or excluded in array:
                    raise ValueError("if 'array' is included in field_parameters, 'excluded' must " \
                                     "be inclueded as well and should not be in 'array'")
                
                # VIIID1. test each possible value in array
                for val in array:
                    run_field_test('array: all individual values',
                                   f'failed for single value: {val}',
                                   True,
                                   new_value=[val])
                
                # VIIID2. single value outside of possible array (match datatype)
                run_field_test('array: single value outside of possible array',
                               f'succssfully ran despite using value not in possible array: {excluded}',
                               False,
                               new_value=[excluded])
                
                # VIIID3. handful of random values from possible array
                for dummy in range(sample_size):
                    num_indices = random.randint(1, len(array))
                    random_indices = random.sample(range(len(array)), num_indices) # Select random non-repeated indices from the array
                    random_indices.sort() # sort in numerical order
                    random_array = [array[index] for index in random_indices] # Create the random array based on the selected indices
                    run_field_test('array: random mix of values',
                                   f'failed for random sampling of {test_field}: {array[random_array]}',
                                   True,
                                   new_value=random_array)
                    
                    # VIIID4. single value outside of possible array (match datatype) included
                    #   with handful of random values from possible array
                    random_array[0] = excluded
                    run_field_test('array: random mix of values with single value outside of possible array',
                                   f'succeeded for random sampling of {test_field}: {array[random_array]} with single value outside of possible array',
                                   False,
                                   new_value=random_array)
                
                # VIIID5. all values in possible array
                run_field_test('array: all values',
                               f'failed for an array of all possible values for {test_field}',
                               True,
                               new_value=array)
                
                # VIIID6. single value outside of possible array (match datatype) included
                #   with all values from possible array
                run_field_test('array: all values with single value outside of possible array',
                               f'succeeded for all values plus single value outside of possible array: {excluded}',
                               False,
                               new_value=array + [excluded])

        ## Process results ------------------------------------------------------------------------

        self.tests_summary_by_field.append({
            'field': test_field,
            'passed_tests': sum([1 for obj in self.results if obj['field'] == test_field and obj['expected_result']]),
            'total_tests': sum([1 for obj in self.results if obj['field'] == test_field]),
            'expected_tests': expected_tests
        })

        return

    def run_custom_inputs(self):
        '''
        runs all tests specified by the custom_inputs attribute

        -- inputs --
        None

        -- outputs --
        None
        '''

        def extract_input_base(obj, attr, alt_value):
            return alt_value if attr not in obj else obj[attr]

        for i, custom_input in enumerate(self.custom_inputs):
            def extract_input(attr, alt_value):
                return extract_input_base(custom_input, attr, alt_value)
            if 'test_expected_api_result' not in custom_input:
                raise ValueError(f'test_expected_api_result missing from custom_inputs test #{i}')
            test_name = extract_input('test_name', f'custom_inputs test #{i}')
            error = extract_input('error', f'error: custom_inputs test #{i}')
            field = extract_input('field', self._general_test_field)
            test_expected_api_result = extract_input('test_expected_api_result', 'err')
            test_header = extract_input('test_header', None)
            test_body = extract_input('test_body', None)
            test_url_ids = extract_input('test_url_ids', None)
            
            expected_result = self.run_one_test(
                test_name=test_name,
                error=error,
                field=field,
                test_expected_api_result=test_expected_api_result,
                test_header=test_header,
                test_body=test_body,
                test_url_ids=test_url_ids,
                test_source='Custom Inputs Test'
            )
            
            
        return
    
    def run_all_tests(self, print_status_override=None, print_json_override=None):
        '''
        runs general tests, all field tests, custom tests then sythesizes results

        -- inputs --
        print_status_override (bool): overrides the self.print_status value, resetting it at the end
        print_json_override (bool): overrides the self.print_json value, resetting it at the end

        -- outputs --
        None
        '''
        # process print statuses ------------------------------------------------------------------
        if print_status_override:
            original_ps = self.print_status
            self.print_status = print_status_override
        if print_json_override:
            original_pj = self.print_json
            self.print_json = print_json_override

        # setup progress bar ----------------------------------------------------------------------
        fields_contribution = 1 if len(self.test_fields) > 0 else 0
        custom_inputs_contribution = 1 if len(self.custom_inputs) > 0 else 0
        custom_contribution = 1 if len(self.custom_tests) > 0 else 0
        self.l1_progress_bar['progress_bar'].steps = 1 + fields_contribution + custom_inputs_contribution + custom_contribution
        self.l1_progress_bar['current_step'] = -1

        # run general tests -----------------------------------------------------------------------
        self.l1_progress_bar['suffix'] = ' {} / {} running general tests'
        self.l3_progress_bar['active'] = True
        self.run_general_tests()
        if self.test['final_undo'] and not self.log['test']['api_result']:
            self.run_one_api('test', self._general_test_field)
        self.l3_progress_bar['active'] = False
        self.l1_progress_bar['current_step'] += 1

        # run field tests ------------------------------------------------------------------------
        if len(self.test_fields) > 0:
            self.l1_progress_bar['suffix'] = ' {} / {} running field tests'
            self.l2_progress_bar['active'] = True
            self.l2_progress_bar['suffix'] = ' {} / {} fields tested'
            self.l2_progress_bar['progress_bar'].steps = len(self.test_fields)
            self.update_progress_bars()
            self.l3_progress_bar['active'] = True
            for i, field in enumerate(self.test_fields):
                self.l3_progress_bar['issues'] = 0
                self.run_one_field(i)
                self.update_progress_bars({'l2': i, 'l3': -1})
            if self.test['final_undo'] and not self.log['test']['api_result']:
                self.run_one_api('test', self._general_test_field)
            self.update_progress_bars({'l2': -1, 'l3': 0-1}, print_progress_override=False)
            self.l3_progress_bar['issues'] = 0
            self.l3_progress_bar['active'] = False
            self.l2_progress_bar['issues'] = 0
            self.l2_progress_bar['active'] = False
            self.l1_progress_bar['current_step'] += fields_contribution

        # run custom input test -------------------------------------------------------------------
        ## TO DO add code to ensure that progress bar works properly around this (might have to jump into run_custom_inputs function
        ##     TO DO also consider adding 'source' to output to say whether the test came from general, field, custom inputs or custom function,
        if len(self.custom_inputs) > 0:
            self.l1_progress_bar['suffix'] = ' {} / {} running custom inputs tests'
            self.l3_progress_bar['active'] = True
            self.l3_progress_bar['progress_bar'].steps = len(self.custom_inputs)
            self.l3_progress_bar['issues'] = 0
            self.update_progress_bars({'l3': -1})
            self.run_custom_inputs()
            if self.test['final_undo'] and not self.log['test']['api_result']:
                self.run_one_api('test', self._general_test_field)
            self.l3_progress_bar['issues'] = 0
            self.l3_progress_bar['active'] = False
            self.l1_progress_bar['current_step'] += custom_inputs_contribution

        # run custom tests ------------------------------------------------------------------------
        if len(self.custom_tests) > 0:
            self.l1_progress_bar['suffix'] = ' {} / {} running custom functions tests'
            self.l2_progress_bar['active'] = True
            self.l2_progress_bar['progress_bar'].steps = len(self.custom_tests)
            for i, test in enumerate(self.custom_tests):
                self.l2_progress_bar['suffix'] = ' {} / {} custom tests'
                custom_tests_out = test['function'](test['inputs'], self)
                self.add_result(custom_tests_out)

        # process results -------------------------------------------------------------------------
        self.l1_progress_bar['current_step'] += custom_contribution
        self.update_progress_bars()

        tests_summary = {
            'passed_tests': sum([obj['passed_tests'] for obj in self.tests_summary_by_field]),
            'total_tests': sum([obj['total_tests'] for obj in self.tests_summary_by_field]),
            'expected_tests': sum([obj['expected_tests'] for obj in self.tests_summary_by_field])
        }

        self.tests_summary = tests_summary
        self.failed_predo = [val for val in self.results if hasattr(val['predo_response'], 'status_code') and val['predo_response'].status_code // 100 != 2]
        self.failed_test = [val for val in self.results if not val['expected_result']]
        self.failed_undo = [val for val in self.results if hasattr(val['undo_response'], 'status_code') and val['undo_response'].status_code // 100 != 2]

        # reset print statuses --------------------------------------------------------------------
        if print_status_override:
            self.print_status = original_ps
        if print_json_override:
            self.print_json = original_pj
        return
    
    def clear_results(self):
        '''
        clears/resets pertinent variables; likely used before running all tests

        -- inputs --
        None

        -- outputs --
        None
        '''
        self.tests_summary = {}
        self.log = self._log_init
        self.l1_progress_bar = self._l1_init
        self.l2_progress_bar = self._l2_init
        self.l3_progress_bar = self._l3_init
        self.results = []
        self.tests_summary_by_field = []
        self.failed_predo = []
        self.failed_test = []
        self.failed_undo = []
        self.total_predo_issues = 0
        self.total_test_issues = 0
        self.total_undo_issues = 0
        self.total_custom_test_issues = 0
        self.last_print = time.perf_counter()
        return
    
    def rerun_rests(self):
        '''
        reruns tests, clearing results and other pertinent fields, then runs all tests

        -- inputs --
        None

        -- outputs --
        None
        '''
        self.clear_results()
        self.run_all_tests()
        return
