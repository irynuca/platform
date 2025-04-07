# Metric Aliases System (Normalization Layer)

## Purpose
The `metric_aliases` table maps various raw company-reported metric names to standardized platform names.

This helps:
- Normalize financials across multiple companies
- Enable flexible querying, calculations, and automation

---

## How It Works

### 1. Manual Aliases
Stored in `METRIC_ALIASES` dictionary in `seed_aliases.py`

Use for:
- Core ratios
- High-priority labels
- Clean aliases for UI

### 2. Auto-Generated Aliases
Extracted from the `financial_metrics` table using:
- `metric_name_eng`
- `metric_name_ro`
- Mapped to `generalized_metric_eng`

Only created when `alias ≠ standardized_metric`.

---

## Table: `metric_aliases`

| Field              | Description                                  |
|-------------------|----------------------------------------------|
| alias              | Raw name used by company                     |
| standardized_metric | Normalized internal name (e.g., Net income) |
| language           | Optional: `en` or `ro`                       |
| source             | `"manual"` or `"auto_generated"`             |

---

## How to Use

- Use `get_standardized_metric_name(DB_PATH, raw_name)` from `helpers.py`
- Combine with fallback matching when ingesting or scraping

---

## Maintenance
- Run `seed_aliases.py` after changes to `financial_metrics`
- Update `METRIC_ALIASES` manually for curated coverage
- Check for duplicates, typos, and overlap periodically

