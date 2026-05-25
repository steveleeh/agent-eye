# @freely-labs/agent-eye 👁️

[![npm version](https://img.shields.io/npm/v/@freely-labs/agent-eye.svg)](https://www.npmjs.com/package/@freely-labs/agent-eye)
[![npm downloads](https://img.shields.io/npm/dm/@freely-labs/agent-eye.svg)](https://www.npmjs.com/package/@freely-labs/agent-eye)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/steveleeh/agent-eye/pulls)

🌐 **[简体中文](README_ZH.md)**

**Agent-Eye** (`@freely-labs/agent-eye`) is an intelligent visual discrepancy and layout feedback engine designed specifically for AI-generated code (Design-to-Code) workflows, automated UI testing, and self-correcting agent loops.

Traditional pixel-by-pixel diffing tools are highly fragile when dealing with minor offsets, subpixel rendering noise, or browser font differences (often leading to a completely red visual diff despite looking identical to the human eye). Agent-Eye resolves this by combining **Structural Similarity Index Measure (SSIM)** with **morphological component clustering** to detect structural shifts, misalignments, and missing elements just like a human tester would, exporting precise bounding boxes and quantitative deviation metrics in structured JSON format.

---

## ✨ Key Features

* 🧠 **Human-like Structural Perception (SSIM)**: Evaluates local texture, luminance, and contrast instead of raw pixel values. Naturally ignores font anti-aliasing noise, subpixel differences, and subtle environmental color shifts.
* 📦 **Semantic Component Clustering**: Custom morphological dilation and bounding box merging algorithms aggregate scattered pixel discrepancies into intuitive "UI Component/Block" bounding boxes.
* 📐 **Auto Canvas Alignment**: Supports automatic padding (with white margins) or smart resizing to handle dimensional differences caused by browser scrollbars, responsive viewport variations, or window sizes.
* 🎨 **Technical Visualization Dashboard**:
  * Outlines discrepancy zones labeled with color-coded **severity ratings (Critical / Warning / Info)** and error ratios.
  * Exports a sleek dark-themed composite panel: `[Design Mockup] | [Annotated Screenshot with Red Tint overlay] | [Colormap Jet Heatmap]`.
* 🤖 **AI-Agent & Self-Correcting Friendly**: Generates structured, high-fidelity **JSON reports** detailing coordinate boxes `[x, y, w, h]` and localized deviation scores. AI agents can easily parse these reports to automatically fix CSS layouts!
* 🔒 **Zero-Conflict isolated Python Setup**: The npm package automatically builds an isolated virtual environment (`.venv/`) inside the package folder during installation, keeping your global Python environment completely clean!

---

## 🛠️ Pipeline Overview

```
[Design Mockup] ──────┐
                      ├──► [Preprocessing & Alignment] ──► [SSIM Matrix Math] ──► [Threshold Masking]
[Screenshot Output] ──┘
                                                                                      │
                                                                                      ▼
[JSON Report Export] ◄─── [Local Scoring & Grading] ◄─── [Bounding Box Merging] ◄─── [Morphology Dilation]
       &
[Composite Dashboard]
```

---

## 📦 Installation & Quick Start

### A. Node.js / Front-end Ecosystem (`npm`)

If you are using JavaScript/TypeScript, visual testing frameworks (Playwright, Puppeteer, Cypress), or Node-based AI tools (e.g. Cursor, Windsurf, Claude Code):

#### 1. Global Installation
```bash
npm install -g @freely-labs/agent-eye
```
*(During installation, it automatically sets up an isolated Python virtual environment inside the package and installs necessary modules like OpenCV and scikit-image).*

#### 2. Run Globally in your Terminal
```bash
# Run the built-in synthetic test suite
agent-eye --test

# Compare design mockup vs screenshot
agent-eye --mockup mockup.png --screenshot screenshot.png
```

#### 3. Zero-Install Execution (npx)
```bash
npx @freely-labs/agent-eye --test
```

---

### B. Python / AI Ecosystem (`pip`)

If you are building Python-based AI Agents (e.g. LangChain, CrewAI, AutoGPT) or custom backend services:

#### 1. Installation
```bash
# Clone the repository
git clone https://github.com/steveleeh/agent-eye.git
cd agent-eye

# Install standard python package globally or in your virtual environment
pip install .
```

#### 2. Run Globally in your Terminal
```bash
# Run the built-in synthetic test suite
agent-eye --test
```

---

## 🖥️ Command Line Interface (CLI)

```bash
agent-eye --mockup <path_to_mockup> --screenshot <path_to_screenshot> [options...]
```

### Options:

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--mockup` | `str` | - | Path to the original design mockup/draft. |
| `--screenshot`| `str` | - | Path to the screenshot generated from the code. |
| `--align` | `str` | `pad` | Canvas alignment method: `pad` (pad with white boundaries to keep aspect ratios) or `resize` (scale/stretch). |
| `--threshold` | `int` | `30` | SSIM difference threshold (0-255). Lower is more sensitive. Default: `30` (~12% discrepancy). |
| `--dilation` | `int` | `18` | Morphological dilation kernel size (pixels). Larger values merge nearby pixel differences. |
| `--min-area` | `int` | `35` | Minimum pixel area to filter out tiny noise (e.g. anti-aliasing artifacts). |
| `--merge-dist`| `int` | `20` | Maximum pixel distance to merge nearby bounding boxes. |
| `--out-panel` | `str` | `diff_panel.png`| Output path for the side-by-side dashboard panel. |
| `--out-json` | `str` | `diff_report.json`| Output path for the JSON discrepancy metadata. |

---

## 🐍 Python SDK Integration API

You can easily integrate Agent-Eye into your own AI Agent loops, visual testing suites, or backend servers:

```python
from agent_eye import ImageCompareEngine, ImageCompareVisualizer
import cv2

# 1. Initialize the engine with custom thresholds
engine = ImageCompareEngine(
    threshold=30,      # Sensitivity threshold
    dilation_size=18,  # Morphological clustering expansion
    min_area=35,       # Anti-noise area size
    merge_dist=20      # Coordinate merging span
)

# 2. Run visual difference comparison
results = engine.compare("path/to/design.png", "path/to/screenshot.png", align_method="pad")

# 3. Read overall summary metrics
print(f"Overall SSIM Index: {results['overall_similarity'] * 100:.2f}%")
print(f"Total Discrepant Regions Found: {len(results['regions'])}")

# 4. Traverse the detected layout/color mismatches
for reg in results["regions"]:
    print(f"Region ID: #{reg['id']} | Severity: {reg['severity']}")
    print(f"Coordinates [x, y, w, h]: {reg['box']}")
    print(f"Local Area Error Ratio: {reg['mismatch_ratio'] * 100:.1f}%")
    print(f"Mean BGR Color absolute difference (MAE): {reg['mean_color_diff']:.2f}")

# 5. Generate and save annotated image
annotated_img = ImageCompareVisualizer.draw_annotated_image(
    results["img2_aligned"], 
    results["regions"], 
    thresh_mask=results["thresh_mask"]
)
cv2.imwrite("annotated_output.png", annotated_img)
```

---

## 📊 Exported JSON Schema (`diff_report.json`)

The generated JSON file provides highly readable, structured debug clues for Large Language Models or Vision-Language Models:

```json
{
    "overall_similarity_score": 0.9686,
    "overall_mismatch_percentage": 3.512,
    "regions_detected_count": 5,
    "mismatched_regions": [
        {
            "id": 2,
            "box": [59, 219, 174, 54],
            "mismatch_ratio": 0.4082,
            "mean_color_diff": 55.018,
            "severity": "Critical"
        },
        {
            "id": 3,
            "box": [459, 158, 178, 37],
            "mismatch_ratio": 0.3831,
            "mean_color_diff": 9.413,
            "severity": "Warning"
        }
    ]
}
```

*   `box`: `[x, y, width, height]` coordinates of the visual mismatch area.
*   `mismatch_ratio`: Proportion of mismatched pixels inside this box (0.0 to 1.0).
*   `severity`: Discrepancy severity classification (**Critical / Warning / Info**) automatically graded using mismatch ratio and color variance.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Feel free to fork, distribute, or open Pull Requests!
