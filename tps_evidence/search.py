import re
import unicodedata
from functools import lru_cache
from rank_bm25 import BM25Okapi
from .corpus import load_corpus, load_json, ROOT
from .models import Hit

def normalize(text):
    text=unicodedata.normalize("NFKC",text).lower()
    return re.sub(r"[\s_]+","",text).replace("ω","ohm")

def tokens(text):
    text=unicodedata.normalize("NFKC",text).lower()
    out=re.findall(r"[a-z]+[a-z0-9]*|\d+(?:\.\d+)?",text)
    for phrase in re.findall(r"[\u4e00-\u9fff]+",text):
        out.extend(phrase[i:i+2] for i in range(len(phrase)-1))
    return out or ["__empty__"]

def alias_match(alias,question):
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*",alias):
        return bool(re.search(r"(?<![A-Za-z0-9])"+re.escape(alias)+r"(?![A-Za-z0-9])",question,re.I))
    return normalize(alias) in normalize(question)

@lru_cache(maxsize=16)
def enhanced_index(chip_id="tps40200",source_hash=None):
    _,ev,parameters=load_corpus(chip_id);items=[]
    for e in ev.values():
        symbols=[p.symbol for p in parameters if e.id in p.evidence_ids and e.id!="design-note" and not e.context_only]
        items.append(e.model_copy(update={"aliases":list(dict.fromkeys(e.aliases+symbols))}))
    model=BM25Okapi([tokens(" ".join([e.title,e.text,e.context,e.summary,*e.aliases])) for e in items])
    return items,model

def retrieve(question,limit=3,*,chip_id="tps40200"):
    source,_,_=load_corpus(chip_id)
    items,model=enhanced_index(chip_id,source["sha256"])
    scores=model.get_scores(tokens(question))
    ranked=[]
    for e,score in zip(items,scores):
        aliases=[a for a in e.aliases if alias_match(a,question)]
        bonus=(100+max(len(normalize(a)) for a in aliases)) if aliases else 0
        # Explicit user qualifiers override a broad symbol match.
        if e.id=="abs" and re.search(r"绝对最大|absolute\s*maximum",question,re.I):bonus+=200
        if e.id=="recommended" and "推荐" in question:bonus+=200
        score=float(score)+bonus
        if score>0:ranked.append(Hit(evidence_id=e.id,score=round(score,5)))
    ranked.sort(key=lambda h:(-h.score,h.evidence_id))
    return ranked[:limit]

@lru_cache(maxsize=16)
def plain_index(chip_id="tps40200",source_hash=None):
    from .chips import data_root,profile
    pages=load_json(data_root(chip_id)/"raw/pages.json");chunks=[]
    for page in pages[:profile(chip_id)["core_pages"]]:
        lines=[l for l in page["lines"] if 74<=l["top"]<735]
        for start in range(0,len(lines),10):
            g=lines[start:start+10]
            if g:chunks.append(dict(page=page["page"],bbox=[54,g[0]["top"],558,max(l["bottom"] for l in g)],text="\n".join(l["text"] for l in g)))
    return chunks,BM25Okapi([tokens(c["text"]) for c in chunks])

def plain_retrieve(question,limit=3,*,chip_id="tps40200"):
    source,_,_=load_corpus(chip_id)
    items,model=plain_index(chip_id,source["sha256"]);scores=model.get_scores(tokens(question))
    ranked=sorted(((float(s),i) for i,s in enumerate(scores) if s>0),reverse=True)[:limit]
    return [dict(items[i],score=score) for score,i in ranked]
