import glob
import os
import re

from datetime import datetime, timedelta

import json

import gemst_globals
from gemst_globals import *

import gemst_logging
from gemst_logging import log, log_val

#################################
# Check if floating point number are acceptably close, per absolute or relative epsilon values
# If return_details==True returns the equivalence, the error magnitude, and the absolute and relative epsilon values used
# Example usage:
#   if is_equiv(x, 0.2):
#   equiv,err,abs_eps,rel_eps = is_equiv(x, 0.2)
#   if !equiv: #log the error and magnitude with relevant epsilon values
#
def is_equiv(x, y, abs_eps=1e-9, rel_eps=1e-12, details=False):
    log(f"is_equiv() Start: x={x}, y={y}, abs_eps={abs_eps}, rel_eps={rel_eps}", dbg="EchoInputs")
    equiv = abs(x - y) < max(abs_eps, rel_eps * max(abs(x), abs(y)))
    if details:
        return equiv, abs(x-y), abs_eps, rel_eps
    return equiv
    
## Example usage
#callable_func = CallableFunc("Hello, World!")
#result = callable_func(1, 2, 3, key="value")
#print(result)
class CallableFunc:
    def __init__(self, string):
        log(f"__init__() Start: self, string = {self, string}", dbg="EchoInputs")
        self.string = string

    def __call__(self, *args, **kwargs):
        log(f"__call__() Start: self, args, kwargs = {self, args, kwargs}", dbg="EchoInputs")
        #print(f"{self} Called with args: {args} and kwargs: {kwargs}")
        return self.string

##########
def sub_in_vals( string_with_params, params_vals ):
    # Copy to we can return original in case of Exception
    string_with_names = string_with_params
    string_with_vals = string_with_params
    try:
        for param_name,param_val in params_vals.items():
            if param_val is not None:
                braced_name = '{' + param_name + '}'
                string_with_vals = re.sub(braced_name, str(param_val), string_with_params)
                if string_with_vals is not None:
                    string_with_params = string_with_vals
    except Exception as e:
        log(f"Exception doing value substitution, where e:{e}", 'sub_in_vals', level='Alert')
        return string_with_params

    return string_with_vals

if tests['test_sub_in_vals']:
    test_str = "{Goodbye} to the {cruel} {world}!"
    replacements = {"Goodbye":"Hello", "cruel":"Beautiful", "world":"Girls"}
    new_str = sub_in_vals( test_str, replacements )

    log_val('new_str', new_str, level='Tests')

    if tests['test_sub_in_vals'] == -1:
        log(f"Done testing. Exiting per request (-1)")
        exit()

#jda Note from Copilot
#Sigmoid blending: scale_expr = "0.5 + 0.5 * tanh(({v}-{c})/eps)", smoothly shifting between states.

##########
# Evaluate expressions like: "v<c", or execute expressions like: "scale=1.0".
def eval_exec( expr, params ):
    global tbd
    log(f"Starting. expr:{expr}, params:{params}", 'eval_exec', dbg="EchoInputs")

    if expr is None or expr == tbd or params is None:
        log(f"I got expr={expr} and params={params}; I get none, you get None back..", 'eval_exec', 
            level='Alert', for_summary=True)
        return None

    # Substitute the values from the params into the expression before solving it
    expr_with_vals = sub_in_vals( expr, params )

    ans = eval(expr_with_vals)

    log(f"Returning ans={ans} from eval {expr_with_vals}", 'eval_exec', dbg="EchoOutputs")
    return ans

if tests['test_eval_exec']:
    scale = 0.0
    cond = None
    got_err = False

    # Test mass at sub-light
    params = {"mass":".0000000000001", "dx":".9", "dt":"1.0", "c":"1.0"}
    cond_expr = "{dx}<{dt} or ({mass}==0.0 and ({dx}/{dt})=={c})"

    cond = eval_exec(cond_expr, params)

    if cond != True:
        log(f"Error in test. Expected True, but cond={cond}", 'test_eval_exec', level='Tests')

    scale_expr = "0.5 if {dx}/{dt} < {c} else 1.0"
    #scale_expr_wVals = sub_in_vals( scale_expr, params )
    scale = eval_exec( scale_expr, params )

    if scale != 0.5:
        got_err = True
        log(f"Error in test. Expected 0.5, but scale={scale}", 'test_eval_exec', level='Tests')

    # Test Energy with no mass at light speed
    params = {"mass":"0.0", "dx":"1.0", "dt":"1.0", "c":"1.0"}
    cond_expr = "{dx}<{dt} or ({mass}==0.0 and ({dx}/{dt})=={c})"

    cond = eval_exec(cond_expr, params)

    if cond != True:
        got_err = True
        log(f"Error in test. Expected True, but cond={cond}", 'test_eval_exec', level='Tests')

    scale_expr = "0.5 if {dx}/{dt} < {c} else 1.0"
    scale = eval_exec( scale_expr, params )

    if scale != 1.0:
        got_err = True
        log(f"Error in test. Expected 1.0, but scale={scale}", 'test_eval_exec', level='Tests')

    # make sure mass can't go faster than light
    params = {"mass":"0.1", "dx":"1.0", "dt":"1.0", "c":"1.0"}
    cond_expr = "{dx}<{dt} or ({mass}==0.0 and ({dx}/{dt})=={c})"

    cond = eval_exec(cond_expr, params)

    if cond != False:
        got_err = True
        log(f"Error in test. Expected False, but cond={cond}", 'test_eval_exec', level='Tests')

    scale_expr = "0.5 if {dx}/{dt} < {c} else 1.0"
    scale = eval_exec( scale_expr, params )

    if scale != 1.0:
        got_err = True
        log(f"Error in test. Expected 1.0, but scale={scale}", 'test_eval_exec', level='Tests')

    # make sure energy can't go faster than light
    params = {"mass":"0.0", "dx":"1.1", "dt":"1.0", "c":"1.0"}
    cond_expr = "{dx}<{dt} or ({mass}==0.0 and ({dx}/{dt})=={c})"

    cond = eval_exec(cond_expr, params)

    if cond != False:
        got_err = True
        log(f"Error in test. Expected False, but cond={cond}", 'test_eval_exec', level='Tests')

    scale_expr = "0.5 if {dx}/{dt} < {c} else 1.0"
    scale = eval_exec( scale_expr, params )

    if scale != 1.0:
        got_err = True
        log(f"Error in test. Expected 1.0, but scale={scale}", 'test_eval_exec', level='Tests')

    if not got_err:
        log("Successful tests.", 'test_eval_exec', level='Tests')

    if tests['test_eval_exec'] == -1:
        log(f"Done testing. Exiting per request (-1)", 'test_eval_exec', level="Tests")
        exit()

