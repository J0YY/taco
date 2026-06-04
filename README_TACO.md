# TACO - The Autonomous Casualty Office

TACO is a self-contained hackathon demo of learned-policy liability insurance for robotics. It prices a conditional quote using replayable robot failure certificates, deterministic internal model risk traces, required runtime controls, exclusions, and binder generation. The investor thesis is that TACO can become the evidence layer that makes frontier robot autonomy insurable before claims history exists.

```bash
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py
```

See `taco_demo/README.md` for the full MVP spec, architecture, metric formulas, quote logic, and demo script.
