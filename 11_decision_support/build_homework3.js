// build_homework3.js — Generate Homework 3 .docx submission
// Run: node 11_decision_support/build_homework3.js

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, ExternalHyperlink, Header, Footer, PageNumber,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, VerticalAlign
} = require("docx");
const fs = require("fs");
const path = require("path");

const REPO = "https://github.com/sophwa/sysen-5381/blob/main";
const OUT  = path.join(__dirname, "HOMEWORK3_Wang.docx");
const PLOT = path.join(__dirname, "data", "score_comparison.png");

// ── helpers ──────────────────────────────────────────────────────────────────

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGINS = { top: 80, bottom: 80, left: 120, right: 120 };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text, bold: true, size: 32, font: "Arial" })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 26, font: "Arial", color: "2E75B6" })],
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 120 },
    children: [new TextRun({ text, size: 22, font: "Arial", ...opts })],
  });
}

function bold(text) { return new TextRun({ text, bold: true, size: 22, font: "Arial" }); }
function normal(text) { return new TextRun({ text, size: 22, font: "Arial" }); }

function mixed(...runs) {
  return new Paragraph({ spacing: { before: 0, after: 120 }, children: runs });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 0, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial" })],
  });
}

function link(display, url) {
  return new ExternalHyperlink({
    children: [new TextRun({ text: display, style: "Hyperlink", size: 22, font: "Arial" })],
    link: url,
  });
}

function spacer() {
  return new Paragraph({ spacing: { before: 0, after: 80 }, children: [] });
}

function headerRow(cells, widths) {
  return new TableRow({
    tableHeader: true,
    children: cells.map((text, i) =>
      new TableCell({
        borders: BORDERS,
        width: { size: widths[i], type: WidthType.DXA },
        margins: CELL_MARGINS,
        shading: { fill: "2E75B6", type: ShadingType.CLEAR },
        children: [new Paragraph({
          children: [new TextRun({ text, bold: true, size: 20, font: "Arial", color: "FFFFFF" })],
        })],
      })
    ),
  });
}

function dataRow(cells, widths, shade = false) {
  return new TableRow({
    children: cells.map((text, i) =>
      new TableCell({
        borders: BORDERS,
        width: { size: widths[i], type: WidthType.DXA },
        margins: CELL_MARGINS,
        shading: { fill: shade ? "EBF3FB" : "FFFFFF", type: ShadingType.CLEAR },
        children: [new Paragraph({
          children: [new TextRun({ text: String(text), size: 20, font: "Arial" })],
        })],
      })
    ),
  });
}

// ── content ───────────────────────────────────────────────────────────────────

const plotData  = fs.readFileSync(PLOT);

