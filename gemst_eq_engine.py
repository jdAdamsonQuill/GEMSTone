# FILE:     gemst_eq_engine.py  
# AUTHOR:   JD Adamson (jda)
# DATE:     05/12-15/2025
#           08/19/2025
# PURPOSE:  General Equation Handling from Strings to implement an Equation Library
#   Converts to Sympify form, and saves then and equations in strings like "v=dx/dt" and solves for v.
#   The Sympify'd equations are cached for efficient future use.
#   Calculations are logged to document any transforms.
#   This capability enables input and processing of arbitrary equations.
gemst_vers = "202510151000"

import re
from re import sub

import json

import sympy as sp
from sympy import symbols, sympify, solve, Eq, sqrt, I, E, pi
from sympy import E as EulerConst

import gemst_globals
from gemst_globals import *

#8/24/25 move to gemst_globals.py
import gemst_constants
from gemst_constants import *

import gemst_logging
from gemst_logging import log, log_val, log_var

#import gemst_testing
#from gemst_testing import tests

import gemst_utilities
from gemst_utilities import is_equiv, eval_exec, params_to_mks, get_timestamp, is_newer, to_float
from gemst_utilities import load_eq_lib, save_eq_lib, reset_eq_lib, parse_dict, to_float, get_obj_list, obj_is_valid

#8/24/25 documentation needs updating
################### The included functions #########################################################
#
# This is the normal user-utilized function to solve and save an equation.
# This routine builds, if necessary, and solves the Sympify equation string, logs it, and return the answer.
# Using Sympify operations; it builds the sympify equation from the input string and {'var':val,...} eq_spec's.
# Example usage: ans = solve_eq_str( eq_str="v=dx/dt", params={'dx':0.25, 'dt':0.5} )
##### solve_eq_str(eq_str, params)

# This routine makes a Sympify Equation (Eq) from the input variable name and formula.
# Example usage: symp_eq = sympify_var_formula( "v", "dx/dt")
##### sympify_var_formula(varname, formula)

# This routine creates a Sympify equation from a string and a dictionary of named parameters with values.
# It also adds the sympify equation into the eq_lib to save that form for future evaluation.
# Example usage: sympify_equation = to_symp_eq(varname="v", formula="dx/dt")
##### to_symp_eq(varname, formula)

# Split the equation string into variable name and formula around the equal-sign to build the equation.
##### def split_eq_str(eq_str)

# This routine solves a general sympify equation where variables are replaced with values.
# Example usage: ans = solve_symp_eq( symp_eq=my_symp_eq, var=v, params={'dx':0.25, 'dt':0.5} )
##### solve_symp_eq(symp_eq, var, params)

# This routine preprocesses the equation library, eq_lib{}, and caches the Sympify Equations.
##### build_symp_eqs()

# This routine saves the equation library in a JSON file
##### save_eq_lib( eq_lib, lib_id, log_content=False )

# This routine loads the equation library from a JSON file
##### load_eq_lib( lib_id, log_content=False )

# Processes the entire equation library repeatedly to solve everything possible from the input params 
# User defined parameters are validated against computed values
##### update_eq_lib( eq_lib, params )
#

#################################
#
# Equation Library

#jda Design Decision:
# Instead of parsing the equation to find variables using operators and parentheses as delimiters,
# and then having to exclude functions, e.g. sqrt, ln,... etc., and
# to facilitate aliasing, where e.g. a local velocity could be called vel where the equation uses v,
# and the association can be accommodated in the definition.

# General format is as a list of lists:
# eq_lib = {'equation_name':eq_spec} where eq_spec is as follows:
#eq_spec = {'ans':symb, 'var1':symb1, 'varN':symbN}

# Combined Form: {'equation_name':{ 'ans':symb, 'var1':symb1, ... 'varN':symbN} }

# The symp_eq's are saved as strings to enable JSON processing, and sympify'd when read in

# Default variable names
#dt = dx = m = E = v = f = s = accel = C = D = r = R = dR = revs = F = p = prop_F = 0
#dx_mks = dt_mks = v_mks = 0

#jda 10/8/25 Just did it again! Solve intersection of imaginary and real of x^2/e^(ix) and first imaginary 0 cross
# This needs to be proved again.. can't find old Gemini discussion that derived it..
##          'dispersion':{"light=(A*x^2)/e^(i*F*x*pi/3)",
##          'amplitude':{"light=(e^(i*F*x*pi/3)/A*x^2)",
##          'particle':{"pho=(-e^(F*x)/(A*x^2)"           # this is wrong.. inverse; simpler.. like +-n*x.
##         } 


###############################

# pending delete
#def eq_engine_init():
#    global eq_lib
#    log(f"Starting gemst_eq_engine.py, version {gemst_vers}", "eq_engine_init")
#
#    eq_lib = load_eq_lib()

def sympify_var_formula(varname, formula):
    log(f"Start: varname={varname}, formula={formula}", 'sympify_var_formula', dbg='EchoInputs')

    var = sympify(varname)
    eq  = sympify(formula)
    var_eq = Eq(var, eq)        # constructs the equation, eg v = dx/dt

    log(f"Returning var_eq={var_eq}", 'sympify_var_formula', dbg='EchoOutputs')
    return var_eq

# This routine creates a sympify equation from a string and a dictionary of named parameters with values.
# It also adds the sympify equation into the eq_lib to save that form for future evaluation.
# Example usage:
#   sympify_equation = to_symp_eq(varname="v", formula="dx/dt")
#
def to_symp_eq(varname, formula):
    log(f"Start: varname:{varname} = formula:'{formula}'", 'to_symp_eq', dbg='EchoInputs')

    var_eq = sympify_var_formula(varname, formula)

    log(f"Returning var_eq:{var_eq}", 'to_symp_eq', dbg='EchoOutputs')
    return var_eq

# Split the equation string into variable name and formula around the equal-sign to build the equation.
# General Equations have the form "equation = 0", e.g E - m*c**2 = 0;
# where general Formulas have the form "ans=formula, e.g. v=dx/dt".
# So "ans=formula" translate to Equation: "ans - formula = 0"
#
def split_eq_str(eq_str):
    log(f"Start: split_eq_str:{eq_str}", 'split_eq_str', dbg='EchoInputs')

    lhs,rhs = [s.strip() for s in eq_str.split('=')]

    if rhs == 0:
        equation = lhs
        var = formula = None
    else:
        var = lhs
        formula = rhs
        equation = f"{var} - {formula}"

    log(f"Returning equation:{equation}, var:{var}, formula:{formula}",
        'split_eq_str', dbg='EchoOutputs')
    return equation,var,formula

# Solve a general sympify equation where variables are replaced with values.
# Example usage:
#   ans = solve_symp_eq( my_symp_eq, v, params={'dx':0.25, 'dt':0.5} )
#
def solve_symp_eq(symp_eq, var, params, numeric_only=False):
    global eq_lib
    log(f"Start: symp_eq:{symp_eq}, params:{params}", 'solve_symp_eq', dbg='EchoInputs')

    symp_eq = sympify(symp_eq)

    # Can't subs the ans.. skip that one
    ans,formula = str(symp_eq).split(',') 

    # Extract the variable names from the input params and use the associated values
    for varname,val in params.items():
        if varname in formula:
            #log(f"varname '{varname}' val:{val} in symp_eq:{symp_eq}")
            symp_eq = symp_eq.subs( symbols(varname), val )

    #log(f"solve_symp_eq() solving after subs symp_eq:'{symp_eq}'")

    # Solve the equation with specific values for the named variable
    var_solution = solve(symp_eq, var)

    #log(f"var_solution:{var_solution}, type:{type(var_solution)}", 'solve_symp_eq', dbg='eq', level='Debug')

    a_list = []
    if type(var_solution) != type(a_list):
        var_val = var_solution
    else: 
        var_val = None
        if var_solution:
            var_val = var_solution[0]
            # Complex answers like N+X*I have the add.Add form
            if numeric_only and \
                not isinstance(var_val, sp.core.numbers.Float) and \
                not isinstance(var_val, sp.core.numbers.Zero) and \
                not isinstance(var_val, sp.core.add.Add) and \
                not isinstance(var_val, sp.core.mul.Mul):

                #log(f"type(var_val):{type(var_val)}", 'solve_symp_eq', "Info", dbg="Verbose")
                log(f"numeric_only={numeric_only} and var_val={var_val} does not qualify as type:{type(var_val)}",
                    'solve_symp_eq', level="Alert")
                var_val = None

    log(f"Returning var_val = {var_val}", 'solve_symp_eq', dbg='EchoOutputs')
    return var_val


