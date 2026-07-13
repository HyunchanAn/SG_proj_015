# E2E Integrated Pipeline Demonstration UI

This directory contains the temporary user interface developed to demonstrate the E2E surface analysis, product matching, and GNN-based inverse molecular design platform. 

All code and assets are self-contained in this `demo_ui` directory so that it can be easily deleted after the demonstration.

## Prerequisites

Ensure you have Python installed and the required libraries from the requirements file:

```bash
pip install -r requirements.txt
```

Also, ensure that Docker Desktop and the backend services for modules 001 through 014 are running locally. The UI will check the status of these ports on launch.

## Execution Method

You can launch the interface by double-clicking the `run_ui.bat` script, or by running the following command in your terminal:

```bash
streamlit run app.py
```

By default, the Streamlit server will run at `http://localhost:8501`.

## Demonstration Scenario

1. [Service Health Check]: Review the status indicators at the top of the page. Make sure the central orchestrator (port 8014) and required module APIs are marked as `ONLINE`.
2. [Input Attributes]: Configure substrate series (e.g., SGV), thickness (e.g., 100um), surface finish, and target physical properties.
   - Note: The initial adhesion target must be less than or equal to the aged adhesion target to satisfy physical domain constraints.
3. [Trigger Pipeline]: Click `Trigger Integrated E2E Pipeline Analysis` to run the E2E logic.
4. [Analyze Outputs]:
   - Review Metrology Calibration to see the Cassie-Baxter & Wenzel corrections.
   - Look at the processability rating to see if thickness penalties were applied.
   - View matching recommendations for commercial products.
   - Examine GNN synthetic recipes (rendered as a pie chart) when inverse molecular engineering is triggered.
5. [Archive Results]: Click the `Archive E2E Demonstration Report` button at the bottom of the page to save the output report to the `reports_archive/demo_reports` folder.

## Clean Up

Once the demonstration is finished, you can completely remove this UI and all its configuration by deleting the `demo_ui` directory.
