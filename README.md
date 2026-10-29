# Daneel — Computational Astrophysics 2026–27

A teaching package for modelling exoplanet transits and building detection
pipelines. The repository contains the course example code, a runnable CLI,
and Sphinx documentation.

Documentation: <https://tiziano1590.github.io/comp_astro_26/>.

## Installation

### Prerequisites

- Python >= 3.10

### Install from source

```bash
git clone https://github.com/tiziano1590/comp_astro_26.git
cd comp_astro_26
pip install .
```

### Development installation

```bash
pip install -e '.[dev,docs]'
```

## Usage

After installation, you can run daneel from the command line:

```bash
daneel -i <input_file> --transit [--output lightcurve.png]
```

### Command-line options

- `-i, --input`: Input parameter file (required)
- `-t, --transit`: Generate a transit light curve from the YAML input
- `-d, --detect`: Reserved for the course detection exercise
- `-a, --atmosphere`: Reserved for the course atmosphere exercise
- `-o, --output`: Output path for the transit plot (default: `lc.png`)

### Examples

```bash
# Run exoplanet detection
daneel -i examples/params.yaml --transit --output lightcurve.png

# Run atmospheric characterization
daneel -i examples/params.yaml --detect

# Run both detection and atmospheric analysis
daneel -i examples/params.yaml --atmosphere
```

### Transit light curve

The `-t` flag calls the `TransitModel` class defined in
`src/daneel/detection/transit.py`, which computes the transit light curve of a
planet with [batman](https://lkreidberg.github.io/batman/docs/html/index.html)
for each limb darkening model listed in the input file, and saves the plot:

```bash
daneel -i path_to_the_parameters.yaml -t
```

For example, with the parameters of K2-18 b provided in the repository:

```bash
daneel -i src/daneel/detection/parameters.yaml -t -o K2-18b_transit.png
```

If `-o` is omitted, the plot is saved as `lc.png`. An existing file with the
same name is overwritten.

### Running daneel outside the repository

Since `daneel` is installed as a package, it can be run from any directory.
Parameter files and outputs should be kept in a separate working directory,
outside the Git repository, so that runs do not modify the code base:

```bash
mkdir run_daneel
cd run_daneel
daneel -i path_to_the_parameters.yaml -t
```

Paths given to `-i` and `-o` are relative to the current directory, so the
output plot is saved in the working directory.

## Input File Format

The input file should be a YAML file containing the necessary parameters for the analysis.

For the transit light curve, the parameters are read from the `transit` section:

```yaml
transit:
  planet_name: K2-18b
  t0: 0.0            # time of inferior conjunction [days]
  per: 32.940045     # orbital period [days]
  rp: 0.05375        # planet radius [stellar radii]
  a: 83.33           # semi-major axis [stellar radii]
  inc: 89.5785       # orbital inclination [deg]
  ecc: 0.20          # eccentricity
  w: -5.70           # longitude of periastron [deg]
  limb_darkening:    # model: coefficients
    uniform: []
    linear: [0.3]
    quadratic: [0.1, 0.3]
    nonlinear: [0.5, 0.1, 0.1, -0.1]
  t_min: -0.1        # time window [days from mid-transit]
  t_max: 0.1
  n_points: 1000
```

- `per`, `rp`, `a` and `inc` are required.
- A light curve is computed for each model under `limb_darkening`; a single model can be given instead with `limb_dark` and `u`.
- `t0`, `ecc`, `w`, `t_min`, `t_max` and `n_points` are optional.

## Development

Run the test suite and style checks with:

```bash
pytest
ruff check .
```

Build the documentation with `make -C docs html`.

## License

This project is licensed under the GNU General Public License v3.0.

## Author

Tiziano Zingales (tiziano.zingales@unipd.it)
