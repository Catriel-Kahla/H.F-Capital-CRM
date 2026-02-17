# Design

Design reference for the Browserling cybersecurity product UI. Implemented in `templates/base.html`.

## Brand

### Logo

- **Asset:** SVG file (served from `static/` or project static directory).
- **Usage:** Shown in the header next to the brand wordmark; also used as a decorative hero graphic (same file, lower opacity). In the header the logo has class `.brand-logo` (height 4vh, width auto).

### Brand text treatment

The brand is the **text treatment** “Browserling” (capital B), not a separate logo font:

- **Wordmark** — Single color: <span style="display:inline-block;width:1.2em;height:1.2em;border-radius:3px;background:#4285F4;border:1px solid #ddd;vertical-align:middle"></span> Blue (`#4285F4`).
- **Font:** [Outfit](https://fonts.google.com/specimen/Outfit), weight 600, size 2.25vw (in header).
- **Markup:** One span: `.brand-text` containing “Browserling”, next to the logo image.

So the logo is the SVG graphic; the wordmark is the blue “Browserling” text in Outfit.

---

## Fonts

| Use | Font | Weights loaded |
|-----|------|------------------|
| **Body / general UI** | [Raleway](https://fonts.google.com/specimen/Raleway) | 400, 500, 600, 700 |
| **Brand (logo wordmark), headings** | [Outfit](https://fonts.google.com/specimen/Outfit) | 400, 500, 600, 700 |

Both loaded from Google Fonts in `base.html`.

---

## Color palette

| Swatch | Use | Color | Hex / value |
|:------:|-----|--------|-------------|
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#4285F4;border:1px solid #ddd;vertical-align:middle"></span> | **Wordmark (brand)** | Blue | `#4285F4` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#fff;border:1px solid #ddd;vertical-align:middle"></span> | Header background, button text, hero text (h1, subheading), input row background | White | `#fff` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#ddd;border:1px solid #ccc;vertical-align:middle"></span> | Header border, input border (input-row) | Light gray | `#ddd` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#333;border:1px solid #333;vertical-align:middle"></span> | Nav links, input text, caret | Dark gray | `#333` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#999;border:1px solid #999;vertical-align:middle"></span> | Input placeholder | Gray | `#999` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#2B3B80;border:1px solid #2B3B80;vertical-align:middle"></span> | Primary (buttons, main background) | Navy | `#2B3B80` |
| <span style="display:inline-block;width:3.5em;height:3.5em;border-radius:6px;background:#a3caf77a;border:1px solid #ddd;vertical-align:middle"></span> | **Accent (light blue)** | Light blue | `#a3caf77a` / `var(--light-blue)` |

Use these consistently for new pages and components so the product stays on-brand. The accent color is used for table headers and alternating row backgrounds.

## Other docs

- [Project overview](PROJECT_OVERVIEW.md)
- [Design](DESIGN.md)
- [Initial pages and design](INITIAL_PAGES_AND_DESIGN.md)
- [Content management system](CONTENT_MANAGEMENT_SYSTEM.md)
- [Documentation section](DOCUMENTATION_SECTION.md)
