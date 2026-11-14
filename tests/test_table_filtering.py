"""Регрессии фильтрации ложных таблиц на страницах электрических схем."""

from __future__ import annotations

from schematic_agent.bom import component_table_regions
from schematic_agent.components import _table_primitive_indices, _table_text_keys
from schematic_agent.geometry import build_geometry
from schematic_agent.parser.pdf_extract import (
    PageExtraction,
    PdfExtraction,
    TableCell,
    TableData,
    TextSpan,
    VectorPrimitive,
)


def _cell(text: str, row: int, col: int) -> TableCell:
    return TableCell(text, 0.0, 0.0, 1.0, 1.0, row, col)


def _page_with_false_and_real_tables() -> PageExtraction:
    # Типичный ложный результат pdfplumber: почти вся страница сведена
    # в одну ячейку с текстом схемы/штампа.
    full_page_table = TableData(
        page=1,
        x0=0.0,
        y0=0.0,
        x1=300.0,
        y1=300.0,
        cells=[_cell("DRAWING TITLE / DEVICE DESIGNATION / DESCRIPTION", 0, 0)],
    )

    # ABB-подобный реестр: DESIGNAT. | FIGURE | DESCRIPTION.
    component_register = TableData(
        page=1,
        x0=50.0,
        y0=50.0,
        x1=150.0,
        y1=100.0,
        cells=[
            _cell("DESIGNAT.", 0, 0),
            _cell("FIGURE", 0, 1),
            _cell("DESCRIPTION", 0, 2),
            _cell("-MAS", 1, 0),
            _cell("FIG.1", 1, 1),
            _cell("MOTOR FOR SPRING CHARGING", 1, 2),
            _cell("-BGS1", 2, 0),
            _cell("FIG.1", 2, 1),
            _cell("CONTACT FOR CHARGER MECHANISM", 2, 2),
        ],
    )

    primitives = [
        VectorPrimitive(
            "line", [(10.0, 10.0), (40.0, 10.0)], 1,
            {"bbox": (10.0, 10.0, 40.0, 10.0)},
        ),
        VectorPrimitive(
            "line", [(60.0, 60.0), (90.0, 60.0)], 1,
            {"bbox": (60.0, 60.0, 90.0, 60.0)},
        ),
        VectorPrimitive(
            "line", [(200.0, 200.0), (230.0, 200.0)], 1,
            {"bbox": (200.0, 200.0, 230.0, 200.0)},
        ),
    ]
    texts = [
        TextSpan("QF1", 10.0, 10.0, 20.0, 20.0, 1),
        TextSpan("-MAS", 60.0, 60.0, 75.0, 70.0, 1),
    ]
    return PageExtraction(
        page=1,
        width=300.0,
        height=300.0,
        texts=texts,
        primitives=primitives,
        tables=[full_page_table, component_register],
    )


def test_only_component_register_is_classified_as_table_region() -> None:
    page = _page_with_false_and_real_tables()

    assert component_table_regions(page) == [(50.0, 50.0, 150.0, 100.0)]


def test_component_filter_does_not_hide_geometry_or_refs_in_full_page_table() -> None:
    page = _page_with_false_and_real_tables()

    assert _table_primitive_indices(page) == {1}
    excluded_texts = _table_text_keys(page)
    assert {key[1] for key in excluded_texts} == {"-MAS"}

    geometry = build_geometry(PdfExtraction(pdf_path="synthetic.pdf", pages=[page]))

    assert len(geometry.segments) == 2
    assert {(segment.x0, segment.x1) for segment in geometry.segments} == {
        (10.0, 40.0),
        (200.0, 230.0),
    }


def test_ansi_function_designations_are_classified() -> None:
    table = TableData(
        page=1,
        x0=10.0,
        y0=10.0,
        x1=100.0,
        y1=80.0,
        cells=[
            _cell("DEVICE TAG", 0, 0),
            _cell("DESCRIPTION", 0, 1),
            _cell("52", 1, 0),
            _cell("CIRCUIT BREAKER", 1, 1),
            _cell("52Y", 2, 0),
            _cell("ANTI-PUMP RELAY", 2, 1),
        ],
    )
    page = PageExtraction(
        page=1,
        width=120.0,
        height=100.0,
        tables=[table],
    )

    assert component_table_regions(page) == [(10.0, 10.0, 100.0, 80.0)]
