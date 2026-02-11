# Challenge JSON Format

All challenges are stored as individual JSON files in `challenges/<category>/`.

## Schema

```json
{
  "id": "string (unique identifier, e.g., crypto-001)",
  "title": "string (display name)",
  "category": "string (must match parent directory name)",
  "difficulty": "string (easy | medium | hard)",
  "points": "integer (points awarded on solve)",
  "description": "string (challenge text, may include markdown/code blocks)",
  "flag": "string (exact flag to match, format: flag{...})",
  "hints": ["array of strings (progressive hints, easy to hard)"],
  "resources": ["array of URLs (learning resources)"]
}
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID across all challenges. Convention: `<prefix>-<number>` |
| `title` | string | Human-readable challenge name |
| `category` | string | Must match the directory: `cryptography`, `osint`, `password-cracking`, `forensics`, `web` |
| `difficulty` | string | One of: `easy`, `medium`, `hard` |
| `points` | integer | Points awarded. Suggested: easy=75-100, medium=150-200, hard=250-500 |
| `description` | string | Full challenge description. Supports newlines and code blocks |
| `flag` | string | Exact flag string. Always format as `flag{...}` |
| `hints` | string[] | Ordered hints from vague to specific. Minimum 2 hints |
| `resources` | string[] | URLs for learning more about the topic |

## Categories

- **cryptography** — Encoding, ciphers, hashing concepts
- **osint** — Open source intelligence gathering
- **password-cracking** — Hash cracking, wordlists, rainbow tables
- **forensics** — File analysis, metadata, steganography, memory forensics
- **web** — SQL injection, XSS, CSRF, authentication bypass

## Adding New Challenges

1. Create a new JSON file in the appropriate `challenges/<category>/` directory
2. Use the next sequential ID number (e.g., `crypto-004`)
3. Ensure `id` is unique across ALL categories
4. Ensure `category` matches the directory name exactly
5. Test flag format: must start with `flag{` and end with `}`
6. Include at least 2 hints and 1 resource URL

## Example

```json
{
  "id": "crypto-001",
  "title": "Caesar's Secret",
  "category": "cryptography",
  "difficulty": "easy",
  "points": 100,
  "description": "Decrypt: Wkh txlfn eurzq ira mxpsv ryhu wkh odcb grj",
  "flag": "flag{the_quick_brown_fox_jumps_over_the_lazy_dog}",
  "hints": [
    "Classic shift cipher",
    "The shift is 3"
  ],
  "resources": [
    "https://en.wikipedia.org/wiki/Caesar_cipher"
  ]
}
```

## Flag Validation Rules

- Flags are case-sensitive
- Flags must match exactly (no whitespace trimming on inner content)
- Format: `flag{<content>}` where content can contain any printable characters
- The `solve` command checks for exact string match after stripping leading/trailing whitespace