# Solves a equation by name, given the params {'var1':val1, ..., 'varN':valN} and returns the answer
# Example usage:
#   v = solve_eq("velocity", {'dx':0.2, 'dt':0.3})
def solve_eq(name, params):
    global eq_lib
    log(f"Start: name:{name}, params:{params}", 'solve_eq', dbg='EchoInputs')
    try:
        eq_spec = eq_lib[name]

        symp_eq = eq_spec['symp_eq']
        ans_symb = eq_spec['ans_symb']

        var = sympify(ans_symb)

        #8/23/25 sympify then overwrite? try without
        #var = ans_symb

        log(f"Calling solve_symp_eq with {symp_eq} for var:{var}, with params:{params}",
            'solve_eq', level="Debug", dbg='eq')
        var = solve_symp_eq(symp_eq, var, params)

        # Log the calculation
        if var is not None:
            log(f"Given input params:{params}, the equation for {name} of {symp_eq} yields: {var}.",
                'solve_eq', level='Document', dbg='eq' )
        else:
            log(f"No solution to {symp_eq} given {params} was found!", 'solve_eq', level='Alert' )

        log(f"Returning var = {var}", 'solve_eq', dbg='EchoOutputs')
        return var

    except Exception as e:
        log(f"Could not solve name={name}! You get None\ne:{e}", 'solve_eq', level='Alert')
        return None

# Solve the equation string, log, and return the answer. Optionally, save the eq_lib as a JSON file
# Uses sympify; builds the sympify equation from the string and {'var':val,...} eq_spec's
# Example usage:
#   ans = solve_eq_str( eq_str="v=dx/dt", params={'dx':0.25, 'dt':0.5}, save_eq=True )
#
def solve_eq_str(eq_str, params, save_eq=True):
    global eq_lib, tbd
    log(f"Start: eq_str='{eq_str}', params={params}, save_eq={save_eq}", 'solve_eq_str', dbg='EchoInputs')

    varname_symbols = {}

    equation,var,formula = split_eq_str(eq_str)

    # Extract the variable names from the input params and save the values
    for varname,val in params.items():
        varname_symbols[varname] = symbols(varname)

    # Build the sympify equation the first time and cache for later.
    symp_eq = None

    if var is None:
        simp_eq = sympify(equation)
    elif formula is not None:
        for name,eq_spec in eq_lib.items():
            for ans,val in eq_spec.items():
                # If the variable we're looking for is the equation's answer, it's the right equation
                if var == ans_symb:
                    symp_eq = eq_lib[name]['symp_eq']
                    log(f"Using symp_eq:{symp_eq} from eq_lib[{name}]['{var}']",
                        'solve_eq_str', level="Debug", dbg='eq')
                    break

        if symp_eq is None or symp_eq == tbd:

            symp_eq = sympify_var_formula(var, formula)

            log(f"Constructed symp_eq:{symp_eq} for var:{var}={formula}",
                'solve_eq_str', dbg='eq', level="Info")

            # Save the Sympify Equation by "answer" name, e.g. "v" 
            #10/3/25 eq_spec = {'ans':str(var), 'dependencies':str(varname_symbols), 'symp_eq':str(symp_eq)}
            dependencies = []
            for varname, varval in varname_symbols:
                dependencies.push(varval)
            eq_spec = {'ans':str(var), 'dependencies':dependencies, 'symp_eq':str(symp_eq)}

            #log(f"Updating eq_lib for {var} with eq_spec:{eq_spec}", 'solve_eq_str', dbg='Verbose')
            eq_lib.update( {var:eq_spec} )

            #if save_eq:
            #    log(f"Per request save_eq={save_eq}, saving the equation library as a JSON file", 
            #        'solve_eq_str', level='Document')
            #    log(f"Calling save_eq_lib", 'solve_eq_str', level='Trace')
            #    save_eq_lib(eq_lib)
        else:
            symp_eq = eq_spec['symp_eq']
        
    # Solve the equation for the variable var given the parameters in params
    var_val = solve_symp_eq( symp_eq, var, params )

    # Log the transformation
    if var_val is not None:
        log(f"Given input params:{params}, {eq_str} yields: var={var_val}.",
            'solve_eq_str', level='Document' )
    else:
        log(f"No solution to {eq_str} given {params} was found!", 'solve_eq_str', level='Alert' )

    log(f"Returning var_val={var_val}", 'solve_eq_str', dbg='EchoOutputs')
    return var_val

# Copilot suggestions:
# Data Streaming vs. Batch Retrieval
# - If acceleration-based simulations generate large data streams over time, you might want incremental updates rather than waiting for full computation cycles.
# - Streaming options could allow users to request data at specific interval resolutions (e.g., every 10 ms or 100 ms, etc.).
# - Alternatively, a snapshot mode where specific time slices (t_start, t_end) are extracted could be useful for batch visualization.

# Returns the scale, offset, and condition results from the equation specification and parameters
def get_scale_offset_cond( eq_spec, eq_params ):
    global eq_lib
    log(f"Starting. eq_spec:{eq_spec}, eq_params:{eq_params}", 'get_scale_offset_cond', dbg='EchoInputs')

    eq_params_names = []
    eq_params_symbs = []
    eq_params_names,eq_params_symbs = parse_dict(eq_params)
    eq_params_symbs = symbols(eq_params_names)

    scale_expr = eq_spec.get('scale_expr')
    cond_expr = eq_spec.get('cond_expr')
    offset_expr = eq_spec.get('offset_expr')

    scale = None
    offset = None
    cond = None

    # 10/20/25 - Some conditions or factors may not be computed yet, so don't throw exceptions

    # Get the scale and offset factors, if specified
    if scale_expr is not None and scale_expr != 1.0 and scale_expr != "" and scale_expr != 'tbd':
        try:
            scale = eval_exec(scale_expr, eq_params)
        except Exception as e:
            #log(f"Error evaluating 'scale' expression:{scale_expr} with eq_params:{eq_params}",
                #'get_scale_offset_cond', level='Exception')
            #return scale, offset, cond
            pass

    if offset_expr is not None and offset_expr != 0.0 and offset_expr != "" and offset_expr != 'tbd':
        try:
            offset = eval_exec(offset_expr, eq_params)
        except Exception as e:
            #log(f"Error evaluating 'offset' expression:{offset_expr} with eq_params:{eq_params}",
                #'get_scale_offset_cond', level='Exception')
            #return scale, offset, cond
            pass

    if cond_expr is None or cond_expr == tbd or cond_expr == "":
        # If no conditions are specified, the lack-of-condition is satisfied..
        cond = True
    else:
        try:
            cond = eval_exec(cond_expr, eq_params)
        except Exception as e:
            #log(f"Error evaluating 'cond' expression:{cond_expr} with eq_params:{eq_params}",
                #'get_scale_offset_cond', level='Exception')
            #return scale, offset, cond
            pass
            
    log(f"Returning scale={scale}, offset={offset}, cond={cond}", 'get_scale_offset_cond', dbg='EchoOutputs')
    return scale, offset, cond

