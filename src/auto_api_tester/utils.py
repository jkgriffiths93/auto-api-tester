import copy
import datetime as dt

def change_date(date_string, days_diff, input_form='%Y-%m-%d'):
    '''
    calculates days difference for a date string

    date_string (string): input date in string form
    days_diff (int): change in days to be calculated
    input_form (string): datetime input format
    '''
    date_obj = dt.datetime.strptime(date_string, input_form)
    new_date_obj = date_obj + dt.timedelta(days=days_diff)
    return new_date_obj.strftime('%Y-%m-%d')

def test_boundary(val, change, test_type):
    '''
    changes a value based on the data type to account for dates, arrays, and numbers
        potentially being changed when testing min and max values

    val (dynamic): the input value that is to be changed
    change (int): the increment by which the value is to be changed
    test_type (string): the data type being tested
    '''
    if test_type == 'date':
        return change_date(val, change)
    if test_type == 'array':
        return [val + change]
    return val + change

def check_field(inpt_obj, field):
    '''
    checks to see if a field of an object exists, including nested fields

    inpt_obj (dict): object to be checked
    field (string): directory of value to be checked (use "." to get to nested layers and 
                    [<ind>] to get the <ind> index of an array within an object)
    '''
    obj = copy.deepcopy(inpt_obj)
    
    keys = field.split('.')  # Split the field string by periods to get individual keys

    for key in keys:
        if key.endswith(']'):
            array_key, index_str = key.split('[')
            index = int(index_str[:-1])
            if array_key not in obj or not isinstance(obj[array_key], list) or len(obj[array_key]) <= index:
                return False
            obj = obj[array_key][index]
        else:
            if key not in obj:
                return False
            obj = obj[key]
    return True

def update_field_value(inpt_obj, field, new_value=None, delete=False):
    '''
    updates a field of an object, including nested values

    inpt_obj (dict): object to be updated
    field (string): directory of value to be updated (use "." to get to nested layers and 
                    [<ind>] to get the <ind> index of an array within an object)
    new_value (any): new value to be input into object (ommitted if delete=True)
    delete (bool): if True, will delete the attribute specified by field
    '''
    out_obj = copy.deepcopy(inpt_obj)
    obj = out_obj
    keys = field.split('.')  # Split the field string by periods to get individual keys
    last_key = keys[-1]  # Get the last key to perform modification or deletion

    for key in keys[:-1]:
        if key.endswith(']'):  # If the key ends with ']', it indicates an array access
            index = int(key[key.index('[') + 1: -1])  # Extract the index value from within brackets
            array_key = key[:key.index('[')]  # Get the array key
            if array_key not in obj:
                obj[array_key] = []  # Create an empty list if the array key doesn't exist
            obj = obj[array_key]  # Get the object corresponding to the array
            if index >= len(obj):
                obj.extend([None] * (index + 1 - len(obj)))  # Extend the list if the index is out of range
            obj = obj[index]  # Access the specific element in the array
        else:
            if key not in obj:
                obj[key] = {}  # Create an empty dictionary if the key doesn't exist
            obj = obj[key]  # Access the object using the key

    if delete:
        if last_key.endswith(']'):
            index = int(last_key[last_key.index('[') + 1: -1])
            array = obj[last_key[:last_key.index('[')]]
            if index < len(array):
                del array[index]
        else:
            if last_key in obj:
                del obj[last_key]
    else:
        if last_key.endswith(']'):
            index = int(last_key[last_key.index('[') + 1: -1])
            array = obj[last_key[:last_key.index('[')]]
            if index < len(array):
                array[index] = new_value
        else:
            obj[last_key] = new_value

    return out_obj

def get_field_value(inpt_obj, field):
    '''
    get value an object at specified location, including nested values

    inpt_obj (dict): object containing value to be found
    field (string): directory of value to be found (use "." to get to nested layers and 
                    [<ind>] to get the <ind> index of an array within an object)
    '''
    if not check_field(inpt_obj, field):
        return None
    
    obj = copy.deepcopy(inpt_obj)
    keys = field.split('.')  # Split the field string by periods to get individual keys

    for key in keys:
        if key.endswith(']'):  # If the key ends with ']', it indicates an array access
            index = int(key[key.index('[') + 1: -1])  # Extract the index value from within brackets
            obj = obj[key[:key.index('[')]]  # Get the object corresponding to the array
            obj = obj[index]  # Access the specific element in the array
        else:
            obj = obj[key]  # Access the object using the key

    return obj

