# Public schematic samples for cross-vendor smoke testing

The PDFs below are manufacturer-published reference documents. They are kept
outside the repository because the source documents are copyrighted; use the
linked originals when running manual parser smoke tests.

## Schneider Electric — Masterclad 27 kV

- Document: 6055-40, Rev. 02, May 2024.
- PDF: https://productinfo.se.com/masterclad_mv_switchgear_ib/6055-40-27-kv-metal-clad-switchgear-instruction-bulletin/English/6055-40%20Masterclad%20MV%20Switchgear%20Indoor%20%28bookmap%29.pdf
- Target: Figure 12, "Typical Control Circuit Schematic", printed page 19.
- Characteristics: charging/closing circuit, trip circuit, auxiliary contacts,
  terminal numbers, wire identifiers and circuit-breaker control plug.

## Eaton — VacClad-W 5–15 kV

- Document: DG022001EN, effective October 2025.
- PDF: https://www.eaton.com/content/dam/eaton/products/design-guides---consultant-audience/eaton-vacclad-w-5-15kv-metal-clad-medium-voltage-switchgear-design-guide-dg022001en.pdf
- Target: Figure 5.1-43, "Typical 5/15/27 kV VCP-W DC and AC Control
  Schematics", printed page 5.1-35.
- Characteristics: ANSI device/function labels, separate AC/DC control
  circuits, optional trip devices, contacts and terminal numbers.

These are schematic-page smoke-test references, not project-specific
as-built drawings. Automated regression tests use synthetic extraction
objects and do not fetch external PDFs at test time.
