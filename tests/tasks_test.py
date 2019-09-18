# core
import logging
import re
import os
import tempfile
import unittest
from shutil import copyfile

# local
from cathsm.apiclient import config
from cathsm.apiclient.tasks import CathSMSequenceFileTask

LOG = logging.getLogger(__name__)
DELETE_TEMP_FILES = False
BOOTSTRAP_TEST_FILES = os.environ.get('BOOTSTRAP_TEST_FILES', 0)

class TasksTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'example_data')

    def test_simple_run(self):
        infile = os.path.join(self.test_data_dir, 'test.fa')
        maxworkers = 1        
        outdir = tempfile.TemporaryDirectory(prefix='cathsm-client')

        expected_pdb_file = os.path.join(self.test_data_dir, 'test.pdb')

        LOG.info('CathSMSequenceFileTask: api1_user=%s, api2_user=%s, infile=%s, outdir=%s', 
                 config.API1_TEST_USER, config.API2_TEST_USER, infile, outdir.name)

        task = CathSMSequenceFileTask(
            infile=infile,
            outdir=outdir.name,
            max_workers=maxworkers,
            api1_base=config.DEFAULT_API1_BASE,
            api2_base=config.DEFAULT_API2_BASE,
            api1_user=config.API1_TEST_USER,
            api2_user=config.API2_TEST_USER,
            api1_password=config.API1_TEST_PASSWORD,
            api2_password=config.API2_TEST_PASSWORD,
            startseq=1,
        )

        task.run()

        output_pdb_file = os.path.join(outdir.name, 'query', 'query.pdb')

        if BOOTSTRAP_TEST_FILES:
            LOG.info("BOOTSTRAP_TEST_FILES=1, copying test data: %s -> %s", output_pdb_file, expected_pdb_file)
            copyfile(output_pdb_file, expected_pdb_file)

        self.assertTrue(os.path.exists(output_pdb_file))
        with open(output_pdb_file, 'rt') as got_fh, open(expected_pdb_file, 'rt') as expected_fh:
            got = got_fh.read()
            expected = expected_fh.read()

        re_revdat = re.compile(r'^(REVDAT|REMARK).*?\n', flags=re.MULTILINE)

        def normalise_model_contents(model_contents):
            """Remove local timings from model PDB files"""
            return re_revdat.sub('', model_contents)

        got = normalise_model_contents(got)
        expected = normalise_model_contents(expected)

        self.assertEqual(len(got.splitlines()), len(expected.splitlines()))
    