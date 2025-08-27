"""
Input file generation and simulation runner for microkinetic modeling.
Fixed all HTML entities, indentation errors, and added proper error handling.
"""

import os
import subprocess
import shutil
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from itertools import zip_longest
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimulationParameters:
    """Container for simulation parameters."""
    temperature: float
    potential: float
    time: float
    abstol: float
    reltol: float
    pressure: float
    pH: float
    pre_exponential_factor: float = 6.21e12


class CoverageManager:
    """Manages coverage data between simulation steps for sweep mode."""

    def __init__(self):
        self.coverage_data: Dict[float, Dict[float, Dict[str, float]]] = {}

    def save_coverage(self, pH: float, V: float, coverage_dict: Dict[str, float]) -> None:
        """Save coverage data for a specific pH/V combination."""
        if pH not in self.coverage_data:
            self.coverage_data[pH] = {}
        self.coverage_data[pH][V] = coverage_dict
        logger.debug(f"Saved coverage for pH={pH}, V={V}: {coverage_dict}")

    def get_coverage(self, pH: float, V: float) -> Optional[Dict[str, float]]:
        """Get coverage data for a specific pH/V combination."""
        return self.coverage_data.get(pH, {}).get(V, None)

    def get_previous_coverage(self, pH: float, V_current: float, V_list: List[float]) -> Optional[Dict[str, float]]:
        """Get coverage from the previous potential step."""
        V_sorted = sorted(V_list, key=abs)  # Use absolute sorting consistently
        try:
            current_idx = V_sorted.index(V_current)
            if current_idx > 0:
                prev_V = V_sorted[current_idx - 1]
                return self.get_coverage(pH, prev_V)
        except ValueError:
            logger.warning(f"Current potential {V_current} not found in V_list")
        return None

    def export_coverage_trajectory(self, output_file: str) -> None:
        """Export coverage trajectory data to a JSON file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.coverage_data, f, indent=2)
            logger.info(f"Coverage trajectory exported to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export coverage trajectory: {e}")


class InputFileGenerator:
    """Generates input files for microkinetic modeling simulations."""

    def __init__(self, executable_path: str = ""):
        """
        Initialize with path to simulation executable.
        """
        self.executable_path = executable_path

    def generate_input_file(
        self,
        data: Dict[str, Any],
        sim_params: SimulationParameters,
        output_filename: str = "input_file.mkm"
    ) -> str:
        """Generate input file for microkinetic modeling."""

        try:
            with open(output_filename, 'w') as f:
                self._write_compounds_section(f, data, sim_params)
                self._write_reactions_section(f, data, sim_params)
                self._write_settings_section(f, sim_params)
                self._write_runs_section(f, sim_params)
            logger.info(f"Generated input file: {output_filename}")
            return output_filename
        except Exception as e:
            logger.error(f"Error generating input file: {e}")
            raise

    def _write_compounds_section(self, file, data: Dict[str, Any], sim_params: SimulationParameters) -> None:
        file.write('&compounds\n\n')

        # Gas-phase compounds
        file.write("#gas-phase compounds\n\n#Name; isSite; concentration\n\n")
        logger.debug(f"Writing compounds: #gases={len(data['gases'])}, #concentrations={len(data['concentrations'])}")
        for compound, concentration in zip_longest(data['gases'], data['concentrations'], fillvalue=0.0):
            if compound.strip("{}") == "OH" and sim_params.pH == 7:
                # Replicating constants from literature
                concentration = 10 ** (-(14 - 9.5))
            file.write(f"{compound:<15}; 0; {concentration}\n")

        # Adsorbates
        logger.debug(f"adsorbates length={len(data['adsorbates'])}, activity length={len(data['activity'])}")
        file.write("\n\n#adsorbates\n\n#Name; isSite; activity\n\n")
        for compound, activity in zip(data['adsorbates'], data['activity']):
            file.write(f"{compound:<15}; 1; {activity}\n")

        # Free sites - dynamic coverage, default to 1.0
        free_site_cov = data.get('free_site_coverage', 1.0)
        file.write("\n#free sites on the surface\n\n")
        file.write("#Name; isSite; activity\n\n")
        file.write(f"*; 1; {free_site_cov}\n\n")

    def _write_reactions_section(self, file, data: Dict[str, Any], sim_params: SimulationParameters) -> None:
        file.write('&reactions\n\n')
        reactions = data['reactions']
        pre_exp = sim_params.pre_exponential_factor
        logger.debug(f"Writing {len(data['reactions'])} reactions")

        for j in range(len(reactions)):
            r1, r2, r3 = data['Reactant1'][j], data['Reactant2'][j], data['Reactant3'][j]
            p1, p2, p3 = data['Product1'][j], data['Product2'][j], data['Product3'][j]
            ea, eb = data['Ea'][j], data['Eb'][j]

            line = self._format_reaction_line(r1, r2, r3, p1, p2, p3, pre_exp, ea, eb)
            file.write(line)

    def _format_reaction_line(self, r1: str, r2: str, r3: str,
                              p1: str, p2: str, p3: str,
                              pre_exp: float, ea: float, eb: float) -> str:
        if r3:
            if p3:
                return f"AR; {r1:<15} + {r2:<15} + {r3:<5} => {p1:<15} + {p2:<15} + {p3:<7};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
            else:
                return f"AR; {r1:<15} + {r2:<15} + {r3:<5} => {p1:<15} + {p2:<20};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
        elif r2:
            if p3:
                return f"AR; {r1:<15} + {r2:<14} => {p1:<10} + {p2:<15} + {p3:<7};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
            elif p2:
                return f"AR; {r1:<15} + {r2:<15} => {p1:<15} + {p2:<20};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
            else:
                return f"AR; {r1:<15} + {r2:<15} => {p1:<15}{'':<23};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
        else:
            if p2:
                return f"AR; {r1:<15} {'':<17} => {p1:<15} + {p2:<20};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"
            else:
                return f"AR; {r1:<15} {'':<17} => {p1:<15}{'':<23};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n"

    def _write_settings_section(self, file, sim_params: SimulationParameters) -> None:
        file.write("\n\n&settings\n")
        file.write("TYPE = SEQUENCERUN\n")
        file.write("USETIMESTAMP = 0\n")
        file.write(f"PRESSURE = {sim_params.pressure}\n")
        file.write("POTAXIS=1\n")
        file.write("DEBUG=0\n")
        file.write("NETWORK_RATES=1\n")
        file.write("NETWORK_FLUX=1\n")

    def _write_runs_section(self, file, sim_params: SimulationParameters) -> None:
        file.write('\n\n&runs\n')
        file.write("# Temp; Potential;Time;AbsTol;RelTol\n")
        line = f"{sim_params.temperature:<5};{sim_params.potential:<5};{sim_params.time:<5.2e};{sim_params.abstol:<5};{sim_params.reltol:<5}"
        file.write(line)

    def run_simulation(self, input_filename: str) -> subprocess.CompletedProcess:
        if not self.executable_path:
            logger.error("Executable path not specified")
            raise ValueError("Executable path must be specified to run simulation")

        if not Path(self.executable_path).exists():
            logger.error(f"Executable not found: {self.executable_path}")
            raise FileNotFoundError(f"Executable not found: {self.executable_path}")

        command = [self.executable_path, '-i', input_filename]

        try:
            logger.info(f"Running simulation with command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info("Simulation completed successfully")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Simulation failed: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            raise


class SimulationRunner:
    """Orchestrates the complete simulation workflow."""

    def __init__(self, config):
        self.config = config
        self.generator = InputFileGenerator(config.executable_path)
        self.coverage_manager = CoverageManager()

    def run_parameter_sweep(self, data_extractor) -> None:
        base_dir = Path.cwd()
        results_dir = Path(self.config.output_base_dir)
        results_dir.mkdir(exist_ok=True)

        for pH in self.config.pH_list:
            pH_dir = results_dir / f"pH_{pH}"
            pH_dir.mkdir(exist_ok=True)

            # Use ordered potentials by absolute value when sweep mode enabled
            if getattr(self.config, "enable_sweep_mode", False):
                V_steps = sorted(self.config.V_list, key=lambda v: abs(v))
            else:
                V_steps = self.config.V_list

            previous_coverage = None  # coverage from last sweep step

            for idx, V in enumerate(V_steps):
                V_dir = pH_dir / f"V_{V}"
                V_dir.mkdir(exist_ok=True)
                os.chdir(V_dir)

                try:
                    # Copy Excel input for modification
                    src = base_dir / self.config.input_excel_path
                    dst = Path("input_data.xlsx")
                    shutil.copyfile(src, dst)

                    # Extract data from Excel
                    data = data_extractor(pH, V, str(dst))
                    if isinstance(data, tuple):
                        data = self._convert_tuple_to_dict(data)

                    # Coverage propagation logic
                    if V == 0.0:
                        # Initial condition: all adsorbates zero, free site = 1.0
                        data['activity'] = [0.0] * len(data['adsorbates'])
                        data['free_site_coverage'] = 1.0
                        logger.info(f"Initial step V=0.0: set adsorbates to zero and free site = 1.0")
                    else:
                        # For other steps, use previous coverage if available
                        if self.config.use_coverage_propagation and previous_coverage:
                            data = self._apply_initial_coverage(data, previous_coverage)
                            data['free_site_coverage'] = previous_coverage.get('*', 1.0)
                            logger.info(f"Step V={V}: using propagated coverage from previous step")
                        else:
                            # No previous coverage, default free site coverage
                            data['free_site_coverage'] = 1.0
                            logger.warning(f"Step V={V}: no previous coverage found, free site set to 1.0")

                    # Determine simulation time per step
                    time_per_step = self.config.time
                    if getattr(self.config, "enable_sweep_mode", False):
                        try:
                            time_per_step = self.config.calculate_step_time()
                        except Exception as e:
                            logger.warning(f"Failed to calculate step time: {e}, using default time")

                    sim_params = SimulationParameters(
                        temperature=self.config.temperature,
                        potential=V,
                        time=time_per_step,
                        abstol=self.config.abstol,
                        reltol=self.config.reltol,
                        pressure=data.get('P', -1),
                        pH=pH,
                        pre_exponential_factor=self.config.pre_exponential_factor,
                    )

                    # Generate input and run simulation
                    input_file = self.generator.generate_input_file(data, sim_params)
                    if self.config.executable_path:
                        start_time = time.perf_counter()
                        self.generator.run_simulation(input_file)
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"Simulation pH={pH}, V={V} completed in {elapsed:.2f} seconds")

                        # Extract final coverage to propagate next
                        if getattr(self.config, "enable_sweep_mode", False):
                            final_cov = self._extract_final_coverage(V_dir)
                            if final_cov:
                                self.coverage_manager.save_coverage(pH, V, final_cov)
                                previous_coverage = final_cov

                    else:
                        logger.warning("Executable path not set; skipping simulation run")

                except Exception as e:
                    logger.error(f"Error at pH={pH}, V={V}: {e}")
                finally:
                    os.chdir(base_dir)

        # Export coverage trajectory once, unconditionally if sweep mode enabled
        if getattr(self.config, "enable_sweep_mode", False):
            traj_file = results_dir / "coverage_trajectory.json"
            self.coverage_manager.export_coverage_trajectory(str(traj_file))

    def _apply_initial_coverage(self, data: Dict[str, Any], prev_coverage: Dict[str, float]) -> Dict[str, Any]:
        """Apply coverage from previous step as initial conditions for adsorbates."""
        data_copy = data.copy()
        if 'adsorbates' in data_copy and 'activity' in data_copy:
            new_activity = []
            for i, adsorbate in enumerate(data_copy['adsorbates']):
                new_activity.append(prev_coverage.get(adsorbate, data_copy['activity'][i]))
            data_copy['activity'] = new_activity
            logger.debug(f"Applied initial coverage: {dict(zip(data_copy['adsorbates'], new_activity))}")
        return data_copy

    def _extract_final_coverage(self, simulation_dir: Path) -> Optional[Dict[str, float]]:
        """
        Extract final coverage from the coverage.dat file inside simulation_dir recursively.
        Looks inside run/range folders and returns coverage dict keyed by species.
        """
        try:
            simulation_dir = Path("run") / "range"
            coverage_files = list(simulation_dir.rglob("coverage.dat"))

            if not coverage_files:
                logger.warning(f"No coverage.dat found inside {simulation_dir}")
                return None

            coverage_file = coverage_files[0]
            logger.info(f"Reading coverage.dat from {coverage_file}")

            lines = coverage_file.read_text().strip().splitlines()
            if len(lines) < 2:
                logger.warning(f"Coverage file {coverage_file} is empty or incomplete")
                return None

            headers = lines[0].split()
            last_values = lines[-1].split()

            final_cov = {}
            for name, value in zip(headers, last_values):
                if "*" in name:
                    try:
                        final_cov[name] = float(value)
                    except ValueError:
                        logger.warning(f"Could not parse coverage value '{value}' for species '{name}'")
                        continue

            return final_cov
        except Exception as e:
            logger.error(f"Error extracting coverage from {simulation_dir}: {e}")
            return None

    def _convert_tuple_to_dict(self, data_tuple: tuple) -> Dict[str, Any]:
        """Convert tuple format to dictionary format."""
        keys = [
            'gases', 'concentrations', 'adsorbates', 'activity',
            'Reactant1', 'Reactant2', 'Reactant3',
            'Product1', 'Product2', 'Product3',
            'Ea', 'Eb', 'P', 'reactions'
        ]
        return dict(zip(keys, data_tuple))
