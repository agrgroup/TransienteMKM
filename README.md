# Transient eMKM Input File Generator and Solver

This application provides both a CLI and a graphical interface (Streamlit) for generating input files for unsteady electrochemical microkinetic modeling (eMKM), running solvers, and visualizing reaction networks. It supports single and multiple-parameter simulations (e.g., pH and potential) and can identify rate-determining steps (RDS). Codes are also available to plot current density vs. potential relationships with and without potential sweeping.

---

## 📁 **File Structure**

```
TransienteMKM/
├── main_application.py      # Main entry point with CLI
├── config.py               # Configuration management (YAML/JSON)
├── data_extraction.py      # Excel data processing 
├── simulation_runner.py    # Input file generation 
├── plotting.py             # Visualization 
├── utilities.py            # Utility functions
├── dependencies_fixed.py   # All imports
├── example_config.yaml     # Example configuration
├── example_config.json     # Example configuration (JSON)
├── input.xlsx             # Your input data
├── test_setup.py          # Setup verification
└── README.md              #  documentation
```

## 🚀 **Quick Start**

## Using CLI

### **1. Installation**
```bash
pip install pandas numpy matplotlib openpyxl xlwings xlrd xlwt xlutils pyyaml
```

### **2. Configuration**
Edit `example_config.yaml` and set your executable path:
```yaml
executable_path: "/path/to/your/mkmcxx.exe"  # UPDATE THIS!
```

### **3. Run**
```bash
# Test setup
python test_setup.py

# Run full workflow
python main_application.py --config example_config.yaml

# Run only simulations
python main_application.py --config example_config.yaml --simulations-only

# Create only plots
python main_application.py --config example_config.yaml --plots-only
```

## Using Streamlit

###  Run
```bash
streamlit run Homepage.py
```

## ⚙️ **Configuration**

All parameters are configurable via YAML or JSON files:

```yaml
# pH and potential ranges
pH_list: [7, 13]
V_list: [0,-0.1,-0.2,-0.3,-0.4,-0.5,-0.6,-0.7,-0.8,-0.9,-1.0]

# Simulation parameters  
temperature: 298
time: 100000.0
abstol: 1.0e-20
reltol: 1.0e-10
enable_sweep_mode: true
sweep_rate: 0.1  (V/sec)
use_coverage_propagation: true

# Paths
input_excel_path: "input.xlsx"
executable_path: "/path/to/your/mkmcxx.exe"
output_base_dir: "results"
```

## 📊 **Features**

### **Parameter Sweeps**
- Automated pH and potential parameter sweeps
- Configurable ranges and values
- Organized output directory structure

### **Data Processing**
- Fixed Excel file handling bugs
- Robust reaction parsing
- Automatic adsorbate detection
- Data validation and error checking

### **Simulation Management**
- Input file generation with proper formatting
- Subprocess management for simulations
- Error handling and logging
- Progress tracking

### **Visualization**
- Coverage vs potential plots
- Multiple pH conditions
- Automatic species formatting (subscripts)
- Summary tables and CSV export
- Customizable plot styling

### **Error Handling**
- Comprehensive validation
- Detailed error messages
- Graceful failure recovery
- Debug mode with verbose output

## 🔍 **Command Line Options**

```bash
python main_application.py [OPTIONS]

Options:
  -c, --config PATH          Configuration file path
  --simulations-only         Run only simulations
  --plots-only              Create only plots  
  --create-example-config    Create example config files
  --export-config PATH       Export current config
  -v, --verbose             Enable verbose logging
  -h, --help                Show help
``` 

## 📋 **Output**

### **Directory Structure:**
```
results/
├── pH_7/
│   ├── V_0/
│   │   ├── input_file.mkm
│   │   └── run_*/range/coverage.dat
│   ├── V_-0.2/
│   └── ...
├── pH_10/
└── pH_13/
```

### **Generated Files:**
- `input_file.mkm` - Simulation input files
- `coverage_pH_*.png` - Coverage plots
- `coverage_summary.csv` - Data summary
- `summary_report.txt` - Execution summary

## 🛠 **Advanced Usage**

### **Custom Configuration:**
```python
from config import SolverSettings

config = SolverSettings()
config.pH_list = [8, 9, 10]
config.V_list = [-0.5, -0.6, -0.7]
config.to_yaml("custom_config.yaml")
```

### **Programmatic Usage:**
```python
from main_application import MicrokineticModeling

app = MicrokineticModeling("my_config.yaml")
app.run_full_workflow()
```

## 🐛 **Troubleshooting**

### **Common Issues:**

1. **"Executable not found"**
   - Update `executable_path` in config file
   - Use full absolute path

2. **Import errors**
   - Install dependencies: `pip install pandas numpy matplotlib openpyxl xlwings pyyaml`

3. **Excel file issues**
   - Ensure `input.xlsx` is in correct location
   - Check sheet names: "Reactions", "Local Environment", "Input-Output Species"

4. **Permission errors**
   - Ensure write permissions in output directory
   - Close Excel files before running

### **Debug Mode:**
```bash
python main_application.py --config example_config.yaml --verbose
```

## 📦 **Dependencies**

```
pandas>=1.3.0
numpy>=1.20.0
matplotlib>=3.5.0
openpyxl>=3.0.0
xlwings>=0.24.0
xlrd>=2.0.0
xlwt>=1.3.0
xlutils>=2.0.0
pyyaml>=6.0.0
```

## ✅ **Testing**

Run the test script to verify setup:
```bash
python test_setup.py
```

This will check:
- All dependencies installed
- All files present
- Configuration loading
- Basic functionality



---

## ✍️ Authors

Developed by [AGR Group @ IISc](https://agrgroup.org/)

Feel free to customize or extend the application.

---

## 📄 Citation & Publication

If you use this application in your work, please cite the following:

**Publication Title:** *Transient Microkinetic Modeling of Electrochemical Reactions: Capturing Unsteady Dynamics of CO Reduction and Oxygen Evolution*  
**Authors:** [Shivam Chaturvedi, Amar Deep Pathak, Nishant Sinha, Ananth Govind Rajan]  
**Journal:** [Advanced Theory and Simulations]  
**Year:** 2025  
**DOI:** [10.1002/adts.202500799])

```bibtex

@article{chaturvedi2025transient,
  title={Transient Microkinetic Modeling of Electrochemical Reactions: Capturing Unsteady Dynamics of CO Reduction and Oxygen Evolution},
  author={Chaturvedi, Shivam and Pathak, Amar Deep and Sinha, Nishant and Rajan, Ananth Govind},
  journal={ChemRxiv},
  year={2025},
  publisher={ChemRxiv},
  doi={10.26434/chemrxiv-2025-rggk3}
}

@article{shivam_2025,
title={Transient microkinetic modeling of electrochemical reactions: capturing unsteady dynamics of CO reduction and oxygen evolution},
 url={https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/adts.202500799},
 DOI={10.1002/adts.202500799},
 journal={Advanced Theory and Simulations},
 author={Chaturvedi, Shivam and Pathak, Amar Deep and Sinha, Nishant and Rajan, Ananth Govind},
 year={2025}, month=nov }
