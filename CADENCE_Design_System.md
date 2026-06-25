Your Markdown design file is ready for use in GitHub Copilot and other AI coding tools.

[file-tag: code-generated-file-0-1781922843920871678]

Below is the complete text of the configuration file. It implements your explicit design constraints, defines color-combination recipes specific to climate/infrastructure modeling, maps out the accessibility parameters, and contains boilerplate styles for **Matplotlib/Seaborn**, **Plotly**, and **Tailwind CSS** to make it immediately actionable for your data pipelines and tools.

***

```markdown
# CIRCAD CADENCE Project Design System & Code Generation Guide
This system prompt defines the visual language, color palette, typography, layout behavior, and interactive constraints for the **CADENCE (Climate-Driven Aging and Dynamic Vulnerability Modeling for Resilient Investment Planning)** project under **CIRCAD**. 

Use this document as an explicit reference file in GitHub Copilot, Cursor, or Gemini prompts to ensure all generated code, user interfaces, dashboards, and data visualizations match strict production-grade standards.

---

## 1. Core Visual Identity & Context
- **Organization:** Center for Innovative Resilience and Climate Adaptation (CIRCAD) — Duke University & University of Georgia.
- **Project:** CADENCE (Climate-Driven Aging and Dynamic Vulnerability Modeling for Resilient Investment Planning).
- **Core Domain:** Climate risk modeling, infrastructure asset degradation, stochastic life-cycle analysis, and resilience investment engineering.
- **Aesthetic Tone:** Scientific, data-dense, highly authoritative, clean, and modern. Avoid generic web UI elements; prioritize explicit technical clarity.

---

## 2. Color Palette Tokens

### Primary Palette (The CADENCE Triad)
CADENCE layouts rely dominantly on the Teal, Grey, and Tan tokens to represent infrastructure, stable baselines, and environmental/aging parameters.

| Token Name | Hex Code | Applied Role | Accessibility / Contrast Note |
| :--- | :--- | :--- | :--- |
| **CADENCE Teal** | `#2F8F7F` | Signature brand color, main UI borders, active states, key data series. | Large text only on light bg. Use for structural components. |
| **CADENCE Grey** | `#333333` | Dominant text color (Ink), heavy structural lines, deep grid anchors. | Pass ≥4.5:1 on White/Ice Blue. Never use light gray for body prose. |
| **CADENCE Tan** | `#D9A341` | Asset degradation markers, financial values, moderate risk warnings. | Do not use for standalone text. Pair with Dark Grey text overlays. |

### Supporting & Secondary Palette
Weave in Blue and Ice Blue for structural depth, water/climate metrics, and secondary layout layers.

| Token Name | Hex Code | Applied Role | Accessibility / Contrast Note |
| :--- | :--- | :--- | :--- |
| **CIRCAD Blue** | `#205196` | Corporate/Institutional accents, primary buttons, water/flooding vectors. | High contrast. Suitable for subheadings and emphasis. |
| **Light Blue** | `#6FA8DC` | Secondary data lines, uncertainty bounds, capacity limits. | Use against dark backgrounds or as a filled area/bar. |
| **Ice Blue** | `#E9ECEF` | Global page background, table header tinting, container backdrops. | Base layer. Pair exclusively with `#333333` body text. |

### Accent & Alert Palette
Use sparingly for extreme value statistics, severe threshold breaches, or high-dimensional classification.

| Token Name | Hex Code | Applied Role | Accessibility / Contrast Note |
| :--- | :--- | :--- | :--- |
| **CIRCAD Red** | `#AA2634` | System failure, extreme climate events, critical risk, structural damage. | High visibility. Use exclusively for warning/error alerts. |
| **CIRCAD Purple** | `#673399` | NASA/Satellite data layers, multi-dimensional interactions, secondary metrics. | Use for distinct categorical separation in charts. |

---

## 3. Data Visualization & Color Combination Recipes

When writing visualization code (Matplotlib, Plotly, Seaborn, Streamlit, or D3.js), apply these specific color combination matrices to represent data semantics accurately:

### A. Categorical / Unrelated Series Mapping
For mapping independent asset classes, climate hazards, or model scenarios:
1. **Series 1 (Primary):** CADENCE Teal (`#2F8F7F`)
2. **Series 2:** CIRCAD Blue (`#205196`)
3. **Series 3:** CADENCE Tan (`#D9A341`)
4. **Series 4:** CIRCAD Purple (`#673399`)
5. **Series 5:** Light Blue (`#6FA8DC`)

### B. Sequential Scales (Asset Aging & Degradation)
For representing continuous variables like cumulative structural wear, time-series projections, or degradation over 50–100 years:
- **Start (New/Healthy):** Ice Blue (`#E9ECEF`) or Light Blue (`#6FA8DC`)
- **Midpoint (Aging):** CADENCE Teal (`#2F8F7F`)
- **End (Severe Degradation):** CADENCE Grey (`#333333`)

### C. Diverging / Risk Scales (Vulnerability & Threshold Breaches)
For climate hazard vulnerability modeling, failure curves, and cost-benefit optimization:
- **Low Risk / High Resilience:** CADENCE Teal (`#2F8F7F`)
- **Moderate Risk / Inflection Point:** CADENCE Tan (`#D9A341`)
- **Critical Risk / Asset Failure:** CIRCAD Red (`#AA2634`)

---

## 4. Typography & Iconography Rules

