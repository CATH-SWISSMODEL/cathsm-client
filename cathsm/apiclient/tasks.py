# core
import hashlib
import json
import logging
import os
import re
from multiprocessing import Pool

# non-core
import requests
import luigi
from Bio import SeqIO

# local
from cathsm.apiclient import managers, models, clients, errors

LOG = logging.getLogger(__name__)


def log_br(log=None):
    if not log:
        log = LOG
    log.info('')


def log_hr(log=None):
    if not log:
        log = LOG
    log.info('')
    log.info('-'*80)
    log.info('')


class CathSelectTemplateHitsTask(luigi.Task):
    """
    Runs a CathSelectTemplate job and caches 'hits' results as JSON file
    """

    seq_id = luigi.Parameter()
    seq_str = luigi.Parameter()
    api1_base = luigi.Parameter()
    api1_user = luigi.Parameter()
    api1_password = luigi.Parameter()
    work_dir = luigi.Parameter()

    @property
    def safe_seq_id(self, id_str):
        re_safe = re.compile(r'[\W]+', re.UNICODE)
        return re_safe.sub('', id_str)

    @property
    def outfile(self):
        return f'{self.work_dir}/select_template.{self.seq_id}.json'

    def output(self):
        return luigi.LocalTarget(self.outfile)

    def run(self):
        log = LOG

        api1submit = models.SubmitSelectTemplate(
            query_id=self.seq_id, query_sequence=self.seq_str)

        api1 = managers.CathSelectTemplateManager(
            base_url=self.api1_base,
            submit_data=api1submit,
            api_user=self.api1_user,
            api_password=self.api1_password,
        )

        api1.run()

        api1_base = self.api1_base
        task_uuid = api1.task_uuid
        headers = api1.api_client.headers

        log.info("Getting hit info ...")
        hits_url = '{api1_base}/api/select-template/{task_uuid}/hits'.format(
            api1_base=api1_base, task_uuid=task_uuid)
        log.info("GET %s", hits_url)
        resp = requests.get(hits_url, headers=headers)
        resp.raise_for_status()
        hits = resp.json()
        log.info("  ... retrieved %s hits", len(hits))

        log.info("Writing results to %s", self.outfile)
        with open(self.outfile, 'wb') as fh:
            fh.write(resp.content)


@requires(CathSelectTemplateHitsTask)
class AlignTemplateAggregator(luigi.Task):
    """
    Generates AlignTemplate task requirements from CathSelectTemplate results
    """

    def get_hits(self):
        hits = None
        with self.input().open('r') as infile:
            hits = json.load(infile)
        return hits

    def run(self):

        log = LOG
        api1_base = self.api1_base
        seq_id = self.seq_id
        headers = {}
        # headers = self.api1.api_client.headers

        hits = self.get_hits()

        for hit_count, hit in enumerate(hits, 1):

            log_hr(log)

            log.info("SEQUENCE %s, HIT %s [%s]: FunFam '%s': %s",
                     seq_id, hit_count, hit['query_range'], hit['ff_id'], hit['ff_name'])

            log.info("Getting template alignments ...")
            hit_uuid = hit['hit_uuid']
            aln_url = f'{api1_base}/api/select-template/hit/{hit_uuid}/alignments'
            log.info("GET %s", aln_url)
            resp = requests.get(aln_url, headers=headers)
            resp.raise_for_status()
            alns = resp.json()
            log.info("  ... retrieved %s template alignments", len(alns))
            log_br(log)

            if not alns:
                log.warning("Found no valid template alignments from hit '%s'. " +
                            "This is probably due to a lack of non-discontinuous CATH domains " +
                            "in the matching FunFam (skipping modelling step).", hit['ff_id'])
                continue

            log_prefix = 'HIT{}'.format(hit_count)
            aln = alns[0]

            log.info("%s: Creating task to model template %s, %s (offset %s) ... ",
                     log_prefix, aln['pdb_id'], aln['auth_asym_id'], aln['template_seqres_offset'])

            task_kwargs = {k: aln[k] for k in [
                'target_sequence', 'template_sequence', 'template_seqres_offset', 'pdb_id', 'auth_asym_id']}

            yield AlignTemplateTask(**task_kwargs)


class AlignTemplateTask(luigi.Task):
    """
    Runs an AlignTemplate job and caches resulting model as PDB file
    """

    target_sequence = luigi.Parameter()
    template_sequence = luigi.Parameter()
    template_seqres_offset = luigi.Parameter()
    pdb_id = luigi.Parameter()
    auth_asym_id = luigi.Parameter()
    api2_base = luigi.Parameter()
    api2_user = luigi.Parameter()
    api2_password = luigi.Parameter()
    work_dir = luigi.Parameter()

    @property
    def pdbfile(self):
        return f'{self.work_dir}/{self.task_id_str}.pdb'

    def output(self):
        return luigi.LocalTarget(self.pdbfile)

    def run(self):
        log = LOG

        api2submit = models.SubmitAlignment(
            target_sequence=self.target_sequence,
            template_sequence=self.template_sequence,
            template_seqres_offset=self.template_seqres_offset,
            pdb_id=self.pdb_id,
            auth_asym_id=self.auth_asym_id,
        )

        api2 = managers.SMAlignmentManager(
            base_url=self.api2_base,
            submit_data=api2submit,
            outfile=self.pdbfile,
            api_user=self.api2_user,
            api_password=self.api2_password,
            logger=log,
        )

        api2.run()
