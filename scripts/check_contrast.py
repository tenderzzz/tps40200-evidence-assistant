"""Check the actual workbench CSS palette; no browser or network dependency."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(foreground, background):
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + .05) / (dark + .05)


def audit():
    css = (ROOT / "tps_evidence/web/app.css").read_text()
    tokens = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})(?=[;}])", css))
    pairs = []
    for foreground, backgrounds in [
        ("ink", ["paper", "surface", "panel", "active"]),
        ("muted", ["paper", "surface", "panel", "active"]),
        ("teal", ["paper", "surface", "active"]),
        ("surface", ["primary", "ink"]),
        ("success", ["success-bg"]),
        ("warning", ["warning-bg"]),
        ("danger", ["danger-bg", "surface"]),
    ]:
        pairs.extend((foreground, background, 4.5, "text") for background in backgrounds)
    for foreground, backgrounds in [
        ("control", ["paper", "surface", "panel", "active"]),
        ("focus", ["paper", "surface", "panel", "active"]),
        ("teal", ["paper", "surface", "active"]),
    ]:
        pairs.extend((foreground, background, 3, "control") for background in backgrounds)
    checks = []
    for foreground, background, required, kind in pairs:
        ratio = contrast(tokens[foreground], tokens[background])
        checks.append(dict(foreground=foreground, background=background, kind=kind,
                           ratio=round(ratio, 3), required=required, passed=ratio >= required))
    return dict(method="WCAG 2.2 relative luminance; CSS token pairs, not a complete accessibility audit",
                colors=tokens, passed=all(c["passed"] for c in checks), checks=checks)


if __name__ == "__main__":
    report = audit()
    (ROOT / "reports/contrast.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Contrast checks: {sum(c['passed'] for c in report['checks'])}/{len(report['checks'])}")
    raise SystemExit(0 if report["passed"] else 1)