# Change literals into strings for sympify
# TODO Make this process nested records and one call could do it all!
def stringify_vals( params ):
    log(f"Starting. params:{params}", 'stringify_vals', dbg='EchoInputs')
    params_str_vals = {}
    for param,val in params.items():
        try:
            params_str_vals[param] = str(val)
        except Exception as e:
            params_str_vals[param] = val

    log(f"Returning params_str_vals: {params_str_vals}", 'stringify_vals', dbg="EchoOutputs")
    return params_str_vals


# Doesn't check nested records
def is_in_dict( symb, rec ):
    in_dict = False
    for cur_param, cur_param_val in rec.items():
        if cur_param != symb:
            continue
        in_dict = True
        break
    return in_dict

####################################################################################################
# Copilot 10/15/25 8:15pm
def is_fully_decomposed(param, eq_lib):
    visited = set()
    def trace(p):
        if p in visited: return False  # loop detected
        visited.add(p)
        deps = eq_lib[p]['dependencies']
        return all(d not in eq_lib or trace(d) for d in deps)
    return trace(param)

def get_formula( symp_eq ):
   comma_pos = -1
   comma_pos = symp_eq.find(',')
   if comma_pos > 0:
       return symp_eq[comma_pos+2:-1]

def decompose_powers( formula, exp_op="**" ):
    log(f"Starting. formula={formula}", 'decompose_powers', dbg="EchoInputs")

    # parse the formula at operators to determine variables
    delims = ", +-*/()"
    parends = "()"

    exponent_op_pos = formula.find(exp_op)

    # For all exponentiation in the formula
    while exponent_op_pos > 0:

        # after expansion, powers may remain..
        exponent_op_pos = formula.find(exp_op)

        if not (exponent_op_pos > 0):
            break

        varname = ""
        exponent = ""

        start_exponent_pos = -1
        end_var_pos = exponent_op_pos-1

        # Skip grouping parentheses
        while end_var_pos > 0 and formula[end_var_pos] in parends:
            end_var_pos -= 1

        # Variable starts at beginining, or a previous operator or grouping delimiter
        start_var_pos = end_var_pos
        while start_var_pos > 1 and formula[start_var_pos] in delims:
            start_var_pos -= 1

        varname = formula[start_var_pos:end_var_pos+1]
        
        start_exponent_pos = exponent_op_pos + len(exp_op)

        # Skip grouping parentheses
        while start_exponent_pos < len(formula)-1 and formula[start_exponent_pos] in parends:
            start_exponent_pos += 1

        # Exponent ends at end of formula or parentheses
        end_exponent_pos = start_exponent_pos
        while end_exponent_pos < len(formula)-1 and formula[end_exponent_pos] in parends:
            end_exponent_pos += 1

        exponent = formula[start_exponent_pos:end_exponent_pos+1]

        # Only integral exponents are expanded
        try:
            exponent_val = int(exponent)
            expanded_term = '(' + varname
            ii = 0
            while ii < exponent_val-1:
                expanded_term += f"*{varname}"
                ii += 1
            expanded_term += ')'

            # express the formula using the expanded term
            expanded_form = formula[0:start_var_pos]
            expanded_form += expanded_term
            expanded_form += formula[end_exponent_pos+1:]

            formula = expanded_form

        except Exception as e:
            # Not integer, so don't expand
            expanded_term = ""

    log(f"returning formula={formula}", 'decompose_powers', dbg="EchoOutputs")
    return formula

# returns decompressed version of eq_lib
def build_decompressed(eq_lib):
    global constants
    log(f"Starting.", 'build_decompressed', dbg="EchoInputs")

    # Holds the updates
    eq_lib_decom = {}
    eq_lib_decom = eq_lib.copy()

    eq_lib_len = len(eq_lib)
    orig_eq_lib_len = eq_lib_len

    for eq,eq_spec in eq_lib_decom.items():

        log(f"Outer loop: eq:{eq}", 'build_decompressed', dbg='decom')

        symp_eq = eq_spec['symp_eq']
        formula = get_formula(symp_eq)
        log(f"Parsed from {eq} symp_eq, formula:{formula}", 'build_decompressed', dbg='decom', indent=1)

        decom_formula = decompose_powers(formula)
        if decom_formula != formula:
            log(f"With powers decomposed, decom_formula:{decom_formula}", 'build_decompressed', dbg='decom', indent=1)

        formula = decom_formula

        # decompress other equation parameters

        #eq1_name = tbd
        eq1_spec = {}

        for eq1,eq1_spec in eq_lib_decom.items():
            if eq1 == eq:
                continue

            eq1_decom_spec = eq1_spec
            if 'decom_params' in eq1_decom_spec['eq_metadata']['solution'] and \
                len(eq1_decom_spec['eq_metadata']['solution']['decom_params']) > 0:

                eq1_decom_params = eq1_decom_spec['eq_metadata']['solution']['decom_params']
            else:
                eq1_decom_params = eq1_decom_spec['eq_metadata']['solution']['params'].copy()

            if is_in_dict(eq, eq1_decom_params):
                log(f"eq={eq} is in the {eq1} params:{eq1_decom_params}", 'build_decompressed', dbg='decom', indent=1)

                # Since eq is in eq1_decom_params, its name is the same as the parameter to change
                # Don't decompress when the parameter is in the formula
                if eq in formula:
                    log(f"symbol {eq} is in the {eq1} formula:{formula}, so do not decompress it here", 
                        'build_decompressed', dbg='decom', indent=1)
                    continue

                if eq1 in formula:
                    log(f"{eq1} is in formula:{formula}, so not a decompression..", 
                        'build_decompressed', dbg='decom', indent=1)
                    continue

                param_symb = eq

                log(f"Decompressing {eq1} param {param_symb} to {formula}", 'build_decompressed', dbg='decom', indent=1)

                eq1_decom_params.update( {param_symb:formula} )

                log(f"eq1_decom_params[{param_symb}]={eq1_decom_params[param_symb]}", 'build_decompressed', dbg='decom', indent=1)

                eq1_decom_meta = eq1_decom_spec['eq_metadata']
                eq1_decom_sol  = eq1_decom_meta['solution']

                eq1_decom_sol.update( {'decom_params':stringify_vals(eq1_decom_params)} );
                eq1_decom_meta.update( {'solution':eq1_decom_sol} )
                eq1_decom_spec.update( {'eq_metadata':eq1_decom_meta} )

                eq_lib_decom.update( {eq1:eq1_decom_spec} )

                log(f"Decompression for {eq1} {param_symb}: {eq_lib_decom[eq1]['eq_metadata']['solution']['decom_params']}",
                    'build_decompressed', dbg='decom', indent=1)
            else:
                log(f"{eq} is not in params of {eq1}: {eq1_decom_params}", 'build_decompressed', dbg='decom', indent=1)

    # end outer eq_lib loop
    eq_lib_decom = eq_lib_decom.copy()

    return eq_lib_decom

