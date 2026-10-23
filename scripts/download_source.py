"""Restore the pinned official source. Never overwrite a changed PDF silently."""
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
EXPECTED="a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240"
URL="https://www.ti.com/lit/ds/symlink/tps40200.pdf"
target=ROOT/"data/source/tps40200-rev-g.pdf"
if target.exists():
    if sha256(target.read_bytes()).hexdigest()!=EXPECTED:raise SystemExit("现有文件版本不同；请复核后再替换，不会自动覆盖。")
    print("固定手册已在本地，无需下载。")
else:
    with urlopen(URL,timeout=60) as r:data=r.read(20_000_000)
    if sha256(data).hexdigest()!=EXPECTED:raise SystemExit("官方文件与已复核版本不同；请重新复核参数和验证集。未写入文件。")
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print("已下载并核对固定手册 SHA-256。")
