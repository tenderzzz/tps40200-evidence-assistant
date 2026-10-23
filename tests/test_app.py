from streamlit.testing.v1 import AppTest
from tps_evidence.corpus import ROOT

def button(app,label):return next(b for b in app.button if b.label==label)

def test_query_submit_and_evidence_selection():
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    assert not at.exception
    at.text_input(key="question").set_value("4.3 V 能正常工作吗？")
    button(at,"查找证据").click().run()
    assert not at.exception
    assert "不满足" in at.session_state.query_result.answer
    assert at.session_state.query_result.evidence_ids==["recommended"]

def test_timing_example_and_form_submission():
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    button(at,"RC 定时检查").click().run()
    assert not at.exception and at.session_state.page=="检查条件"
    assert at.text_input(key="point_resistance").value=="200 kΩ"
    at.text_input(key="point_resistance").set_value("1 kΩ")
    button(at,"检查条件").click().run()
    assert not at.exception
    assert next(c for c in at.session_state.check_result.checks if c.rule=="rc_current").status=="violated"

def test_validation_page_loads():
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    at.sidebar.radio[0].set_value("验证结果").run()
    assert not at.exception
    assert any(t.value=="结果怎样验证" for t in at.title)