#############################
def reset_eq_lib(eq_lib_data="default", lib_id="default", log_content=False):
    log(f"Starting. lib_id:{lib_id}", 'reset_eq_lib', dbg="Verbose", level="Document")
    global eq_lib, doi
    global tbd, OK, ERR

    if lib_id == "default":
        lib_id = doi

    json_filename = f"json/{lib_id}.json"

    if eq_lib_data == "default":
        eq_lib_data = load_eq_lib(lib_id=lib_id)

    # Careful not to save a corrupted file (due to errors in processing)
    try:
        eq_name = tbd
        eq_spec = {}
        eq_solution = {}
        eq_metadata = {}

        for eq_name,eq_spec in eq_lib_data.items():
            #log(f"in for loop, eq_name: {eq_name}, eq_spec:{eq_spec}", 'reset_eq_lib')

            # Copy out all the existing data
            eq_metadata = eq_spec['eq_metadata']
            eq_solution = eq_spec['eq_metadata']['solution']

            # Update the solution status so we know we need to calculate
            eq_solution['validation_status'] = tbd
            eq_solution['ans'] = tbd
            eq_solution['mks_val'] = tbd
            eq_solution['ans_source'] = tbd
            eq_solution['validation_timestamp'] = tbd

            # Update the eq_metadata
            eq_metadata.update({"solution":eq_solution})

            # Put the updated eq_metadata back into the eq_spec
            eq_spec.update({'eq_metadata':eq_metadata})

            #log(f"updating eq_lib_data for {eq_name} with spec: {eq_spec}", 'reset_eq_lib', level="Info")

            # Update the eq_lib_data with the updated eq_spec
            eq_lib_data.update( {eq_name:eq_spec} )

        log(f"Did reset the validation data in eq_lib_data to default values",
            'reset_eq_lib', level="Document", dbg="Verbose", for_summary=True)

        #if (lib_id != 'default'):
        #    log(f"Calling save_eq_lib", 'reset_eq_lib', level='Document')
        #    save_eq_lib(eq_lib, lib_id=lib_id, log_content=False)

    except Exception as e:
        log(f"Exception: {e}", 'reset_eq_lib', level="EXCEPTION")

    return eq_lib_data

##########
# Convert all params to mks units
# returns params_mks
def params_to_mks( params=None ):
    global pico_fact, quad_fact, quint_fact, kg_fact, Em_fact
    global tbd, OK, ERR
    global eq_lib
    log(f"Starting - params:{params}", 'params_to_mks', dbg="EchoInputs")

    if params is None:
        log(f"Sorry, can't process with input params={params}. Returning None", 'params_to_mks', level='Alert')
        return None

    params_mks = {}
    #factors = {}
    mks_val = 0.0
    var_val = 0.0
    fact = 1.0
    scaledBy = 1.0

    for var,val in params.items():
        if val != "tbd" and var != "tbd":
            var_val = val

            found_it = False

            for eq,eq_spec in eq_lib.items():
                if eq_spec['ans_symb'] == var:

                    meta_scaling = {}
                    eq_metadata = {}
                    eq_solution = {}
                    fact_str = tbd
                    scaledBy = tbd

                    try:
                        eq_metadata = eq_spec['eq_metadata']
                        eq_solution = eq_metadata['solution']
                        meta_scaling = eq_metadata["scaling"]

                    except Exception as e:
                        log(f"eq:{eq}, eq_spec:{eq_spec}", 'params_to_mks', level="EXCEPTION")
                        break

                    try:
                        fact_str = meta_scaling["fact"]
                        scaledBy_str = meta_scaling["scaledBy"]

                        #log(f"fact_str:{fact_str}, scaledBy_str:{scaledBy_str}")

                    except Exception as e:
                        log(f"Can't extract scaling fact and scaledBy for {eq}. Defaulting to 1.0's", 
                                'params_to_mks', level="EXCEPTION")
                        break
                    try:
                        fact = float(fact_str)
                        scaledBy = float(scaledBy_str)
                    except Exception as e:
                        fact = 1.0;
                        scaledBy = 1.0;
                        log(f"Error converting to string of fact_str:{fact_str}, scaledBy_str:{scaledBy_str}", 
                                'params_to_mks', "level=EXCEPTION")
                        break

                    #scaling.update( {eq:{"fact":fact, "scaledBy":scaledBy}} )

                    #log(f"scaling for {eq}: fact={fact}, scaledBy:{scaledBy}", 'params_to_mks', level="Info")
                    found_it = True
                    break

            # end of eq loop
            if not found_it or fact == tbd or scaledBy == tbd:
                fact = 1.0
                scaledBy = 1.0
                log(f"No conversion factors for scaling found in equation spec for '{var}'", 
                    'params_to_mks', level="Alert")

            #log(f"For conversion to mks, fact={fact} and scaledBy={scaledBy}", 'params_to_mks', level='mks')
            tot_scaling = fact*scaledBy

            log(f"The total conversion to mks multiplier={tot_scaling}", 'params_to_mks', level='Info', dbg="Verbose")

            mks_val = var_val * tot_scaling

            params_mks.update( {var:mks_val} )

            #try:
            #except Exception as e:
                #log(f"Exception converting to mks for parameter '{var}'\ne:{e}", 'params_to_mks', level='Alert')

        # end for all params
        
    return params_mks

    
##########
# Saves the equation library as a JSON file and optionally logs the contents
def save_eq_lib( eq_lib_data="default", lib_id="default", log_content=False ):
    log(f"Starting save_eq_lib(lib_id={lib_id})", 'save_eq_lib', dbg="EchoInputs");
    global doi, eq_lib

    if lib_id == "default":
        lib_id = doi
    
    json_filename = "json/" + lib_id + ".json"

    log(f"Saving eq_lib for {lib_id} to JSON file: {json_filename}", 'save_eq_lib', level="Document")

    if eq_lib_data == "default":
        eq_lib_data = eq_lib

    # Make sure the recid's are in numeric order
    recid = 1
    for eq, spec in eq_lib_data.items():
        spec['recid'] = str(recid)
        eq_lib_data[eq] = spec
        recid += 1
    
    # Preventing json file corruption by making sure it works to a temp file before updating the saved file
    #
    temp_fname = "/tmp/temp_eq_lib.json"
    with open(temp_fname, "w") as temp_eq_lib_json_file:
        try:
            json.dump(eq_lib_data, temp_eq_lib_json_file, indent=4)  # `indent=4` makes it readable
        except Exception as e:
            log(f"Error in the json; can't update file {json_filename}; e: {e}", "save_eq_lib", level="EXCEPTION")
            return ERR

    # The above json.dump to the temp file had no exception, so update the actual file
    with open(json_filename, "w") as eq_lib_json_file:
        json.dump(eq_lib_data, eq_lib_json_file, indent=4)  # `indent=4` makes it readable

    if log_content:
        log(f"Content of {json_filename} after saving:\n{eq_lib}", 'save_eq_lib', dbg="Verbose", level="Document")

    return OK

