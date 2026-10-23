"""PDFium uses process-wide native state, including the font cache."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from tps_evidence import render, workbench
from tps_evidence.engine import query


def test_page_and_evidence_renderers_never_overlap_native_calls(monkeypatch):
    counter_lock = threading.Lock()
    start = threading.Barrier(6)
    active = maximum = calls = 0

    class Image:
        def draw_rect(self, *args, **kwargs):
            return self

        def save(self, target, **kwargs):
            target.write(b'\x89PNG\r\n\x1a\n')

    class Page:
        width, height = 612, 792

        def to_image(self, **kwargs):
            nonlocal active, maximum, calls
            with counter_lock:
                active += 1
                maximum = max(maximum, active)
                calls += 1
            # Native rendering releases the GIL; make concurrent entry observable.
            time.sleep(0.02)
            with counter_lock:
                active -= 1
            return Image()

    class Document:
        pages = [Page()] * 68

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    evidence_id = query('VFB').evidence_ids[0]
    monkeypatch.setattr(workbench.pdfplumber, 'open', lambda *a, **k: Document())
    workbench._page_image.cache_clear()
    render.evidence_image.cache_clear()

    def run(index):
        start.wait(timeout=5)
        if index < 4:
            chip = ('tps40200', 'lm2596-adj', 'lm358', 'ne555')[index]
            return workbench.page_image(5, chip)
        return render.evidence_image(evidence_id, cropped=False)

    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            assert all(data.startswith(b'\x89PNG') for data in pool.map(run, range(6)))
        assert calls >= 5
        assert maximum == 1, 'PDFium entered concurrently across rendering paths'
    finally:
        workbench._page_image.cache_clear()
        render.evidence_image.cache_clear()
