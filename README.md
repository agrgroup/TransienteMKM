# Transient eMKM Input File Generator and Solver

This Streamlit-based application provides a graphical interface for generating input files for unsteady electrochemical microkinetic modeling (eMKM), running solvers, and visualizing reaction networks. It supports single and multiple-parameter simulations (e.g., pH and potential) and can identify rate-determining steps (RDS). Codes are also available to plot current density vs. potential relationships with and without potential sweeping.

---

## Features

- ✅ Generate `.mkm` input files from Excel data.
- ⚙️ Run MKM solvers for single or batch input files.
- 🧬 Visualize reaction networks from DOT files.
- 🔍 Identify rate-determining steps (RDS).
- 📦 Download simulation results and modified input files.

---

## File Structure

```text
.
├── Homepage.py                # Main interface for single-run simulations
├── MKM with input file.py     # Interface to upload and run existing MKM files
├── Multiple runs.py           # Batch processing for multiple pH and potential values
├── utility.py                 # Backend utility functions 
├── graph_helper.py            # DOT graph handling and visualization
├── inp_file_multiple.py       # Batch input file generator 
├── run/                       # Stores output and network plots
└── single_run/                # Files for single-run execution

```
## 🖥 Installation & Requirements

### Requirements

- Python 3.8+
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [NetworkX](https://networkx.org/)
- [Graphviz](https://graphviz.org/)

### Install All Dependencies

Run the following command in your terminal:

```bash
pip install streamlit pandas numpy openpyxl networkx graphviz
```
## 🚀 Getting Started
Run the application using:
```bash
streamlit run Homepage.py
```
## 📄 Homepage.py (Single-Run UI)

### Key Functions

- Upload Excel file with 3 sheets: `Reactions`, `Local Environment`, `Input-Output Species`
- Preview each sheet's contents
- Generate `.mkm` input files
- Run MKM solver and display coverage data
- Visualize reaction network from `.dot` file
- Identify RDS and list associated paths and rates
- Download simulation output folder as a zip

## 📄  MKM with input file.py (Existing MKM File UI)

### Key Functions

- Upload a `.mkm` file directly
- View and preview the content
- Run MKM solver
- Generate reaction network plots
- Detect and report RDS
- Download results

  
## 📄  Multiple runs.py (Batch Processing for Multiple pH & V)

### Key Functions

- Upload a base Excel file
- Select multiple pH and potential (V) values
- Auto-generate modified Excel files
- Create MKM input files for each parameter pair
- Run solver across all parameter combinations
- Download individual input files and solver outputs


## 📂 Input Excel Format

Ensure the uploaded Excel contains:

- **Reactions Sheet** – Reaction definitions.
- **Local Environment Sheet** – Must contain:
  - `B2` → Potential  
  - `C2` → pH
- **Input-Output Species Sheet** – Specifies species flow.

---

## 🧾 Output
- MKM simulation results in the `run/` directory.
- Reaction networks as `.dot` and `.svg` files.
- Downloadable `.zip` of simulation folder.

---
## 🛠️ Utilities

The app leverages the following helper functions (defined in `utility.py`, `graph_helper.py`, `inp_file_multiple.py`):

- `inp_file_gen()`, `inp_file_gen_multiple()` – Input file generators
- `run_executable()` – Solver runner
- `coverage()` – Coverage display
- `create_reaction_network_visualization()` 
- `parse_dot_file()`, `extract_reactions()`, `find_rds()`

---

## 📦 Deployment

For local use. If deploying to a server or cloud, ensure writable permissions in the working directory.

## ✍️ Authors

Developed by [AGR Group @ IISc](https://agrgroup.org/)

Feel free to customize or extend the application.

---

## 📄 Citation & Publication

If you use this application in your work, please cite the following:

```bibtex

@article{chaturvedi2025transient,
  title={Transient Microkinetic Modeling of Electrochemical Reactions: Capturing Unsteady Dynamics of CO Reduction and Oxygen Evolution},
  author={Chaturvedi, Shivam and Pathak, Amar Deep and Sinha, Nishant and Rajan, Ananth Govind},
  journal={ChemRxiv},
  year={2025},
  publisher={ChemRxiv},
  doi={10.26434/chemrxiv-2025-rggk3}
}

