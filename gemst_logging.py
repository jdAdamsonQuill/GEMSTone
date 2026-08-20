from datetime import datetime
import inspect

import json

import gemst_globals
from gemst_globals import options_lib
from gemst_globals import *

logging_vers = "20251009_1100"

open_levelfiles = []
log_filename = "GEMST_log"

def logging_init():
    global log_filename 
    filename = log_filename + ".txt"
    with open(filename, 'w') as gemst_logfile:
        print(f"gemst_logging.py: Starting version {logging_vers} at {datetime.now().strftime('%Y%m%d_%H_%M_%S')}")
        print(f"gemst_logging.py: Starting version {logging_vers} at {datetime.now().strftime('%Y%m%d_%H_%M_%S')}", file=gemst_logfile)

##### Log all annunciated information together
# The higher the debug number, the more debug you get; so the less you want to see it, make its required level higher
def log(msg, routine="", dbg=1, level="Log", indent=0, count=None, print_version=False, print_too=True, for_summary=False):
    global dbg_keys, logging_vers, log_filename, options_lib
    count_str = ""
    indent = "   " * indent

    if dbg in dbg_keys:
        dbg_level = dbg_keys[dbg]
    else:
        try:
            dbg_level = int(dbg)
        except:
            dbg_level = -1

    dbg_option = options_lib['dbg']
    if dbg_option in dbg_keys:
        options_dbg_level = dbg_option
    else:
        try:
            options_dbg_level = int(dbg_option)
        except:
            options_dbg_level = -2

    # dbg_leve=0 turns off; dbg_level=1 turns on; dbg_level>1 turns down.. Use options_lib['dbg'] to control
    if dbg_level != 0 and dbg_level <= options_dbg_level or dbg in dbg_keys and dbg_keys[dbg]:
        if count is not None:
            count_str = str(count) + ':'
        else:
            count = ""

        if routine is not None:
            routine += '():'
        else:
            routine = ""

        if level is not None:
            level_str = level+':'
        else:
            level = ""

        if print_version:
            version_str = 'v'+logging_vers+':'
        else:
            version_str = ""

        msg = f"{level_str}{routine}{version_str}{count_str}{indent}{msg}"
        text_filename = log_filename + ".txt"
        with open(text_filename, 'a') as gemst_logfile:
            print(msg, file=gemst_logfile)
        if print_too:
            print(msg)

        # Copy messages with given levels into individual log files
        if for_summary:
            summary_filename = log_filename+"_Summary.txt"
            if summary_filename not in open_levelfiles:
                with open(summary_filename, 'w') as gemst_summary_file:
                    open_levelfiles.append(summary_filename)
                    print(msg, file=gemst_summary_file)
            else:
                with open(summary_filename, 'a') as gemst_summary_file:
                    print(msg, file=gemst_summary_file)

        if level != "Log":
            filename = log_filename + "_"+level + ".txt"
            if filename not in open_levelfiles:
                with open(filename, 'w') as gemst_levelfile:
                    open_levelfiles.append(filename)
                    print(msg, file=gemst_levelfile)
            else:
                with open(filename, 'a') as gemst_levelfile:
                    print(msg, file=gemst_levelfile)


def log_val( text, val, routine="log_val", level="Info", print_too=True, dbg=1 ):
    log(f"{text} = {val}", routine=routine, level=level, dbg=dbg)

def log_var(var_name, routine="log_var", level="Info", print_too=True, dbg=1 ):
    frame = inspect.currentframe().f_back
    local_vars = frame.f_locals

    if var_name in local_vars:
        log(f"{var_name} = {local_vars[var_name]}", routine="log_var", level="Info", print_too=True, dbg=1 )
    else:
        log(f"Undefined variable: {var_name}", routine="log_var", level="Info", print_too=True, dbg=1)

#####
if tests['test_log']:
    log(f"Test with indent=3; expect message indented 9 spaces", level="Test", indent=3)

    log(f"Testing logging this message and parts without count", 
        dbg=2, level="Test", print_too=1, routine='test_log')
    log(f"Testing logging this message and parts with count=3", 
        count=3, dbg=3, level="Test", print_too=1, routine='test_log')
    log(f"Test Not logging this message with too low a base dbg level", 
        dbg=10, level="Test", print_too=1, routine='test_log')
    orig_dbg_v = dbg_keys['v']
    dbg_keys['v'] = 1
    log(f"Test logging with a dbg_key of 'v' including the 'logging_vers' and a summary entry",
        dbg='v', level="Test", print_too=True, print_version=True, routine='test_log', for_summary=True)
    dbg_keys['v'] = orig_dbg_v
    orig_dbg_dx = dbg_keys['dx']
    dbg_keys['dx'] = 0
    log(f"Test Not logging with a dbg_key of 'dx' 0 in the dbg_keys dict",
        dbg='dx', level="Test", print_too=1, routine='test_log')
    dbg_keys['dx'] = orig_dbg_dx
    log(f"You should Not see 'Not logging' in successful Test log output..", 
        print_version=True, level="Tests", routine="test_log")

    x = 2.1
    log(f"Testing log_val with 'x' and 2.1", 
        print_version=True, level="Tests", routine="test_log")
    log_val('x', x)

    if tests['test_log'] == -1:
        log(f"test_log is Done. Exiting now by request (-1).")
        exit()

def log_param_lib(params):
    global param_lib
    log(f"Starting; params:'{params}'", 'log_param_lib')
    
    param_lib = json.loads(params)
    metadata = {}
    for name, metadata in param_lib.items():
        log(f"{name}: {metadata}", 'log_param_lib', level='Info')

if tests['test_log_param_lib']:
    log_param_lib()

    if tests['test_log_param_lib'] == -1:
        log("Exiting Test on request (value=-1)", 'test_log_param_lib', 'Tests')
        exit()