def build_ancestry(eq_lib):
    global ans_sources, constants
    log(f"Starting", 'build_ancestry', dbg="EchoInputs")

    ancestry = {}

    # Build ancestry of calculated values; not constants. Trail ends at input data
    for eq,eq_spec in eq_lib.items():
        log(f"Building ancestry for {eq}", 'build_ancestry', dbg='ancest', indent=1)

        ancestry = {}

        eq_metadata = eq_spec['eq_metadata']
        eq_solution = eq_metadata['solution']
        eq_params = eq_solution['params'].copy()

        log(f"The {eq} params are: {eq_params}", 'build_ancestry', dbg='ancest', indent=1)

        for param_name,param_val in eq_params.items():

            log(f"Param loop: param_name:{param_name}, param_val={param_val}", 'build_ancestry', dbg='ancest', indent=2)

            # Build ancestry of calculated values, not constants
            # 'scale' and 'offset' have no equation entries as their own category, so skip them
            if param_name == "scale" or param_name == "offset":
                log(f"Skipping inherent parameter {param_name}", 'build_ancestry', dbg='ancest', indent=2)
                continue

            if is_in_dict(param_name, constants):
                log(f"Skipping constant {param_name}", 'build_ancestry', dbg='ancest', indent=2)
                continue

            ancest_params = eq_lib[param_name]['eq_metadata']['solution']['params'].copy()

            log(f"Processing params:{ancest_params}", 'build_ancestry', dbg='ancest', indent=2)
            for ancest_param_name, ancest_param_val in ancest_params.items():
                log(f"ancest_param_name:{ancest_param_name}, ancest_param_val:{ancest_param_val}", 
                    'build_ancestry', dbg='ancest', indent=3)

                # Skip 'scale', 'offset' and constants
                if ancest_param_name == "scale" or ancest_param_name == "offset":
                    log(f"Skipping inherent parameter {ancest_param_name}", 'build_ancestry', dbg='ancest', indent=3)
                    continue

                if is_in_dict(ancest_param_name, constants):
                    log(f"Skipping {ancest_param_name} which is a constant", 'build_ancestry', dbg='ancest', indent=3)
                    continue

                # Include input data in the ancestry
                #if eq_lib[ancest_param_name]['eq_metadata']['solution']['ans_source'] == ans_sources['input_data']:

                ancestry.update( {param_name:{ancest_param_name:
                                    {'ans_source':eq_lib[ancest_param_name]['eq_metadata']['solution']['ans_source'], 
                                    'ans':eq_lib[ancest_param_name]['eq_metadata']['solution']['ans'],
                                    'timestamp':eq_lib[ancest_param_name]['eq_metadata']['solution']['timestamp']}} } )

                log(f"For {eq}, Updated {ancest_param_name} ancestry:{ancestry}", 'build_ancestry', dbg='ancest', indent=3)

        log(f"Save the ancestery in the equation library", 'build_ancestry', dbg='ancest', indent=1)
        eq_solution.update( {'ancestry':ancestry.copy()} )
        eq_metadata.update( {'solution':eq_solution.copy()} )
        eq_spec.update( {'eq_metadata':eq_metadata.copy()} )
        eq_lib.update( {eq:eq_spec.copy()} )

    return eq_lib.copy()

####################################################################################################
def get_ans( obj, param ):
    return obj[param]['eq_metadata']['solution']['ans']

def get_ans_val( obj, param ):
    ans = get_ans(obj, param)
    try: 
        ans_val = float(ans)
        return ans_val
    except Exception as e:
        log(f"{param} has non-numeric val: {ans}; returning None", 'get_ans_val');
        return None

# returns: gem_norm_E, gem_norm_m, gem_norm_dx, gem_norm_C, gem_norm_dt, gem_norm_D, gem_norm_F, gem_norm_p
def Normalize( gemstone ):
    global c, planck_h

    log(f"Starting for {gemstone}", 'Normalize', dbg='Super')

    gem = load_eq_lib(gemstone)

    #log(f"gem:{gem}", 'Normalize', dbg='Super')

    try:

        gem_E  = get_ans_val( gem, 'Energy' )
        gem_F  = gem_E/planck_h
        gem_m  = get_ans_val( gem, 'm' )
        gem_D  = get_ans_val( gem, 'D' )
        gem_dx = get_ans_val( gem, 'dx' )
        gem_dt = get_ans_val( gem, 'dt' )
        gem_v  = gem_dx/gem_dt

        log(f"gem_E:{gem_E}, gem_m:{gem_m}, gem_D:{gem_D}, gem_dx:{gem_dx}, gem_dt:{gem_dt}, gem_v:{gem_v}",
                'Normalize', dbg='Super')
    except Exception as e:
        log(f"Error getting numeric values of required GEMSTone parameters:\ne:{e}", 'Normalize', level='Exception')
        return None

    if is_equiv( gem_v, c ):
        log(f"gemstone has v=c so no Normalization done", 'Normalize', level="Alert")
        return gem_E, gem_m, gem_dx, gem_dt, gem_C, gem_D, gem_F, 0
    
    gem_vfr = gem_v/c
    gem_nu = math.atan(gem_vfr)
    log(f"gem_vfr={gem_vfr}, gem_nu:{gem_nu}", 'Normalize', dbg='Super')

    gem_omega = math.atan(gem_v)
    log(f"gem_v:{gem_v}, gem_vfr={gem_vfr}, gem_omega:{gem_omega}, gem_nu:{gem_nu}", 'Normalize', dbg='Super')

    gem_norm_dtfr = math.sin(gem_nu) # Intrinsic Time fraction Dilation with acceleration
    gem_norm_dxfr = math.cos(gem_nu) # dx fraction contraction with Time fraction Dilation normalized with acceleration
    gem_LTF = math.cos(gem_nu)      # Notice it's the Same as dxfr?!  Bang, it IS the Normalization triangle of v/c.

    gem_norm_dt = math.sin(gem_omega)
    gem_norm_dx = math.cos(gem_omega)
    gem_norm_v = gem_norm_dx/gem_norm_dt
    log(f"gem_norm_dx={gem_norm_dx}, gem_norm_dt={gem_norm_dt}, gem_norm_v={gem_norm_v}", 'Normalize', dbg='Super')

    gem_norm_D = math.cos(gem_omega)   # Intrinsic Length Contraction with acceleration
    gem_norm_C = pi*gem_norm_D      # Circumference change associated with Diameter contraction under linear acceleration
    log(f"gem_norm_D={gem_norm_D}, gem_norm_C={gem_norm_C}", 'Normalize', dbg='Super')

    gem_norm_m = math.sin(gem_omega)   # Intrinsic equivalent mass increase with acceleration adding KE
    gem_norm_p = math.cos(gem_omega)   # momentum contraction to maintain p=m*v -> p/m=v with acceleration
    log(f"gem_norm_m={gem_norm_m}, gem_norm_p={gem_norm_p}", 'Normalize', dbg='Super')


    # Kinematic Energy since v<c (results in the 4 constant multiplier instead of 2 when v=c)
    gem_norm_E = (gem_norm_m * gem_norm_dx * gem_norm_C) / (4 * gem_norm_dt * gem_norm_D)

    gem_norm_F = gem_norm_E/planck_h

    log(f"gem_norm_E:{gem_norm_E}, gem_norm_F:{gem_norm_F}",
             'Normalize', dbg='Super')

    return gem_norm_E, gem_norm_m, gem_norm_dx, gem_norm_C, gem_norm_dt, gem_norm_D, gem_norm_F, gem_norm_p


if tests['test_normalize']:
    
    #electron = load_eq_lib( "Electron" )

    E, m, dx, C, dt, D, F, p = Normalize('Electron') 

    log(f"After Normalize('Electron'):\nE:{E}, m:{m}, dx:{dx}, C:{C}, dt:{dt}, D:{D}, F:{F}, p:{p}",
        'test_normalize', level="Tests")

if tests['test_normalize'] == -1:
    log("test_normalize is Done; Exit requested (via -1) - Bye", level="Tests")
    exit()
    

