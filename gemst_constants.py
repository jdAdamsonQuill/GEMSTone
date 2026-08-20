import math
from math import pi, e

c               = pi/2.0            # v is angle as fraction of light_speed; max slope is pi/2 Radians
cc              = c*c               # pi**2/4 ~9/4 ~2.4674
c_mks           = 299792458.0       # Speed of light, c, in meters per second
c_mks_inverse   = (1.0/299792458.0) # Inverse Speed of light, c, in sec/meter
cc_mks          = c_mks**2          # c-squared in meters per second
cc_mks_inverse  = 1.0/cc_mks          # c-squared in meters per second

Em_fact         = cc/cc_mks         # 1 kg*Em_Fact = 1Em; E/m = c^2. in cradians c=pi/2, in mks, c=277972458. 1J/1kg=c_mks^2; 1Em/1Em=pi^2/4 
kg_fact         = cc_mks/cc         # 1 Em * kg_fact = c^2 (kg) [1 Joule = 1 kg * c^2 (meters/sec) -> 1 (kg) = c^2/1 (m/J*s) = c^2
joule_fact      = cc_mks/cc         # 1 Em * joule_fact = c^2 (Joules) [1 Joule = 1 kg * c^2 (mks) -> 1 (J) = c^2 (m*kg/s)]

piPi            = pi**2             # pi squared
piOver2         = pi/2.0            # pi/2
hapi            = pi/2.0            # Half pi (aka 'hapi')
piUnder2        = 2.0/pi            # 2/pi

kg_to_lb_fact   = 0.45392           # Convert kilograms (kg) to pounds (lb)

# Looks like 10**-9 becomes 1e-9 which sympify isn't recognizing..
pico            = 10**9            # Scale 3*10^8 meters/sec to 1 meter=0.3 picoFrac for dx, and 1 sec=0.3 picoFrac for dt (c=dx/dt=1->dx=dt)
quad            = 10**15           # since 1 Joule and 1 kg = c^2 Em, scale c_mks^2 = ~9*10^16 meters/sec^2 to 90 quadEm = 1 kg = 1 Joule
quint           = 10**18           # Scale c_mks^2 to 0.09 quintEm, so 1 kg = 1 Joule = 0.09 quintEm
pico_fact       = 1.0e-09
quad_fact       = 1.0e-15
quint_fact      = 1.0e-18

planck_h        = 6.62607015e-34    # Planck constant. E = planck_h*Frequency

km_to_xfrac_fact = c_mks_inverse
sec_to_tfrac_fact = c_mks_inverse

bool_to_int     = {"False":0, "True":1}

FAIL            = -1                # Fatal problem
ERR             = 0                 # Detected error
OK              = 1                 # Nominal and fine

tbd             = "tbd"
#user_defined    = "GUI"
na              = "n/a"

# Master library
doi             = "DomainOfInteraction"

# Default path and filenames
#obj_path        = '/mnt/d/Users/jd/Projects/GEMSTone'
obj_path        = '/home/jd/jd/Projects/GEMSTone/json'
obj_filenames   = "[!_]*.json"      # Object filenames don't start with underscore by convention

# The physical constants used by the equation library objects
constants = { "pi":pi, "piPi":piPi, "hapi":hapi, "piOver2":piOver2, "piUnder2":piUnder2,
             "c":c, "cc":cc, "c_mks":c_mks, "cc_mks":cc_mks, "planck_h":planck_h,
             "kg_to_lb_fact":kg_to_lb_fact, "Em_fact":cc_mks, "kg_to_Em_fact":cc_mks, "Em_to_kg_fact":cc_mks_inverse,
             "pico_fact":pico_fact, "quad_fact":quad_fact, "quint_fact":quint_fact, "kg_to_lb_fact":kg_to_lb_fact,
             "km_to_xfrac_fact":km_to_xfrac_fact, "sec_to_xfrac_fact":c_mks_inverse, "Em_fact":Em_fact, "kg_fact":kg_fact }

