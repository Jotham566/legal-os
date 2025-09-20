from __future__ import annotations

from typing import List

from ..schemas import (
    DoclingResult,
    LayoutBlock,
    LayoutBox,
    LayoutText,
    PageLayout,
)


class DoclingClient:
    """Stubbed Docling v2 client.

    In future, integrate with real Docling APIs/models. For now, produce a
    deterministic layout result based on simple heuristics of the input.
    """

    def analyze(self, content: bytes, content_type: str | None) -> DoclingResult:
        text_ratio = self._text_ratio(content)
        # Confidence increases with text ratio
        confidence = max(0.0, min(1.0, 0.5 + 0.5 * text_ratio))
        notes: List[str] = []
        if not content:
            notes.append("empty")
        if content_type and not content_type.startswith("application/"):
            notes.append("non-application content-type")

        # Create a single page with one text block if text is present
        page = PageLayout(page_number=1, blocks=[])
        if text_ratio > 0.1:
            box = LayoutBox(page=1, x=50, y=50, width=500, height=100)
            text = LayoutText(text="Sample text", confidence=confidence, box=box)
            block = LayoutBlock(kind="text", confidence=confidence, box=box, texts=[text])
            page.blocks.append(block)
        else:
            # very low text ratio -> maybe a figure block with lower confidence
            box = LayoutBox(page=1, x=40, y=40, width=520, height=320)
            block = LayoutBlock(kind="figure", confidence=max(0.2, confidence - 0.2), box=box)
            page.blocks.append(block)

        return DoclingResult(pages=[page], confidence=confidence, page_count=1, notes=notes)

    @staticmethod
    def _text_ratio(data: bytes) -> float:
        if not data:
            return 0.0
        text_like = sum(1 for b in data if 9 <= b <= 13 or 32 <= b <= 126)
        return text_like / max(1, len(data))
