"""Run deterministic parser smoke tests on public Schneider and Eaton PDFs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pymupdf

from schematic_agent.bom import build_bom_with_source
from schematic_agent.components import detect_components
from schematic_agent.geometry import build_geometry
from schematic_agent.netlist import build_netlist
from schematic_agent.parser.pdf_extract import PdfExtraction, extract_page


SAMPLES: dict[str, dict[str, Any]] = {
    "schneider": {
        "markers": ("figure 12", "typical control circuit schematic"),
        "minimum_primitives": 20,
        "minimum_segments": 10,
    },
    "eaton": {
        "markers": ("figure 5.1-43", "typical 5/15/27 kv vcp-w"),
        "minimum_primitives": 20,
        "minimum_segments": 10,
    },
}


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _find_target_page(pdf_path: Path, markers: tuple[str, ...]) -> tuple[int, str]:
    """Find the schematic page by its printed figure caption, not a fixed index."""
    matches: list[tuple[int, str]] = []
    with pymupdf.open(str(pdf_path)) as document:
        for page_index, page in enumerate(document):
            text = _normalized(page.get_text("text"))
            if all(marker in text for marker in markers):
                matches.append((page_index + 1, text))

    if len(matches) != 1:
        raise AssertionError(
            f"{pdf_path.name}: expected exactly one page containing {markers}; "
            f"found {len(matches)} matches at {[page for page, _ in matches]}"
        )
    return matches[0]


def _inspect_sample(vendor: str, pdf_path: Path) -> dict[str, Any]:
    config = SAMPLES[vendor]
    if not pdf_path.is_file() or pdf_path.stat().st_size < 100_000:
        raise AssertionError(f"{vendor}: PDF is missing or unexpectedly small: {pdf_path}")

    page_number, page_text = _find_target_page(pdf_path, config["markers"])
    page = extract_page(str(pdf_path), page_number)
    extraction = PdfExtraction(pdf_path=str(pdf_path), pages=[page])

    geometry = build_geometry(extraction)
    components, component_issues = detect_components(geometry, extraction)
    nets, netlist_issues = build_netlist(geometry, components, extraction)
    bom_items, bom_issues, bom_source = build_bom_with_source(extraction, components)

    primitive_kinds = Counter(item.kind for item in page.primitives)
    report = {
        "vendor": vendor,
        "pdf": pdf_path.name,
        "file_size_bytes": pdf_path.stat().st_size,
        "target_page": page_number,
        "target_markers": list(config["markers"]),
        "text_spans": len(page.texts),
        "vector_primitives": len(page.primitives),
        "primitive_kinds": dict(sorted(primitive_kinds.items())),
        "tables": len(page.tables),
        "geometry_segments": len(geometry.segments),
        "geometry_nodes": len(geometry.nodes),
        "crossings": len(geometry.crossings),
        "components_detected": len(components),
        "component_designations": sorted(
            {
                str(component.ref_designation)
                for component in components
                if getattr(component, "ref_designation", "")
            }
        ),
        "nets_detected": len(nets),
        "bom_items": len(bom_items),
        "bom_source": bom_source,
        "issues": {
            "component": len(component_issues),
            "netlist": len(netlist_issues),
            "bom": len(bom_issues),
        },
        "status": "passed",
    }

    failures: list[str] = []
    if page.raster_only:
        failures.append("target schematic page was classified as raster-only")
    if len(page.texts) < 20:
        failures.append(f"expected >=20 text spans, got {len(page.texts)}")
    if len(page.primitives) < config["minimum_primitives"]:
        failures.append(
            f"expected >={config['minimum_primitives']} vector primitives, "
            f"got {len(page.primitives)}"
        )
    if len(geometry.segments) < config["minimum_segments"]:
        failures.append(
            f"expected >={config['minimum_segments']} geometry segments, "
            f"got {len(geometry.segments)}"
        )

    if failures:
        report["status"] = "failed"
        report["failures"] = failures
        raise AssertionError(json.dumps(report, ensure_ascii=False, indent=2))

    # Keep a short caption excerpt in the report for traceability.
    report["caption_excerpt"] = page_text[:500]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test the parser on public Schneider and Eaton schematic PDFs."
    )
    parser.add_argument("--schneider", type=Path, required=True)
    parser.add_argument("--eaton", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, Any]] = []
    failures: list[str] = []

    for vendor, pdf_path in (
        ("schneider", args.schneider),
        ("eaton", args.eaton),
    ):
        try:
            reports.append(_inspect_sample(vendor, pdf_path))
        except Exception as exc:  # preserve diagnostics for the CI artifact
            failures.append(f"{vendor}: {exc}")
            reports.append(
                {
                    "vendor": vendor,
                    "pdf": pdf_path.name,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    payload = {
        "status": "passed" if not failures else "failed",
        "samples": reports,
        "failures": failures,
    }
    args.report.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