### Core Typography Matrix
- **UI & Visualization Engine Text:** Use a clean, robust, geometric or humanist sans-serif family (`Inter`, `system-ui`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `Arial`).
- **Body Prose Constraints:**
  - Limit paragraph line lengths strictly to **65–75 characters (ch)** to optimize technical readability.
  - Set `text-wrap: pretty` on all paragraph selectors to completely eliminate orphaned words.
- **Headings (H1, H2, H3):**
  - Apply `text-wrap: balance` to ensure clean multi-line header layouts.
  - **Display Heading Ceiling:** Limit font sizes using CSS `clamp()` up to a maximum ceiling of `6rem` (~96px). Anything higher compromises technical layout polish.
  - **Letter-Spacing Floor:** For large bold display headings, never drop below a letter-spacing floor of `-0.04em`. Tight letters must never touch.

### Iconography: Font Awesome 6 Free
Use **Font Awesome 6 Free** strictly for functional user interface indicators, metadata callouts, and chart control buttons. Do not use icons as standalone design decoration.
- **Implementation Syntax Examples:**
  - Asset/Infrastructure: `<i class="fa-solid fa-building-shield"></i>`
  - Climate/Weather: `<i class="fa-solid fa-cloud-sun-rain"></i>`
  - Time/Stochastic Iterations: `<i class="fa-solid fa-timeline"></i>`
  - Chart/Data Layer: `<i class="fa-solid fa-chart-line"></i>`
  - Risk/Alert: `<i class="fa-solid fa-triangle-exclamation"></i>`

---

## 5. UI Layout & Structural Framework

- **Layout Grid Controls:**
  - Use **Flexbox** for one-dimensional layouts (toolbars, metadata rows, control panels) and use `flex-wrap` where applicable instead of forcing structural grids.
  - Use **CSS Grid** for two-dimensional dashboards. For responsive grids without break-points, always use the automated fluid syntax:
    ```css
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    ```
- **Component Structures:**
  - **Anti-Pattern Ban:** Avoid generic container cards unless absolutely necessary to isolate distinct analytical models. **Nested cards are strictly banned.**
  - **Z-Index Architectural Scale:** Never assign arbitrary z-index values (e.g., `999` or `9999`). Utilize this rigid semantic scale:
    1. Dropdowns / Popovers: `z-index: 1000;`
    2. Sticky Navigation / Section Headers: `z-index: 1010;`
    3. Modal Backdrop Layers: `z-index: 1020;`
    4. Modals / Dialog Windows: `z-index: 1030;`
    5. Toast Notification System: `z-index: 1040;`
    6. System Tooltips: `z-index: 1050;`

---

## 6. Interaction, Motion, & Animation Constraints

- **Hard Ban on Image Hover Animations:** Never animate `<img>` elements or their direct child visual vectors on pointer hover state. This includes Tailwind patterns like `group-hover:scale-*` or manual CSS transformations. To provide interactive UI feedback on a component, animate the parent container's background color, border color, or shadow layer instead.
- **Dropdown Overflows:** Do not render custom `position: absolute` dropdown menus inside containers configured with `overflow: hidden` or `overflow: auto`, as this clips critical data selectors. Use the native HTML `<dialog>` element, the modern Popover API, or `position: fixed` contexts.
- **Motion Profiles:**
  - All transitions must use smooth, premium exponential easing profiles rather than standard linear values.
  - **Approved Timing Functions:** `cubic-bezier(0.16, 1, 0.3, 1)` (easeOutExpo) or `cubic-bezier(0.25, 1, 0.5, 1)` (easeOutQuart).
  - **Strict Ban:** No bounce, no elastic overshoots, and no generic linear/uniform animation curves.
- **Accessibility & Motion Gating:**
  - Every animation loop or structural transition codeblock must include an explicit fallback context honoring user system parameters:
    ```css
    @media (prefers-reduced-motion: reduce) {
      /* Force instant state transition or basic alpha opacity crossfade */
      .animated-component {
        animation: none !important;
        transition: opacity 150ms ease-in-out !important;
      }
    }
    ```
  - Content visibility must never be dependent on active JavaScript transition events. Components must render fully visible by default and use motion strictly as an elective enhancement layer.

---

## 7. Standard Code Snippets for Immediate Injection

### A. Python Matplotlib & Seaborn Global Configuration
```python
import matplotlib.pyplot as plt
import seaborn as sns

def apply_cadence_plot_style():
    # Define Explicit CADENCE Hex Hex-Tokens
    cadence_colors = {
        'teal': '#2F8F7F',
        'grey': '#333333',
        'tan': '#D9A341',
        'blue': '#205196',
        'light_blue': '#6FA8DC',
        'ice_blue': '#E9ECEF',
        'red': '#AA2634',
        'purple': '#673399'
    }
    
    # Establish Global RcParams
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Inter', 'DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['text.color'] = cadence_colors['grey']
    plt.rcParams['axes.labelcolor'] = cadence_colors['grey']
    plt.rcParams['xtick.color'] = cadence_colors['grey']
    plt.rcParams['ytick.color'] = cadence_colors['grey']
    
    plt.rcParams['axes.edgecolor'] = '#CCCCCC'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.color'] = cadence_colors['ice_blue']
    plt.rcParams['grid.alpha'] = 0.7
    
    # Register Custom Palette Matrix
    custom_palette = [
        cadence_colors['teal'],
        cadence_colors['blue'],
        cadence_colors['tan'],
        cadence_colors['purple'],
        cadence_colors['light_blue']
    ]
    sns.set_palette(sns.color_palette(custom_palette))
    
    print("CADENCE design token environment initialized for Matplotlib.")

# Execute inline prior to rendering charts
apply_cadence_plot_style()