def Superposition( obj1, obj2 ):
    global objs, c

    gem1_q = 0
    gem2_q = 0

    superSTone = {}
    obj_spec = {}

    gem1_name = obj1['id']
    obj1_Q = obj1['Q']
    gem1_q = to_float( obj1_Q )
    if gem1_q == None:
        gem1_q = 1

    gem2_name = obj2['id']
    obj2_Q = obj2['Q']
    gem2_q = to_float( obj2_Q )
    if gem2_q == None:
        gem2_q = 1
    
    gem1 = Normalize(obj1)
    gem2 = Normalize(obj2)

    super_name = f"{gem1_q}{gem1_name}_{gem2_q}{gem2_name}"
    super_symb = f"{gem1_q}{gem1_name}_{gem2_q}{gem2_name}"
    log(f"Creating superposition object named: {super_name}", 'Superposition', level='Document', for_summary=True)

    super_spec = {}
    super_spec.update( {'recid':'1'} )
    super_spec.update( {'ans_name':super_name })
    super_spec.update( {'ans_symb':f"{gem1_name}_{gem2_name}"} )
    super_spec.update( {'dependencies':[gem1_name, gem2_name]} )
    super_spec.update( {'scale_expr':""} )
    super_spec.update( {'offset_expr':""} )
    super_spec.update( {'cond_expr':""} )
    super_spec.update( {'symp_eq':"Superposition"} )

    super_meta = {}
    # 'ans' is E or KE, which has this scaling
    super_meta.update( {'scaling': {
                            "fact": "3.642517540571808e+16",
                            "scaledBy": "1e-15" } 
                       })

    super_meta.update( {'eq_source': 'Superposition'} )
    super_meta.update( {'version': get_timestamp()} )

    super_sol = {}
    #TODO Blending algorithm application
    super_sol.update( {'color_spec': gem1['eq_metadata']['solution']['color_spec'].copy() })

    gem1_dx = to_float( gem1['dx']['eq_metadata']['ans'] )
    gem1_dt = to_float( gem1['dt']['eq_metadata']['ans'] )
    gem1_v = gem1_dx/gem1_dt

    gem2_dx = to_float( gem2['dx']['eq_metadata']['ans'] )
    gem2_dt = to_float( gem2['dt']['eq_metadata']['ans'] )
    gem2_v = gem2_dx/gem2_dt

    # Are both objects mass having v<c?
    if not is_equiv( gem1_v, c) and not is_equiv( gem2_v, c):
        super_dx = (gem1_q * gem1_norm_dx) + (gem2_q * gem2_norm_dx)
        super_dt = (gem1_q * gem1_norm_dt) + (gem2_q * gem2_norm_dt)

        # This can occur in matter|antimatter interactions 
        # e.g. between 1 electron and 1 positron with opposite time directions (ala Feynman)
        if is_equiv( super_dt, 0.0 ):
            # Can't calculate velocity unless dx is 0 too, and if so limit as space|time->0 dx/dt=>0/0=c
            if is_equiv( super_dx, 0.0 ):
                # Energy forms from matter|antimatter interaction, and its velocity is c.
                super_v = c

                # Energy is fundamentally yellow
                super_sol.update( { 'color_spec': {'RGB_hex':"0xFFFF00"} })
            else:
                log(f"Error. Denominator dt={super_dt} invalidates velocity calculation dx/dt", 'Superposition', level='Alert')
                return None
        else:
            super_v = super_dx/super_dt

    super_E = (gem1_q * gem1_norm_E) + (gem2_q * gem2_norm_E)
    super_m = (gem1_q * gem1_norm_m) + (gem2_q * gem2_norm_m)
    super_D = (gem1_q * gem1_norm_D) + (gem2_q * gem2_norm_D)
    super_C = pi * super_D

    super_params = { super_E, super_m, super_dx, super_C, super_dt, super_D }
    super_sol.update( {'params': stringify_vals(super_params).copy()} )

    GEMST_scaling = 2.0 if is_equiv(super_v, c) else 4.0
    E_GEMSTone = (super_m * super_dx * super_C) / (GEMST_scaling * super_dt * super_C)
    super_sol.update( {'ans':str(E_GEMSTone)} )
    
    super_sol.update( {'ans_source': 'Superposition()'} )

    super_meta.update( {'solution':super_sol.copy()} )
    super_spec.update( {'eq_metadata':super_meta.copy()} )

    superSTone.update( {super_symb:super_spec} )

    KE_scaling = 1.0 if is_equiv(super_v, c) else 0.5
    Energy_Exchange = KE_scaling * super_m * v^2  # If v=c then E=m*c^2 form, else KE = 0.5*m*v^2 form

    log(f"Energy Exchange calculations follow:", 'Superposition', dbg='Super')
    log(f"Normalized Energy Difference: {super_E}", 'Superposition', dbg='Super', indent=1)
    log(f"E = (v<c?.5)*m*v^2: {Energy_Exchange}", 'Superposition', dbg='Super', indent=1)
    log(f"GEMSTone calculation: {E_GEMSTone}", 'Superposition', dbg='Super', indent=1)

    return superSTone.copy()

if tests['test_superposition']:
    global objs
    
    electron = objs['Electron']
    positron = objs['Positron']

    electron['Q'] = 1
    positron['Q'] = 1

    superSTone = {}
    superSTone = Superposition( electron, positron );
    
    log(f"After Superposition superSTone:\n{superSTone}", 'test_superposition', level="Tests")
    log(f"After Superposition objs:\n{objs}", 'test_superposition', level="Tests")

    if tests['test_superposition'] == -1:
        log("test_superposition is Done; Exit requested (via -1) - Bye", level="Tests")
        exit()

####################################################################################################

# returns: missing_params, io_params, params
def fetch_eq_data(dependencies, io_params, params, input_data_timestamp):
    log(f"Starting. io_params:{io_params}, params:{params}", 'fetch_eq_data', dbg='EchoInputs')
    global constants, eq_lib
    global valid, invalid, stale, na, tbd, needData, needsValidation, OK, ERR, FAIL

    # Remember missing params to report to the GUI for identification
    missing_params = []

    # Dependencies can be objects as equation libraries
    gem = {}

    ## Get list of available objects
    #obj_list = []
    #obj_list = get_obj_list()

    # Determine if all required depencencies are available to calculate the parameter
    for dependsOn in dependencies:

        is_in_objs = False

        # If the dependency is a full object, the equation checks aren't applicable; check first
        if dependsOn in obj_list:
            is_in_objs = True
            gem = load_eq_lib(dependsOn)
            is_valid,eq,stat = obj_is_valid(gem)
            if not is_valid:
                log(f"At timestamp {get_timestamp()}, Object {dependsOn} is not fully valid; {eq} status is: {stat}", 
                        'fetch_eq_data', for_summary=True)
                missing_params.append(dependsOn)
                continue

        is_in_constants = False
        is_in_in_params = False
        is_in_updated_params = False

        # First, check if the dependency is a constant and needs no calculation
        for const_name,const_val in constants.items():
            if dependsOn == const_name :
                is_in_constants = True

                log(f"Adding {dependsOn}={const_val} from constants into equation params", 'fetch_eq_data', dbg="fetch")
                # Update the equation param data with the constant value
                params.update( {dependsOn:const_val} )

                break
        if is_in_constants:
            continue

        # Not in constants..
        # Look in the io_params to see if dependencies are input data
        for in_param_name,in_param_val in io_params.items():
            if dependsOn == in_param_name:
                # We have the required dependency data
                is_in_in_params = True

                # Update the equation param data with the input value
                log(f"Adding {dependsOn}={in_param_val} from inputs into equation params", 'fetch_eq_data', dbg="fetch")
                params.update( {dependsOn:in_param_val} )

                break

        if not is_in_constants and not is_in_in_params:

            # Check the values in the equation params data to see if dependency is newly calculated
            for cur_param_name,cur_param_val in params.items():

                if dependsOn == cur_param_name:

                    # if dependencies are out of date, new computations are needed
                    dependsOn_timestamp = eq_lib[dependsOn]['eq_metadata']['solution']['timestamp']

                    if float(dependsOn_timestamp) < float(input_data_timestamp):
                        params.update( {dependsOn:eq_states['stale']} )
                    else:
                        is_in_updated_params = True
                        ans_str = eq_lib[dependsOn]['eq_metadata']['solution']['ans']
                        try:
                            ans_val = float(ans_str)
                            log(f"Updating io_params[{dependsOn}]={ans_val}", 'fetch_eq_data', dbg="fetch")
                            io_params.update( {dependsOn:ans_val} )
                        except Exception as e:
                            not_numeric = True
                            log(f"Cannot convert ans for {eq} to numeric", 'update_eq_lib', dbg='fetch', level="Info")

                # end if: dependency is recently calculated
            # end for all params in the eq_lib

            if not is_in_updated_params:
                missing_params.append(dependsOn)

        # end if: not constant or input params

    # end for all dependencies
    
    return missing_params, io_params, params


