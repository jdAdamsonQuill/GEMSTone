import json

import gemst_constants
from gemst_constants import *

# Multiply the cradian units by the factor to convert to the specified units values
# Note: each "ans" in the equation library eq_lib.json needs to have scaling specified here
# c=pi/2, vfr=v/c, pif=2*v/pi, v=c*pif
# v_mks=(2*v/pi)*c_mks
# v=dx/dt, dx=v*dt, dt=dx/v, c=dx/dt, 
# a = d^2x/dt**2, max=c^2, afr=a/c^2
# dt_mks: c(m)/1(s) = pi/2(rad)/t(tpif) --> pi/2 = c_mks*t, t=pi/2*c_mks *dt = 5.240e-9 s
# dx_mks: c(m)/1(s) = x(xpif)/(pi/2*c_mks) --> x = c_mks*(pi/2*c_mks) = pi/2 *dx
# v_mks = c = dx/dt = (pi/c)/(pi/2*c_mks) = (pi*(2*c))/(pi*c) = 2*c/c = c -ok-
# v=dx/dt  dx=v/dt, dt=dx*v, v=c->dx/dt=pi/2, 2*dx=pi*dt -> dx=pi*dt/2, dt=2*dx/pi
# tpif = pi/2*c while xpif = pi/c; the ratio tpif to xpif is pi/2*c / pi/c = c*pi/2*c*pi = 0.5 -> xpif/tpif = 2.0
# v as cfrac converts to mks by c(m/s); v as pif ratio to c=pi/2 is cfrac
# convert cfrac dist&dur 
# let xfrac/tfrac = .1c; v=.1(pi/2); v=cfrac*pi/2; dx/dt = cfrac*pi/2, dx = cfrac*pi*dt/2, dt = cfrac*pi/2*dx
# 0 <= v <= pi/2; 0 <= dx/dt <= pi/2; vpif = (dx/dt)/pi/2 = 2*dx/pi*dt; 
# c_mks/1 = pi/2; pi=2*c_mks; 
# v_mks = v*c_mks*2/pi
# subs pi=2*c_mks c_mks*2/2*c_mks = 1.0 = v..
# dx_mks/dt_mks = ((dx/dt)*c_mks*2)/pi
# dx_mks = ((dx/dt)*c_mks*2)/pi)*dt_mks = dx*dt_mks/dt
# dt_mks = dx_mks/((dx/dt)*4*c_mks**2), 
# dt_mks = dt* 2*c_mks/(2*c_mks)=1.0
           #'v':{'fact':c_mks*(2/pi), 'scaledBy':no_scaling},
# v=(2*c_mks)/pi
# v=dx/dt
# Nope. pi/2 is not distance, but velocity as pif.  c_mks/1_s = (pi/2)/x_t; pi/2*1_s = c_mks*x_t;  x_t = pi/(2*c_mks)
# c_mks = pi/2 rad ; c=dx/dt; pi/2=dx/dt; pi*dt=2*dx dx=(pi*dt)/2; dt=(2*dx)/pi
# dx = pi/2 * dt/2, dt=2/pi * dx/pi; dx = c * dt/2, dt = 1/c * dx/pi
# dx = v*dt, dx = (2*c_mks)*dt/pi
# dt = dx/v, dt = (dx*pi)/(2*c_mks)
# v=(2*c_mks)/pi 
# pi-fraction:: 1 pif:: pi*.01; c = 0.5 pif = pi/2 radians
# distance-fraction:: 1 
# mks cfrac = 0.01 * c_mks
# cradian pif:: 0.01 * 0.5*pi
# cradian xpif:: 0.01 * 0.5*pi * c_mks = 0.005*pi*c_mks
# cradian tpif = 1/c_mks * xpif/pi = (0.005 * c_mks)/(c_mks) = 0.005

no_scaling = 1.0

