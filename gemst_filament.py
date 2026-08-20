# filament_cradian.py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---------------------------
# Parameters (tweak these)
# ---------------------------
r0    = 0.1        # base radius offset
k     = 0.02       # radial growth coefficient (r(x) = r0 + k*x^2)
A0    = 1.0        # amplitude scale
alpha = 0.5        # mapping from theta -> x, x = alpha * theta
f0    = 1.0        # reference frequency/density
p     = 1.0        # packing exponent (f(x) = f0 * (r_ref / r(x))^p)
r_ref = 1.0        # reference radius for density scaling
gamma = 1.0        # geometry constant for local energy density
eta   = 0.02       # damping rate per time step
eps_min = 1e-6     # minimum permitted local energy density (floor)
c_cradian = np.pi/2  # cradian speed mapping (if used)

# Numerical settings
theta_max = 200.0          # maximum theta to sample
n_points = 8000            # number of discrete filament points
dt = 0.1                   # simulation time-step
n_steps = 200              # number of dissipation steps to run

# ---------------------------
# Derived arrays (initial)
# ---------------------------
thetas = np.linspace(0.1, theta_max, n_points)   # avoid x=0 singularity
xs = alpha * thetas                               # longitudinal coordinate
rs = r0 + k * xs**2                               # radial packing curve

# Parametric helix (cylindrical mapping)
X = rs * np.cos(thetas)
Y = rs * np.sin(thetas)
Z = xs

# Amplitude and frequency/density model
Amp = A0 / (xs**2)                                 # 1/x^2 amplitude decay
Amp[np.isnan(Amp)] = A0/(0.1**2)                   # guard small-x
Amp[np.isinf(Amp)] = A0/(0.1**2)
freq = f0 * (r_ref / rs)**p                        # packing -> frequency/density

# Local energy density per unit length (phenomenological)
eps = gamma * Amp * freq
eps = np.maximum(eps, eps_min)

# Precompute angular speed upper bound for tip-speed ~ c (cradian or SI)
# omega(θ) = c / r(θ)  but enforce a soft cap in visualization (not evolving here)
omega_cap = c_cradian / np.maximum(rs, 1e-8)

# ---------------------------
# Dissipation loop
# ---------------------------
# Simple exponential-like dissipation with neighborhood coupling (diffusive smoothing)
for step in range(n_steps):
    # local dissipation
    deps = -eta * eps * dt
    eps += deps

    # simple coupling (nearest-neighbor diffusion) to model tension relaxation
    # (discrete Laplacian smoothing)
    eps_pad = np.pad(eps, (1,1), mode='edge')
    lap = eps_pad[2:] - 2*eps_pad[1:-1] + eps_pad[:-2]
    eps += 0.1 * lap * dt

    # enforce floor
    eps = np.maximum(eps, eps_min)

# recompute amplitude and frequency proxies after dissipation if desired
# here we keep Amp proportional to eps for visualization
Amp_vis = np.clip(eps / (gamma * freq + 1e-12), 1e-8, None)

# ---------------------------
# Visualization: 3D filament colored by amplitude
# ---------------------------
fig = plt.figure(figsize=(12,5))

ax1 = fig.add_subplot(1,2,1, projection='3d')
# color by log amplitude for dynamic range
col = np.log(Amp_vis + 1e-12)
p = ax1.scatter(X, Y, Z, c=col, cmap='viridis', s=1, linewidth=0)
ax1.set_title('Parametric Filament (color ~ log amplitude)')
ax1.set_xlabel('X'); ax1.set_ylabel('Y'); ax1.set_zlabel('Z')
ax1.view_init(elev=25, azim=120)
fig.colorbar(p, ax=ax1, shrink=0.6, label='log(Amp)')

# ---------------------------
# Visualization: energy density vs x
# ---------------------------
ax2 = fig.add_subplot(1,2,2)
ax2.plot(xs, eps, lw=1)
ax2.set_xscale('linear')
ax2.set_yscale('log')
ax2.set_xlabel('x (longitudinal coordinate)')
ax2.set_ylabel('local energy density ε(x) [log scale]')
ax2.set_title('Energy density along filament')
ax2.grid(True, which='both', ls=':', alpha=0.6)

plt.tight_layout()
plt.show()

# ---------------------------
# Export arrays for engine integration
# ---------------------------
# You can return or save (X,Y,Z,Amp_vis,eps,rs,xs) for rendering in your GUI/server.
# Example:
# np.savez('filament_data.npz', X=X, Y=Y, Z=Z, Amp=Amp_vis, eps=eps, r=rs, x=xs)
