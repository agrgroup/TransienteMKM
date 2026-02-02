"""
Input file generation and simulation runner for microkinetic modeling.

This rewrite adds robust handling of coverages to ensure that:
- Negative or near-zero (numerical noise) coverages never propagate.
- All coverages are sanitized with a configurable tolerance EPS.
- Free-site coverage is (optionally) rebalanced to keep the site balance consistent.

Other improvements:
- Clear separation of responsibilities and small helper utilities.
- Safer parsing of coverage files.
- Consistent potential ordering in sweep mode.
"""

import os
import subprocess
import shutil
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Iterable, Tuple
from itertools import zip_longest
import logging

logger = logging.getLogger(__name__)


# --------------------------- Data containers ---------------------------

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


# --------------------------- Coverage management ---------------------------

class CoverageManager:
    """
    Manages coverage data between simulation steps for sweep mode.

    Structure:
        coverage_data[pH][V] = {species_name: coverage_value, ...}
    """

    def __init__(self):
        self.coverage_data: Dict[float, Dict[float, Dict[str, float]]] = {}

    def save_coverage(self, pH: float, V: float, coverage_dict: Dict[str, float]) -> None:
        """Save coverage data for a specific pH/V combination."""
        if pH not in self.coverage_data:
            self.coverage_data[pH] = {}
        self.coverage_data[pH][V] = dict(coverage_dict)  # store a copy
        logger.debug(f"Saved coverage for pH={pH}, V={V}: {coverage_dict}")

    def get_coverage(self, pH: float, V: float) -> Optional[Dict[str, float]]:
        """Get coverage data for a specific pH/V combination."""
        return self.coverage_data.get(pH, {}).get(V, None)

    def get_previous_coverage(self, pH: float, V_current: float, V_list: List[float]) -> Optional[Dict[str, float]]:
        """
        Get coverage from the previous potential step.
        Uses absolute sorting consistently to define sweep order.
        """
        V_sorted = sorted(V_list, key=abs)
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


# --------------------------- Input file generator ---------------------------

class InputFileGenerator:
    """Generates input files for microkinetic modeling simulations."""

    def __init__(self, executable_path: str = ""):
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

        # Free sites - dynamic coverage
        free_site_cov = data.get('free_site_coverage', 1.0)
        file.write("\n#free sites on the surface\n\n")
        file.write("#Name; isSite; activity\n\n")
        file.write(f"*; 1; {free_site_cov}\n\n")

    def _write_reactions_section(self, file, data: Dict[str, Any], sim_params: SimulationParameters) -> None:
        file.write('&reactions\n\n')
        reactions = data['reactions']
        pre_exp = sim_params.pre_exponential_factor
        logger.debug(f"Writing {len(reactions)} reactions")

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
                return (f"AR; {r1:<15} + {r2:<15} + {r3:<5} => "
                        f"{p1:<15} + {p2:<15} + {p3:<7};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; "
                        f"{ea:<10} ; {eb:<10} \n")
            else:
                return (f"AR; {r1:<15} + {r2:<15} + {r3:<5} => "
                        f"{p1:<15} + {p2:<20};{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; "
                        f"{ea:<10} ; {eb:<10} \n")
        elif r2:
            if p3:
                return (f"AR; {r1:<15} + {r2:<14} => {p1:<10} + {p2:<15} + {p3:<7};"
                        f"{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n")
            elif p2:
                return (f"AR; {r1:<15} + {r2:<15} => {p1:<15} + {p2:<20};"
                        f"{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n")
            else:
                return (f"AR; {r1:<15} + {r2:<15} => {p1:<15}{'':<23};"
                        f"{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n")
        else:
            if p2:
                return (f"AR; {r1:<15} {'':<17} => {p1:<15} + {p2:<20};"
                        f"{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n")
            else:
                return (f"AR; {r1:<15} {'':<17} => {p1:<15}{'':<23};"
                        f"{pre_exp:<10.2e} ; {pre_exp:<10.2e} ; {ea:<10} ; {eb:<10} \n")

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


# --------------------------- Simulation runner ---------------------------