##########
# Removes the equation from the library
def rm_eq( eq_name, lib_id='default', log_content=False ):
    global eq_lib

    log(f"Removing {eq_name} from eq_lib", 'rm_eq', dbg="Verbose", level="Document")
    eq_lib.pop( eq_name, None )

    save_eq_lib(eq_lib, lib_id=lib_id, log_content=True)

##########
# Opens the JSON file containing the equation library and loads it
def load_eq_lib( lib_id="default", log_content=False ):
    global eq_lib, doi

    if lib_id == "default":
        json_filename = f"json/{doi}.json"
    else:
        json_filename = f"json/{lib_id}.json"

    with open(json_filename, "r") as eq_lib_json_file:
        eq_lib = json.load(eq_lib_json_file)

    if log_content:
        log(f"Content of {lib_id} after loading:\n{eq_lib}", 'load_eq_lib', level="Document")

    return eq_lib

##########
# return the date-time as an integer, which can be used in comparisons to see which is newest..
def get_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M.%f")

def is_newer( first_dt, sec_dt ):
    if sec_dt > first_dt:
        return True
    return False

##########
# Saves the options_lib dictionary as a JSON file and optionally prints the contents
#def save_options_lib( log_content=False ):
#    global options_lib, options_json_filename
#    log(f"Starting. Saving options_lib to JSON file: {options_lib['filename']}",
#            'save_options_lib', dbg="Verbose", level="Info", for_summary=True)
#
#    if options_json_filename is None:
#        log(f"options_json_filename is None so nothing to process. See gemst_globals.py", 
#            'save_options_lib', level="Alert", for_summary=True)
#        return ERR
#
#    with open(options_json_filename, "w") as opt_file:
#        json.dump(options_lib, opt_file, indent=4)  # `indent=4` makes it readable
#
#    if log_content:
#        log(f"Content of {options_json_filename} after saving:\n{options_lib}", 'save_options_lib', level="Document")
#
#    return OK

##########
# Saves the parameter library as a JSON file and optionally logs the contents
def save_param_lib( log_content=False ):
    global param_lib, param_lib_json_filename
    log(f"Starting. Saving param_lib to JSON file: {param_lib_json_filename}", 'save_param_lib', dbg="EchoInputs")
    
    # Preventing json file corruption by making sure it works to a temp file before updating the saved file
    #
    temp_fname = "/tmp/temp_param_lib.json"
    with open(temp_fname, "w") as temp_param_lib_json_file:
        try:
            json.dump(param_lib, temp_param_lib_json_file, indent=4)  # `indent=4` makes it readable
        except Exception as e:
            log(f"Error in the json; can't update {param_lib_json_filename}; e: {e}", "save_param_lib", level="EXCEPTION")
            return ERR

    # The above json.dump to the temp file had no exception, so update the actual file
    with open(param_lib_json_filename, "w") as param_lib_json_file:
        json.dump(param_lib, param_lib_json_file, indent=4)  # `indent=4` makes it readable

    if log_content:
        log(f"Content of {param_lib_json_filename} after saving:\n{param_lib}", 'save_param_lib', level="Document")

    return OK

##########
def make_param_lib():
    global eq_lib, param_lib, valid
    log(f"Starting make_param_lib", dbg='EchoInputs')

    param_lib = load_param_lib()

    # Go through the entire equation library
    for eq_name,eq_spec in eq_lib.items():

        eq_metadata = eq_spec['eq_metadata'].copy()
        eq_solution = eq_metadata['solution'].copy()
        validity = eq_solution['validation_status']

        ans_symb = eq_spec['ans_symb']

        # Add new parameter values to param_lib when param status not valid or eq_lib has newer value
        if ans_symb in param_lib:

            param_time = param_lib[ans_symb]['validation_timestamp']
            eq_time = eq_solution['validation_timestamp']
            if param_lib[ans_symb]['status'] != valid or \
             (param_time != tbd and eq_time != tbd and eq_time > param_time): 

                param_meta = {}
                ###params_mks.update( {"val":str(val)+"("+str(scaledBy)+")"} )
                param_meta.update( {"val":eq_solution['ans']} )

                # if you still want to do this, look it up (def a fn) in the eq_lib for ans_symb
                #param_meta.update( {"scaledBy":str(scaling[ans_symb])} )
                param_meta.update( {"ans_source":eq_solution['ans_source']} )
                param_meta.update( {"validation_timestamp":eq_solution['validation_timestamp']} )
                param_meta.update( {"mks_val":eq_solution['mks_val']} )
                param_meta.update( {"status":eq_solution['validation_status']} )

                param_lib.update( {ans_symb:param_meta} )

        save_param_lib( log_content=True )

##########
# Opens the JSON file containing the options_lib and loads it
#def load_options_lib( log_content=False ):
#    global options_lib, options_json_filename
#    log(f"Starting. Loading file: {options_json_filename}", 'load_options_lib', dbg='EchoInputs')
#
#    if options_json_filename is None:
#        log(f"options_json_filename is None, so nothing to process. See gemst_globals.py 'options_json_filename'", 
#            'save_options_lib', level="Alert", for_summary=True)
#        return ERR
#
#    with open(options_json_filename, "r") as options_file:
#        options_lib = json.load(options_file)
#
#    if log_content:
#        log(f"Content of {options_json_filename} after loading:\n{options_lib}", 'load_options_lib', level="Document")

##########
def set_scaling():
    global scaling, eq_lib
    global no_scaling

    eq_lib = load_eq_lib()

    eq_metadata = {}
    factors = {"scaledBy":str(no_scaling), "fact":str(no_scaling)}
    eq_metadata.update( {'scaling':factors} )

    for eq_symb, eq_spec in eq_lib.items():
        #log(f"eq_symb:{eq_symb}", 'set_scaling', level="Trace")
        ans_symb = eq_spec["ans_symb"]
        eq_metadata = eq_spec["eq_metadata"]
        for scaling_symb, scaling_rec in scaling.items():
            #log(f"scaling_symb:{scaling_symb}", 'set_scaling', level="Trace")

            if ans_symb == scaling_symb:
                factors = scaling[ans_symb]
                fact_str = str(factors["fact"])
                scaledBy_str = str(factors["scaledBy"])
                factors.update( {"fact":fact_str, "scaledBy":scaledBy_str} )
                log(f"updating {eq_symb} scaling factors to {factors}", 'set_scaling', level="Document")
                eq_metadata.update( {"scaling":factors} )
                
                break

        eq_spec["eq_metadata"] = eq_metadata
        eq_lib[eq_symb] = eq_spec

    save_eq_lib(eq_lib)

if tests['test_set_scaling']:
    
    log(f"In test_set_scaling calling set_scaling")
    set_scaling()

    if tests['test_set_scaling'] == -1:
        log("Exiting Test on request (value=-1)", 'test_set_scaling', 'Tests')
        exit()

##########
def get_first_field( rec ):
    for field_name,field_val in rec.items():
        return field_val;

