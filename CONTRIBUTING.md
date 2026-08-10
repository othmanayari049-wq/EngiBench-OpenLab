# Contributing to EngiBench OpenLab

Contributions from students, educators, embedded developers, and robotics enthusiasts are welcome.

## Local development

```bash
git clone https://github.com/othmanayari049-wq/EngiBench-OpenLab.git
cd EngiBench-OpenLab
python -m venv .venv
```

Activate the environment, then install the project:

```bash
pip install -e ".[dev]"
pytest
streamlit run app.py
```

## Contribution workflow

1. Open or choose an issue.
2. Create a focused branch.
3. Add tests for behavior changes when practical.
4. Run `pytest` and `ruff check .`.
5. Open a pull request explaining the engineering problem and your solution.

Please keep new hardware integrations modular and avoid introducing cloud dependencies for core telemetry features unless they are optional.