def update_eq_lib( eq_lib_data='default', lib_id='default', io_params='default', symbolic_or_numeric="numeric", load=False, save=False):
    log(f"Starting.  io_params={io_params}, load={load}, lib_id={lib_id}", 'update_eq_lib', dbg="eq")
    global constants, eq_lib, objs, obj_list
    global eq_states, ans_sources
    global na, tbd, OK, ERR, FAIL

    # Just read the object library json files once per update and keep the list global.
    obj_list = get_obj_list()

    if load:
        if eq_lib_data != 'default':
            log(f"eq_lib_data was specified as input with 'load=True' option, so that input data is irrelevant",
            'update_eq_lib', level="Alert")

        log(f"Loading eq_lib id:{lib_id}", 'update_eq_lib', level="Document", for_summary=True)
        eq_lib = load_eq_lib(lib_id=lib_id)

    else:
        if eq_lib_data == 'default':
            log(f"Either specify load=True or provide the eq_lib_data. Neither, so doing nothing..", 'update_eq_lib', level='Alert')
            return tbd, io_params, io_params

        log(f"Using input eq_lib_data, lib_id:{lib_id}", 'update_eq_lib', level="Document", for_summary=True );
        eq_lib = eq_lib_data;

    if io_params == 'default':
        io_params = {}
        for eq,eq_spec in eq_lib.items():
            formula = get_formula( eq_spec['symp_eq'] )
            io_params.update( {eq:formula} )

    # Mark the user input set. These are the basis for the updates; they don't get calculated but set..
    input_data_timestamp = get_timestamp()
    for param_name,param_val in io_params.items():
        if is_in_dict( param_name, eq_lib ):
            for eq,eq_spec in eq_lib.items():
                if eq_spec['ans_symb'] == param_name:
                    eq_lib[eq]['eq_metadata']['solution']['ans'] = str(io_params[param_name])
                    eq_lib[eq]['eq_metadata']['solution']['ans_source'] = ans_sources['input_data']
                    eq_lib[eq]['eq_metadata']['solution']['validation_status'] = ans_sources['input_data']
                    eq_lib[eq]['eq_metadata']['solution']['timestamp'] = input_data_timestamp

                    log(f"Set {eq} validation_status to {eq_lib[eq]['eq_metadata']['solution']['validation_status']}", 'update_eq_lib', dbg='eq')
                    break
            # end for: updating eq lib as user input
        # end if: checking that parameters are actually specifeid in the equation library; not error for symantic relationship
    # end for: processing user input

    # Keep trying until no more equations can be solved
    done = False
    num_loops = 0
    max_loops = max( len(io_params), 2 )

    # First validate the input parameters if there are self-interacting sets
    do_validation = True

    # Solve everything possible from the input data set
    while not done and num_loops <= max_loops:
        num_loops += 1
        if num_loops > 1:
            do_validation = False

        got_new_ans = False

        # Check each equation to see if its required parameters are available and valid
        for eq, eq_spec in eq_lib.items():

            # clear out every loop
            dependencies = []
            eq_metadata = {}
            solution = {}
            scaling = {}
            params_strs = {}
            params = {}

            # pull records and data from the equation library

            # Nested records
            dependencies = eq_spec['dependencies']

            eq_metadata = eq_spec['eq_metadata']
            scaling = eq_metadata['scaling']

            solution = eq_metadata['solution']
            params_strs = solution['params']             # values are stringified for json

            decom_params = {}
            if 'decom_params' in solution:
                decom_params = solution['decom_params']

            # Parameter values
            ans_symb = eq_spec['ans_symb']
            ans_str = solution['ans']
            timestamp = solution['timestamp']

            # First pass just validates the input parameters, if interdependent variable-sets are input
            if do_validation:
                if not is_in_dict( eq, io_params ):
                    continue
                log(f"Doing validation pass on input parameter {eq} with input {io_params}", 'update_eq_lib', dbg="eq")
            else: 
                # After the validation pass, input parameters are "specified" and not computed
                if solution['ans_source'] == ans_sources['input_data']:
                    log(f"{eq} is an input parameter, not computing it..", 'update_eq_lib', dbg="eq")
                    continue

            # Don't recalculate already updated values 
            try:
                timestamp_val = float(solution['timestamp'])
                if solution['validation_status'] == eq_states['valid'] and timestamp_val >= float(input_data_timestamp): 
                    continue
            except Exception as e:
                pass

            not_numeric = False

            # TODO make utility routine compliment to stringify_vals as vals_to_float..
            # Make floats out of numeric params when possible
            for param_name, val_str in params:
                try:
                    params[param_name] = float(val_str)
                except Exception as e:
                    not_numeric = True

            log(f"Checking all dependencies for {eq}: {dependencies}", 'update_eq_lib', dbg="eq")

            missing_params = []

            missing_params, io_params, params = fetch_eq_data( dependencies, io_params, params, input_data_timestamp )

            if len(missing_params) > 0:

                log(f"Cannot calculate {eq} numerically because these parameters are missing: {missing_params}", 
                    'update_eq_lib', dbg="eq")

                # For input-parameter sets, the answer was assigned so not all dependencies need to be available
                if solution['ans_source'] == ans_sources['input_data']:
                    continue

                # This can be updated by sympy returning answers that contain variables, instead of numeric values
                solution.update( {'ans':eq_states['needs_data']} )

                eq_metadata.update( {'missing_params': missing_params} )
                eq_metadata.update( {'solution': solution} )
                eq_spec.update( {'eq_metadata':eq_metadata} )
                eq_lib.update( {eq:eq_spec} );

                if do_validation:
                    # no validation possible. Input that is not self-contradictory (which this cannot be) is valid
                    log(f"Input parameter is not inconsistent", 'update_eq_lib', level="Document", for_summary=True )
                    solution['validation_status'] = eq_states['valid']

                    log(f"Set {eq} validation_status to {solution['validation_status']}", 'update_eq_lib', dbg='eq')
                    continue

            # Nothing missing since we're here.. if params were missing before, they aren't now..
            missing_params = []
            eq_metadata.update( {'missing_params': missing_params} )

            # Make the Sympify symbols
            eq_symbols = {}
            for paramname,paramval in params.items():
                symb = symbols(paramname)
                eq_symbols[paramname] = symb

            name_arr = []
            symb_arr = []
            eq_symb_arr = []
            name_arr,symb_arr = parse_dict( eq_symbols )
            eq_symb_arr = symbols(name_arr).copy()

            cond = False
            scale = 1.0
            offset = 0.0

            # Valid data is: the constants, validated input data, and newly calculated parameters
            if symbolic_or_numeric == "numeric":
                eq_valid_data = {**constants, **io_params, **params}
            else:
                eq_valid_data = {**constants, **io_params, **decom_params}

            # Do the scale and offset calculations and the condition evaluation
            scale, offset, cond = get_scale_offset_cond( eq_spec, eq_valid_data )

            if cond is not None:
                eq_valid_data.update( {'cond': cond} )
            if scale is not None:
                eq_valid_data.update( {'scale': scale} )
            if offset is not None:
                eq_valid_data.update( {'offset': offset} )

            eq_metadata.update( {'condition_satisfied': str(cond)} )

            if cond:
                log(f"The pre-condition for {eq} was satisfied; solving it.", 'update_eq_lib', dbg="eq")

                symp_eq = eq_spec["symp_eq"]

                # Special case calculation sets
                if symp_eq == 'Superposition':
                    superSTone = Superposition( eq_spec["dependencies"] )
                    super_symb = superSTone['ans_symb']
                    eq_lib[super_symb] = superSTone
                    continue

                # Solve the Sympify Equation
                ans,formula = str(symp_eq).split(',') 
                sympy_ans = sympify(ans_symb)
                sympy_ans = solve_eq(eq, eq_valid_data)
                log(f"solve_eq returned sympy_ans={sympy_ans}", 'update_eq_lib', dbg="eq")

                log(f"Solved {eq} for {ans_symb}={sympy_ans} using params:{params}", 
                     'update_eq_lib', level='Document', for_summary=True)

                if sympy_ans is None:
                    log(f"Could not solve for {eq}!", 'update_eq_lib', level='Alert', for_summary=True)
                    continue
                else:
                    cur_timestamp = get_timestamp()
                    got_new_ans = True

                    # Note that sympy computes both numerically and tracking variables
                    try:
                        sympy_ans_val = float(sympy_ans)

                    except Exception as e:
                        not_numeric = True
                        log(f"Solution is non-numeric; parameterized as {sympy_ans}", 'update_eq_lib', dbg="eq")
                        if do_validation:
                            log(f"No input parameter inconsistency", 'update_eq_lib', level="Document", for_summary=True)

                    solution.update( {'ans':str(sympy_ans)} ) 

                    # computed numerical values are valid; validation is for input parameter set consistency
                    solution['validation_status'] = eq_states['valid']

                    log(f"Set {ans_symb} validation_status to {solution['validation_status']}", 'update_eq_lib', dbg='eq')

                    if not not_numeric:
                        # collect the answer as new valid data
                        eq_valid_data.update( {ans_symb:sympy_ans_val} )

                        # update return parameters
                        io_params.update( {ans_symb:sympy_ans_val} )

                        # Use scaling data factors to do units conversion
                        mks_params = params_to_mks( {ans_symb:sympy_ans_val} )
                        solution.update( {'mks_val':str(mks_params[ans_symb])} )

                    solution['timestamp'] = cur_timestamp

                    # Don't updated specified input parameter values
                    if not is_in_dict( ans_symb, io_params ):
                        log(f"At datetime {cur_timestamp}, Updating ans for {eq} to {str(sympy_ans)}", 'update_eq_lib', dbg="eq")

                        # This will keep symbolic solutions as well as numeric ones
                        solution.update( {'ans':str(sympy_ans)} ) 

                    # Change literals into strings for sympify
                    valid_data_str = stringify_vals( eq_valid_data )

                    # Stringify the actual values used in the calculation for the json structure
                    params_strs = stringify_vals(params)

                    # Remember the data and equation that led to the answer
                    solution.update( {'params': params_strs} )
                    solution.update( {'ans_source': eq_spec['symp_eq']} )
                    solution.update( {'validation_status': eq_states['valid']} )
                    solution.update( {'timestamp': get_timestamp()} ) 

                    if do_validation and solution['ans_source'] == ans_sources['input_data']: 

                        in_val = io_params[ans_symb]

                        # Check the equivalence and keep the details for reporting validity
                        equiv,diff,abs_eps,rel_eps = is_equiv( sympy_ans, in_val, details=True )

                        solution['error'] = str(diff)
                        solution['abs_eps'] = str(abs_eps)
                        solution['rel_eps'] = str(rel_eps)

                        if not equiv:
                            log(f"Validation error. {ans_symb} computed from {eq_spec['symp_eq']} to be {sympy_ans}, "
                                f"but input data has {ans_symb} = {in_val}.\n"
                                f"Difference={diff} with abs,relative epsilons: {abs_eps},{rel_eps}",
                                'update_eq_lib', level="VALIDATION_ERROR", for_summary=True)

                            solution['validation_status'] = invalid
                            log(f"Set {eq} validation_status to {solution['validation_status']}", 'update_eq_lib', dbg='eq')

                            eq_valid_data.pop( ans_symb, None )
                            continue
                        else:
                            log(f"Setting validation_status to {valid} for {eq_name}:{ans}",
                                'update_eq_lib', level='Document', for_summary=True)
                            solution['validation_status'] = valid

                            log(f"Set {eq} validation_status to {solution['validation_status']}", 'update_eq_lib', dbg='eq')

                    log(f"Solved {eq} for {ans_symb}={sympy_ans} using params:{params}", 
                         'update_eq_lib', level='Document', for_summary=True)

                    eq_metadata.update( {'solution': solution} );
                    eq_spec.update( {'eq_metadata': eq_metadata} )
                    eq_lib[eq] = eq_spec

                    eq_valid_data.update( {ans_symb:sympy_ans} )
                    io_params.update( {ans_symb:sympy_ans} )

            else:
                pass
            # end: if cond is satisfied

            eq_spec.update( {'eq_metadata':eq_metadata} )
            eq_lib.update( {eq:eq_spec} )

        # end: for all equations

        # done at end of above loop; no need to dup
        #eq_spec.update( {'eq_metadata':eq_metadata} )
        #eq_lib.update( {eq:eq_spec} )

        # validating the input parameters the first pass
        if do_validation:
            log(f"Done with validation pass", 'update_eq_lib', dbg="eq")
            do_validation = False
        else:
            # If we run through all the equations and can't calculate anything new, we're done
            if not got_new_ans:
                done = True

    # end: while looping over the equations to find more to solve with new answers

    eq_lib = build_ancestry(eq_lib)

    #TODO Need to expand symbols in answers, e.g. c_dx_dt -> dx/dt, c_geom -> PI/2.0

    # make sure recid fields are numerically sequential
    recid = 1
    for eq,eq_spec in eq_lib.items():
        eq_spec['recid'] = str(recid)
        eq_lib[eq] = eq_spec
        recid += 1

    if save:
        log(f"Saving the eq_lib with id: {lib_id}", 'update_eq_lib', level='Document', for_summary=True);
        save_eq_lib(eq_lib, lib_id=lib_id, log_content=False)

    log(f"Returning eq_lib:{lib_id} and updated io_params:{io_params}", 'update_eq_lib', dbg="EchoOutputs")
    return eq_lib.copy(), io_params.copy()


