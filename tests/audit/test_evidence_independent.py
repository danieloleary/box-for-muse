"""Independent opt-in gather evidence contract. No Box, auth, or network.
Run from project root: python3 review/sprint/test_evidence_independent.py
Optional first argument: another workflows.py candidate.
"""
import copy
import importlib.util
import json
from pathlib import Path
import socket
import sys
import unittest

SOURCE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'src/box/workflows.py'
spec = importlib.util.spec_from_file_location('independent_evidence_workflows', SOURCE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
def deny(*args, **kwargs): raise AssertionError('network prohibited in independent evidence tests')
socket.socket.connect = deny
socket.create_connection = deny
CUSTOMERS = [{'name': 'Cedar', 'aliases': ['Cedar Works'], 'cases': []}]
BUCKETS = ('confirmed_files', 'ambiguous_files', 'unmatched_files', 'unassessed_files')
def records(result): return [item for bucket in BUCKETS for item in result[bucket]]
def payload(text='Cedar Works. Unique body evidence.'):
    return {'ok': True, 'version': {'verified': True, 'file_version_id': 'read-v2', 'sha1': 'read-hash', 'size': 100}, 'version_changed_during_read': False, 'version_after': 'read-v2', 'extraction': {'status': 'ok', 'format': 'txt', 'text': text, 'truncated': False, 'total_length': len(text)}}
class Fake:
    API_BASE = 'https://api.box.com/2.0'
    valid_id = staticmethod(lambda value: isinstance(value, str) and value.isdigit())
    def __init__(self, replies, names=None):
        self.replies = replies; self.calls = []; self.names = names or {}
    def do_request(self, url):
        entries = [{'id': key, 'type': 'file', 'name': self.names.get(key, 'notes-'+key+'.txt'), 'file_version': {'id': 'listing-v1'}, 'sha1': 'listing-hash', 'size': 90} for key in self.replies]
        return 200, json.dumps({'entries': entries, 'offset': 0, 'limit': 100, 'total_count': len(entries)}).encode(), {}
    def cmd_read_file(self, args):
        self.calls.append(args.file_id)
        rc, body = self.replies[args.file_id]
        print(json.dumps(body)); return rc

def run(client, include=False, **kwargs):
    return w.gather_customer_files(client, '10', copy.deepcopy(CUSTOMERS), include_evidence=include, **kwargs)

class IndependentEvidence(unittest.TestCase):
    def test_default_body_omitted_and_baseline_result_unchanged(self):
        client = Fake({'101': (0, payload())})
        default = run(client)
        enabled = run(Fake({'101': (0, payload())}), True)
        self.assertNotIn('evidence_summary', default)
        self.assertNotIn('Unique body evidence', json.dumps(default))
        for record in records(default): self.assertNotIn('evidence', record)
        enabled.pop('evidence_summary')
        for record in records(enabled): record.pop('evidence')
        self.assertEqual(default, enabled)

    def test_opt_in_reuses_existing_reads_and_read_version(self):
        base = Fake({'101': (0, payload()), '102': (0, payload('Different customer.'))})
        extra = Fake(copy.deepcopy(base.replies))
        run(base); result = run(extra, True)
        self.assertEqual(base.calls, extra.calls)
        self.assertEqual(extra.calls, ['101', '102'])
        evidence = result['confirmed_files'][0]['evidence']
        self.assertEqual(evidence['source']['file_version_id'], 'read-v2')
        self.assertEqual(evidence['source']['sha1'], 'read-hash')
        self.assertTrue(evidence['complete'])

    def test_name_match_does_not_download_just_for_evidence(self):
        client = Fake({'101': (0, payload())}, {'101': 'Cedar Works proposal.txt'})
        result = run(client, True)
        self.assertEqual(client.calls, [])
        evidence = result['confirmed_files'][0]['evidence']
        self.assertFalse(evidence['available'])
        self.assertNotIn('text', evidence)
        self.assertFalse(result['evidence_summary']['complete'])

    def test_unverified_or_failed_reads_never_return_text(self):
        variants=[]
        a=payload();a['version']['verified']=False;variants.append((0,a))
        a=payload();a['ok']=False;variants.append((1,a))
        a=payload();a['version'].pop('sha1');variants.append((0,a))
        a=payload();a['version'].pop('file_version_id');variants.append((0,a))
        variants.append((1,{'ok':False,'status':403}))
        for rc, body in variants:
            with self.subTest(body=body):
                result=run(Fake({'101':(rc,body)}),True)
                evidence=records(result)[0]['evidence']
                self.assertFalse(evidence['available'])
                self.assertNotIn('text',evidence)
                self.assertFalse(result['coverage']['complete'])

    def test_changed_or_unchecked_versions_never_return_text(self):
        for changes in ({'version_changed_during_read':True}, {'version_check_note':'post-download metadata unavailable'}, {'version_changed_during_read':None,'version_after':None}):
            body=payload();body.update(changes)
            with self.subTest(changes=changes):
                result=run(Fake({'101':(0,body)}),True)
                self.assertFalse(records(result)[0]['evidence']['available'])
                self.assertNotIn('text',records(result)[0]['evidence'])

    def test_partial_and_truncated_extractions_are_explicit(self):
        for changes in ({'status':'partial','limits':['headers omitted']},{'truncated':True}):
            body=payload();body['extraction'].update(changes)
            with self.subTest(changes=changes):
                result=run(Fake({'101':(0,body)}),True)
                evidence=records(result)[0]['evidence']
                self.assertTrue(evidence['available'])
                self.assertFalse(evidence['complete'])
                self.assertFalse(result['evidence_summary']['complete'])
                self.assertFalse(result['coverage']['complete'])
                self.assertEqual(evidence['extraction']['status'],body['extraction']['status'])
                self.assertEqual(evidence['extraction']['truncated'],body['extraction']['truncated'])

    def test_utf8_perfile_and_aggregate_caps_are_enforced(self):
        text='Cedar Works '+('\U0001F332'*3000)
        client=Fake({str(101+i):(0,payload(text)) for i in range(6)})
        result=run(client,True)
        evidence=[record['evidence'] for record in records(result)]
        sizes=[len(item.get('text','').encode('utf-8')) for item in evidence]
        self.assertTrue(all(size<=8000 for size in sizes))
        self.assertLessEqual(sum(sizes),32000)
        self.assertEqual(sum(sizes),result['evidence_summary']['text_bytes'])
        self.assertTrue(all(item['output_truncated'] for item in evidence))
        self.assertFalse(result['evidence_summary']['complete'])
        self.assertFalse(result['coverage']['complete'])
        self.assertEqual(len(client.calls),6)
        for item,size in zip(evidence,sizes):
            self.assertEqual(item['text_bytes'],size)
            self.assertNotIn('\ufffd',item['text'])

    def test_budget_exhaustion_never_triggers_extra_read(self):
        client=Fake({'101':(0,payload()),'102':(0,payload())})
        result=run(client,True,max_content_reads=1)
        self.assertEqual(client.calls,['101'])
        unassessed=result['unassessed_files'][0]
        self.assertFalse(unassessed['evidence']['available'])
        self.assertNotIn('text',unassessed['evidence'])
        self.assertFalse(result['coverage']['complete'])

if __name__=='__main__':unittest.main(verbosity=2)