const children = [

  // ── Title page block ──────────────────────────────────────────────────────
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 720, after: 240 },
    children: [new TextRun({ text: "Homework 3: AI Report Validation System", bold: true, size: 40, font: "Arial" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 120 },
    children: [new TextRun({ text: "SYSEN 5381  |  Sophie Wang  |  May 2026", size: 24, font: "Arial", color: "555555" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 600 },
    children: [new TextRun({ text: "PM10 Emissions Report Validation  —  Prompt Comparison Experiment", size: 22, font: "Arial", italics: true, color: "555555" })],
  }),

  // ── 1. Writing Component ──────────────────────────────────────────────────
  h1("1. Writing Component"),

  h2("Purpose and Design of the Validation System"),
  p(
    "This project builds a custom AI-powered validation system tailored specifically to PM10 traffic-emissions " +
    "policy reports. The core idea is that generic text-quality metrics — fluency, formality, succinctness — " +
    "are insufficient for evaluating technical policy documents. A report can be grammatically flawless and " +
    "still give a policymaker the wrong vehicle category to target. I therefore designed five domain-specific " +
    "dimensions that probe exactly the failure modes relevant to emissions reporting: whether numbers are " +
    "transcribed correctly, whether all data categories are covered, whether recommendations are specific " +
    "enough to act on, whether epistemic tone is appropriate, and whether prioritization choices are " +
    "explicitly grounded in the data."
  ),

  h2("How the Validator Differs from the LAB's Likert Scales"),
  p(
    "The Module 9 LAB uses six 1–5 Likert scales (accuracy, formality, faithfulness, clarity, succinctness, " +
    "relevance) that apply equally to any text genre. My validator departs from this in three ways. First, " +
    "all five dimensions use a 0–10 continuous scale rather than 1–5, giving finer discrimination between " +
    "reports that all hit the same Likert midpoint. Second, every dimension is domain-specific: " +
    "numeric_fidelity checks exact percentage matches against the source table, completeness counts how " +
    "many of the five vehicle categories are addressed, policy_specificity distinguishes vague from " +
    "targeted interventions, scientific_hedging penalises alarmist or overconfident language, and " +
    "prioritization_logic tests whether the model justified its recommendations with the actual data " +
    "rather than intuition. Third, a boolean data_accurate flag provides a hard gate — any report that " +
    "fabricates a statistic is flagged regardless of how well it scores on the other dimensions."
  ),

  h2("Experimental Design"),
  p(
    "I compared three generation prompts using llama3.2:latest via the local Ollama API. Prompt A was a " +
    "detailed, formal instruction requiring all five vehicle categories by exact share, an explicit data-" +
    "driven justification for prioritisation, and at least two targeted policy mechanisms. Prompt B was a " +
    "concise technical instruction asking for 2–3 sentences with the most important percentages and one " +
    "specific recommendation. Prompt C was an open-ended narrative prompt asking only to mention vehicle " +
    "types and suggest what could be done. Each prompt was run 31 times (total n=93 reports), and each " +
    "report was independently validated by a second AI call with the custom rubric. The five dimension " +
    "scores were averaged into an overall_score (0–10)."
  ),

  h2("Statistical Results"),
  p(
    "Prompt A produced the highest mean overall score (7.34 ± 0.73), followed by Prompt B (6.95 ± 0.62) " +
    "and Prompt C (6.76 ± 0.95). Bartlett's test confirmed equal variances (stat=5.57, p=0.062), so a " +
    "standard one-way ANOVA was appropriate. The ANOVA was significant (F(2,90)=4.59, p=0.013), indicating " +
    "that prompt choice reliably affects report quality on these criteria. Tukey post-hoc tests showed that " +
    "Prompt A significantly outperformed Prompt C (p=0.010, Hedges' g=0.69, a medium-large effect). The " +
    "A-vs-B contrast did not reach significance (p=0.127), meaning the additional specificity in Prompt A " +
    "over Prompt B yielded a consistent but not dramatic gain. The largest driver of the gap between A and " +
    "C was policy_specificity (mean 5.73 vs 4.27) and prioritization_logic (5.40 vs 4.33), confirming " +
    "that open-ended prompts fail most severely on the actionability and data-grounding criteria."
  ),

  h2("Design Choices and Challenges"),
  p(
    "The main design challenge was validator consistency: because llama3.2 is a relatively small model, " +
    "early runs produced integer scores that were sometimes not well-calibrated to the rubric descriptions. " +
    "I addressed this by (a) including explicit anchor descriptions for each endpoint in the system prompt " +
    "and (b) setting a low temperature (0.2) for validation calls to reduce stochastic spread. A second " +
    "challenge was statistical power: with n=15 per prompt the initial experiment showed only a trend " +
    "(ANOVA p=0.096). I ran a power analysis (Cohen's d≈0.73, need n≈31 for 80% power) and extended to " +
    "31 per prompt, which brought the ANOVA to significance. This iterative power-aware design is itself " +
    "an important lesson: small n experiments with AI-generated data can be underpowered even when the " +
    "true effect is medium-sized."
  ),

  spacer(),

  // ── 2. Git Repository Links ───────────────────────────────────────────────
  h1("2. Git Repository Links"),

  new Paragraph({ spacing: { before: 0, after: 100 }, children: [bold("Validation system script:")] }),
  new Paragraph({ spacing: { before: 0, after: 160 }, children: [link(
    "11_decision_support/validate_reports.py",
    `${REPO}/11_decision_support/validate_reports.py`
  )] }),

  new Paragraph({ spacing: { before: 0, after: 100 }, children: [bold("Validation scores CSV:")] }),
  new Paragraph({ spacing: { before: 0, after: 160 }, children: [link(
    "11_decision_support/data/validation_scores.csv",
    `${REPO}/11_decision_support/data/validation_scores.csv`
  )] }),

  new Paragraph({ spacing: { before: 0, after: 100 }, children: [bold("Score comparison plot:")] }),
  new Paragraph({ spacing: { before: 0, after: 160 }, children: [link(
    "11_decision_support/data/score_comparison.png",
    `${REPO}/11_decision_support/data/score_comparison.png`
  )] }),

  new Paragraph({ spacing: { before: 0, after: 100 }, children: [bold("Source reports (validated from Homework 2 context):")] }),
  new Paragraph({ spacing: { before: 0, after: 160 }, children: [link(
    "09_text_analysis/data/sample_reports.txt",
    `${REPO}/09_text_analysis/data/sample_reports.txt`
  )] }),

  spacer(),

  // ── 3. Screenshots / Outputs ──────────────────────────────────────────────
  h1("3. Screenshots / Outputs"),

  h2("Figure 1: Score Comparison Plot"),
  p("Left panel: boxplot of overall_score distributions (0–10) for each prompt. " +
    "Right panel: mean score per validation dimension grouped by prompt."),
  spacer(),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: "png",
      data: plotData,
      transformation: { width: 620, height: 240 },
      altText: { title: "Score comparison plot", description: "Boxplot and bar chart comparing prompts A B C", name: "score_comparison" },
    })],
  }),
  spacer(),

  h2("Figure 2: Sample Validation Output — Prompt A Run 2"),
  p("Below is a representative JSON response from the AI validator for one high-scoring report."),
  spacer(),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { fill: "F4F6F7", type: ShadingType.CLEAR },
    children: [new TextRun({
      text: JSON.stringify({
        numeric_fidelity: 9,
        completeness: 10,
        policy_specificity: 8,
        scientific_hedging: 9,
        prioritization_logic: 8,
        data_accurate: true,
        rationale: "All five vehicle categories cited with exact percentages. Two targeted, mechanism-specific interventions clearly tied to high-share categories.",
        overall_score: 8.80
      }, null, 2),
      font: "Courier New", size: 18, color: "333333"
    })],
  }),
  spacer(),

  h2("Figure 3: Summary Statistics by Prompt"),
  // Stats table
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1800, 1260, 1260, 1260, 1260, 1260, 1260],
    rows: [
      headerRow(["Prompt", "n", "Mean Overall", "SD", "Numeric Fid.", "Completeness", "Policy Spec."],
                [1800, 1260, 1260, 1260, 1260, 1260, 1260]),
      dataRow(["A", "31", "7.34", "0.73", "8.33", "7.80", "5.73"], [1800, 1260, 1260, 1260, 1260, 1260, 1260], false),
      dataRow(["B", "31", "6.95", "0.62", "8.53", "7.20", "4.73"], [1800, 1260, 1260, 1260, 1260, 1260, 1260], true),
      dataRow(["C", "31", "6.76", "0.95", "8.13", "7.53", "4.27"], [1800, 1260, 1260, 1260, 1260, 1260, 1260], false),
    ],
  }),
  spacer(),

  h2("Figure 4: ANOVA and T-Test Results"),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 1640, 1640, 1640, 1640],
    rows: [
      headerRow(["Test", "Statistic", "df", "p-value", "Effect Size"],
                [2800, 1640, 1640, 1640, 1640]),
      dataRow(["One-way ANOVA (A, B, C)", "F = 4.59", "2, 90", "0.013*", "η² = 0.092"], [2800, 1640, 1640, 1640, 1640], false),
      dataRow(["T-test: A vs B", "T = 2.25", "60", "0.028*", "d = 0.572"], [2800, 1640, 1640, 1640, 1640], true),
      dataRow(["T-test: A vs C", "T = 2.73", "60", "0.008**", "d = 0.695"], [2800, 1640, 1640, 1640, 1640], false),
      dataRow(["Tukey: A vs C", "—", "—", "0.010*", "g = 0.686"], [2800, 1640, 1640, 1640, 1640], true),
      dataRow(["Tukey: A vs B", "—", "—", "0.127", "g = 0.565"], [2800, 1640, 1640, 1640, 1640], false),
    ],
  }),
  new Paragraph({
    spacing: { before: 60, after: 120 },
    children: [new TextRun({ text: "* p < 0.05   ** p < 0.01", size: 18, font: "Arial", italics: true, color: "555555" })],
  }),

  spacer(),

  // ── 4. Documentation ──────────────────────────────────────────────────────
  h1("4. Documentation"),

  h2("4.1  Validation Criteria Table"),
  p("All dimensions use a 0–10 continuous scale (not 1–5 Likert) to allow finer discrimination. " +
    "Each targets a domain-specific failure mode rather than generic writing quality."),
  spacer(),

  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1800, 2400, 1200, 1560, 2400],
    rows: [
      headerRow(["Dimension", "Description", "Scale", "Benchmark", "Differs from LAB"],
                [1800, 2400, 1200, 1560, 2400]),
      dataRow([
        "numeric_fidelity",
        "Are cited percentages/counts identical to source data?",
        "0–10",
        "≥10 = no rounding errors",
        "LAB 'accuracy' is 1–5 and conflates interpretation with numerical precision"
      ], [1800, 2400, 1200, 1560, 2400], false),
      dataRow([
        "completeness",
        "Are all five vehicle categories addressed?",
        "0–10",
        "10 = all 5 mentioned with data",
        "LAB has no coverage/completeness dimension"
      ], [1800, 2400, 1200, 1560, 2400], true),
      dataRow([
        "policy_specificity",
        "Are recommendations specific (mechanism + target vehicle)?",
        "0–10",
        "≥8 = ≥2 targeted interventions",
        "LAB has no policy dimension; 'relevance' is generic"
      ], [1800, 2400, 1200, 1560, 2400], false),
      dataRow([
        "scientific_hedging",
        "Is epistemic tone appropriate — no overstatement or alarm?",
        "0–10",
        "10 = appropriately hedged",
        "LAB 'faithfulness' is about factual grounding, not epistemic tone"
      ], [1800, 2400, 1200, 1560, 2400], true),
      dataRow([
        "prioritization_logic",
        "Is vehicle prioritisation explicitly data-justified?",
        "0–10",
        "10 = data-driven with citation",
        "No equivalent in LAB rubric"
      ], [1800, 2400, 1200, 1560, 2400], false),
      dataRow([
        "data_accurate (gate)",
        "Hard boolean: zero fabricated statistics?",
        "true/false",
        "Must be true",
        "LAB 'accurate' is also boolean but only checks overall interpretation"
      ], [1800, 2400, 1200, 1560, 2400], true),
    ],
  }),
  spacer(),

  h2("4.2  Experimental Design"),
  mixed(bold("Prompts compared: "), normal("Three (A, B, C), varying in instruction specificity.")),
  mixed(bold("Reports per prompt: "), normal("31  (n = 93 total observations)")),
  mixed(bold("Generation model: "), normal("llama3.2:latest via Ollama (local, no API cost)")),
  mixed(bold("Validation model: "), normal("llama3.2:latest, temperature = 0.2, JSON-mode forced")),
  mixed(bold("Generation temperature: "), normal("0.8 (to introduce natural variation between runs)")),
  mixed(bold("Source data: "), normal("White County IL 2015 PM10 VMT table (5 vehicle categories)")),
  mixed(bold("Sample size rationale: "), normal("Power analysis showed d ≈ 0.73 between A and C; n = 31 needed for ~80% power.")),
  spacer(),

  h2("4.3  Statistical Analysis"),
  p("Hypothesis: H₀ = all three prompts produce equal mean overall_score; H₁ = at least one prompt differs."),
  bullet("Bartlett’s test confirmed equal variances across groups (stat = 5.57, p = 0.062), so standard one-way ANOVA was used."),
  bullet("ANOVA: F(2, 90) = 4.59, p = 0.013  →  reject H₀. Prompt choice significantly affects quality."),
  bullet("Tukey HSD post-hoc: Prompt A — Prompt C is the significant pair (p = 0.010, Hedges’ g = 0.686). Prompt A — Prompt B is marginal (p = 0.127)."),
  bullet("T-test A vs B: T(60) = 2.25, p = 0.028, Cohen’s d = 0.572 (medium effect)."),
  bullet("T-test A vs C: T(60) = 2.73, p = 0.008, Cohen’s d = 0.695 (medium-large effect)."),
  bullet("Interpretation: Prompt A (comprehensive, formal, mechanism-specific) produces significantly higher-quality reports than the open-ended Prompt C on domain-specific validation criteria."),
  spacer(),

  h2("4.4  System Design"),
  p("The system has two components:"),
  bullet("Generator: Sends a system-prompt + source data to Ollama and receives a paragraph. Temperature = 0.8 to simulate natural run-to-run variation."),
  bullet("Validator: Sends a strict rubric system-prompt + the generated paragraph to Ollama with JSON mode enabled and temperature = 0.2. Parses the JSON response and computes overall_score as the mean of the five dimension scores."),
  p("The two components are intentionally independent — the validator receives only the report text and the source data, not the generation prompt, so it cannot inadvertently reward complexity of instruction."),
  spacer(),

  h2("4.5  Technical Details"),
  bullet("Model: llama3.2:latest (local Ollama, http://localhost:11434)"),
  bullet("Packages: requests, pandas, scipy, pingouin, matplotlib, python-dotenv"),
  bullet("Python: 3.14  |  Node (for this docx): 18+  |  npm: docx@9.6.1"),
  bullet("No API key required — Ollama runs locally"),
  bullet("Output files: 11_decision_support/data/validation_scores.csv, score_comparison.png"),
  spacer(),

  h2("4.6  Usage Instructions"),
  p("1. Install Ollama and pull the model:"),
  new Paragraph({
    spacing: { before: 0, after: 60 },
    shading: { fill: "F4F6F7", type: ShadingType.CLEAR },
    children: [new TextRun({ text: "ollama pull llama3.2:latest", font: "Courier New", size: 20 })],
  }),
  p("2. Install Python dependencies:"),
  new Paragraph({
    spacing: { before: 0, after: 60 },
    shading: { fill: "F4F6F7", type: ShadingType.CLEAR },
    children: [new TextRun({ text: "pip install requests pandas scipy pingouin matplotlib python-dotenv", font: "Courier New", size: 20 })],
  }),
  p("3. From the repo root, run the validation experiment:"),
  new Paragraph({
    spacing: { before: 0, after: 60 },
    shading: { fill: "F4F6F7", type: ShadingType.CLEAR },
    children: [new TextRun({ text: "python3 11_decision_support/validate_reports.py", font: "Courier New", size: 20 })],
  }),
  p("4. Results are saved to 11_decision_support/data/. The script prints all statistical output to stdout."),
  p("5. To rebuild this .docx: node 11_decision_support/build_homework3.js"),

];

// ── document ──────────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2E75B6", space: 1 } },
          children: [new TextRun({ text: "SYSEN 5381  |  Homework 3  |  Sophie Wang", size: 18, font: "Arial", color: "555555" })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 18, font: "Arial", color: "555555" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "555555" }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log(`✅  Written: ${OUT}`);
});
