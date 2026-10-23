"""Reproduce the nine new examples without writing any user records."""
from tps_evidence.chip_specs import SPECS
from tps_evidence.chips import ROOT,profile
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.export import json_export,markdown_export

def main():
    for chip,spec in SPECS.items():
        folder=ROOT/'examples/chips'/chip;folder.mkdir(parents=True,exist_ok=True)
        for case in spec['cases']:
            req=case['request']
            result=query(req['question'],req.get('conditions'),chip_id=chip) if req['kind']=='query' else check(req['point'],chip_id=chip)
            (folder/(case['id']+'.json')).write_text(json_export(result)+'\n')
            (folder/(case['id']+'.md')).write_text(markdown_export(result))
        print(profile(chip)['name'],len(spec['cases']),'examples')

if __name__=='__main__':main()
