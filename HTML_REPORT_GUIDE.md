# GCP Cost Analyzer - HTML Report Generation Guide

This guide explains how to create professional HTML reports from your GCP billing analysis using the Rete branding template.

## Overview

The HTML report format provides a professional, presentation-ready document that can be:
- Viewed in any web browser
- Printed to PDF
- Shared with clients
- Presented in meetings

## Prerequisites

1. **Complete the analysis** using `/analyze-gcp-costs` command
2. **Markdown report generated** (e.g., `gcp-billing-analysis-report.md`)
3. **Logo assets available** in `assets/logo/`

## Assets Included

The plugin includes Rete Consulting branding assets:

```
assets/
├── logo/
│   ├── icon.png    # Rete icon (square logo)
│   └── text.png    # Rete text logo
└── report-styles.css  # Professional CSS styling
```

## Quick Start

### Option 1: Use the CSS Stylesheet

Link the CSS file in your HTML:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GCP Billing Analysis Report</title>
    <link rel="stylesheet" href="../assets/report-styles.css">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Your content here -->
</body>
</html>
```

### Option 2: Inline Styles

For portability, you can inline the CSS from `report-styles.css` into a `<style>` tag.

## Report Structure

### Slide-Based Layout

Each section is a "slide" (full-page view):

```html
<div class="slide">
    <h2>Section Title</h2>
    <!-- Content -->
</div>
```

### Key Components

#### 1. Cover Slide with Logo

```html
<div class="slide">
    <div style="text-align: center;">
        <div class="logo-container">
            <img src="../assets/logo/icon.png" alt="Rete Icon" class="logo-icon" />
            <img src="../assets/logo/text.png" alt="Rete" class="logo-text" />
        </div>
        <h1>Google Cloud Billing Analysis Report</h1>
        <div class="subtitle">Project: [PROJECT_NAME]</div>
        <div class="meta">Analysis Date: [DATE]</div>
        <div class="meta">Period Analyzed: [PERIOD]</div>
    </div>
</div>
```

#### 2. Statistics Cards

```html
<div class="grid">
    <div class="stat-card">
        <div class="stat-value">$XXX.XX</div>
        <div class="stat-label">Service Name</div>
        <p>Brief description</p>
    </div>
</div>
```

#### 3. Data Tables

```html
<table>
    <tr>
        <th>Metric</th>
        <th>Value</th>
    </tr>
    <tr>
        <td>Document Reads</td>
        <td>70,000,000</td>
    </tr>
</table>
```

#### 4. Warning Boxes

```html
<div class="warning">
    <p><strong>⚠️ ASSUMPTION:</strong> Without access to your source code, I cannot confirm which of these issues exist.</p>
    <p><strong>Recommended:</strong> Provide GitHub repository access to analyze...</p>
</div>
```

#### 5. Code Blocks

```html
<div class="code-block">
    <pre><code>gcloud run services update "function-name" \
  --region=us-central1 \
  --min-instances=0</code></pre>
</div>
```

#### 6. Priority Cards

```html
<div class="card priority-1">
    <h3>🔴 PRIORITY 1: [Recommendation Title]</h3>
    <p><strong>Potential Savings: $100-110/month</strong></p>
    <!-- Details -->
</div>
```

Priority levels:
- `.priority-1` - Red border (critical)
- `.priority-2` - Orange border (high)
- `.priority-3` - Yellow border (medium)

#### 7. Highlight Boxes

```html
<div class="highlight">
    <p><strong>Expected:</strong> $XXX/month → $YYY/month</p>
    <p><strong>Trade-off:</strong> [Any caveats]</p>
</div>
```

## Typical Report Flow

1. **Cover** - Logo, project name, date
2. **Executive Summary** - Total cost, top 3 drivers
3. **Findings** - One slide per finding with:
   - Verified metrics (table)
   - Issue analysis (what this means)
   - Assumptions (warning box)
4. **Recommendations** - Priority-ranked with:
   - Overview (savings, current vs target)
   - Implementation (code examples)
   - Expected results
5. **Summary** - Savings breakdown, monitoring commands
6. **Next Steps** - Action items
7. **Footer** - Contact info with logo

## Export to PDF

1. Open HTML in Chrome/Firefox
2. Print (Cmd/Ctrl + P)
3. Select "Save as PDF"
4. Settings:
   - Layout: Portrait
   - Paper size: Letter/A4
   - Margins: None
   - Background graphics: ✓ (enabled)
   - Headers/Footers: ✗ (disabled)

## Customization

### Change Branding

To use different branding:

1. Replace logo files in `assets/logo/`
2. Update logo references in HTML
3. Optionally change colors in CSS

### Adjust Layout

Key CSS variables in `report-styles.css`:
- `.slide` padding: `60px 40px`
- Font sizes: `h1` (3.5rem), `h2` (2.5rem)
- Colors: Black background (`#000000`), white text (`#ffffff`)
- Priority borders: `.priority-1` (#ff4444), etc.

## Tips

1. **One topic per slide** - Keep slides focused
2. **Visual hierarchy** - Use cards, highlights, warnings appropriately
3. **Code readability** - JetBrains Mono font for code blocks
4. **Print preview** - Always check PDF output before sharing
5. **Mobile friendly** - Template is responsive
6. **Clear assumptions** - Use warning boxes for unverified items
7. **Section numbers** - "Finding 1 of 5" helps navigation

## Template Structure

### Minimal Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCP Billing Analysis Report</title>
    <link rel="stylesheet" href="../assets/report-styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Cover Slide -->
    <div class="slide">
        <div style="text-align: center;">
            <div class="logo-container">
                <img src="../assets/logo/icon.png" alt="Logo Icon" class="logo-icon" />
                <img src="../assets/logo/text.png" alt="Logo Text" class="logo-text" />
            </div>
            <h1>Google Cloud Billing Analysis Report</h1>
            <div class="subtitle">Project: [PROJECT_NAME]</div>
            <div class="meta">Analysis Date: [DATE]</div>
        </div>
    </div>

    <!-- Executive Summary -->
    <div class="slide">
        <h2>Executive Summary</h2>
        <div class="highlight">
            <div class="stat-value" style="font-size: 3rem;">$XXX<span style="font-size: 1.5rem;">/month</span></div>
        </div>
    </div>

    <!-- Add more slides as needed -->

    <!-- Footer -->
    <div class="slide">
        <div class="footer">
            <div class="footer-logo">
                <img src="../assets/logo/icon.png" alt="Logo" class="footer-logo-icon" />
                <img src="../assets/logo/text.png" alt="Logo" class="footer-logo-text" />
            </div>
            <div><strong>Your Name</strong></div>
            <div><a href="mailto:your@email.com">your@email.com</a></div>
        </div>
    </div>
</body>
</html>
```

## Support

For questions or issues:
- GitHub: https://github.com/rete-consulting/gcp-cost-analyzer
- Email: andrii@reteconsulting.dev