def get_first_field_named( name, rec, max_nesting=9, min_nesting=0, nesting=-1 ):
    #log(f"Starting get_first_field_named(name={name}, max_nesting={max_nesting}, min_nesting={min_nesting})", level="Trace");
    nesting += 1

    for field_name,field_val in rec.items():
        #log(f"nesting={nesting}; field_name:{field_name}", 'get_first_field_named', level="Trace")
        if nesting >= min_nesting:
            if field_name == name:
                nesting -= 1
                #log(f"returning {field_val}", 'get_first_field_named', level="Trace")
                return field_val
        if nesting >= max_nesting:
            #log(f"nesting={nesting} >= max_nesting={max_nesting} so not descending", 'get_first_field_named', level="Trace")
            continue

        try:
            if len(field_val) >= 1:
                try:
                    # If not a compatible record, it's a string or array..
                    json_rec_str = json.dumps(field_val)
                    # No exception, so traverse field_val as a subrecord recursively
                    #log(f"{field_name} field_val:{field_val}, json_rec_str:{json_rec_str}", 'get_first_field_named', level='Trace');
                    subrec = {}
                    subrec = get_first_field_named( name, field_val, max_nesting=max_nesting, min_nesting=min_nesting, nesting=nesting)

                    if subrec is not None:
                        nesting -= 1
                        return subrec
                except Exception as e:
                    # not a record to traverse
                    continue 
            else:
                continue
        except:
            continue

    nesting -= 1
    return None

