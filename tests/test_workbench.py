import json
import threading
from http.client import HTTPConnection
from io import BytesIO

import pytest
from PIL import Image

from scripts.check_contrast import audit
from tps_evidence.corpus import ROOT, load_corpus, load_json
from tps_evidence.server import Handler, WorkbenchServer
from tps_evidence.workbench import PINS, bootstrap


@pytest.fixture(scope="module")
def http():
    server = WorkbenchServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path, data=None, headers=None):
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=15)
        body = None if data is None else json.dumps(data, ensure_ascii=False).encode()
        conn.request("GET" if data is None else "POST", path, body,
                     headers={**({"Content-Type": "application/json"} if data is not None else {}), **(headers or {})})
        response = conn.getresponse()
        output = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return output

    yield request
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_warm_palette_text_and_functional_controls_have_contrast():
    report = audit()
    assert report["passed"], [c for c in report["checks"] if not c["passed"]]


def test_all_parameter_regions_belong_to_their_cited_table():
    manifest, evidence, parameters = load_corpus()
    regions = load_json(ROOT / "data/curated/row_regions.json")
    assert regions["source_sha256"] == manifest["sha256"]
    assert set(regions["regions"]) == {p.id for p in parameters}
    for p in parameters:
        region = regions["regions"][p.id]
        x0, y0, x1, y1 = region["bbox"]
        supports = [evidence[eid] for eid in p.evidence_ids if evidence[eid].page == region["page"]]
        assert supports
        assert any(e.bbox[1] - 1 <= y0 < y1 <= e.bbox[3] + 1 for e in supports), p.id
        assert 0 <= x0 < x1 <= 612


def test_pin_diagram_uses_d_package_top_view_and_same_source():
    assert [(p["number"], p["name"]) for p in PINS if p["side"] == "left"] == [(1, "RC"), (2, "SS"), (3, "COMP"), (4, "FB")]
    assert [(p["number"], p["name"]) for p in PINS if p["side"] == "right"] == [(8, "VDD"), (7, "ISNS"), (6, "GDRV"), (5, "GND")]
    b = bootstrap()
    assert len(b["page_sizes"]) == b["source"]["pages"] == 52
    assert b["initial"]["source"]["sha256"] == b["source"]["sha256"]


def test_http_parameter_answer_keeps_all_conditions_and_row_regions(http):
    status, _, body = http("/api/query", {"question": "VFB"})
    payload = json.loads(body)
    assert status == 200
    assert len(payload["result"]["parameters"]) == len(payload["row_regions"]) == 4
    assert payload["row_regions"]["vfb-125"]["page"] == 5
    assert payload["row_regions"]["vfb-125"]["bbox"][1] > payload["row_regions"]["vfb-85"]["bbox"][1]
    assert payload["evidence"][0]["context_bboxes"]


def test_http_check_and_export_use_identical_input_context(http):
    point = {"vdd": "12000 mV", "resistance": "0.2 MΩ", "capacitance": "0.47 nF"}
    status, _, body = http("/api/check", {"point": point})
    payload = json.loads(body)
    assert status == 200
    checks = {c["rule"]: c for c in payload["result"]["checks"]}
    assert checks["rc_frequency"]["value"] == pytest.approx(101.3171225937)
    assert checks["rc_current"]["value"] == 60
    status, headers, body = http("/api/export", {"kind": "check", "point": point, "format": "json"})
    exported = json.loads(body)
    assert status == 200 and "attachment" in headers["Content-Disposition"]
    assert exported["result"] == payload["result"]
    assert exported["result"]["inputs"] == point
    assert exported["source"]["sha256"] == payload["source"]["sha256"]


def test_http_markdown_export_includes_source_and_conditions(http):
    status, _, body = http("/api/export", {"kind": "query", "question": "4.3 V 能正常工作吗？", "format": "md"})
    text = body.decode()
    assert status == 200
    assert "4.3" in text and "推荐" in text and "欠压启动阈值的典型值不能代替" in text and "SHA-256" in text


def test_http_invalid_units_are_recoverable_results(http):
    status, _, body = http("/api/check", {"point": {"resistance": "0 Ω", "capacitance": "470 pF"}})
    result = json.loads(body)["result"]
    assert status == 200 and result["status"] == "invalid"
    assert next(c for c in result["checks"] if c["rule"] == "rc_frequency")["status"] == "invalid"


@pytest.mark.parametrize("point", [{"vdd": 12}, {"unknown": "12 V"}, "12 V"])
def test_http_rejects_malformed_points(http, point):
    status, _, body = http("/api/check", {"point": point})
    assert status == 400 and json.loads(body)["error"]


def test_http_original_page_pixels_and_bounds(http):
    status, headers, body = http("/api/pages/5.png")
    image = Image.open(BytesIO(body))
    assert status == 200 and headers["Content-Type"] == "image/png"
    assert image.size == (1224, 1584)
    assert http("/api/pages/0.png")[0] == 404
    assert http("/api/pages/53.png")[0] == 404


def test_http_only_serves_local_app_files_and_blocks_foreign_origins(http):
    assert http("/../data/source/manifest.json")[0] == 404
    assert http("/api/health", headers={"Host": "external.example"})[0] == 403
    assert http("/api/check", {"point": {}}, headers={"Origin": "https://external.example"})[0] == 403
    status, headers, body = http("/")
    assert status == 200 and b"/app.js" in body
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert http("/app.js")[0] == 200
    assert http("/app.css")[0] == 200
    assert http("/icons.svg")[0] == 200


def test_http_bootstrap_evaluation_and_full_source_are_available(http):
    assert json.loads(http("/api/bootstrap")[2])["version"] == "0.4.0"
    assert json.loads(http("/api/evaluation")[2])["report"]["metrics"]["passed"] == 60
    status, _, body = http("/api/source.pdf")
    assert status == 200 and body.startswith(b"%PDF")


def test_http_filtered_query_save_reload_compare_and_export(http,monkeypatch,tmp_path):
    monkeypatch.setenv("TPS_RECORDS_HOME",str(tmp_path/"local-records"))
    req={"kind":"query","question":"VFB","conditions":{"vdd":"12 V","temperature":"100 °C","temperature_kind":"test","frequency":"100 kHz"}}
    status,_,body=http("/api/query",req)
    result=json.loads(body)["result"]
    assert status==200 and any(m["status"]=="applicable" for m in result["applicability"])
    status,_,body=http("/api/records",{"name":"高温方案","request":req});a=json.loads(body)
    assert status==201 and a["snapshot"]["result"]==result
    req["conditions"]["temperature"]="25 °C"
    b=json.loads(http("/api/records",{"name":"常温方案","request":req})[2])
    assert len(json.loads(http("/api/records")[2])["records"])==2
    assert json.loads(http(f"/api/records/{a['id']}")[2])["snapshot"]["result"]==result
    comparison=json.loads(http("/api/records/compare",{"a":a["id"],"b":b["id"]})[2])
    assert any(p["changed"] for p in comparison["parameters"])
    status,_,body=http("/api/records/compare",{"a":a["id"],"b":b["id"],"format":"md"})
    assert status==200 and "SHA-256" in body.decode()
    assert http("/api/records/../../source")[0]==404
