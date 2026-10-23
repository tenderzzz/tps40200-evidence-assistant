import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from .models import Evidence, Parameter

ROOT = Path(os.environ.get("TPS_EVIDENCE_HOME", Path(__file__).resolve().parents[1]))
PDF = ROOT / "data/source/tps40200-rev-g.pdf"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def dump_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

@lru_cache(maxsize=16)
def _cached_corpus(chip_id="tps40200", source_hash=None):
    from .chips import data_root,pdf_path
    root=data_root(chip_id)
    manifest=load_json(root/"source/manifest.json")
    actual=hashlib.sha256(pdf_path(chip_id).read_bytes()).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError("手册哈希与已复核版本不一致。请恢复固定资料，或重新复核并导入。")
    evidence=[Evidence.model_validate(e) for e in load_json(root/"processed/evidence.json")]
    parameters=[Parameter.model_validate(p) for p in load_json(root/"curated/parameters.json")]
    return manifest,{e.id:e for e in evidence},parameters

def load_corpus(chip_id="tps40200"):
    from .chips import data_root,pdf_path
    manifest=load_json(data_root(chip_id)/"source/manifest.json")
    corpus=_cached_corpus(chip_id,manifest["sha256"])
    # Recheck the small pinned file even when parsed data is cached. A running
    # app must not show new PDF pixels next to old parameter values.
    if hashlib.sha256(pdf_path(chip_id).read_bytes()).hexdigest()!=corpus[0]["sha256"]:
        raise ValueError("手册哈希与已复核版本不一致。请恢复固定资料，或重新复核并导入。")
    return corpus
