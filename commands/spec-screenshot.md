---
argument-hint: [--deep] [output-path]
description: Analyze website screenshots and generate detailed implementation specs
---

## Context

- Current directory: !`pwd`
- Target output: !`test -f SPEC.md && echo "SPEC.md exists (will be overwritten)" || echo "Will create new SPEC.md"`
- Arguments: $ARGUMENTS
- Thinking mode: !`echo "$ARGUMENTS" | grep -q -i "\-\-deep\|deep" && echo "DEEP (sequential thinking enabled)" || echo "STANDARD (regular analysis)"`

## Your Task

### STEP 1: Validate prerequisites

CHECK for images in conversation history:
- SCAN recent messages for screenshots or images
- IF no images found: ERROR "❌ No screenshots detected in conversation. Please paste website screenshots before running this command."
- IF images found: LOG "✓ Found screenshots ready for analysis"

### STEP 2: Perform ultra-detailed analysis

DETERMINE thinking mode from arguments:
- IF `$ARGUMENTS` contains "deep" or "--deep": USE sequential thinking tool (`mcp__sequential-thinking__sequentialthinking`)
- ELSE (STANDARD mode): Perform regular analysis

**Analysis framework - cover ALL of these aspects:**

1. **Layout Architecture**
   - Overall page structure (header, navigation, hero, main content, sidebars, footer)
   - Grid system and column layouts
   - Container widths and max-widths
   - Section hierarchy and nesting

2. **Typography System**
   - Font families (identify primary, secondary, monospace)
   - Font sizes for each text level (h1-h6, body, small, etc.)
   - Font weights used (light, regular, medium, semibold, bold)
   - Line heights and letter spacing
   - Text colors and contrast ratios

3. **Color Palette**
   - Primary brand colors
   - Secondary/accent colors
   - Background colors (main, sections, cards)
   - Text colors (headings, body, muted, links)
   - Border colors
   - State colors (success, error, warning, info)
   - Color codes in hex/rgb (best approximation)

4. **Spacing System**
   - Margins between major sections
   - Padding within components
   - Gap spacing in flex/grid layouts
   - Consistent spacing scale (e.g., 4px, 8px, 16px, 24px, 32px)
   - Vertical rhythm patterns

5. **Component Inventory**
   - Buttons (styles, sizes, states)
   - Input fields and forms
   - Cards and containers
   - Navigation elements
   - Icons and their style
   - Badges, tags, labels
   - Modals, tooltips, dropdowns
   - List items and data tables

6. **Visual Design Details**
   - Border radius values
   - Shadow styles (box-shadow parameters)
   - Border styles and thicknesses
   - Background patterns or gradients
   - Opacity/transparency effects

7. **Images and Media**
   - Image locations and dimensions
   - Image aspect ratios
   - Icon sets (are they SVG, font icons, or images?)
   - Logo placement and size
   - Decorative vs content images
   - **CRITICAL**: Note which images need to be sourced/created

8. **Interactive Elements** (if discernible)
   - Hover states visible
   - Active/focus states
   - Transition/animation hints
   - Interactive feedback patterns

9. **Responsive Design** (if multiple viewports shown)
   - Breakpoints observable
   - Layout changes per breakpoint
   - Component behavior changes
   - Mobile-specific patterns

10. **Accessibility Considerations**
    - Color contrast issues
    - Heading hierarchy
    - Interactive element sizes
    - Text readability

**Analysis process:**
- Start with high-level layout observations
- Progressively zoom into details
- Measure or estimate dimensions
- Identify patterns and systems
- Note uncertainties or assumptions
- Cross-reference across multiple screenshots if provided

**DEEP mode only:** Use sequential thinking to systematically work through each aspect above with thorough reasoning.
**STANDARD mode:** Analyze directly without sequential thinking tool.

### STEP 3: Generate comprehensive SPEC.md

DETERMINE output path:
- PARSE arguments to extract output path (ignore --deep/deep flags)
- IF custom path provided in `$ARGUMENTS`: USE it (e.g., `./docs/spec.md`)
- ELSE: USE default `./SPEC.md`

**Content structure for SPEC.md:**

````markdown
# Website Implementation Specification

> Generated from screenshot analysis on [DATE]

## Overview

