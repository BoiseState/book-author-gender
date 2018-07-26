# Book Rec Bias repository

This archive contains the files to reproduce _Exploring Author Gender in Book Rating and Recommendation_, published in RecSys 2018.

## Requirements

* Java 8
* Conda with R, the Tidyverse, RSTAN, RPostgreSQL, xtable, and Jupyter Notebook
* Node.js
* Data sets (described in in `ol-processing-tools/data`)

For 64-bit Linux, we have provided a Conda environment file to install the analysis & import environment (R, Jupyter, Node.js).

    conda env create -f environment-linux-x64.yml

Data storage requires PostgreSQL 10 with the [orafce](https://github.com/orafce/orafce) extension.

This experiment also requires the following hardware:

-   300GB storage for the PostgreSQL database
-   40GB storage for data files, experiment results, etc.
-   A large compute server for running recommenders — we used a 2x12-core Xeon with 192GB RAM.
-   At least 16, preferably 32 or 64, GB of RAM for running analysis notebooks

Re-running everything, from data import to final results, will probably take a full week at least.

## Data Import

We use PostgreSQL to store and manage data and munge it for use in the experiment.  The ol-import-tools directory contains code and instructions for importing and integrating the data sets.

All of the scripts are set up to expect the data to live in the database `openlib`, and to read other connection parameters (host, user, password) from the standard PostgreSQL environment variables

## Exporting and Sampling Data

Run the export and sample tasks:

    ./gradlew sampleBXExplicit sampleBXImplicit sampleAmazonUsers
    ./gradlew prepSweepBX prepSweepAZ

The sweep prep prepares the train-test data for the accuracy evaluation. It's called `prepSweep` because we also used it for sweeping parameters (a separate run with a different sample).

## Running Recommenders

The base recommender tasks are:

- evaluateBXExplicit
- evaluateBXImplicit
- evaluateAZExplicit
- evaluateAZImplicit

These can take a while - each of the Amazon ones took between 6 and 8 hours on our Xeon server.

## Running Analysis

The analysis is contained in Jupyter notebooks using IRkernel.  Run the following notebooks:

- DatasetSummary.ipynb
- GenderCoverage.ipynb
- ProfileModels.ipynb
- RecListModels.ipynb