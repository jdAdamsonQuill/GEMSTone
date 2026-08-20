import math
from math import pi

import re

import gemst_globals
from gemst_globals import *

import gemst_logging
from gemst_logging import log

import gemst_utilities
from gemst_utilities import get_timestamp

import gemst_eq_engine

def main():

    gemst_logging.logging_init()

    log(f"main(): Starting gemst_eq_engine.run_tests() at date/time:{get_timestamp()}")
    gemst_eq_engine.run_tests()

if __name__ == "__main__":
    log(f"Starting main() for the Cradian System")
    main()

