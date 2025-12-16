# Data Format Security

## CSV/Tabular Data

Guard against formula injection attacks. Cells beginning with `=`, `+`, `-`, or `@` can execute formulas when opened in Excel or Google Sheets. Applications will prompt or auto-execute depending on security settings. Prefix dangerous values with a single quote or tab character. Sanitize all user-controlled data before CSV export.

Handle delimiters correctly. Fields containing the delimiter character require quoting. Embedded quotes need escaping via double-quote convention. Newlines within fields also require quoting the entire field.

Specify encoding explicitly. UTF-8 BOM can break parsers expecting raw UTF-8. Relying on Latin-1 versus UTF-8 detection creates ambiguity. Declare encoding in headers or documentation.

## JSON/YAML

Never use `yaml.load()` with untrusted input—it executes arbitrary Python code. Always use `yaml.safe_load()`. Beware the Norway problem: the string `NO` parses as boolean `False` in unquoted YAML. Quote strings explicitly.

`JSON.parse()` is generally safe from code execution but prototype pollution occurs during object merges. Libraries like lodash `merge()` can overwrite `Object.prototype`. JavaScript numbers lose precision beyond 2^53—use strings for large integers or IDs.

Validate schema before processing. Use JSON Schema, Zod, or Yup to enforce structure. Fail fast on invalid input rather than assuming shape.

## Binary Data

Allocate buffers with explicit sizes. Fixed-size reads truncate data silently. Verify length before accessing offsets. Integer overflow in size calculations leads to buffer overflows—validate calculations stay within bounds.

Validate file formats via magic bytes, not extensions. File extensions are user-controlled and unreliable. Check headers before invoking parsers.

Use battle-tested parsing libraries, not custom implementations. Binary parsers are frequent fuzzing targets. Enforce memory limits on untrusted input to prevent resource exhaustion.

Image processing carries unique risks. ImageTragick-style vulnerabilities exploit ImageMagick delegates. SVG files can embed JavaScript. Decompression bombs upload small files that expand to massive dimensions, exhausting memory during decode.
