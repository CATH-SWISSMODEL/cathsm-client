import json
import logging

from Bio import SeqIO

LOG = logging.getLogger(__name__)


class Model(object):
    """
    Base class for all models
    """

    @classmethod
    def load(cls, infile):
        """Creates a new instance of this model from a JSON filehandle."""
        try:
            data = json.load(infile)
        except Exception as err:
            LOG.error("failed to load json file '{}': {}".format(infile, err))
            raise

        try:
            instance = cls(**data)
        except Exception as err:
            LOG.error("failed to create instance of class {} from data: {} (file: {})".format(
                cls.__name__, data, infile))
            raise

        return instance

    def to_file(self, outfile):
        """Save class instance to JSON file"""
        json.dump(self.as_dict(), outfile)

    def as_dict(self, *, remove_meta=True):
        """Represents the model as a dict (removes optional keys that do not have values)"""
        data = self.__dict__
        if remove_meta and 'meta' in data:
            del data['meta']
        data = dict((k, v) for k, v in data.items() if v is not None)
        return data


class SubmitSelectTemplate(Model):
    """Represents the data required to submit a job to the CATH select template API."""

    def __init__(self, *, query_id, query_sequence, task_id=None, meta=None):

        if not meta:
            meta = {}

        self.query_id = str(query_id)
        self.query_sequence = str(query_sequence)
        self.task_id = task_id
        self.meta = meta

    @classmethod
    def load_from_fasta(cls, infile):
        """Creates a new instance of this model from a FASTA filehandle."""
        try:
            for seq in SeqIO.parse(infile, "fasta"):
                first_seq = seq
                break
            data = {'query_id': first_seq.id, 'query_sequence': first_seq.seq}
        except Exception as err:
            LOG.error("failed to load FASTA file: %s", err)
            raise

        try:
            instance = cls(**data)
        except Exception as err:
            LOG.error("failed to create instance of class {} from data: {} (file: {})".format(
                cls.__name__, data, infile))
            raise

        return instance



class SubmitAlignment(Model):
    """Represents the data required to submit a job to the SM Alignment API."""

    def __init__(self, *, target_sequence, template_sequence, template_seqres_offset,
                 pdb_id, auth_asym_id, assembly_id=None, project_id=None, meta=None):

        if not meta:
            meta = {}

        self.target_sequence = target_sequence
        self.template_sequence = template_sequence
        self.template_seqres_offset = template_seqres_offset
        self.pdb_id = pdb_id
        self.auth_asym_id = auth_asym_id
        self.assembly_id = assembly_id
        self.project_id = project_id
        self.meta = meta

