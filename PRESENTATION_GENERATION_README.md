# PowerPoint Presentation Generation

This document explains how to generate the `.pptx` file from the markdown presentation content.

## Prerequisites

1. **Python 3.7+** installed
2. **python-pptx** library installed

## Installation

Install the required library:

```bash
pip install python-pptx
```

Or if using a virtual environment:

```bash
python3 -m pip install python-pptx
```

## Generation

Run the script to generate the PowerPoint presentation:

```bash
python3 scripts/create_presentation.py
```

The script will:
- Read `HACKATHON_PRESENTATION.md`
- Parse all 15 slides
- Create a formatted PowerPoint presentation
- Save it as `Hackathon_Presentation.pptx` in the project root

## Output

The generated file will be:
- **Location:** `Hackathon_Presentation.pptx`
- **Format:** PowerPoint (.pptx) compatible with Microsoft PowerPoint, Google Slides, and LibreOffice
- **Total Slides:** 15 slides (Title + 14 content slides)

## Slide Structure

1. **Title Slide** - Project name, tagline, team, hackathon
2. **Problem Background** - Current challenges and why traditional solutions fail
3. **Core Challenge** - What needs to be built and why multi-agent system is required
4. **Proposed Solution Overview** - High-level description and team behavior
5. **Primary Use Case** - Real-world scenario and impact
6. **Agentic AI Capabilities** - RAG, chunking, memory, guardrails, planning
7. **Agent Roles & Responsibilities** - All 8 agents detailed
8. **System Architecture** - Agent interaction flow with diagram
9. **Sample Scenarios** - Three real-world examples
10. **Observability & Explainability** - Live execution and transparency
11. **Expected Hackathon Outcome** - What judges should see
12. **Conclusion** - Key takeaways and why it stands out
13. **Technical Stack** - Core technologies and architecture
14. **Demo Flow** - Live demonstration steps
15. **Q&A** - Contact information

## Customization

To customize the presentation:

1. **Edit Content:** Modify `HACKATHON_PRESENTATION.md`
2. **Edit Diagrams:** Modify `PRESENTATION_DIAGRAMS.md`
3. **Regenerate:** Run `python3 scripts/create_presentation.py` again

## Troubleshooting

### Import Error
If you see `ModuleNotFoundError: No module named 'pptx'`:
```bash
pip install python-pptx
```

### Permission Errors
If you encounter permission errors:
```bash
python3 -m pip install --user python-pptx
```

### File Not Found
Ensure you're running from the project root:
```bash
cd /path/to/Prompt-Pirates-Hackathon-2026
python3 scripts/create_presentation.py
```

## Manual Alternative

If you prefer to create the presentation manually:

1. Open PowerPoint, Google Slides, or LibreOffice Impress
2. Use `HACKATHON_PRESENTATION.md` as content reference
3. Use `PRESENTATION_DIAGRAMS.md` for visual diagrams
4. Apply the color scheme from the diagrams file

## Color Scheme

- **Primary Agents:** #4A90E2 (Blue)
- **Parallel Execution:** #F5A623 (Orange)
- **Guardrails/Safety:** #D0021B (Red)
- **Memory/Storage:** #7ED321 (Green)
- **Observability:** #9013FE (Purple)
- **Input/Output:** #50E3C2 (Teal)

## Notes

- The script automatically formats bullet points, headers, and paragraphs
- Diagrams are included as monospace text (can be replaced with visual diagrams manually)
- All slides use consistent formatting and color scheme
- The presentation is ready for hackathon judges and technical audiences
