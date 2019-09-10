# core
import logging
import re
import os
import tempfile
import unittest

# local
from cathsm.apiclient.config import DEFAULT_API1_BASE, DEFAULT_API2_BASE
from cathsm.apiclient.tasks import CathSMSequenceFileTask

LOG = logging.getLogger(__name__)
DELETE_TEMP_FILES = False

class TasksTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'example_data')

    def test_simple_run(self):
        apiuser = 'apiuser'
        apipassword = 'apiuserpassword'
        infile = os.path.join(self.test_data_dir, 'test.fa')
        maxworkers = 1        
        outdir = tempfile.TemporaryDirectory(prefix='cathsm-client')

        expected_pdb_file = os.path.join(self.test_data_dir, 'test.pdb')

        LOG.info('CathSMSequenceFileTask: apiuser=%s, infile=%s, outdir=%s', 
                 apiuser, infile, outdir.name)

        task = CathSMSequenceFileTask(
            infile=infile,
            outdir=outdir.name,
            max_workers=maxworkers,
            api1_base=DEFAULT_API1_BASE,
            api2_base=DEFAULT_API2_BASE,
            api1_user=apiuser,
            api2_user=apiuser,
            api1_password=apipassword,
            api2_password=apipassword,
            startseq=1,
        )

        task.run()

        output_pdb_file = os.path.join(outdir.name, 'query', 'query.pdb')

        self.assertTrue(os.path.exists(output_pdb_file))
        with open(output_pdb_file, 'rt') as got_fh, open(expected_pdb_file, 'rt') as expected_fh:
            got = got_fh.read()
            expected = expected_fh.read()

        re_revdat = re.compile(r'^REVDAT.*?\n', flags=re.MULTILINE)

        def normalise_model_contents(model_contents):
            """Remove local timings from model PDB files"""
            return re_revdat.sub('', model_contents)

        got = normalise_model_contents(got)
        expected = normalise_model_contents(expected)

        self.assertEqual(got, expected)
    