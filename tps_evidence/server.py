"""Loopback-only HTTP transport for the offline workbench; stdlib, no CDN."""
import argparse
import json
import mimetypes
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from urllib.request import urlopen
from pydantic import ValidationError
from .corpus import ROOT,PDF,load_corpus,load_json
from .engine import query
from .rules import check
from .export import json_export,markdown_export
from .workbench import bootstrap,present,page_image
from . import __version__, records
from .chips import profile,catalogue,pdf_path

WEB=Path(__file__).resolve().parent/"web"
EVAL_LOCK=threading.Lock()
STATIC={"/":"index.html","/app.css":"app.css","/app.js":"app.js","/records-ui.js":"records-ui.js","/chip-ui.js":"chip-ui.js","/icons.svg":"icons.svg"}

def request_result(data):
    chip_id=data.get('chip_id','tps40200');profile(chip_id)
    kind=data.get("kind","query")
    if kind=="query":
        question=data.get("question")
        if not isinstance(question,str):raise ValueError("请提供文本问题。")
        conditions=data.get("conditions")
        if conditions is not None:
            if not isinstance(conditions,dict) or any(v is not None and not isinstance(v,(str,bool)) or isinstance(v,str) and len(v)>96 for v in conditions.values()):
                raise ValueError("筛选条件应为含单位的短文本或明确的布尔条件。")
        return query(question,conditions,chip_id=chip_id)
    if kind=="check":
        point=data.get("point")
        if not isinstance(point,dict):raise ValueError("请提供检查条件。")
        if any(v is not None and (not isinstance(v,str) or len(v)>96) for v in point.values()):
            raise ValueError("条件应为含单位的短文本，例如 12 V、200 kΩ。")
        return check(point,chip_id=chip_id)
    raise ValueError("未知操作。")

class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True

