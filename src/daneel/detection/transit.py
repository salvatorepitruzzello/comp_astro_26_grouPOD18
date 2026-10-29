import batman
import numpy as np
import matplotlib.pyplot as plt

params = batman.TransitParams()       # object to store transit parameters
params.t0 = 0.                        # time of inferior conjunction
params.per = 32.940045                # orbital period
params.rp = 0.05375                   # planet radius (in units of stellar radii)
params.a = 83.33                      # semi-major axis (in units of stellar radii)
params.inc = 89.5785                  # orbital inclination (in degrees)
params.ecc = 0.20                     # eccentricity
params.w = - 5.70                     # longitude of periastron (in degrees)
params.limb_dark = "nonlinear"        # limb darkening model
params.u = [0.5, 0.1, 0.1, -0.1]      # limb darkening coefficients [u1, u2, u3, u4]

t = np.linspace(-0.1, 0.1, 1000)      # times at which to calculate light curve
m = batman.TransitModel(params, t)    # initializes model
flux = m.light_curve(params)          # calculates light curve

radii = np.linspace(0.09, 0.11, 20)
for r in radii:
        params.rp = r                 # updates planet radius
        new_flux = m.light_curve(params) # recalculates light curve

params.rp = 0.05375 

ld_options = ["uniform", "linear", "quadratic", "nonlinear"]
ld_coefficients = [[], [0.3], [0.1, 0.3], [0.5, 0.1, 0.1, -0.1]]

plt.figure()

for i in range(4):
        params.limb_dark = ld_options[i]          # specifies the LD profile
        params.u = ld_coefficients[i]             # updates LD coefficients
        m = batman.TransitModel(params, t)        # initializes the model
        flux = m.light_curve(params)              # calculates light curve
        plt.plot(t, flux, label = ld_options[i])

plt.legend()
plt.xlabel("Time [days]")
plt.ylabel("Relative flux")
plt.title("Transit Light Curve K2-18b")
plt.savefig("K2-18b_assignment1_taskF.png")