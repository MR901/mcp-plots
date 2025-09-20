from __future__ import annotations

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def register_tools(mcp_server, config: Dict[str, Any] = None):
    """Register visualization tools into the MCP server."""

    # Lazy import heavy deps to avoid import-time failures
    from src.visualization.chart_config import ChartConfig, ChartType, OutputFormat, Theme
    from src.visualization.generator import ChartGenerator

    @mcp_server.tool()
    def list_chart_types() -> Dict[str, Any]:
        """List supported chart types."""
        try:
            types = [t.value for t in ChartType]
            return {"status": "success", "chart_types": types}
        except Exception as e:
            logger.error(f"list_chart_types failed: {e}")
            return {"status": "error", "error": str(e)}

    @mcp_server.tool()
    def list_themes() -> Dict[str, Any]:
        """List available themes."""
        try:
            return {"status": "success", "themes": [t.value for t in Theme]}
        except Exception as e:
            logger.error(f"list_themes failed: {e}")
            return {"status": "error", "error": str(e)}

    @mcp_server.tool()
    def suggest_fields(sample_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest likely field roles (x, y, category, value) from sample data rows."""
        try:
            if not isinstance(sample_rows, list) or not sample_rows:
                return {"status": "error", "error": "sample_rows must be a non-empty list of objects"}

            # Simple heuristic: numeric -> candidates for y/value; non-numeric -> candidates for x/category
            first = sample_rows[0]
            numeric_fields: List[str] = []
            text_fields: List[str] = []
            for key in first.keys():
                values = [row.get(key) for row in sample_rows[:10]]
                if any(isinstance(v, (int, float)) for v in values if v is not None):
                    numeric_fields.append(key)
                else:
                    text_fields.append(key)

            suggestions = {
                "x_candidates": text_fields,
                "y_candidates": numeric_fields,
                "category_candidates": text_fields,
                "value_candidates": numeric_fields,
            }
            return {"status": "success", "suggestions": suggestions}
        except Exception as e:
            logger.error(f"suggest_fields failed: {e}")
            return {"status": "error", "error": str(e)}

    @mcp_server.tool()
    def render_chart(
        chart_type: str,
        data: List[Dict[str, Any]],
        field_map: Dict[str, str] = None,
        config_overrides: Dict[str, Any] = None,
        options: Dict[str, Any] = None,
        output_format: str = "MCP_IMAGE"
    ) -> Dict[str, Any]:
        """
        Render a chart from tabular data and return MCP-compatible content.

        - chart_type: one of list_chart_types()
        - data: list of objects (rows)
        - field_map: keys like x_field, y_field, category_field, value_field, group_field, size_field
        - config_overrides: subset of ChartConfig as dict (width, height, title, theme, dpi, etc.)
        - options: generator-specific options (e.g., smooth, stack)
        - output_format: MCP_IMAGE (PNG) or MCP_TEXT (SVG)
        """
        try:
            if not isinstance(data, list) or not data:
                return {"status": "error", "error": "data must be a non-empty list of objects"}

            field_map = field_map or {}
            options = options or {}
            config_overrides = config_overrides or {}

            # Build config
            try:
                fmt = OutputFormat(output_format)
            except Exception:
                fmt = OutputFormat.MCP_IMAGE

            cfg = ChartConfig(**{**config_overrides, "output_format": fmt})

            # Route to chart engine
            usable_kwargs = {}
            for key in [
                "x_field", "y_field", "category_field", "value_field",
                "group_field", "size_field", "source_field", "target_field", "name_field", "time_field"
            ]:
                if key in field_map:
                    usable_kwargs[key] = field_map[key]

            # Merge generator options
            usable_kwargs.update(options)

            result = ChartGenerator.run(
                chart_type,
                data=data,
                config=cfg,
                **usable_kwargs
            )

            # Normalize to MCP content
            if isinstance(result, dict) and "content" in result:
                return {"status": "success", **result}

            if isinstance(result, (bytes, bytearray)):
                import base64
                b64 = base64.b64encode(result).decode("utf-8")
                return {
                    "status": "success",
                    "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                }

            if hasattr(result, "getvalue"):
                import base64
                result.seek(0)
                b64 = base64.b64encode(result.getvalue()).decode("utf-8")
                return {
                    "status": "success",
                    "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                }

            if isinstance(result, str):
                # Assume data URI or raw base64 string for image
                if result.startswith("data:image"):
                    try:
                        b64 = result.split(",", 1)[1]
                    except Exception:
                        b64 = result
                    return {
                        "status": "success",
                        "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                    }
                else:
                    # Treat as SVG or textual output
                    return {
                        "status": "success",
                        "content": [{"type": "text", "text": result}],
                    }

            return {"status": "error", "error": "Unsupported chart result type"}

        except Exception as e:
            logger.error(f"render_chart failed: {e}")
            return {"status": "error", "error": str(e)}


