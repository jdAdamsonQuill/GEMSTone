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
    max_x = pi/2 

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, max_x)
    ax.set_title("Omega<>Velocity, Nu<>V_Fraction")
    #ax.axhline(0, color='gray', linestyle='--', lw=1) # The center line

    # Arcs
    line1, = ax.plot([], [], lw=2, color='magenta', label='Omega<>v')
    line2, = ax.plot([], [], lw=2, color='cyan', label='Nu<>vfr')

    # Vectors
    line3, = ax.plot([], [], lw=2, color='magenta', label='Omega<>v')
    line4, = ax.plot([], [], lw=2, color='cyan', label='Nu<>vfr')

    ax.legend()

    x_last = np.pi/2
    x = np.linspace(0, x_last, 101)

    radius_scaling = math.sqrt(0.5)

    hapi = np.pi/2
    num_frames = 101
    ani_frac = 1.0/float(num_frames)
    log(f"num_frames={num_frames}, ani_frac={ani_frac}, max_x={max_x}", 'omega_nu_ani_frames')

    def animate(frame):
        # 0<=frac_frame<=1, 0 <= omega <= pi/2
        # arctan(1)=pi/4
        # arcsin(1)=pi/2
        #frac_frame = float(frame)/float(num_frames)
        nu = np.arctan(x[frame]/x_last)
        #omega = frac_frame*hapi
        omega = x[frame]
        #log(f"frame={frame}, x[frame]={x[frame]}, nu={nu}, omega={omega}", 'animate')

        # x = cos(omega), omega=cos^-1(x), y = sin(omega)

        # x as nu

        y1 = np.sin(x) * radius_scaling
        y2 = np.sin(x/x_last) * radius_scaling

        # Arcs
        line1.set_data(np.cos(x)*radius_scaling, y1)
        line2.set_data(np.cos(x/x_last)*radius_scaling, y2)

        # Vectors
        line3.set_data(x, x*np.tan(omega))
        line4.set_data(x, x*np.tan(nu))

        return line1, line2, line3, line4
        #return line1, line2

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