def create_test_field(test_field, test_type, field_parameters, required, default, deletable, acceptable_input, array_type=None):
    '''
    creates a single dict to be used as one of potentially many dicts in the array 
        'test_fields', an input for APITester object
        
    test_field (string): name of the field being tested
    test_type (string): data type of field (can be one of the following: 'string',
        'integer', 'float', 'boolean', 'array', 'date', 'password', 'password_confirmation',
        'email', 'original_password', 'dict')
    field_parameters (dict): contains various parameters to be used in tests done on the
        field. The following are valid values and circumstances in which they can be used:
            'min' (integer): minimum value possible (integer/float fields/array_type)
            'min_inc' (bool): inclusive minimum bound; def=True (integer/float
                fields/array_type)
            'min' (integer): maximum value possible (integer/float fields/array_type)
            'min_inc' (bool): inclusive maximum bound; def=True
                (integer/float fields/array_type)
            'array' (list): list of possible values (string/int/float fields/array_type)
            'excluded' (misc): should be paired with 'array' input; value not in 'array' to be used
                to test to make sure that values outside of 'array' cannot be included
            'duplicates' (bool): can contain duplicate values (list)
            'length' (int): min length of acceptable string (password)
            'upper_case' (bool): string should contain an upper case (password)
            'lower_case' (bool): string should contain a lower case (password)
            'number' (bool): string should contain a number (password)
            'special_character' (bool): string should contain a special character
            'existing_email' (string): an email that exists in the database used to make sure that
                duplicate values cannot be submitted
    required (bool): whether the field is required
    default (bool): whether the fields has a default value in the data schema
    deletable (bool): whether the field can be deleted
    acceptable_input (dict): acceptable baseline 'json' for body of API request
    array_type (string): data type of values in array ('string', 'integer', 'float', 'boolean',
        'date'); default is None (for non-array test_type)
    '''
    return {'test_field': test_field,
            'test_type': test_type,
            'field_parameters': field_parameters,
            'required': required,
            'default': default,
            'deletable': deletable,
            'array_type': array_type,
            'acceptable_input': acceptable_input}

def update_url_id(url, ids, placeholder = '<id>'):
    '''
    replaces a placeholders in input url with input id values; there should be the same number
        of values in the input 'ids' as there are placeholders in input 'url'
    
    url (string): url with placeholders that will be modified and used in API request
    ids (list): array of string ids that will replace placeholds in 'url'
    placeholder (string): placeholder that is to be replaced with ids (default = '<id>')
    '''
    if not (len(ids) == url.count(placeholder)):
        raise ValueError(f'length of ids ({len(ids)}) array and "{placeholder}" count in url are not equal ({url})')
        return
    for i, val in enumerate(ids):
        url = url.replace(placeholder, str(val), 1)

    return url

def find_vals(input_obj, log, field, error_ref, delete_value=None):
    '''
    process a dict from the find_hb_vals or find_id_vals function

    input_obj (dict): object with the following structure:
        sources (string): either 'predo', 'test', or 'redo' depending on which request
            gives the needed information
        component (string): either 'body' or 'header' (possibly 'url_id')
        location (string): directory of value to be found (use "." to get to nested layers and 
            [<ind>] to get the <ind> index of an array within an object
        function (function): function with a single output to be done on the value found in the input
            source/component/location combination
    log (dict): a log of the previously run predo, test, undo that for each of the 
        three api requests should contain body, header, url_ids, url, expected_result, api_result,
        field_index, and test_index
    field (string): current field being tested
    error_ref (string): string referenced to point user to key or index causing errorm should
        be in the form 'for <ref>' where <ref> is either the key or index value
    '''
    item = copy.deepcopy(input_obj)

    for val in ['source', 'component', 'location']:
        if val not in item:
            raise ValueError(f"{item} missing component {val} {error_ref} (should contain ['source', 'component', 'location'])")
    if item['source'] not in log:
        raise ValueError(f"{item['source']} not found in the log {error_ref}")
    if item['component'] not in log[item['source']]:
        raise ValueError(f"{item['component']} not found in {item['source']} {error_ref}")
    location = field if item['location'] == '<field>' else item['location']
    if not check_field(log[item['source']][item['component']], location):
        if delete_value:
            return delete_value
        else:
            raise ValueError(f"{field} (original input: {item['location']}) not found in " \
                f"source-component {error_ref}: {log[item['source']][item['component']]}; consider " \
                f"adding delete_value to tester")
    out = get_field_value(log[item['source']][item['component']], location)
    if 'function' in item:
        out = item['function'](out)
    
    return out

