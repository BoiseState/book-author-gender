# Book Rec Bias repository

**Note:** this repository uses submodules.  Either clone with:

    git clone --recursive https://github.com/BoiseState/book-experiments.git

Or, after cloning, run:

    git submodule update --init --recursive
    
New changes you pull may change Git submodules, but they do not auto-update.  To refresh, re-run the update command above.

After pulling, you will need to update your Conda environment if the `environment.yml` file has changed.

## Requirements

* Anaconda
* The book data, as imported by the `bookdata` tools

The Conda environment file adds all required packages:

    conda env update -f environment.yml
    conda activate bookfair

This will also install `dvc`, which we use to script the experiment and store data.

## Configuration

The scripts need to know how to connect to the database.  There are two ways to set 
this up:

-   A `DB_URL` environment variable containing an SQLAlchemy-compatible PostgreSQL URL
-   A config file `db.cfg` containing database parameters.  This is the same configuration
    file as the one used by the [book data tools][bookdata].  This file is automatically
    excluded from Git checkouts.

[bookdata]: https://github.com/BoiseState/bookdata-tools

If you are inside Boise State and want to share our DVC resources, you also need to
set up DVC to connect to our data server.  Set up the `piret-minio` AWS credentials
in `~/.aws/credentials`.  This file needs a section that looks like:

    [piret-minio]
    aws_access_key_id = <access>
    aws_secret_access_key = <secret>


## Directory Layout and Code Practices

We try to keep this repository clean and well-organized.

- `bookgender` is a Python package that contains our support and configuration code.
- `data` contains the data and trained recommendation models.
- `steps` contains high-level DVC step files to ask for different
  parts of the analysis.
- `scripts` contains scripts to run.  Run these with `python -m scripts.name`
  to set up `$PYTHONPATH` correctly.
- `models` contains STAN models.
- Primary notebooks live in the top-level directory.
- Exploratory notebooks live in `explore`.
- The file `job.sh` runs commands through the `job.py` script, which sets up
  the environment to correctly run on the R2 cluster, and can notify Slack
  channels when jobs complete or fail.

The random seed is stored in `random.toml`, and accessed through `bookgender.config.rng_seed()`.
See scripts such as `split-ratings.py` to see how we manage random seeds for individual scripts.

We use `docopt` for parsing command-line arguments to scripts.  The `bookgender.util` package
contains `OptionReader` and `get_opt` utilities to make it easier to pass command-line options
around in a script.  See `split-ratings.py` for an example of using these helpers.

DVC steps should depend on the script and the input data.  Occasionally steps will depend on
other code files, but this is not common.

The `run-notebook.py` script re-runs a notebook; by default, it runs in-place.  The notebook
file should be a dependency of the DVC step, and the corresponding HTML file an output; the
notebook will be modified during the run, but that works with DVC just fine.

## Getting Data

To download all pre-built models and data from within Boise State, run:

    dvc pull

## Running Everything

To re-run the experiment, run;

    dvc repro

To reproduce the entire experiment, including export and hyperparamter tuning, run:

    dvc unlock data/*/tuning/*-search.dvc data/version-stamp.dvc
    dvc repro

This will probably take at least a week on a substantial computer (28 cores, 512GB RAM).  Individual
steps may require fine-tuning of LensKit parallelism parameters depending on your specific hardware
configuration.
