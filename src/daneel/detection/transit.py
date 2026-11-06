import importlib
import matplotlib.pyplot as plt
import numpy as np
import setuptools  # noqa: F401

batman = importlib.import_module("batman")

class TransitModel:
    """
    Transit light curve computed with batman for multiple planets, 
    for one or more limb darkening models.
    """

    def __init__(self, params_dict):
        
        self.planets = params_dict.get("planets", {})

        if "limb_darkening" in params_dict:
            self.limb_darkening = params_dict["limb_darkening"]
        else:
            self.limb_darkening = {
                params_dict.get("limb_dark", "quadratic"): params_dict.get("u", [0.1, 0.3])
            }

        # Time array, days from mid transit
        self.t = np.linspace(
            params_dict.get("t_min", -0.1),
            params_dict.get("t_max", 0.1),
            params_dict.get("n_points", 1000),
        )

    def compute_light_curve(self):
        """
        Compute the light curve for each planet and each limb darkening model.
        """
        self.flux = {}
        
        for planet_name, p_params in self.planets.items():
            self.flux[planet_name] = {}
            
            params = batman.TransitParams()
            params.t0 = p_params.get("t0", 0.0)
            params.per = p_params["per"]
            params.rp = p_params["rp"]
            params.a = p_params["a"]
            params.inc = p_params["inc"]
            params.ecc = p_params.get("ecc", 0.0)
            params.w = p_params.get("w", 90.0)

            # limb darkening models
            for model, coefficients in self.limb_darkening.items():
                params.limb_dark = model
                params.u = coefficients
                m = batman.TransitModel(params, self.t)
                self.flux[planet_name][model] = m.light_curve(params)
                
        return self.flux

    def plot_light_curve(self, output_file="lc.png", show=False):
        """Plot and save the transit light curves for all planets."""
        if not hasattr(self, "flux"):
            self.compute_light_curve()

        fig, ax = plt.subplots(figsize=(10, 6))
        
        for planetk, models in self.flux.items():
            planet_name = self.planets[planetk].get("planet_name", planetk)
            
            for model, flux in models.items():
                label = f"{planet_name} ({model})" if len(self.limb_darkening) > 1 else planet_name
                ax.plot(self.t, flux, label=label)

        ax.set(
            xlabel="Time [days]",
            ylabel="Relative flux",
            title="Transit Light Curves for multiple planets",
        )
        ax.legend(title="Planet + LD Model")
        fig.tight_layout()
        fig.savefig(output_file, dpi=150)
        
        if show:
            plt.show()
        plt.close(fig)
        print(f"Light curves saved to {output_file}")

    def run(self, output_file="lc.png"):
        
        self.compute_light_curve()
        self.plot_light_curve(output_file)