################################################################################
### Tests ###


def run_tests():
    global eq_lib

    if tests['test_build_decompressed']:

        eq_lib = load_eq_lib(lib_id="test_lib")

        eq_lib_decom = build_decompressed(eq_lib)

        log(f"Decompressed test_lib.json to {json.dumps(eq_lib_decom,indent=4)}", 'test_build_decompressed', level="Tests")

        io_params = { "v":1.0, "dt":1.0, "m":0.1, "D":1.0 }

        log(f"Calling update_eq_lib() with input:io_params={io_params}, lib_id=decom_test_lib", 
            'test_build_decompressed', level="Tests")

        eq_lib,io_params = update_eq_lib( eq_lib_decom, io_params=io_params, lib_id='decom_test_lib', load=False, save=True )

        if tests['test_build_decompressed'] == -1:
            log("test_build_decompressed is Done; Exit requested (via -1) - Bye", level="Tests")
            exit()

    if tests['test_update_eq_lib_symb']:

        # def update_eq_lib( eq_lib_data='default', lib_id='default', params='default', load=False):

        eq_lib = {}
        eq_lib_id = "test_lib"
        eq_lib = load_eq_lib(eq_lib_id)

        eq_lib_decom = build_decompressed(eq_lib)

        io_params = { "v":1.0, "dt":1.0, "m":0.1, "D":1.0 }

        log(f"Calling update_eq_lib() for Symbolic computions, lib_id={eq_lib_id}", 
            'test_update_eq_lib_symb', level="Tests")

        eq_lib_decom_symb,io_params = update_eq_lib( eq_lib_decom, lib_id=eq_lib_id, symbolic_or_numeric="symbolic", save=False )

        log(f"After update_eq_lib for Symbolic, io_params:{io_params}", 'test_update_eq_lib_symb', level="Tests")

        log(f"eq_lib_decom_symb follows:\n{json.dumps(eq_lib_decom_symb, indent=4)}", 'test_update_eq_lib_symb', level="Tests")

        eq_lib_id = "decom_test_lib_symb"
        save_eq_lib(eq_lib_decom_symb, lib_id=eq_lib_id)

        log(f"Calling update_eq_lib() a 2nd time for Symbolic computions, lib_id={eq_lib_id}", 
            'test_update_eq_lib_symb', level="Tests")

        eq_lib_decom_symb_2,io_params = update_eq_lib( eq_lib_decom_symb, lib_id=eq_lib_id, symbolic_or_numeric="symbolic", save=False )
        log(f"eq_lib_decom_symb_2 follows:\n{json.dumps(eq_lib_decom_symb_2, indent=4)}", 'test_update_eq_lib_symb', level="Tests")

        if tests['test_update_eq_lib_symb'] == -1:
            log("test_update_eq_lib_symb is Done; Exit requested (via -1) - Bye", level="Tests")
            exit()

    if tests['test_update_eq_lib']:

        # def update_eq_lib( eq_lib_data='default', lib_id='default', params='default', load=False):

        eq_lib_id = "DomainOfInteraction"

        eq_lib = {}

        io_params = { "v":1.0, "dt":1.0 }

        log(f"Calling update_eq_lib() with input:io_params={io_params}, lib_id={eq_lib_id}", 'test_update_eq_lib', level="Tests")
        eq_lib,io_params = update_eq_lib( eq_lib, io_params=io_params, lib_id=eq_lib_id, load=True, save=False )
        log(f"After update_eq_lib, io_params:{io_params}", 'test_update_eq_lib', level="Tests")

        if tests['test_update_eq_lib'] == -1:
            log("test_update_eq_lib is Done; Exit requested (via -1) - Bye", level="Tests")
            exit()

    if tests['test_solve_symp_eq']:

        #def solve_eq_str(eq_str, params, save_eq=True):
        log(f"Calling solve_eq_str ", 'test_solve_symp_eq', level="Tests")
        #my_velocity = solve_eq_str( "my_velocity=dx/dt", {'dx':0.25, 'dt':0.5}, save_eq=True )
        gam = solve_eq_str( "gam=atan(vfr)", {'vfr':1.0} )

        log(f"solve_symp_eq returned from atan(vfr): {gam}", 
            'test_solve_symp_eq', "Tests");

        if tests['test_solve_symp_eq'] == -1:
            log("solve_symp_eq is Done; Exit requested (via -1) - Bye")
            exit()

    if tests['test_decompose_powers']:

        # nominal case: decompose squares
        formula = "v**2"
        log(f"Testing decompose_powers('{formula}'); expect 'v*v': '{decompose_powers(formula)}'",
            'test_decompose_powers', level="Tests")

        # test with operators 
        formula = "m*v**2"
        log(f"Testing decompose_powers('{formula}'); expect 'm*v*v': '{decompose_powers(formula)}'",
            'test_decompose_powers', level="Tests")

        # test with multiple powers and parentheses
        formula = "(C**2)/(4*D**2)"
        log(f"Testing decompose_powers('{formula}'); expect '(C*C)/(4*D*D)': '{decompose_powers(formula)}'",
            'test_decompose_powers', level="Tests")

        if tests['test_decompose_powers'] == -1:
            log("test_decompose_powers is Done; Exit requested (via -1) - Bye", level="Tests")
            exit()


    if tests['test_solve_eq']:
        p = solve_eq('momentum', {'m':2.0, 'v':0.2})
        log(f"Solving 'momentum' for m:2.0, v:0.2 so expect p=0.4: {p}", 'test_solve_eq', level="Tests")
        if not is_equiv(p, 0.4):
            log(f"Expected p=0.4 but got: {p}!", 'test_solve_eq', level="ERROR")
        else:
            log(f"Success.", 'test_solve_eq', level="Tests")

        if tests['test_solve_eq'] == -1:
            log("Exiting Test on request (value=-1)", 'test_solve_eq_str', 'Tests')
            exit(-1)

    if tests['test_solve_eq_str']:
        my_velocity = solve_eq_str( "my_velocity=dx/dt", {'dx':0.25, 'dt':0.5}, save_eq=True )
        log(f"Where dx=0.25 and dt=0.5, expect my_velocity=dx/dt=0.5: {my_velocity}", 
            'run_tests():test_solve_eq_str 1', level='Tests')
        if my_velocity != 0.5:
            log(f"Error! my_velocity={my_velocity}, not 0.5 as expected!", 
                'run_tests():test_solve_eq_str', level='Error')
        else:
            # Make sure the new equation got saved to the JSON file
            eq_lib = load_eq_lib( 'default', log_content=True )
            eq_spec = eq_lib['my_velocity']
            if eq_spec is not None:
                log(f"Found my_velocity in equ_lib with eq_spec:{eq_spec}", 'run_tests():test_solve_eq_str', level='Tests')
                log(f"Success 1.", 'run_tests():test_solve_eq_str', level='Tests')

        # Validate the manually entered equation in the DomainOfInteraction.json file
        manual_velocity = solve_eq( 'manual_velocity', {'dx':0.5, 'dt':0.3} )
        if not is_equiv( manual_velocity, 0.5/0.3 ):
            log(f"Testing Error: expected {0.5/0.3} but manual_velocity={manual_velocity}!",
                'run_tests():test_solve_eq_str 1a', level='ERROR')
        else:
            log(f"Success 1a.", 'run_tests():test_solve_eq_str', level='Tests')

        # Validate the caching.. 
        my_velocity = solve_eq( "my_velocity", {'dx':1.5, 'dt':2.0} )
        log(f"Where dx=1.5 and dt=2.0, expect my_velocity=dx/dt=0.75: {my_velocity}", 
            'run_tests():test_solve_eq_str 1b', level='Tests')
        if my_velocity != 0.75:
            log(f"Error! my_velocity={my_velocity}, not 0.75 as expected!", 
                'run_tests():test_solve_eq_str 1b', level='Error')
        else:
            log(f"Success 1b.", 'run_tests():test_solve_eq_str 1b', level='Tests')

            log(f"Now removing my_velocity from the equation library and re-saving")
            rm_eq( 'my_velocity', log_content=True )

        # End on request
        if tests['test_solve_eq_str'] == -1:
            log("Exiting Test on request (value=-1)", 'test_solve_eq_str', 'Tests')
            exit()

    if tests['test_build_symp_eqs']:

        build_symp_eqs()

        # use the pre-built equation for duration from dx,v for a solve
        symp_eq = sympify(eq_lib['duration']['symp_eq'])
        if symp_eq is None:
            log("Error: symp_eq is None!", 'test_build_symp_eqs', level="ERROR")
            #exit()

        ans = solve_symp_eq( symp_eq, 'dt', {'dx':2,'v':4} )

        log(f"Solving duration for dx:2,v:4; expect 0.5: {ans}", 'test_build_symp_eqs', level='Tests')
        if (not is_equiv(ans, 0.5)):
            log(f"Error, expecting 0.5 but got ans={ans}", 'test_biuld_symp_eqs', level="ERROR")
        else:
            log(f"Success 3.", 'test_biuld_symp_eqs', level="Tests")

        if tests['test_build_symp_eqs'] == -1:
            log("Exiting Test on request (value=-1)", 'test_build_symp_eqs', 'Tests')
            exit()

