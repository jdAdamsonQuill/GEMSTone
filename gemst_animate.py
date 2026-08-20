import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import gemst_globals
from gemst_globals import *

import gemst_logging
from gemst_logging import log, log_val, log_var

import gemst_utilities
from gemst_utilities import is_equiv, is_newer, to_float, eval_exec, params_to_mks, get_timestamp
from gemst_utilities import load_eq_lib, save_eq_lib, reset_eq_lib, get_obj_list, obj_is_valid

#import gemst_eq_engine
#from gemst_eq_engine import Normalize, Superposition

# # 1. Prepare your data
# x = np.array([0, 1, 2, 3, 4, 5])
# y = np.array([0, 2, 4, 6, 8, 10])
# 
# # 2. Create the plot
# plt.plot(x, y)
# 
# # 3. Add labels and a title (optional but recommended for clarity)
# plt.xlabel("X-axis Label")
# plt.ylabel("Y-axis Label")
# plt.title("Simple Line Plot")

# 4. Display the plot
#plt.show()

def omega_nu_ani_frames():
    hapi = np.pi/2
    radius_offset = math.sqrt(0.5)  # ~0.707; unit circle hypotenuse from (0,sqrt(.5))
    x_uc = 1+radius_offset

    # Unit circle center is offset form origin
    max_x = hapi+radius_offset

    # make 10% bigger for circle completion (worked; without just short)
    max_x *= 1.1

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.set_xlim(0, max_x)

    # Unit circle center is on X-axis with y=0, so no vertical offset - but keep plot symmetrical for circles
    ax.set_ylim(0, max_x)

    ax.set_title("Omega<>Velocity, Nu<>V_Fraction")
    #ax.axhline(0, color='gray', linestyle='--', lw=1) # The center line

    # Arcs are a function of x, within each frame
    line1, = ax.plot([], [], lw=2, color='gray', label='Unit Circle')

    # Vectors are a function of angle as arctan related to frame
    line2, = ax.plot([], [], lw=2, color='black', label='Hypotenuse/Radius=1')
    line3, = ax.plot([], [], lw=2, color='magenta', label='Omega<>v')
    line4, = ax.plot([], [], lw=2, color='cyan', label='Nu<>vfr')
    line5, = ax.plot([], [], lw=2, color='red', label='Time Dilation')
    line6, = ax.plot([], [], lw=2, color='blue', label='Length Contraction')

    ax.legend()

    # Each frame is 1% of max-v=c=pi/2
    num_frames = math.ceil(100)
    frame_frac = 1.0/float(num_frames)

    x = np.linspace(0, max_x, 1000)

    log(f"num_frames={num_frames}, frame_frac={frame_frac}, max_x={max_x}", 'omega_nu_ani_frames')

    # x's increase over their range within each frame, whose collection is the animation
    def animate(frame):
        cur_frame = frame
        # 0<=frac_ani<=1, 0 <= omega <= pi/2
        # arctan(1)=pi/4
        # arcsin(1)=pi/2

        # Increasing frames, where each frame is a state in an accelerating system
        frac_ani = float(frame)/float(num_frames)

        nu    = np.arctan(frac_ani)     # so tan(nu)=frame/num_frames as v/c
        omega = frac_ani*hapi           # so tan(omega)=frame as v in cradians, where v=pi/2 is v=c at end of animation

        #log(f"frame={frame}, x[frame]={x[frame]}, nu={nu}, np.arctan(x)={np.arctan(x)}", 'animate')

        # x = cos(np.arctan(x)), np.arctan(x)=cos^-1(x), y = sin(np.arctan(x))
        # x as angle, 0=>pi/2 by frame_frac steps as percent of the whole animation
        #orig y1 = np.sin(x)
        #orig y2 = np.sin((x)/(max_x))

        # Arc is the same each frame; not dependent on frame, just x, f(x)
        # Points don't need length multipliers
        line1.set_data(np.cos(x)+radius_offset, np.sin(x))

        # Vectors
        #line3.set_data(x, x*np.tan(omega))
        #line4.set_data(x, x*np.tan(nu))
        line3.set_data(x, x*np.tan(omega) )
        line4.set_data(x, x*np.tan(nu) )

        # LTF Projections
        def f(x):
            return (max_x+np.sin(nu))/x
            
# LEFT OFF HERE
        x1 = x_uc + np.sin(x/max_x)
        line5.set_data( x1, np.tan(nu) )

        # 0->circ = tan(nu)
        # Hypotenuse len=1 -> x=sqrt(.5)=y
        # a**2+b**2=c**2=tan(np.arctan(x))**2
        #line2.set_data(x/max_x, (x/max_x)*np.cos(nu)/np.sin(nu))

        #y3 = x*np.tan(np.arctan(x))
        #y4 = x*np.tan(nu)

        # x^2 + y^2 = tan()^2 -> x = sqrt(tan()^2 - y^2)
        # y3^2 = (x*tan(np.arctan(x)))^2 ; tan(np.arctan(x))^2 - x^2*tan(np.arctan(x))^2 ; tan(np.arctan(x))^2*(1-x^2)  
        # y4^2 = (x*tan(nu))^2 ; tan(nu)^2*(1-x^2)

        # Time Dilation
        #orig line5.set_data(radius_offset+x, np.sin(nu) )

        # Length Contraction
        #orig line6.set_data(radius_offset*np.cos(nu), np.sin(x)*np.sin(nu) )

        return line1, line2, line3, line4, line5, line6

    ani = animation.FuncAnimation(fig, animate, frames=num_frames, interval=50, blit=True)

    # Save the animation as a GIF
    ani.save('omega_nu.gif', writer='pillow')

    plt.close(fig)

# Function to generate frames
def create_animation_frames():
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_xlim(0, 2 * np.pi)
    ax.set_ylim(-1.5, 1.5)
    ax.set_title("Inverse Sine Waves Forming a Line")
    ax.axhline(0, color='gray', linestyle='--', lw=1) # The center line

    line1, = ax.plot([], [], lw=2, color='blue', label='Wave 1')
    line2, = ax.plot([], [], lw=2, color='red', label='Wave 2 (Inverse)')
    line3, = ax.plot([], [], lw=2, color='black', label='Net Interaction')
    ax.legend()

    x = np.linspace(0, 2 * np.pi, 1000)

    def animate(frame):
        # Shift the waves to simulate movement towards the center
        # Wave 1 moving right, Wave 2 moving left
        y1 = np.sin(x - frame * 0.1)
        y2 = np.sin((2 * np.pi - x) - frame * 0.1) * -1 # Inverse and moving left

        # The net interaction (superposition)
        y3 = y1 + y2

        line1.set_data(x, y1)
        line2.set_data(x, y2)
        line3.set_data(x, y3)
        return line1, line2, line3,

    ani = animation.FuncAnimation(fig, animate, frames=60, interval=50, blit=True)

    # Save the animation as a GIF
    ani.save('inverse_sine_waves.gif', writer='pillow')

    plt.close(fig)

# Run the function to generate the GIF file
#create_animation_frames()

omega_nu_ani_frames()

