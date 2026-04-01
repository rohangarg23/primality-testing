# Primality Testing Project

This project explores multiple ways to test whether a number is prime and compares their runtime behavior on real inputs.

It currently includes:
- A custom `big_int` implementation for large integer arithmetic
- Miller-Rabin primality testing with two modular reduction strategies
- An AKS primality test implementation
- A simple square-root primality baseline
- A C++ console app for manual testing and dataset checks
- A C++ backend plus Python Tkinter GUI applet
- Benchmark and plotting scripts for cumulative runtime comparison

## Algorithms Included

### 1. Square-root primality test
This is the simple baseline method:
- Try dividing `n` by integers up to `sqrt(n)`
- Exact, but slow for larger inputs
- Included mainly for comparison

Reference file:
- `simple-square-root-algo.cpp`

### 2. Miller-Rabin with ordinary modulo
This version uses the project's normal division/modulo path for modular multiplication.

Properties:
- Fast in practice
- Probabilistic in general
- Used in the comparison app and benchmark scripts

### 3. Miller-Rabin with fast modulo
This version uses the project's custom `fast_mod` reduction path.

Properties:
- Same primality logic as Miller-Rabin ordinary modulo
- Different modular arithmetic implementation
- Intended to compare arithmetic performance

Main files:
- `miller_rabin.cpp`
- `miller_rabin.h`
- `big_int.cpp`
- `big_int.h`

### 4. AKS primality test
This is a deterministic primality test.

Properties:
- Exact, unlike Miller-Rabin
- Much slower than Miller-Rabin in practice
- Useful for correctness comparison and study

Main files:
- `aks.cpp`
- `aks.h`

## Main Project Files

- `big_int.cpp`, `big_int.h`: big integer arithmetic
- `miller_rabin.cpp`, `miller_rabin.h`: Miller-Rabin implementation and prime generation
- `aks.cpp`, `aks.h`: AKS primality test
- `primality_backend.cpp`: command-line backend used by the GUI and benchmark scripts
- `primality_gui.py`: Tkinter applet for checking primality and generating probable primes
- `main.cpp`: console menu app for decimal, hexadecimal, and dataset-based testing
- `benchmark.cpp`: older runtime benchmark for Miller-Rabin ordinary vs fast modulo
- `plot_benchmark.py`: plot generator for `benchmark.cpp` output
- `plot_prime_cumulative_benchmark.py`: cumulative benchmarking script using uploaded prime list data
- `plot_pairwise_comparisons.py`: generates pairwise comparison plots from the cumulative benchmark CSV
- `primes1_till_1e8.txt`: whitespace-separated prime list used for cumulative runtime experiments

## Requirements

### C++
- A compiler with C++17 support
- Example: `g++`

### Python
- Python 3
- Tkinter for the GUI applet

The Python plotting scripts in this repo do not require external plotting libraries such as `matplotlib`; they generate SVG files directly.

## Build Instructions

### Build the GUI/backend executable
```powershell
g++ -std=c++17 -O2 -Wall -Wextra -pedantic primality_backend.cpp big_int.cpp miller_rabin.cpp aks.cpp -o primality_backend.exe
```

### Build the console application
```powershell
g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp big_int.cpp miller_rabin.cpp aks.cpp -o primality_testing_app.exe
```

### Build the older Miller-Rabin benchmark
```powershell
g++ -std=c++17 -O2 -Wall -Wextra -pedantic benchmark.cpp big_int.cpp miller_rabin.cpp -o benchmark.exe
```

## How To Run

### 1. Run the GUI applet
First build `primality_backend.exe`, then run:

```powershell
python primality_gui.py
```

The applet supports:
- Decimal input
- Hexadecimal input
- Checking with Miller-Rabin ordinary modulo
- Checking with Miller-Rabin fast modulo
- Checking with AKS
- Generating a probable prime of a chosen bit length

Note:
- AKS is exact but slow
- For larger numbers, the AKS result may take much longer than Miller-Rabin

### 2. Run the console app
```powershell
.\primality_testing_app.exe
```

It provides:
- Decimal number testing
- Hexadecimal number testing
- Batch testing from a Wycheproof-style JSON dataset

### 3. Use the backend directly
Check a decimal number:

```powershell
.\primality_backend.exe check dec 101
```

Check a hexadecimal number:

```powershell
.\primality_backend.exe check hex FF
```

Generate a probable prime:

```powershell
.\primality_backend.exe generate 128
```

Backend output includes:
- The number
- Bit length
- Miller-Rabin ordinary result and time
- Miller-Rabin fast result and time
- AKS result and time
- Agreement flags

## Benchmarking

### A. Older Miller-Rabin benchmark
This compares ordinary modulo vs fast modulo Miller-Rabin across bit lengths.

Run:
```powershell
.\benchmark.exe
python plot_benchmark.py
```

Outputs:
- `benchmark_times.csv`
- `benchmark_plot.svg`

### B. Cumulative benchmark using prime list
This script reads primes from `primes1_till_1e8.txt`, benchmarks:
- square-root test
- Miller-Rabin ordinary modulo
- Miller-Rabin fast modulo
- AKS

and then plots cumulative time from the first processed prime up to each x-axis prime value.

Run:
```powershell
python plot_prime_cumulative_benchmark.py --max-primes 100
```

Useful options:
- `--input`: choose a different prime list file
- `--backend`: choose a different backend executable
- `--max-primes`: number of primes to benchmark
- `--plot-every`: keep every Nth processed prime as an output point
- `--progress-every`: print progress during long runs

Outputs:
- `prime_cumulative_benchmark.csv`
- `prime_cumulative_benchmark.svg`

Important:
- AKS becomes very slow quickly
- Running this over a large portion of all primes up to `1e8` can take a very long time

## Pairwise Plot Generation

If `prime_cumulative_benchmark.csv` already exists, generate comparison plots directly from it:

```powershell
python plot_pairwise_comparisons.py
```

This creates:
- `comparison_plots/square_root_vs_aks.svg`
- `comparison_plots/square_root_vs_miller_rabin.svg`
- `comparison_plots/miller_rabin_fast_vs_ordinary.svg`
- `comparison_plots/aks_vs_miller_rabin.svg`

## Example Workflow

### Check a number in the applet
1. Build `primality_backend.exe`
2. Run `python primality_gui.py`
3. Enter a decimal or hexadecimal number
4. Click `Check Prime`
5. Read the result and timings for all methods

### Generate benchmark plots
1. Build `primality_backend.exe`
2. Run:

```powershell
python plot_prime_cumulative_benchmark.py --max-primes 100
python plot_pairwise_comparisons.py
```

3. Open the generated SVG files in a browser or image viewer

## Notes and Limitations

- Miller-Rabin in this project is used as a practical fast primality checker
- AKS is included for deterministic comparison, not for speed
- The square-root method is only practical for relatively small numbers
- The custom `big_int` implementation is educational and project-specific, not a replacement for industrial big integer libraries
- The GUI depends on the backend executable being present in the same folder
- Some generated `.exe`, `.csv`, and `.svg` files in the repo are build/runtime artifacts

## Current Outputs You May See In The Repo

Depending on what has already been run, the repo may contain generated files such as:
- `primality_backend.exe`
- `primality_testing_app.exe`
- `benchmark.exe`
- `prime_cumulative_benchmark.csv`
- `prime_cumulative_benchmark.svg`
- files inside `comparison_plots/`

## Project Goal

The goal of this project is not only to test primality, but also to compare:
- simple exact methods
- fast probabilistic methods
- deterministic polynomial-time methods

in one codebase with both interactive and benchmarking workflows.