class SimulationRunner:
    """Orchestrates the complete simulation workflow with noise-robust coverage propagation."""

    # Default tolerance for treating tiny values (incl. tiny negatives) as zero
    EPS: float = 1e-9

    # If True, enforce site balance by recomputing free sites as 1 - sum(adsorbates)
    ENFORCE_SITE_BALANCE: bool = True

    # Clip upper bound for any coverage (use 1.0 for probabilities/fractions)
    MAX_COVERAGE: float = 1.0

    def __init__(self, config):
        self.config = config
        self.generator = InputFileGenerator(config.executable_path)
        self.coverage_manager = CoverageManager()

        # Allow config to override EPS and enforcement flags if present
        self.EPS = getattr(config, "coverage_epsilon", self.EPS)
        self.ENFORCE_SITE_BALANCE = getattr(config, "enforce_site_balance", self.ENFORCE_SITE_BALANCE)
        self.MAX_COVERAGE = getattr(config, "max_coverage", self.MAX_COVERAGE)

    # ---------- Utilities for coverage handling ----------

    def _sanitize_value(self, x: float) -> float:
        """
        Clamp negative or near-zero values to zero, and cap at MAX_COVERAGE.
        """
        try:
            if x < self.EPS:
                return 0.0
            if x > self.MAX_COVERAGE:
                return self.MAX_COVERAGE
            return x
        except Exception:
            return 0.0

    def _sanitize_mapping(self, cov: Dict[str, float]) -> Dict[str, float]:
        """Apply _sanitize_value to all coverage values."""
        return {k: self._sanitize_value(float(v)) for k, v in cov.items()}

    def _renormalize_free_site(self, adsorbates: Iterable[str], activities: Iterable[float]) -> Tuple[List[float], float]:
        """
        Recompute free-site coverage from adsorbate coverages to maintain site balance:
            theta_* = max(0, 1 - sum_i theta_i)
        Returns (sanitized_adsorbate_coverages, free_site).
        """
        act_list = [self._sanitize_value(a) for a in activities]
        total_ads = sum(act_list)
        # Avoid tiny negative due to rounding
        theta_free = max(0.0, 1.0 - total_ads)
        theta_free = self._sanitize_value(theta_free)
        return act_list, theta_free

    # ---------- Main workflow ----------

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
                V_steps = list(self.config.V_list)

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

                    # Extract data from Excel (user-supplied function)
                    data = data_extractor(pH, V, str(dst))
                    if isinstance(data, tuple):
                        data = self._convert_tuple_to_dict(data)

                    # ---------------- Coverage propagation logic ----------------
                    if V == 0.0:
                        # Initial condition: all adsorbates zero, free site = 1.0
                        adsorbates = data.get('adsorbates', [])
                        data['activity'] = [0.0] * len(adsorbates)
                        data['free_site_coverage'] = 1.0
                        logger.info("Initial step V=0.0: set adsorbates to zero and free site = 1.0")
                    else:
                        # For other steps, use previous coverage if available
                        if self.config.use_coverage_propagation and previous_coverage:
                            data = self._apply_initial_coverage(data, previous_coverage)
                            # If previous coverage has '*' use it; else recompute below if enabled
                            if '*' in previous_coverage:
                                data['free_site_coverage'] = self._sanitize_value(previous_coverage.get('*', 1.0))
                            else:
                                # fallback; will be recalculated if ENFORCE_SITE_BALANCE
                                data['free_site_coverage'] = 1.0
                            logger.info(f"Step V={V}: using propagated (sanitized) coverage from previous step")
                        else:
                            data['free_site_coverage'] = 1.0
                            logger.warning(f"Step V={V}: no previous coverage found, free site set to 1.0")

                    # Enforce site balance if requested
                    if self.ENFORCE_SITE_BALANCE and 'adsorbates' in data and 'activity' in data:
                        sanitized_acts, theta_free = self._renormalize_free_site(data['adsorbates'], data['activity'])
                        data['activity'] = sanitized_acts
                        data['free_site_coverage'] = theta_free
                        logger.debug(
                            f"Site balance enforced. Sum(ads)={sum(sanitized_acts):.6g}, "
                            f"free={theta_free:.6g}"
                        )
                    else:
                        # If not enforcing, at least sanitize existing numbers
                        data['activity'] = [self._sanitize_value(a) for a in data.get('activity', [])]
                        data['free_site_coverage'] = self._sanitize_value(data.get('free_site_coverage', 1.0))

                    # ---------------- Simulation timing ----------------
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

                    # ---------------- Generate input and run simulation ----------------
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
                                # Sanitize and (optionally) recompute free site before saving/propagating
                                final_cov = self._sanitize_mapping(final_cov)
                                if self.ENFORCE_SITE_BALANCE:
                                    # If we know the adsorbates list, rebalance
                                    ads_list = data.get('adsorbates', [])
                                    # Build vector from the dict
                                    ads_vals = [final_cov.get(a, 0.0) for a in ads_list]
                                    ads_vals, theta_free = self._renormalize_free_site(ads_list, ads_vals)
                                    # Push back into dict
                                    for a, v in zip(ads_list, ads_vals):
                                        final_cov[a] = v
                                    final_cov['*'] = theta_free
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

    # --------------------------- Helpers ---------------------------

    def _apply_initial_coverage(self, data: Dict[str, Any], prev_coverage: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply (sanitized) coverage from previous step as initial conditions for adsorbates.
        Negative and tiny values are clamped to zero; large values are capped.
        """
        data_copy = data.copy()
        if 'adsorbates' in data_copy and 'activity' in data_copy:
            new_activity = []
            for i, adsorbate in enumerate(data_copy['adsorbates']):
                raw_value = prev_coverage.get(adsorbate, data_copy['activity'][i])
                clean_value = self._sanitize_value(float(raw_value))
                new_activity.append(clean_value)
            data_copy['activity'] = new_activity
            logger.debug(f"Applied initial coverage (sanitized): {dict(zip(data_copy['adsorbates'], new_activity))}")
        return data_copy

    def _extract_final_coverage(self, simulation_dir: Path) -> Optional[Dict[str, float]]:
        """
        Extract final coverage from the first 'coverage.dat' found under run/range.
        Returns coverage dict keyed by species (includes '*' and adsorbates if present).
        """
        try:
            search_root = Path("run") / "range"
            coverage_files = list(search_root.rglob("coverage.dat"))

            if not coverage_files:
                logger.warning(f"No coverage.dat found inside {search_root}")
                return None

            coverage_file = coverage_files[0]
            logger.info(f"Reading coverage.dat from {coverage_file}")

            lines = coverage_file.read_text().strip().splitlines()
            if len(lines) < 2:
                logger.warning(f"Coverage file {coverage_file} is empty or incomplete")
                return None

            # Heuristic: header is first non-empty line; final values are last non-empty line
            headers = lines[0].split()
            last_values = lines[-1].split()

            # If column counts mismatch, try to align by trimming to min length
            n = min(len(headers), len(last_values))
            headers = headers[:n]
            last_values = last_values[:n]

            final_cov: Dict[str, float] = {}
            for name, value in zip(headers, last_values):
                try:
                    cov_val = float(value)
                    final_cov[name] = cov_val
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
