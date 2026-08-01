"""Product normaliser — raw dict → ``ProductResult``."""

from __future__ import annotations

import re
from typing import Any, cast

from browser_mcp.plugins.scraper.models import ProductResult, ScrapeMeta
from browser_mcp.plugins.scraper.urls import normalize_href

__all__ = ["ProductNormalizer"]


class ProductNormalizer:
    """Normalises raw product-collector output into :class:`ProductResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> ProductResult:
        data: dict[str, Any] = raw.get("raw", {})
        source: str = str(raw.get("source", "unknown"))
        base_url: str | None = raw.get("base_url")

        name = self._first(data, ["name", "product_name", "title"])
        description = self._first(data, ["description", "product.description"])
        price = self._extract_price(data)
        currency = self._first(
            data,
            ["priceCurrency", "currency", "og:price:currency", "offers.priceCurrency", "offers.currency"],
        )
        brand = self._first(data, ["brand", "brand.name", "manufacturer.name"])
        sku = self._first(data, ["sku", "productID", "gtin"])
        availability = self._first(data, ["availability", "og:availability"])
        condition = self._first(data, ["itemCondition", "condition", "og:condition"])
        image_raw = self._first(data, ["image", "image.url", "og:image"])
        url = self._first(data, ["url", "og:url", "product.url"])
        # Fall back to the SKU as a path when no explicit product URL is present.
        if url is None:
            url = self._first(data, ["sku"])
        rating = self._first(data, ["ratingValue", "rating.value", "aggregateRating.ratingValue"])
        rating_count = self._first(data, ["ratingCount", "reviewCount", "aggregateRating.reviewCount"])

        image = normalize_href(str(image_raw), base_url) if image_raw else None
        resolved_url = normalize_href(str(url), base_url) if url else None

        return ProductResult(
            meta=meta,
            name=name,
            description=description,
            price=price,
            currency=currency,
            brand=brand,
            sku=sku,
            availability=availability,
            condition=condition,
            image=image,
            url=resolved_url,
            rating_value=self._to_float(rating),
            rating_count=self._to_int(rating_count),
            source=source,
            raw=data,
        )

    @staticmethod
    def _first(data: dict[str, Any], keys: list[str]) -> str | None:
        """Return the first non-empty string found under ``keys``.

        Dotted keys (``a.b``) drill into nested dicts; non-dict values and
        primitive scalars (str/int/float/bool) are coerced to strings via
        :meth:`_scalar_text`, which also drills into nested objects such as
        ``{"name": "Acme"}`` (JSON-LD ``brand``).
        """
        for key in keys:
            if "." in key:
                node: object = ProductNormalizer._get_path(data, key)
            else:
                node = data.get(key)
            value = ProductNormalizer._scalar_text(node)
            if value is not None:
                return value
        return None

    @staticmethod
    def _get_path(data: dict[str, Any], dotted: str) -> object:
        """Resolve a dotted ``a.b.c`` path through nested dicts."""
        node: object = data
        for part in dotted.split("."):
            if isinstance(node, dict):
                d = cast(dict[str, object], node)
                node = d.get(part)
            else:
                return None
        return node

    @staticmethod
    def _extract_price(data: dict[str, Any]) -> float | None:
        for key in ["price", "offers.price", "og:price:amount", "product.price"]:
            val = ProductNormalizer._first(data, [key])
            if val:
                return ProductNormalizer._to_float(val)
        return None

    @staticmethod
    def _scalar_text(value: object) -> str | None:
        """Coerce an arbitrary JSON-LD value into a string.

        Strings are returned directly; numbers/booleans are stringified;
        dicts are drilled for a named scalar (``name``/``text``/``value``/
        ``title``) before falling back to the first scalar child; lists return
        the first non-empty scalar element.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, dict):
            d_val = cast(dict[str, object], value)
            for sub in ("name", "text", "value", "title", "@type"):
                sub_val = d_val.get(sub)
                if isinstance(sub_val, str):
                    return sub_val
            for sub_val_item in d_val.values():
                extracted = ProductNormalizer._scalar_text(sub_val_item)
                if extracted is not None:
                    return extracted
        if isinstance(value, list):
            l_val = cast(list[object], value)
            for item in l_val:
                extracted = ProductNormalizer._scalar_text(item)
                if extracted is not None:
                    return extracted
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return None

    @staticmethod
    def _to_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            cleaned = re.sub(r"[^0-9.]", "", str(val))
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _to_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(float(str(val).strip()))
        except (ValueError, TypeError):
            return None
