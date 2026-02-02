# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-02-02

### Added
- **Sweep Mode**: Integrated sweep functionality (`--sweep-mode`) with automated coverage propagation from previous steps.
- **Improved CLI**: New command line arguments for controlling sweep rate and simulation parameters.
- **Performance**: Cached Excel data processing to significantly reduce I/O overhead during parameter sweeps.
- **Benchmarking**: Added `--benchmark` flag to test data access performance.

### Changed
- **Configuration**: Simplified configuration by merging `use_coverage_propagation` into `enable_sweep_mode`.
- **Code Structure**: Renamed optimized core files to standard names (`main_application.py`, `simulation_runner.py`, `data_extraction.py`).
- **Documentation**: Updated README with comprehensive installation, configuration, and usage instructions.

### Fixed
- **Input Parsing**: Enhanced robustness of reaction and species parsing from Excel.
- **Coverage Propagation**: Fixed issues with continuous coverage tracking across potential steps.
