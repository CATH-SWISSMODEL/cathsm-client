#!/usr/bin/env python3
"""Test API1 (CATH select template)"""

# core
import logging
import json
import os
import tempfile
import time
import unittest

# import
import requests

# local
from cathsm.apiclient import clients, managers, config

LOG = logging.getLogger(__name__)

DELETE_TEMP_FILES = False

EXAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'example_data')

class CathSelectTemplateClientTest(unittest.TestCase):

    def setUp(self):
        self.base_url = config.DEFAULT_API1_BASE

    def test_defaults(self):
        client = clients.CathSelectTemplateClient()

        self.assertIsInstance(client, clients.CathSelectTemplateClient)

        self.assertEqual(client.base_url, 'https://api01.cathdb.info')

        self.assertEqual(
            client.get_url('submit'),
            client.base_url + '/api/select-template/')

        self.assertEqual(
            client.get_url('status', {"task_id": "foo"}),
            client.base_url + '/api/select-template/foo/')

        self.assertEqual(
            client.get_url('results', {"task_id": "foo"}),
            client.base_url + '/api/select-template/foo/results')


class CathSelectTemplateManagerTest(unittest.TestCase):

    def setUp(self):
        self.base_url = config.DEFAULT_API1_BASE
        self.auth_data = {
            "username": config.API1_TEST_USER,
            "password": config.API1_TEST_PASSWORD,
        }
        self.infile = os.path.join(
            EXAMPLE_DATA_PATH, 'select-template-01.json')

        with open(self.infile, 'r') as io:
            data = io.read()
            self.submit_data_01 = json.loads(data)

    def test_requests_client(self):
        """Confirm that the API endpoints can be accessed manually.."""

        # auth
        res = requests.post(
            self.base_url + '/api/api-token-auth/',
            data=self.auth_data,
        )
        res.raise_for_status()

        # get auth token
        token_id = res.json()['token']
        self.assertTrue(token_id)
        headers = {'Authorization': 'Token ' + token_id}

        # submit task
        res = requests.post(self.base_url + '/api/select-template/',
                            data=self.submit_data_01, headers=headers)
        LOG.info("submit_data: %s", self.submit_data_01)
        LOG.info("headers: %s", headers)
        res.raise_for_status()
        task_id = res.json()['uuid']
        self.assertTrue(task_id)

        # check task
        status = 'unknown'
        res = None
        while status in ['unknown', 'queued', 'running']:
            time.sleep(2)
            res = requests.get(self.base_url + '/api/select-template/' + task_id + '/',
                               headers=headers)
            res.raise_for_status()
            status = res.json()['status']
        self.assertEqual(status, 'success')

        # results
        res = requests.get(self.base_url + '/api/select-template/' + task_id + '/results',
                           headers=headers)
        res.raise_for_status()
        results_data = json.loads(res.json()['results_json'])
        self.assertTrue(results_data['funfam_resolved_scan'])

    def test_manager(self):
        """Perform the API call via the Manager"""

        outfile1 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)

        # run with user auth
        client1 = managers.CathSelectTemplateManager(base_url=self.base_url,
                                                     infile=self.infile,
                                                     outfile=outfile1.name,
                                                     api_user=config.API1_TEST_USER,
                                                     api_password=config.API1_TEST_PASSWORD)

        client1.run()
        self.assertTrue(client1.funfam_resolved_scan(),
                        'retrieved funfam_resolved_scan (user auth)')

        api_token = client1.api_token
        LOG.debug("api_token: %s", api_token)

        # run with token auth
        outfile2 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client2 = managers.CathSelectTemplateManager(base_url=self.base_url,
                                                     infile=self.infile, outfile=outfile2.name,
                                                     api_token=api_token)
        client2.run()
        self.assertTrue(client2.funfam_resolved_scan(),
                        'retrieved funfam_resolved_scan (token auth)')

        # run with token auth (automatically retrieved from config)
        outfile3 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client3 = managers.CathSelectTemplateManager(base_url=self.base_url,
                                                     api_user=config.API1_TEST_USER,
                                                     infile=self.infile, outfile=outfile3.name,)
        client3.run()
        self.assertTrue(client3.funfam_resolved_scan(),
                        'retrieved funfam_resolved_scan (token auth from config)')
