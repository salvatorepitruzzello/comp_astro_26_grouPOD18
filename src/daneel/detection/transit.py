import importlib

import matplotlib.pyplot as plt
import numpy as np
import setuptools  # noqa: F401  # Provides distutils compatibility for batman.

batman = importlib.import_module("batman")


class TransitModel:
    """
    Transit light curve of a planet computed with batman, for one or more
    limb darkening models.

    The parameters are read from the "transit" section of the YAML file
    passed to daneel with -i.
    """

    def __init__(self, params_dict):
        """
        Parameters
        ----------
        params_dict : dict
            Transit parameters loaded from the YAML file
        """
        self.name = params_dict.get("planet_name", "planet")

        self.params = batman.TransitParams()
        self.params.t0 = params_dict.get("t0", 0.0)
        self.params.per = params_dict["per"]
        self.params.rp = params_dict["rp"]
        self.params.a = params_dict["a"]
        self.params.inc = params_dict["inc"]
        self.params.ecc = params_dict.get("ecc", 0.0)
        self.params.w = params_dict.get("w", 90.0)

        # Limb darkening: several models from "limb_darkening",
        # or a single model from "limb_dark" and "u"
        if "limb_darkening" in params_dict:
            self.limb_darkening = params_dict["limb_darkening"]
        else:
            self.limb_darkening = {
                params_dict.get("limb_dark", "quadratic"): params_dict.get("u", [0.1, 0.3])
            }

        # Time array for model evaluation [days from mid-transit]
        self.t = np.linspace(
            params_dict.get("t_min", -0.1),
            params_dict.get("t_max", 0.1),
            params_dict.get("n_points", 1000),
        )

    def compute_light_curve(self):
        """
        Compute the light curve for each limb darkening model.

        Returns
        -------
        flux : dict
            Relative flux array for each limb darkening model
        """
        self.flux = {}
        for model, coefficients in self.limb_darkening.items():
            self.params.limb_dark = model
            self.params.u = coefficients
            # batman requires a new model whenever the limb darkening law changes
            m = batman.TransitModel(self.params, self.t)
            self.flux[model] = m.light_curve(self.params)
        return self.flux

    def plot_light_curve(self, output_file="lc.png", show=False):
        """
        Plot and save the transit light curves.

        Parameters
        ----------
        output_file : str, optional
            Output filename for the plot (default: 'lc.png')
        show : bool, optional
            Also display the plot on screen (default: False)
        """
        if not hasattr(self, "flux"):
            self.compute_light_curve()

        fig, ax = plt.subplots(figsize=(10, 6))
        for model, flux in self.flux.items():
            ax.plot(self.t, flux, label=model)
        ax.set(
            xlabel="Time [days]",
            ylabel="Relative flux",
            title=f"{self.name} transit light curve",
        )
        ax.legend(title="Limb darkening")
        fig.tight_layout()
        fig.savefig(output_file, dpi=150)
        if show:
            plt.show()
        plt.close(fig)
        print(f"Light curve saved to {output_file}")

    def run(self, output_file="lc.png"):
        """Compute and plot the transit light curve."""
        self.compute_light_curve()
        self.plot_light_curve(output_file)
