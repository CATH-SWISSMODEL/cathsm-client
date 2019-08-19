
# CATH-SM Client

This repository contains scripts and libraries to simplify interaction with the CATH / SWISS-MODEL (CATH-SM) protein modelling pipeline.

The interacts with the [public API](https://api01.cathdb.info/swagger) of a running version of [`cathsm-server`](https://github.com/CATH-SWISSMODEL/cathsm-server).

## Setup

Create your own virtual environment (optional, but recommended):

```bash
python3 -m venv venv
. venv/bin/activate
```

Install the requirements:

```bash
pip install .
```

## Usage

The following examples assume that you moved to the root directory of this repository and activated the virtual environment (see above).

```bash
cd /path/to/cathsm-client
. venv/bin/activate
```

General usage:

```bash
$ ./scripts/cathsm-api
usage: cathsm-api [-h] --in INFILE --outdir OUTDIR --api1_user API1_USER
                  [--api2_user API2_USER] [--max_workers MAX_WORKERS]
                  [--api1_base API1_BASE] [--api2_base API2_BASE]
                  [--startseq STARTSEQ] [--delete-invalid-token]
cathsm-api: error: the following arguments are required: --in/-i, --outdir/-o, --api1_user/-u
```

## Examples

#### Run a query sequence through the full 3D modelling pipeline

```bash
./scripts/cathsm-api \
  --in example_data/test.fasta \
  --outdir results/ \
  --api1_user <your_api_username>
```

## Advanced Usage

#### Testing against a development version of the backend servers

If you are testing a development version of [`cathsm-server`](https://github.com/CATH-SWISSMODEL/cathsm-server),
override the `--api1_base` parameter to point to the base URL of your server instance, eg

```bash
./scripts/cathsm-api \
  --in example_data/test.fasta \
  --outdir results/ \
  --api1_user <your_api_username> \
  --api_base=http://localhost:3000
```

#### API2: Build a 3D model from template alignment data with the SWISS-MODEL API

```bash
./scripts/api2.py --in example_data/A0PJE2__35-316.json --out tmp.pdb
```

input (ie `example_data/A0PJE2__35-316.json`):

```json
{
    "auth_asym_id": "A",
    "pdb_id": "3rd5",
    "target_sequence": "---------E--VQIPGRVFLVTGGNSGI...",
    "template_seqres_offset": 0,
    "template_sequence": "GSMTGWTAADLP-SFAQRTVVITGANSGL..."
}
```

### Development

The repo has the following layout:

* `scripts/` -- command line scripts
* `cathsm/` -- python libraries
* `example_data/` -- example data
* `tests/` -- tests
