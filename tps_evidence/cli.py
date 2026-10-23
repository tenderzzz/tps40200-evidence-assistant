import argparse
import json
from pathlib import Path
from .engine import query
from .rules import check
from .export import json_export, markdown_export
from .chips import CHIPS
from .chip_specs import SPECS

def main():
    p=argparse.ArgumentParser(description="多芯片本地证据助手")
    sub=p.add_subparsers(dest="command",required=True)
    q=sub.add_parser("query");q.add_argument("question");q.add_argument("--format",choices=["json","md"],default="json")
    c=sub.add_parser("check")
    for field in ["vdd","tj","frequency","resistance","capacitance","ambient-temperature","resistance-tolerance","capacitance-tolerance"]:c.add_argument("--"+field)
    old_fields={"vdd","tj","frequency","resistance","capacitance","ambient_temperature","resistance_tolerance","capacitance_tolerance"}
    for name in sorted({f['name'] for spec in SPECS.values() for f in spec['check_fields']}-old_fields):c.add_argument('--'+name.replace('_','-'))
    q.add_argument('--chip',choices=list(CHIPS),default='tps40200')
    c.add_argument('--chip',choices=list(CHIPS),default='tps40200')
    c.add_argument("--format",choices=["json","md"],default="json")
    e=sub.add_parser("evaluate");e.add_argument("--split",choices=["dev","holdout","all"],default="all")
    e.add_argument('--chip',choices=[*CHIPS,'all'],default='tps40200')
    sub.add_parser('ingest').add_argument('--chip',choices=list(CHIPS),default='tps40200')
    args=p.parse_args()
    if args.command=="ingest":
        from .ingest import ingest
        print(json.dumps(ingest(args.chip),ensure_ascii=False));return
    if args.command=="evaluate":
        from .evaluate import evaluate,markdown_report
        from .corpus import ROOT
        reports=[]
        for chip in CHIPS if args.chip=='all' else [args.chip]:
            r=evaluate(args.split,chip_id=chip);reports.append(r)
            folder=ROOT/('reports' if chip=='tps40200' else f'reports/chips/{chip}')
            (folder/'evaluation.md').write_text(markdown_report(r))
            print(json.dumps(dict(chip_id=chip,**r['metrics']),ensure_ascii=False))
        if any(r['metrics']['passed']!=r['metrics']['cases'] for r in reports):raise SystemExit(1)
        return
    if args.command=="query":result=query(args.question,chip_id=args.chip)
    else:
        names=['vdd','tj','frequency','resistance','capacitance','ambient_temperature','resistance_tolerance','capacitance_tolerance'] if args.chip=='tps40200' else [f['name'] for f in SPECS[args.chip]['check_fields']]
        supplied={k:v for k,v in vars(args).items() if k not in ('command','chip','format') and v is not None}
        result=check(supplied,chip_id=args.chip)
    print(markdown_export(result) if args.format=="md" else json_export(result))

if __name__=="__main__":main()
