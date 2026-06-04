# TACO - The Autonomous Casualty Office

TACO is a self-contained hackathon demo layered on top of DreamAudit. It demonstrates conditional learned-policy liability insurance for robotics, priced using DreamAudit replayable failure certificates and internal model risk signatures.

```bash
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py
```

See `taco_demo/README.md` for the full PRD, architecture, data contracts, and demo script.

