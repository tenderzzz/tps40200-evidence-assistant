from functools import lru_cache
from io import BytesIO
import pdfplumber
from .corpus import PDF, load_corpus
from .pdf_runtime import PDF_RENDER_LOCK

@lru_cache(maxsize=64)
def evidence_image(evidence_id: str, cropped: bool=True) -> bytes:
    _,ev,_=load_corpus();e=ev[evidence_id]
    with PDF_RENDER_LOCK, pdfplumber.open(PDF) as pdf:
        page=pdf.pages[e.page-1]
        if cropped:
            top=max(0,min([e.bbox[1]]+[b[1] for b in e.context_bboxes])-8)
            bottom=min(page.height,max([e.bbox[3]]+[b[3] for b in e.context_bboxes])+8)
            page=page.crop((max(0,e.bbox[0]-8),top,min(page.width,e.bbox[2]+8),bottom))
        img=page.to_image(resolution=144)
        img.draw_rect(e.bbox,stroke=(18,104,120,255),fill=(18,104,120,20),stroke_width=2)
        for box in e.context_bboxes:
            img.draw_rect(box,stroke=(149,98,26,255),fill=(149,98,26,12),stroke_width=1)
        out=BytesIO();img.save(out,format="PNG");return out.getvalue()