def find_hb_vals(request_obj, focus, input_log, field, delete_value=None):
    '''
    creates an output object based on either explicit values or values referenced in an
    input log

    request_obj (dict): body or head information used to create output; should contain
        keys needed to run the API with either explicit values or a dict with references
        to pull the values from a log with a structure as follows:
        sources (string): either 'predo', 'test', or 'redo' depending on which request
            gives the needed information
        component (string): either 'body' or 'header' (possibly 'url_id')
        location (string): directory of value to be found (use "." to get to nested layers and 
            [<ind>] to get the <ind> index of an array within an object
    focus (string): either 'header' or 'body', focus object of the request_obj
    input_log (dict): a log of the previously run predo, test, undo that for each of the 
        three api requests should contain body, header, url_ids, url, expected_result, api_result,
        field_index, and test_index
    field (string): current field being tested
    '''
    obj = copy.deepcopy(request_obj)
    log = copy.deepcopy(input_log)

    out = {}

    if focus not in ['header', 'body']:
        raise ValueError(f"focus value of '{focus}' not in permissible values ('header', 'body')")

    for key, item in obj[focus].items():
        used_key = key if (not key == '<field>') else field
        ref_val = False
        if isinstance(item, dict):
            if 'referenced_value' in item:
                ref_val = item['referenced_value']
        out[used_key] = item if not ref_val else find_vals(item, log, field, f'for {used_key}', delete_value)

    return out

def find_ids_vals(request_arr, input_log, field):
    '''
    creates an output array based on either explicit values or values referenced in an
    input log

    request_arr (list): url_ids information used to create output; should be a list of
        either explicit values or a dict with references to pull the values from a log
        with a structure as follows:
        sources (string): either 'predo', 'test', or 'redo' depending on which request
            gives the needed information
        component (string): either 'body' or 'header' (possibly 'url_id')
        location (string): directory of value to be found (use "." to get to nested layers and 
            [<ind>] to get the <ind> index of an array within an object
    input_log (dict): a log of the previously run predo, test, undo that for each of the 
        three api requests should contain body, header, url_ids, url, expected_result, api_result,
        field_index, and test_index
    '''
    arr = copy.deepcopy(request_arr['url_ids'])
    log = copy.deepcopy(input_log)

    out = []

    for i, item in enumerate(arr):
        ref_val = False
        if isinstance(item, dict):
            if 'referenced_value' in item:
                ref_val = item['referenced_value']
        temp_value = item if not ref_val else find_vals(item, log, field, f'for index {i}')
        out.append(temp_value)

    return out

def result_template(
        expected_result,
        expected_api_success,
        test_name,
        error,
        field = 'n/a',
        predo_input = None,
        predo_status = 'not run',
        predo_response = None,
        predo_json = None,
        test_input = None,
        test_status = 'not run',
        test_response = None,
        test_json = None,
        undo_input = None,
        undo_status = 'not run',
        undo_response = None,
        undo_json = None,
        test_source = 'not provided'
        ):
    '''
    creates a dictionary output that can be included in the objects result list
    expected_result (bool): whether the output is as expected
    expected_api_success (bool): whether the api was expected to be successful
    test_name (string): name of the test being run
    error (string): description of the error that will have occured if not succesful
    field (string): name of the field being tested
    predo_input (dict): url, header, and body sent in predo API request
    predo_status (string): status of the predo api request (successful, not needed, etc.)
    predo_response (dict): obj response of predo api request
    predo_json (dict): json response of predo api request
    test_input (dict): url, header, and body sent in test API request
    test_status (string): status of the test api request (successful, not needed, etc.)
    test_response (dict): obj response of test api request
    test_json (dict): json response of test api request
    undo_input (dict): url, header, and body sent in undo API request
    undo_status (string): status of the undo api request (successful, not needed, etc.)
    undo_response (dict): obj response of undo api request
    undo_json (dict): json response of undo api request
    test_source (string): which method produced ran this test
    '''
    return {'expected_result': expected_result,
            'expected_api_success': expected_api_success,
            'test_name': test_name,
            'error': error if not expected_result else '',
            'field': field,
            'predo_input': predo_input,
            'predo_status': predo_status,
            'predo_response': predo_response,
            'predo_json': predo_json,
            'test_input': test_input,
            'test_status': test_status,
            'test_response': test_response,
            'test_json': test_json,
            'undo_input': undo_input,
            'undo_status': undo_status,
            'undo_response': undo_response,
            'undo_json': undo_json,
            'test_source': test_source,
            }