if tests['test_get_first_field_named']:

    eq_rec = { "vfr": {
                "recid": "12",
                "ans_name": "V_fraction",
                "ans_symb": "vfr",
                "scale_expr": "1.0",
                "offset_expr": "0.0",
                "cond_expr": "",
                "symp_eq": "Eq(vfr, v/c)",
                "dependencies": ["v", "c"],
                "eq_metadata": {
                    "scaling": {
                        "fact": "1.0",
                        "scaledBy": "1.2345"
                    },
                    "solution": {
                        "params": {
                            "v": "1.5707963267949",
                            "c": "1.5707963267948966"
                        },
                        "ans": "1.234",
                        "mks_val": "1234.0",
                        "ans_source": "Eq(vfr, v/c)",
                        "validation_status": "Valid",
                        "validation_timestamp": "20250929215323"
                    },
                    "eq_source": "GUI",
                    "version": "9/23/2025, 2:18:17 PM",
                    "condition_satisfied": "True"
                }
            }
        }
    
    log(f"Expect first field='vfr' : {get_first_field(eq_rec)}", 'test_get_first_field', level="Tests")

    log(f"Expect 'ans_symb'='vfr' : {get_first_field_named('ans_symb', eq_rec)}", 'test_get_first_field_named', level='Tests')

    if tests['test_get_first_field_named'] == -1:
        log("test_get_first_field_named is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()

####################################################################################################

# Determine whether all the parameters in the equation set object are valid
def obj_is_valid( obj ):
    global ans_sources, eq_states

    for eq,eq_spec in obj.items():
        val_stat = eq_spec['eq_metadata']['solution']['validation_status']
        if val_stat != ans_sources['input_data'] and val_stat != eq_states['valid']:
            return False, eq, val_stat

    return True, None, None

if tests['test_obj_is_valid']:
    obj = {
        "KE": {
            "recid": "1",
            "ans_name": "Kinetic Energy",
            "ans_symb": "KE",
            "dependencies": [
                "m_KE",
                "C_KE",
                "dx_KE",
                "D_KE",
                "dt_KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "_remark": "Kinetic Energy is where v=dx/dt<c",
            "cond_expr": "not is_equiv({D_KE}*{dt_KE}*{dt}, 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(KE, (m_KE*C_KE*dx_KE)/(4*D_KE*dt_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0xffff00"
                    },
                    "ans": "0.0196349540849362",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {},
                    "decom_params": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "True",
                "missing_params": []
            }
        },
        "m_KE": {
            "recid": "2",
            "ans_name": "Mass Kinetic",
            "ans_symb": "m_KE",
            "dependencies": [
                "C_KE",
                "dx_KE",
                "D_KE",
                "dt_KE",
                "KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "_remark": "Equivalent mass Kinetic is where v=dx/dt<c",
            "cond_expr": "not is_equiv({C_KE}*{dx_KE}*{dt}, 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(m, (4*Energy*dt_KE*D_KE)/(C_KE*dx_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0x0000ff"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "True",
                "missing_params": []
            }
        },
        "dx_KE": {
            "recid": "3",
            "ans_name": "Distance Kinetic",
            "ans_symb": "dx_KE",
            "dependencies": [
                "m_KE",
                "C_KE",
                "D_KE",
                "dt_KE",
                "KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "_remark": "For Kinetic values, v=dx/dt<c",
            "cond_expr": "not is_equiv({C_KE}*{m_KE}*{dt}, 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(dx, (4*Energy*dt_KE*D_KE)/(C_KE*m_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0xff00ff"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "True",
                "missing_params": []
            }
        },
        "dt_KE": {
            "recid": "4",
            "ans_name": "Duration Kinetic ",
            "ans_symb": "dt_KE",
            "dependencies": [
                "m_KE",
                "C_KE",
                "dx_KE",
                "D_KE",
                "KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "cond_expr": "not is_equiv({Energy}*{D_KE}*{dt}), 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(dt, ((m_KE*C_KE*dx_KE)/(4*Energy*D_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0x00ffff"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "None",
                "missing_params": []
            }
        },
        "D_KE": {
            "recid": "5",
            "ans_name": "Diameter Kinetic",
            "ans_symb": "D_KE",
            "dependencies": [
                "m_KE",
                "C_KE",
                "dx_KE",
                "dt_KE",
                "KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "_remark": "For Kinetic Energy v=dx/dt<c",
            "cond_expr": "not is_equiv({dt_KE}*{Energy}*{dt}, 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(D, ((m_KE*C_KE*dx_KE)/(4*Energy*dt_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0xff0000"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "None",
                "missing_params": []
            }
        },
        "C_KE": {
            "recid": "6",
            "ans_name": "Circumference Kinetic",
            "ans_symb": "C_KE",
            "dependencies": [
                "m_KE",
                "dx_KE",
                "D_KE",
                "dt_KE",
                "KE"
            ],
            "scale_expr": "",
            "offset_expr": "",
            "_remark": "For Kinetic Energy v=dx/dt<c",
            "cond_expr": "not is_equiv({m_KE}*{dx_KE}*{dt}, 0.0) and ({dx}/{dt}<{c})",
            "symp_eq": "Eq(C, (4*Energy*dt_KE*D_KE)/(dx_KE*m_KE))",
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-15"
                },
                "solution": {
                    "params": {},
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0x00ff00"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "2.8608265865080877",
                    "ans_source": "Input Data",
                    "timestamp": "202511041934.258820",
                    "validation_status": "Input Data",
                    "ancestry": {}
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191241",
                "condition_satisfied": "True",
                "missing_params": []
            }
        },
        "v": {
            "recid": "7",
            "ans_name": "Velocity",
            "ans_symb": "v",
            "dependencies": [
                "dx",
                "dt"
            ],
            "cond_expr": "not is_equiv({dt}, 0.0)",
            "symp_eq": "Eq(v, dx/dt)",
            "eq_metadata": {
                "scaling": {
                    "fact": "190853806.3694777",
                    "scaledBy": "1.0"
                },
                "solution": {
                    "params": {
                        "dx": "1.00000000000000",
                        "dt": "1.00000000000000"
                    },
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0xffff00"
                    },
                    "ans": "1.00000000000000",
                    "mks_val": "190853806.3694777",
                    "ans_source": "Eq(v, dx/dt)",
                    "timestamp": "202511041934.740300",
                    "validation_status": "Valid",
                    "ancestry": {
                        "dx": {
                            "v": {
                                "ans_source": "Eq(v, dx/dt)",
                                "ans": "1.00000000000000",
                                "timestamp": "202511041934.740300"
                            }
                        },
                        "dt": {
                            "v": {
                                "ans_source": "Eq(v, dx/dt)",
                                "ans": "1.00000000000000",
                                "timestamp": "202511041934.740300"
                            }
                        }
                    }
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510191300",
                "condition_satisfied": "True",
                "missing_params": []
            },
            "scale_expr": "1.0",
            "offset_expr": "0.0"
        },
        "p": {
            "recid": "8",
            "ans_name": "Momentum",
            "ans_symb": "p",
            "scale_expr": "1.0",
            "offset_expr": "0.0",
            "cond_expr": "not is_equiv({dt}, 0.0)",
            "symp_eq": "Eq(p, m_KE*v)",
            "dependencies": [
                "v",
                "m_KE"
            ],
            "eq_metadata": {
                "scaling": {
                    "fact": "3.642517540571808e+16",
                    "scaledBy": "1e-18"
                },
                "solution": {
                    "params": {
                        "v": "1.00000000000000",
                        "m_KE": "0.0785398163397448"
                    },
                    "color_spec": {
                        "hue": "210",
                        "saturation": "0.85",
                        "brightness": "0.65",
                        "RGB_hex": "0x00ff00"
                    },
                    "ans": "0.0785398163397448",
                    "mks_val": "0.0028608265865080872",
                    "ans_source": "Eq(p, m_KE*v)",
                    "timestamp": "202511041934.838144",
                    "validation_status": "Valid",
                    "ancestry": {
                        "v": {
                            "dt": {
                                "ans_source": "Eq(dt, dx/v)",
                                "ans": "1.00000000000000",
                                "timestamp": "202511041934.655833"
                            }
                        }
                    }
                },
                "eq_source": "gemst_eq_lib",
                "version": "202510140744",
                "condition_satisfied": "True",
                "missing_params": []
            }
        }
    }

    is_valid,eq,stat = obj_is_valid(obj)

    log(f"obj_is_valid(obj):Expect Valid, None, None: Validity:{is_valid}, invalid eq:{eq}, reason: {stat}", 'test_obj_is_valid', level="Tests")

    obj['KE']['eq_metadata']['solution']["validation_status"] = "tbd"
    is_valid,eq,stat = obj_is_valid(obj)

    log(f"obj_is_valid(obj):Expect Invalid, KE, tbd: Validity:{is_valid}, invalid eq:{eq}, reason: {stat}", 'test_obj_is_valid', level="Tests")

    if tests['test_obj_is_valid'] == -1:
        log("test_obj_is_valid is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()


def get_obj_list():
    global obj_path, obj_filenames
    log(f"cd to {obj_path}; looking for {obj_filenames}", 'get_obj_list')
    os.chdir(obj_path)

    obj_files = glob.glob(obj_filenames)

    os.chdir("..")

    objs = []

    # Strip off ".json"
    for obj_file in obj_files:
        ext_pos = obj_file.find('.json')
        objs.append(obj_file[0:ext_pos])

    return objs

if tests['test_get_obj_list']:
    global obj_path, obj_filenames, objs

    log(f"GEMSTone directory listing for {obj_path}:{os.listdir(obj_path)}", 'test_get_obj_list', level="Tests")

    obj_list = get_obj_list()
    log(f"obj_list: {obj_list}", 'test_get_obj_list', level='Tests')

    if tests['test_get_obj_list'] == -2:
        for obj in obj_list:
            q_rec = {'Q':'1'}
            log(f"updating objs with {obj} quantity:{q_rec}", 'test_get_obj_list', level="Tests");
            objs.update({obj:q_rec}) 

        log(f"{objs}", level="objs")

    if tests['test_get_obj_list'] < 0:
        log("test_get_obj_list is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()


####################################################################################################

##########
def get_first_rec_named( name, rec, max_nesting=9, min_nesting=0, nesting=-1 ):
    #log(f"Starting get_first_rec_named(name={name}, max_nesting={max_nesting}, min_nesting={min_nesting})", dbg="EchoInputs");
    nesting += 1

    for field_name,field_val in rec.items():
        #log(f"nesting={nesting}; field_name:{field_name}", 'get_first_rec_named', level="Trace")
        if nesting >= min_nesting:
            if field_name == name:
                nesting -= 1
                return field_val
        if nesting >= max_nesting:
            #log(f"nesting={nesting} >= max_nesting={max_nesting} so not descending", 'get_first_rec_named', level="Trace")
            continue

        try:
            if len(field_val) >= 1:
                try:
                    # If not a compatible record, it's a string or array..
                    json_rec_str = json.dumps(field_val)
                    # No exception, so traverse field_val as a subrecord recursively
                    found_rec = {}
                    #log(f"{field_name} field_val:{field_val}, json_rec_str:{json_rec_str}", 'get_first_rec_named', level='Trace');
                    found_rec = get_first_rec_named( name, field_val, max_nesting=max_nesting, min_nesting=min_nesting, nesting=nesting)

                    if found_rec is not None:
                        nesting -= 1
                        return found_rec
                except Exception as e:
                    # not a record to traverse
                    continue 
            else:
                continue
        except:
            continue

    nesting -= 1
    return None

if tests['test_get_first_rec_named']:

    eq_rec = { "vfr": {
                "recid": "12",
                "ans_name": "V_fraction",
                "ans_symb": "vfr",
                "scale_expr": "1.0",
                "offset_expr": "0.0",
                "cond_expr": "",
                "symp_eq": "Eq(vfr, v/c)",
                "dependencies": ["v", "c"],
                "eq_metadata": {
                    "scaling": {
                        "fact": "1.0",
                        "scaledBy": "1.2345"
                    },
                    "solution": {
                        "params": {
                            "v": "1.5707963267949",
                            "c": "1.5707963267948966"
                        },
                        "ans": "1.234",
                        "mks_val": "1234.0",
                        "ans_source": "Eq(vfr, v/c)",
                        "validation_status": "Valid",
                        "validation_timestamp": "20250929215323"
                    },
                    "eq_source": "GUI",
                    "version": "9/23/2025, 2:18:17 PM",
                    "condition_satisfied": "True"
                }
            }
        }
    
    log(f"From 'vfr' expect ans_name 'V_fraction' : {get_first_rec_named('vfr', eq_rec)['ans_name']}", 'test_get_first_rec_named', level='Tests')
    log(f"From 'solution.ans' expect 1.234 : {get_first_rec_named('solution', eq_rec)['ans']}", 'test_get_first_rec_named', level='Tests')
    log(f"From 'params' expect c ~1.5708 : {get_first_rec_named('params', eq_rec)['c']}", 'test_get_first_rec_named', level='Tests')

    if tests['test_get_first_rec_named'] == -1:
        log("test_get_first_rec_named is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()


##########
def set_first_in_rec( name, rec, new_val, max_nesting=9, min_nesting=0, nesting=-1 ):
    log(f"Starting set_first_in_rec(name={name}, new_val={new_val}, max_nesting={max_nesting}, min_nesting={min_nesting})", dbg="EchoInputs");
    nesting += 1

    for field_name,field_val in rec.items():
        #log(f"nesting={nesting}; field_name:{field_name}", 'set_first_in_rec', level="Trace")
        if nesting >= min_nesting:
            if field_name == name:
                rec[field_name] = new_val
                nesting -= 1
                return new_val
        if nesting >= max_nesting:
            #log(f"nesting={nesting} >= max_nesting={max_nesting} so not descending", 'set_first_in_rec', level="Trace")
            continue

        try:
            if len(field_val) >= 1:
                try:
                    # If not a compatible record, it's a string or array..
                    json_rec_str = json.dumps(field_val)
                    # No exception, so traverse field_val as a subrecord recursively
                    nested_field_val = set_first_in_rec(name, field_val, new_val, max_nesting=max_nesting, min_nesting=min_nesting, nesting=nesting)

                    if nested_field_val is not None:
                        field_val[name] = new_val
                        nesting -= 1
                        return new_val
                except Exception as e:
                    # not a record to traverse
                    continue 
            else:
                #log(f"set_first_in_rec() len({field_name})={len(field_name)}", 'set_first_in_rec', level="Trace");
                continue
        except:
            continue

    nesting -= 1
    return None

##########
def get_first_in_rec( name, rec, max_nesting=9, min_nesting=0, nesting=-1 ):
    log(f"Starting get_first_in_rec(name={name}, max_nesting={max_nesting}, min_nesting={min_nesting})", dbg="EchoInputs");
    nesting += 1

    # if rec isn't valid, return None
    try:
        rec_str = json.dumps(rec)
    except Exception as e:
        return None

    for field_name,field_val in rec.items():
        #log(f"nesting={nesting}; field_name:{field_name}", 'get_first_in_rec', level="Trace")

        if nesting >= min_nesting:
            # debug
            #if nesting > 1:
                #log(f"nesting={nesting} >= min_nesting={min_nesting}", 'get_first_in_rec', level='Trace')
            if field_name == name:
                nesting -= 1
                return field_val

        if nesting >= max_nesting:
            #log(f"nesting={nesting} >= max_nesting={max_nesting} so not descending", 'get_first_in_rec', level="Trace")
            continue

        try:
            if len(field_val) >= 1:
                try:
                    # If not a compatible record, it's a string or array..
                    json_rec_str = json.dumps(field_val)
                    # No exception, so traverse field_val as a subrecord recursively
                    nested_field_val = get_first_in_rec(name, field_val, max_nesting=max_nesting, min_nesting=min_nesting, nesting=nesting)

                    if nested_field_val is not None:
                        nesting -= 1
                        return nested_field_val
                except Exception as e:
                    # not a record to traverse
                    continue 
            else:
                #log(f"get_first_in_rec() len({field_name})={len(field_name)}", 'get_first_in_rec', level="Trace");
                continue
        except:
            continue

    nesting -= 1
    return None

##########
def is_in_rec( name, rec, max_nesting=9, min_nesting=0 ):
    val = get_first_in_rec( name, rec, max_nesting=max_nesting, min_nesting=min_nesting )
    if val is None:
        return False
    return True

if tests['test_is_in_rec']:
    its_there = is_in_rec('dx', {'v': 1.0, 'dt': 1.0, 'mass': 0.1, 'dx': 1.00000000000000})
    log(f"Expect True; its_there:{its_there}", 'test_is_in_rec', level="Tests")

    eq_rec = { "vfr": {
                "recid": "12",
                "ans_name": "V_fraction",
                "ans_symb": "vfr",
                "scale_expr": "1.0",
                "offset_expr": "0.0",
                "cond_expr": "",
                "symp_eq": "Eq(vfr, v/c)",
                "dependencies": ["v", "c"],
                "eq_metadata": {
                    "scaling": {
                        "fact": "1.0",
                        "scaledBy": "1.2345"
                    },
                    "solution": {
                        "params": {
                            "v": "1.5707963267949",
                            "c": "1.5707963267948966"
                        },
                        "ans": "1.00000000000000",
                        "mks_val": "1.00000000000000",
                        "ans_source": "Eq(vfr, v/c)",
                        "validation_status": "Valid",
                        "validation_timestamp": "20250929215323"
                    },
                    "eq_source": "GUI",
                    "version": "9/23/2025, 2:18:17 PM",
                    "condition_satisfied": "True"
                }
            }
        }

    log(f"Is ans_source there? Expect True: {is_in_rec('ans_source', eq_rec)}", 'test_is_in_rec', level='Tests')
    log(f"Is version there? Expect True: {is_in_rec('version', eq_rec)}", 'test_is_in_rec', level='Tests')
    log(f"Is valid there? Expect False: {is_in_rec('valid', eq_rec)}", 'test_is_in_rec', level='Tests')

    log(f"Is fact there with max_nesting=1? Expect False: {is_in_rec('fact', eq_rec, max_nesting=1)}", 'test_is_in_rec', level='Tests')

    if tests['test_is_in_rec'] == -1:
        log("Exiting Test on request (value=-1)", 'test_is_in_rec', level='Tests')
        exit()

if tests['test_get_first_in_rec']:

    eq_rec = { "vfr": {
                "recid": "12",
                "ans_name": "V_fraction",
                "ans_symb": "vfr",
                "scale_expr": "1.0",
                "offset_expr": "0.0",
                "cond_expr": "",
                "symp_eq": "Eq(vfr, v/c)",
                "dependencies": ["v", "c"],
                "eq_metadata": {
                    "scaling": {
                        "fact": "1.0",
                        "scaledBy": "1.2345"
                    },
                    "solution": {
                        "params": {
                            "v": "1.5707963267949",
                            "c": "1.5707963267948966"
                        },
                        "ans": "1.00000000000000",
                        "mks_val": "1.00000000000000",
                        "ans_source": "Eq(vfr, v/c)",
                        "validation_status": "Valid",
                        "validation_timestamp": "20250929215323"
                    },
                    "eq_source": "GUI",
                    "version": "9/23/2025, 2:18:17 PM",
                    "condition_satisfied": "True"
                }
            }
        }

    log(f"eq_rec: {eq_rec}", 'test_get_first_in_rec', level="Tests")

    log(f"expect recid=12: {get_first_in_rec('recid', eq_rec)}", 'test_get_first_in_rec', level="Tests")
    log(f"expect ans_symb='vfr': {get_first_in_rec('ans_symb', eq_rec)}", 'test_get_first_in_rec', level="Tests")
    log(f"expect eq_source='GUI': {get_first_in_rec('eq_source', eq_rec)}", 'test_get_first_in_rec', level="Tests")

    log(f"expect ans=1.000..: {get_first_in_rec('ans', eq_rec)}", 'test_get_first_in_rec', level="Tests")
    log(f"expect mks_val=1.000..: {get_first_in_rec('mks_val', eq_rec)}", 'test_get_first_in_rec', level="Tests")
    log(f"expect v='v'..: {get_first_in_rec('v', eq_rec)}", 'test_get_first_in_rec', level="Tests")
    log(f"What is 'v' with min_nesting=3? Expect ~1.5708: {get_first_in_rec('v', eq_rec, min_nesting=3)}", 'test_is_in_rec', level='Tests')
    log(f"expect scaledBy=1.2345: {get_first_in_rec('scaledBy', eq_rec)}", 'test_get_first_in_rec', level="Tests")

    params_found = get_first_in_rec('params', eq_rec)
    log(f"What if a record is identified? params_found={params_found}", 'test_get_first_in_rec', level="Tests")

    if tests['test_get_first_in_rec'] == -1:
        log("Exiting Test on request (value=-1)", 'test_get_first_in_rec', 'Tests')
        exit()

if tests['test_set_first_in_rec']:

    eq_rec = { "vfr": {
                "recid": "12",
                "ans_name": "V_fraction",
                "ans_symb": "vfr",
                "scale_expr": "1.0",
                "offset_expr": "0.0",
                "cond_expr": "",
                "symp_eq": "Eq(vfr, v/c)",
                "dependencies": ["v", "c"],
                "eq_metadata": {
                    "scaling": {
                        "fact": "1.0",
                        "scaledBy": "1.2345"
                    },
                    "solution": {
                        "params": {
                            "v": "1.5707963267949",
                            "c": "1.5707963267948966"
                        },
                        "ans": "1.00000000000000",
                        "mks_val": "1.00000000000000",
                        "ans_source": "Eq(vfr, v/c)",
                        "validation_status": "Valid",
                        "validation_timestamp": "20250929215323"
                    },
                    "eq_source": "GUI",
                    "version": "9/23/2025, 2:18:17 PM",
                    "condition_satisfied": "True"
                }
            }
        }

    log(f"eq_rec: {eq_rec}", 'test_set_first_in_rec', level="Tests")

    log(f"expect recid=13: {set_first_in_rec('recid', eq_rec, 13)}", 'test_set_first_in_rec', level="Tests")
    log(f"expect ans_symb='vfrac': {set_first_in_rec('ans_symb', eq_rec, 'vfrac')}", 'test_set_first_in_rec', level="Tests")
    log(f"expect eq_source='GEMST': {set_first_in_rec('eq_source', eq_rec, 'GEMST')}", 'test_set_first_in_rec', level="Tests")

    log(f"expect ans=0.555..: {set_first_in_rec('ans', eq_rec, 0.555)}", 'test_set_first_in_rec', level="Tests")
    log(f"expect mks_val=1.234..: {set_first_in_rec('mks_val', eq_rec, 1.234)}", 'test_set_first_in_rec', level="Tests")
    log(f"expect v='vel'..: {set_first_in_rec('v', eq_rec, 'vel')}", 'test_set_first_in_rec', level="Tests")
    log(f"Set 'v' with min_nesting=3; expect 0.1234: {set_first_in_rec('v', eq_rec, 0.1234, min_nesting=3)}", 'test_is_in_rec', level='Tests')
    log(f"expect scaledBy=2.468: {set_first_in_rec('scaledBy', eq_rec, 2.468)}", 'test_set_first_in_rec', level="Tests")

    params_found = set_first_in_rec('params', eq_rec, {'v':0.0246, 'c':1.0246})
    log(f"What if a record is set? expect |'v':0.0246, 'c':1.0246|: params_found={params_found}", 'test_set_first_in_rec', level="Tests")

    log(f"Make sure the updates latched in the eq_rec: {eq_rec}")

    if tests['test_set_first_in_rec'] == -1:
        log("Exiting Test on request (value=-1)", 'test_set_first_in_rec', 'Tests')
        exit()

##########
def parse_dict( rec ):
    name_arr = []
    symb_arr = []
    for name, symb in rec.items():
        name_arr.append(name)
        symb_arr.append(symb)
    
    return name_arr,symb_arr

if tests['test_parse_dict']:

    a_rec = {'v1':'val1', 'v2':2.0, 'v3':True}

    names = []
    vals = []

    names,vals = parse_dict(a_rec)

    log(f"Expect names[]=['v1','v2','v3'], vals[]=['val1',2.0,True] : names={names}, vals={vals}", 'test_parse_dict', level="Tests")

    if tests['test_parse_dict'] == -1:
        log("Testing Done; Exit requested (via -1) - Bye", 'test_parse_dict', level="Tests")
        exit()


##########
def to_float( val_str='tbd' ):
    val_float = 0.0
    try: 
        val_float = float(val_str)
    except:    
        level_str = "Info"
        if (val_str != tbd):
            level_str = "Alert"
        log(f"val_str:{val_str} does not convert to float.. returning None", 'to_float', level=level_str)
        return None 

    return val_float

########## Copilot 10/18/2025 default mode
# scale adjusts how tightly the mapping hugs the center 
# You can modulate saturation and brightness by energy and amplitude, as you’ve already envisioned
def frequency_to_color(frequency, f0=5e14, scale=1.0):
    import math
    log_ratio = math.log10(frequency / f0)
    hue = 180 + scale * log_ratio * 120  # center at green (180°), ±range
    hue = max(0, min(360, hue))  # clamp to visible hue range
    return hsv_to_rgb(hue, saturation, brightness)

def primary_compliment( a_color ):
    opp_color = a_color.copy()
    rgb_hex = a_color['RGB_hex']
    rgb_val = int(rgb_hex, 16)

    #log(f"rgb_hex:{rgb_hex}, rgb_val:{hex(rgb_val)}", 'primary_compliment')

    opp_rgb = ~rgb_val
    
    # Mask out any unused bits
    opp_rgb = opp_rgb & 0xFFFFFF

    #log(f"opp_rgb {hex(opp_rgb)}", 'primary_compliment')

    opp_color['RGB_hex'] = str(hex(opp_rgb))

    return opp_color

# ColorWheel opposites: Blue 0x0000FF flip everything 0xFFFF00 cut green in half 0xFF7F00 is orange.
#                       Red 0xFF0000 flip all 0x00FFFF cut blue in half 0x00FF7f is green.
#                       Green 0x00FF00 flip all 0xFF00FF cut blue in half is red-ish
# The low order bits are halved. 
# TODO: Bring in logic from GEMSTone.html
def colorWheel_opposite( a_color ):
    global red_mask, green_mask, blue_mask

    opp_color = a_color.copy()

    rgb_hex = a_color['RGB_hex']
    rgb_val = int(rgb_hex, 16)

    log(f"rgb_hex:{rgb_hex}, rgb_val:{hex(rgb_val)}", 'colorWheel_opposite')

    red_val = rgb_val >> 16
    green_val = (green_mask & rgb_val) >> 8
    blue_val = blue_mask & rgb_val 

    log(f"red_val={hex(red_val)}, green_val={hex(green_val)}, blue_val={hex(blue_val)}", 'colorWheel_opposite')

    red_opp = (0xFF - red_val)
    green_opp = (0xFF - green_val)
    blue_opp = 0xFF - blue_val

    log(f"red_opp={hex(red_opp)}, green_opp={hex(green_opp)}, blue_opp={hex(blue_opp)}", 'colorWheel_opposite')

    opp_rgb = 0xFFFFFF

    # To look color-wheel opposite in subtractive colors (paint), cut the low-order-bits of what's left in half

    dom_color = max(red_val, green_val, blue_val)
    min_color = min(red_val, green_val, blue_val)

    log(f"dom_color:{dom_color}", 'colorWheel_opposite')
    log(f"min_color:{min_color}", 'colorWheel_opposite')

    if dom_color == red_val:

        # The red part gets the blue part cut in half
        opp_rgb = (red_opp<<16) + (green_opp<<8) + int(blue_opp/2)
        
        if min_color == blue_val:
            # Yellow, e.g. FFFF00 has colorWheel opposite purple: 7f00FF.. add half-red
            opp_rgb = ((red_opp + int(red_val/2))<<16) + (green_opp<<8) + int(blue_opp/2)


        elif min_color == green_val:
            green_opp = green_opp - red_opp - blue_opp
            log(f"min_color green: green_opp={green_opp}")
            green_opp = max(0, green_opp)
            opp_rgb = (red_opp<<16) + (green_opp<<8) + blue_opp

    elif dom_color == blue_val:
        # The blue part gets the green part cut in half
        opp_rgb = (red_opp<<16) + (int(green_opp/2)<<8) + blue_opp

        if min_color == red_val:
            # Cyan, e.g. 00FFFF has colorWheel opposite orange; .. add half-green
            opp_rgb = (red_opp<<16) + (int(green_opp/2 + green_val/2)<<8) + blue_opp

        elif min_color == green_val:
            # Magenta, e.g. FF00FF has colorWheel opposite green; add half-blue
            opp_rgb = ((red_opp + int(red_val/2))<<16) + (int(green_opp/2)<<8) + blue_opp

    elif dom_color == green_val:
        # The green part gets the blue part cut in half
        opp_rgb = (red_opp<<16) + (green_opp<<8) + int(blue_opp/2)

        # TODO tired guessing
        if min_color == blue_val:
            opp_rgb = ((red_opp + int(red_val/2))<<16) + (green_opp<<8) + int(blue_opp + blue_val/2) 

        elif min_color == red_val:
            opp_rgb = ((red_opp + int(red_val/2))<<16) + (green_opp<<8) + int(blue_opp + blue_val/2) 

    log(f"opp_rgb={hex(opp_rgb)}", 'colorWheel_opposite')

    opp_color['RGB_hex'] = str(hex(opp_rgb))

    return opp_color

global red, green, blue, magenta, yellow, cyan, red_mask, green_mask, blue_mask
if tests['test_colorWheel_opposite']:
    blue_opp_color = colorWheel_opposite( blue )

    log(f"colorWheel_opposite of blue {blue['RGB_hex']} should be orangeish, #FF7F00: {blue_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    orange_opp_color = colorWheel_opposite( blue_opp_color )
    log(f"colorWheel_opposite of orange {blue_opp_color['RGB_hex']} should be blueish, ~#00807f: {orange_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    red_opp_color = colorWheel_opposite( red )
    log(f"colorWheel_opposite of red {red['RGB_hex']} should be greenish, ~#00FF7f: {red_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    green_color = colorWheel_opposite(red_opp_color)
    log(f"colorWheel_opposite of red_opp_color {red_opp_color['RGB_hex']} should be redish, ~#ff0040: {green_color}",
        'test_colorWheel_opposite', level='Tests' )

    yellow_opp_color = colorWheel_opposite(yellow)
    log(f"colorWheel_opposite of yellow {yellow['RGB_hex']} should be purple, ~#7F007F: {yellow_opp_color}",
        'test_colorWheel_opposite', level='Tests' )
    
    purple_color = colorWheel_opposite(yellow_opp_color)
    log(f"colorWheel_opposite of yellow-opposite {yellow_opp_color['RGB_hex']} should be purplish, : {purple_color}",
        'test_colorWheel_opposite', level='Tests' )

    magenta_opp_color = colorWheel_opposite(magenta)
    log(f"colorWheel_opposite of magenta {magenta['RGB_hex']} should be greenish, : {magenta_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    green_opp_color = colorWheel_opposite(magenta_opp_color)
    log(f"colorWheel_opposite of magenta-opposite {magenta_opp_color['RGB_hex']} should be magenta'ish, : {green_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    cyan_opp_color = colorWheel_opposite(cyan)
    log(f"colorWheel_opposite of cyan {cyan['RGB_hex']} should be orange'ish, : {cyan_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    orange_opp_color = colorWheel_opposite(cyan_opp_color)
    log(f"colorWheel_opposite of cyan-opposite {cyan_opp_color['RGB_hex']} should be orange'ish, : {orange_opp_color}",
        'test_colorWheel_opposite', level='Tests' )

    if tests['test_colorWheel_opposite'] == -1:
        log("test_colorWheel_opposite is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()

if tests['test_primary_compliment']:
    blue_opp_color = primary_compliment( blue )

    log(f"primary_compliment of blue should be orange, ~#FF7F00: {blue_opp_color}",
        'test_primary_compliment', level='Tests' )

    if tests['test_primary_compliment'] == -1:
        log("test_primary_compliment is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()

