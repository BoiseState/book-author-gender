# Book Rec Bias repository

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
-   A config file `data_conf.ini` with a section `postgresql` containing PsycoPG2
    configuration parameters.

If you are inside Boise State and want to share our DVC resources, you also need to
set up DVC to connect to our data server.  There are two steps here:

-   Set up the `piret-minio` AWS credentials in `~/.aws/credentials`.  This file needs
    a section that looks like:

        [piret-minio]
        aws_access_key_id = <access>
        aws_secret_access_key = <secret>

-   Tell DVC to use it:

        dvc remote modify --local minio profile piret-minio

## Directory Layout

We try to keep this repository clean and well-organized.

- `bookgender` is a Python package that contains our support code.
- `data` contains the data and traind recommendation models.
- `steps` contains high-level DVC step files to ask for different
  parts of the analysis.
- `scripts` contains scripts to run.  Run these with `python -m scripts.name`
  to set up `$PYTHONPATH` correctly.
- Primary notebooks live in the top-level directory.
- Exploratory notebooks live in `explore`.

## Getting Data

To download all pre-built models and data from within Boise State, run:

    dvc pull

## Running Everything

To reproduce the entire experiment, run:

    dvc unlock data/*/tuning/*-search.dvc data/version-stamp.dvc
    dvc repro

This will probably take at least a week on a substantial computer (28 cores, 512GB RAM).  Individual
steps may require fine-tuning of LensKit parallelism parameters depending on your specific hardware
configuration.