# These have been integrated into the Equation Spec for each parameter
# instead of being dynamically extracted from this record, which requires
# that the structure include all scaling information, which is inconvenient in the GUI specifications.
# This is How the scaling factors and "scaledBy" powers-of-10 are defined.
# the "xxx_fact" and "xxx" scalings are inverses of each other.. so pico is 10^9, pico_fact is 10^-9..
scaling = {'dx':{'fact':(piUnder2*c_mks)*pico_fact, 'scaledBy':pico},
           'dt':{'fact':no_scaling, 'scaledBy':no_scaling},
           'v':{'fact':(2*c_mks/pi)*no_scaling, 'scaledBy':no_scaling},
           'vfr':{'fact':no_scaling, 'scaledBy':no_scaling},
           'C':{'fact':no_scaling, 'scaledBy':no_scaling},
           'D':{'fact':no_scaling, 'scaledBy':no_scaling},
           'nu':{'fact':no_scaling, 'scaledBy':no_scaling},
           'v_new':{'fact':(2*c_mks)/pi, 'scaledBy':no_scaling},
           'accel':{'fact':cc/cc_mks, 'scaledBy':quad},
           'mass':{'fact':kg_fact, 'scaledBy':quint_fact},
           'mass_equiv':{'fact':kg_fact, 'scaledBy':quint_fact},
           'm_E_CD':{'fact':kg_fact, 'scaledBy':quint_fact},
           'energy':{'fact':joule_fact, 'scaledBy':quint_fact},
           'energy_equiv':{'fact':joule_fact, 'scaledBy':quint_fact},
           'E_m_dx_dt':{'fact':joule_fact, 'scaledBy':quad_fact},
           'E_m_CD':{'fact':joule_fact, 'scaledBy':quad_fact},
           'dx_E_m_dt':{'fact':pi/c_mks, 'scaledBy':pico},
           'dt_E_m_dx':{'fact':pi/(2*c_mks), 'scaledBy':pico},
           'p':{'fact':cc/cc_mks, 'scaledBy':quad_fact},
           'force':{'fact':cc/cc_mks, 'scaledBy':quint_fact},
           'work':{'fact':cc/cc_mks, 'scaledBy':quint_fact} 
          }

# To build a .json file from the hardcoded dictionary..
# Note that indent=4 "pretty prints" the json output string
#scaling_json = json.dumps(scaling, indent=4)
#print(f"scaling_json = {scaling_json}")
# copy/paste the results; or open and write to the file if other than infrequent..

# 'filename':'gemst_options_lib.json',  # The json file that holds the options dictionary (if we implement that)
options_lib = {'dbg':9,                             # dbg level
               'X_axis':'dx_m',                     # Recognized: dt=duration, dx=distance; m=mass; E=Energy; _ delimits
               'Y_axis':'dt_p',                     # Recognized: dt=duration, dx=distance; m=mass; E=Energy; _ delimits
               'Z_axis':'E_F',                      # Recognized: dt=duration, dx=distance; m=mass; E=Energy; _ delimits
               'plot_duration':10,                  # Seconds of velocity to disply points for 
               'time_interval':1.0                  # Seconds between points   
              }

# Note: the "level" options collects just those messages into output files with that identification
dbg_keys = {'dx':0, 'dt':0, 'E':0, 'm':0, 
            'v':0, 's':0, 'accel':0, 'p':0, 'F':0, 
            'C':0, 'D':0, 'r':0, 'R':0, 'dR':0, 'revs':0, 'prop_F':0,
            'vals':0, 'work':0, 'I':0, 
            'EchoInputs':0, 'EchoOutputs':0, 'Testing':0, 'PathCheck':0,
            'eq':1, 'Validity':0, 'Trace':0, 'eq_lib':0, 'decom':0, 'ancest':0, 'fetch':0,
            'Verbose':0, 'Super':1
            }

# Holds the equation library read/written from/to the JSON file
eq_lib = {}

# Holds the objects as equation sets having Quantity
# TODO: Read from file obj_lib.json
objs = {
    "DomainOfInteraction":{'id':'DomainOfInteraction', "Q": "1"}, 
    "Electron":{'id':'Electron', "Q": "1"}, 
    "Photon":{'id':'Photon', "Q": "1"}, 
    "Positron":{'id':'Positron', "Q": "1"}
}
obj_list = []


# Test Template. Add "test_name":0 to tests dictionary.
#
#if tests['test_name']:
##   body of test
#    if tests['test_name'] == -1:
#        log("test_name is Done; Exit requested (via -1) - Bye", level="Tests")
#        exit()

