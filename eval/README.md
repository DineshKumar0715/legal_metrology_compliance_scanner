# OCR and Compliance Evaluation Set

Store representative package images under `eval/images/` and annotate them in a
JSON file following `ground_truth.example.json`.

## Required annotation fields

- `id`: Stable document identifier.
- `image`: Path relative to `eval/`.
- `text`: Human-corrected text visible in the image. Preserve numbers and words;
  line breaks are useful but are not required to match exactly.
- `fields`: Expected declaration values. Use `null` when the declaration is
  genuinely absent from the package.
- `expected_compliance.status`: `compliant` or `non_compliant`.
- `expected_compliance.missing_declarations`: Canonical field names missing from
  the package. Use an empty list when none are missing.
- `capture_conditions`: Tags describing the image conditions.

The canonical field names match the API response:
`mrp`, `net_quantity`, `date_of_packing`, `consumer_care`,
`manufacturer_details`, and `country_of_origin`.

## Recommended sample mix

Aim for 10-20 images:

- 6-8 clean, flat labels
- 4-5 curved bottles or pouches
- 3-4 images with poor lighting or glare
- 2-3 genuinely non-compliant packages

Useful condition tags include `flat`, `curved`, `good_light`, `low_light`,
`glare`, `blur`, `skew`, `low_dpi`, `small_text`, `multi_column`, and `table`.

Do not put synthetic expected text in the dataset. The `text` and field values
should be transcribed from the actual image by a human reviewer.