[2-3 sentence summary of the website's purpose and design style]

## Layout Architecture

### Page Structure
- [Describe overall layout]
- [Container constraints]
- [Section breakdown]

### Grid System
- [Grid configuration]
- [Column structure]
- [Responsive behavior]

## Typography

### Font Stack
- Primary: [font family]
- Secondary: [font family]
- Monospace: [font family]

### Type Scale
| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| H1      | Xpx  | X      | X           | #HEX  |
| H2      | Xpx  | X      | X           | #HEX  |
| Body    | Xpx  | X      | X           | #HEX  |
| ...     |      |        |             |       |

### Text Styling
- [Letter spacing, text transforms, etc.]

## Color System

### Palette
```css
/* Primary Colors */
--color-primary: #XXXXXX;
--color-primary-dark: #XXXXXX;
--color-primary-light: #XXXXXX;

/* Secondary Colors */
--color-secondary: #XXXXXX;

/* Neutrals */
--color-background: #XXXXXX;
--color-surface: #XXXXXX;
--color-text: #XXXXXX;
--color-text-muted: #XXXXXX;

/* Semantic */
--color-success: #XXXXXX;
--color-error: #XXXXXX;
--color-warning: #XXXXXX;

/* Borders */
--color-border: #XXXXXX;
```

### Color Usage
- [Where each color is applied]

## Spacing System

### Scale
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;
--space-3xl: 64px;
```

### Application
- Section margins: [values]
- Card padding: [values]
- Element gaps: [values]

## Component Specifications

### Component: [Name]
- **Dimensions**: [width x height]
- **Padding**: [values]
- **Border**: [style, width, color, radius]
- **Shadow**: [box-shadow values]
- **Typography**: [size, weight, color]
- **States**: [default, hover, active, disabled]
- **Variants**: [if applicable]

[Repeat for each component]

## Images and Assets

### Required Images
1. **[Image name/purpose]**
   - Location: [where in layout]
   - Dimensions: [WxH or aspect ratio]
   - Format suggestion: [JPG/PNG/SVG]
   - Content: [description of image content]

2. [Continue for all images]

### Icon Set
- Style: [outlined/filled/line/custom]
- Size: [standard sizes used]
- Source suggestion: [e.g., Heroicons, Font Awesome, custom]

### Logo
- Dimensions: [WxH]
- Format: [preferably SVG]
- Variations: [light/dark, horizontal/stacked]

## Responsive Behavior

### Breakpoints
```css
--breakpoint-mobile: 640px;
--breakpoint-tablet: 768px;
--breakpoint-desktop: 1024px;
--breakpoint-wide: 1280px;
```

### Layout Changes
- [Describe how layout adapts at each breakpoint]

## Interactive Elements

### Buttons
- [Hover effects]
- [Active states]
- [Transition timing]

### Forms
- [Focus styles]
- [Validation states]

### Navigation
- [Interaction patterns]

## Technical Recommendations

### Framework Suggestions
- [Recommended frameworks based on complexity]

### Implementation Notes
- [Key architectural decisions]
- [Performance considerations]
- [Accessibility requirements]

### Dependencies
- [Suggested libraries for icons, animations, etc.]

## Open Questions / Assumptions

- [List any uncertainties]
- [Areas needing clarification]
- [Assumptions made during analysis]

## Next Steps

1. [Verification tasks]
2. [Asset procurement tasks]
3. [Implementation phases]

---

*Note: All measurements are approximations based on screenshot analysis. Verify exact values during implementation.*
````

WRITE the file with comprehensive, specific details from your analysis.

CONFIRM write operation:
- IF successful: LOG "✓ Written to [path]"
- IF failed: ERROR "Failed to write file: [reason]" and suggest fix

### STEP 4: Present summary to user

DISPLAY concise summary (NOT the full spec):

```
## Screenshot Analysis Complete ✓

### Overview
[1-2 sentence description]

### Key Findings
- **Layout**: [brief description]
- **Components**: [count] distinct components identified
- **Color Palette**: [count] colors in system
- **Typography**: [primary font family], [count] type levels
- **Spacing**: [spacing scale summary]
- **Assets**: [count] images/icons to source

### Output
📄 Full specification: `[output path]`

### Recommendations
[1-2 key technical recommendations]
```

## Examples

**Basic usage (standard mode, default output):**
```
/spec-screenshot
```

**Deep mode (with sequential thinking):**
```
/spec-screenshot --deep
```

**Custom output path:**
```
/spec-screenshot ./docs/landing-page-spec.md
```

**Deep mode with custom output path:**
```
/spec-screenshot --deep ./docs/landing-page-spec.md
```

**Multi-screenshot workflow:**
```
1. Paste multiple screenshots (desktop, tablet, mobile)
2. Run: /spec-screenshot --deep
3. Review SPEC.md for comprehensive breakdown
```

## Notes

- **Thinking modes**:
  - **STANDARD** (default): Fast analysis with direct reasoning
  - **DEEP**: Uses sequential thinking tool for thorough, step-by-step analysis (slower but more comprehensive)
- **Approximations**: All measurements are best-effort approximations; verify during implementation
- **Image sourcing**: Command explicitly notes which images need to be obtained or created
- **Overwrite behavior**: Running command multiple times will overwrite existing SPEC.md
- **Context efficiency**: Only summary shown in chat; full spec written to file
- **Multi-screenshot support**: Analyzes all images in conversation context
- **Best results**: Higher resolution screenshots provide more accurate measurements
- **When to use deep mode**: Complex designs, large component libraries, or when you need extremely thorough analysis