tests = {'test_get_dx':0, 'test_get_dt':0, 'test_get_m':0, 'test_get_E':0, 'test_pct_cc_to_Em':0, 'test_nom_to_ccfr':0,
         'test_get_v':0, 'test_get_s':0, 'test_get_accel':0, 'test_get_F':0, 'test_get_p':0,
         'test_get_C':0, 'test_get_D':0, 'test_get_r':0, 'test_get_R':0, 'test_get_dR':0, 'test_get_revs':0,
         'test_get_prop_F':0, 'test_log_params':0, 'test_log':0, 'test_cfrac_pct_c':0, 'test_micro_to_frac':0,
         'test_frac_to_micro':0, 'test_m_pct_c':0, 'test_mks_micro':0, 'test_kg_Xforms':0, 'test_kg_pct_c':0,
         'test_put_dx':0, 'test_put_dt':0, 'test_put_dxDt':0, 'test_put_m':0, 'test_put_E':0,
         'test_put_v':0, 'test_put_s':0, 'test_put_a':0, 'test_get_locals':0, 'test_set_params':0, 
         'test_work':0, 'test_F_ma':0, 'test_p_mv':0, 'test_p_pi':0, 'test_dx_v':0, 'test_dt_v':0,
         'test_v_dxDt':0, 'test_v_a_dt':0, 'test_s_dR':0, 'test_s_geo':0, 'test_s_radius':0,
         'test_a_mF':0, 'test_geometry':0, 'test_dt_p':0, 'test_eval_exec':0,
         'test_kg_to_Em':0, 'test_Em_to_kg':0, 'test_to_pct_cc':0, 'test_pct_cc_to_Em':0, 
         'test_set_geom':0, 'test_set_v':0, 'test_set_p':0, 'test_set_F':0, 'test_set_r':0, 'test_set_D':0,
         'test_set_R':0, 'test_set_dx':0, 'test_set_dt':0, 'test_set_Em':0, 'test_apply_v_impacts':0,
         'test_build_symp_eqs':0, 'test_solve_eq':0, 'test_solve_eq_str':0, 
         'test_check_consistency':0, 'test_set_option':0, 'test_get_option':0, 'test_sub_in_vals':0,
         'test_log_param_lib':0, 'test_make_param_lib':0, 'test_load_param_lib':0, 
         'test_compute_all_E':0, 'test_compute_all_m':0, 'test_set_scaling':0, 'test_solve_symp_eq':0, 'test_parse_dict':0,
         'test_is_in_rec':0, 'test_get_first_in_rec':0, 'test_set_first_in_rec':0, 
         'test_get_first_rec_named':0, 'test_get_first_field_named':0,
         'test_update_eq_lib':0, 'test_build_decompressed':0, 'test_decompose_powers':0, 'test_update_eq_lib_symb':0,
         'test_primary_compliment':0, 'test_colorWheel_opposite':0, 'test_obj_is_valid':0, 'test_get_obj_list':0, 
         'test_superposition':0, 'test_normalize':0
         } 

# Note: these string values are processed in GEMSTone.html for color-coding; changes must propagate..
eq_states = {"needs_data":"Needs Data", "cond_false":"Invalid Conditions",
             "needs_validation":"Needs Validation", "valid":"Valid", "invalid":"Invalid", "stale":"Stale"}

ans_sources = {"gui":"GUI", "input_data":"Input Data", "eq_lib":"Equation Library", "computed":"Eq(tbd, tbd)"}

color_spec = {
  "hue": 210,
  "saturation": 0.85,
  "brightness": 0.65,
  "RGB_hex": "0xRRGGBB"
}
red_mask = 0xFF0000
green_mask = 0x00FF00
blue_mask = 0x0000FF

black = color_spec.copy()
black['RGB_hex'] = "0x000000"

red = color_spec.copy()
red['RGB_hex'] = "0xFF0000"

green = color_spec.copy()
green['RGB_hex'] = "0x00FF00"

blue = color_spec.copy()
blue['RGB_hex'] = "0x0000FF"

yellow = color_spec.copy()
yellow['RGB_hex'] = "0xFFFF00"

cyan = color_spec.copy()
cyan['RGB_hex'] = "0x00FFFF"

magenta = color_spec.copy()
magenta['RGB_hex'] = "0xFF00FF"

white = color_spec.copy()
white['RGB_hex'] = "0xFFFFFF"

# Blue color opposite
orange = color_spec.copy()
orange['RGB_hex'] = "0xFF7F00"