class Handler(BaseHTTPRequestHandler):
    server_version="TPSWorkbench/0.4"
    def log_message(self,*args):pass
    def response(self,status,body,content_type="application/json; charset=utf-8",headers=None):
        if not isinstance(body,bytes):body=body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for key,value in (headers or {}).items():self.send_header(key,value)
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def js(self,status,data):self.response(status,json.dumps(data,ensure_ascii=False))
    def allowed_host(self):
        return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}"}
    def guard(self):
        if not self.allowed_host():self.js(403,{"error":"仅允许通过本机地址访问。"});return False
        origin=self.headers.get("Origin")
        if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"}:
            self.js(403,{"error":"请求来源与本机工作台不一致。"});return False
        return True
    def do_GET(self):
        if not self.guard():return
        path=urlsplit(self.path).path
        try:
            if path in STATIC:
                p=WEB/STATIC[path]
                self.response(200,p.read_bytes(),mimetypes.guess_type(p.name)[0] or "application/octet-stream");return
            params=parse_qs(urlsplit(self.path).query,keep_blank_values=True)
            chip_id=params.get('chip_id',['tps40200'])[0];profile(chip_id)
            if path=="/api/chips":self.js(200,{'chips':catalogue(),'default':'tps40200'});return
            if path=="/api/bootstrap":self.js(200,bootstrap(chip_id));return
            if path=="/api/health":self.js(200,{"app":"tps40200-workbench","version":__version__});return
            if path=="/api/records":self.js(200,{"records":records.list_records(chip_id if 'chip_id' in params else None)});return
            if path=="/api/records/export":
                self.response(200,json.dumps({"format_version":"1.0","records":records.list_records()},ensure_ascii=False,indent=2),headers={"Content-Disposition":"attachment; filename=tps40200-records.json"});return
            if path.startswith("/api/records/"):
                self.js(200,records.read(path.removeprefix("/api/records/")));return
            m=re.fullmatch(r"/api/pages/(\d+)\.png",path)
            if m:self.response(200,page_image(int(m[1]),chip_id),"image/png");return
            if path=="/api/source.pdf":
                load_corpus(chip_id);p=pdf_path(chip_id);self.response(200,p.read_bytes(),"application/pdf",{"Content-Disposition":f"attachment; filename={p.name}"});return
            if path=="/api/evaluation":
                load_corpus(chip_id)
                with EVAL_LOCK:
                    p=ROOT/('reports' if chip_id=='tps40200' else f'reports/chips/{chip_id}')/"evaluation-all.json"
                    report=load_json(p) if p.exists() else None
                boundaries=ROOT/('reports' if chip_id=='tps40200' else f'reports/chips/{chip_id}')/"capability-boundaries.json"
                self.js(200,{"report":report,"boundaries":load_json(boundaries) if boundaries.exists() else []});return
            if path=="/api/evaluation.md":
                from .evaluate import markdown_report
                with EVAL_LOCK:report=load_json(ROOT/('reports' if chip_id=='tps40200' else f'reports/chips/{chip_id}')/"evaluation-all.json")
                self.response(200,markdown_report(report),"text/markdown; charset=utf-8",{"Content-Disposition":f"attachment; filename={chip_id}-validation.md"});return
            self.js(404,{"error":"未找到页面或证据。"})
        except (KeyError,FileNotFoundError):self.js(404,{"error":"资料不存在或页码超出范围。"})
        except ValueError as e:self.js(409,{"error":str(e)})
        except Exception:self.js(500,{"error":"资料暂时无法读取，请重新启动工作台后再试。"})
    def do_POST(self):
        if not self.guard():return
        try:
            if self.headers.get_content_type()!="application/json":self.js(415,{"error":"请求须为 JSON。"});return
            size=int(self.headers.get("Content-Length","0"))
            if not 0<size<=32768:self.js(413,{"error":"请求为空或过大。"});return
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError("请求应为对象。")
            path=urlsplit(self.path).path
            if path=="/api/query":self.js(200,present(request_result({**data,"kind":"query"})));return
            if path=="/api/check":self.js(200,present(request_result({**data,'kind':'check'})));return
            if path=="/api/export":
                result=request_result(data)
                fmt=data.get("format","json")
                if fmt not in ("json","md"):raise ValueError("导出格式应为 JSON 或 Markdown。")
                content=json_export(result) if fmt=="json" else markdown_export(result)
                ctype="application/json; charset=utf-8" if fmt=="json" else "text/markdown; charset=utf-8"
                self.response(200,content,ctype,{"Content-Disposition":f"attachment; filename={result.chip_id}-evidence.{fmt}"});return
            if path=="/api/records":
                request=data.get("request")
                if not isinstance(request,dict):raise ValueError("请提供已经完成的查询或检查。")
                result=request_result(request)
                canonical={"kind":request.get("kind","query"),'chip_id':result.chip_id}
                if canonical["kind"]=="query":
                    canonical["question"]=result.question
                    if request.get("conditions") is not None:canonical["conditions"]=result.condition_inputs
                else:canonical["point"]=result.inputs
                self.js(201,records.save(data.get("name"),canonical,present(result)));return
            if path=="/api/records/compare":
                comparison=records.compare(records.read(data.get("a")),records.read(data.get("b")))
                if data.get("format")=="md":
                    self.response(200,records.comparison_markdown(comparison),"text/markdown; charset=utf-8",{"Content-Disposition":"attachment; filename=tps40200-comparison.md"})
                else:self.js(200,comparison)
                return
            if path=="/api/evaluate":
                from .evaluate import evaluate,markdown_report
                with EVAL_LOCK:
                    chip_id=data.get('chip_id','tps40200');profile(chip_id)
                    report=evaluate("all",chip_id=chip_id)
                    folder=ROOT/('reports' if chip_id=='tps40200' else f'reports/chips/{chip_id}');folder.mkdir(parents=True,exist_ok=True)
                    (folder/"evaluation.md").write_text(markdown_report(report))
                self.js(200,{"report":report});return
            self.js(404,{"error":"未找到该操作。"})
        except KeyError:self.js(404,{"error":"记录不存在。"})
        except ValidationError:self.js(400,{"error":"检查或筛选字段无效。请使用含单位的文本，并确认字段名称与温度类型。"})
        except (ValueError,json.JSONDecodeError) as e:self.js(400,{"error":str(e)})
        except Exception:self.js(500,{"error":"操作未完成，请重试；如资料已更换，请重新复核并导入。"})

def main():
    parser=argparse.ArgumentParser(description="多芯片本地证据工作台")
    parser.add_argument("--port",type=int,default=8502)
    parser.add_argument("--open",action="store_true",help="在默认浏览器打开")
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error("端口范围为 1–65535。")
    try:server=WorkbenchServer(("127.0.0.1",args.port),Handler)
    except OSError as e:
        try:
            with urlopen(f"http://127.0.0.1:{args.port}/api/health",timeout=2) as response:health=json.load(response)
        except Exception:health={}
        if health.get("app")=="tps40200-workbench":
            print(f"工作台已在运行：http://127.0.0.1:{args.port}/")
            if args.open:webbrowser.open(f"http://127.0.0.1:{args.port}/")
            return
        parser.exit(1,f"无法启动本地工作台：{e}\n端口可能被其他程序占用；可使用 --port 指定另一端口。\n")
    print(f"芯片手册证据工作台：http://127.0.0.1:{args.port}/",flush=True)
    if args.open:webbrowser.open(f"http://127.0.0.1:{args.port}/")
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=="__main__":main()
