from __future__ import annotations

import argparse
import csv
import math
import subprocess
import time
from pathlib import Path


DEFAULT_INPUT = Path("primes1_till_1e8.txt")
DEFAULT_BACKEND = Path("primality_backend.exe")
DEFAULT_CSV = Path("prime_cumulative_benchmark.csv")
DEFAULT_SVG = Path("prime_cumulative_benchmark.svg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark cumulative primality-testing time on primes read from a whitespace-separated file "
            "and generate both CSV and SVG output."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the prime list text file.")
    parser.add_argument(
        "--backend",
        type=Path,
        default=DEFAULT_BACKEND,
        help="Path to primality_backend.exe used for Miller-Rabin and AKS timings.",
    )
    parser.add_argument(
        "--max-primes",
        type=int,
        default=100,
        help="How many primes to benchmark from the start of the file. Default: 100.",
    )
    parser.add_argument(
        "--plot-every",
        type=int,
        default=1,
        help="Write every Nth processed prime as a plotted point while still benchmarking all processed primes.",
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Output CSV file.")
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG, help="Output SVG plot file.")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=10,
        help="Print progress after every N processed primes. Default: 10.",
    )
    return parser.parse_args()


def ensure_backend_exists(path: Path) -> None:
    if path.exists():
        return

    raise FileNotFoundError(
        "C++ backend not found at "
        f"{path}. Build it with:\n"
        "g++ -std=c++17 -O2 -Wall -Wextra -pedantic "
        "primality_backend.cpp big_int.cpp miller_rabin.cpp aks.cpp -o primality_backend.exe"
    )


def iter_numbers(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        buffer = ""
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break

            buffer += chunk
            parts = buffer.split()

            if chunk[-1].isspace():
                buffer = ""
            else:
                buffer = parts.pop() if parts else buffer

            for token in parts:
                yield int(token)

        if buffer.strip():
            yield int(buffer.strip())


def is_prime_square_root(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = math.isqrt(n)
    divisor = 3
    while divisor <= limit:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def time_square_root_ms(n: int) -> tuple[bool, float]:
    start = time.perf_counter_ns()
    result = is_prime_square_root(n)
    end = time.perf_counter_ns()
    return result, (end - start) / 1_000_000.0


def run_backend(backend: Path, n: int) -> dict[str, str]:
    completed = subprocess.run(
        [str(backend), "check", "dec", str(n)],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or "Backend failed."
        raise RuntimeError(f"Backend failed for n={n}: {error_text}")

    data: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def write_csv(rows: list[dict[str, float | int]], path: Path) -> None:
    fieldnames = [
        "index",
        "prime",
        "sqrt_ms",
        "sqrt_cumulative_ms",
        "ordinary_mr_ms",
        "ordinary_mr_cumulative_ms",
        "fast_mr_ms",
        "fast_mr_cumulative_ms",
        "aks_ms",
        "aks_cumulative_ms",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def scale(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max == src_min:
        return dst_min
    return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)


def build_svg(rows: list[dict[str, float | int]], svg_path: Path) -> None:
    width = 1280
    height = 760
    left = 90
    right = 30
    top = 70
    bottom = 90

    max_prime = max(int(row["prime"]) for row in rows)
    max_time = max(
        max(
            float(row["sqrt_cumulative_ms"]),
            float(row["ordinary_mr_cumulative_ms"]),
            float(row["fast_mr_cumulative_ms"]),
            float(row["aks_cumulative_ms"]),
        )
        for row in rows
    )
    max_time = max(max_time, 1.0)

    series = [
        ("Square Root", "sqrt_cumulative_ms", "#111111"),
        ("Miller-Rabin Ordinary", "ordinary_mr_cumulative_ms", "#c0392b"),
        ("Miller-Rabin Fast", "fast_mr_cumulative_ms", "#1f78b4"),
        ("AKS", "aks_cumulative_ms", "#2e8b57"),
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="34" text-anchor="middle" font-size="24" font-family="Segoe UI">Cumulative Prime Checking Time</text>',
        f'<text x="{width / 2:.1f}" y="58" text-anchor="middle" font-size="13" fill="#555555" font-family="Segoe UI">X axis: prime value. Y axis: cumulative time from the first processed prime up to that x-value.</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<text x="{width / 2:.1f}" y="{height - 24}" text-anchor="middle" font-size="16" font-family="Segoe UI">Prime value (x)</text>',
        f'<text x="26" y="{height / 2:.1f}" text-anchor="middle" font-size="16" font-family="Segoe UI" transform="rotate(-90 26,{height / 2:.1f})">Cumulative time (ms)</text>',
    ]

    y_ticks = 6
    x_ticks = 6

    for tick in range(y_ticks + 1):
        value = max_time * tick / y_ticks
        y = scale(value, 0, max_time, height - bottom, top)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#e8e8e8"/>')
        parts.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="12" font-family="Consolas">{value:.1f}</text>'
        )

    for tick in range(x_ticks + 1):
        value = max_prime * tick / x_ticks
        x = scale(value, 0, max_prime, left, width - right)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" stroke="#f1f1f1"/>')
        parts.append(
            f'<text x="{x:.2f}" y="{height - bottom + 24}" text-anchor="middle" font-size="12" font-family="Consolas">{int(value)}</text>'
        )

    legend_x = width - 310
    legend_y = top + 20
    for idx, (label, key, color) in enumerate(series):
        y = legend_y + idx * 24
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 26}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{legend_x + 36}" y="{y + 4}" font-size="13" font-family="Segoe UI">{label}</text>'
        )

        points = []
        for row in rows:
            x = scale(float(row["prime"]), 0, max_prime, left, width - right)
            y_point = scale(float(row[key]), 0, max_time, height - bottom, top)
            points.append(f"{x:.2f},{y_point:.2f}")
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.3" points="{" ".join(points)}"/>')

    parts.append("</svg>")
    svg_path.write_text("\n".join(parts), encoding="utf-8")


def benchmark_primes(args: argparse.Namespace) -> list[dict[str, float | int]]:
    ensure_backend_exists(args.backend)

    rows: list[dict[str, float | int]] = []
    sqrt_total = 0.0
    ordinary_total = 0.0
    fast_total = 0.0
    aks_total = 0.0

    for index, prime in enumerate(iter_numbers(args.input), start=1):
        if index > args.max_primes:
            break

        sqrt_result, sqrt_ms = time_square_root_ms(prime)
        backend_data = run_backend(args.backend, prime)

        ordinary_result = backend_data["ordinary"] == "prime"
        fast_result = backend_data["fast"] == "prime"
        aks_result = backend_data["aks"] == "prime"

        ordinary_ms = float(backend_data["ordinary_ms"])
        fast_ms = float(backend_data["fast_ms"])
        aks_ms = float(backend_data["aks_ms"])

        if not (sqrt_result and ordinary_result and fast_result and aks_result):
            raise RuntimeError(f"Unexpected composite result while benchmarking prime {prime}.")

        sqrt_total += sqrt_ms
        ordinary_total += ordinary_ms
        fast_total += fast_ms
        aks_total += aks_ms

        if index % args.plot_every == 0 or index == 1 or index == args.max_primes:
            rows.append(
                {
                    "index": index,
                    "prime": prime,
                    "sqrt_ms": round(sqrt_ms, 6),
                    "sqrt_cumulative_ms": round(sqrt_total, 6),
                    "ordinary_mr_ms": round(ordinary_ms, 6),
                    "ordinary_mr_cumulative_ms": round(ordinary_total, 6),
                    "fast_mr_ms": round(fast_ms, 6),
                    "fast_mr_cumulative_ms": round(fast_total, 6),
                    "aks_ms": round(aks_ms, 6),
                    "aks_cumulative_ms": round(aks_total, 6),
                }
            )

        if args.progress_every > 0 and index % args.progress_every == 0:
            print(
                f"processed={index} prime={prime} "
                f"sqrt_total_ms={sqrt_total:.3f} ordinary_total_ms={ordinary_total:.3f} "
                f"fast_total_ms={fast_total:.3f} aks_total_ms={aks_total:.3f}"
            )

    if not rows:
        raise RuntimeError("No data points were generated. Check the input file and max-primes value.")

    return rows


def main() -> None:
    args = parse_args()

    if args.max_primes <= 0:
        raise SystemExit("--max-primes must be positive.")
    if args.plot_every <= 0:
        raise SystemExit("--plot-every must be positive.")
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    rows = benchmark_primes(args)
    write_csv(rows, args.csv)
    build_svg(rows, args.svg)

    print(f"Wrote CSV: {args.csv}")
    print(f"Wrote SVG: {args.svg}")
    print(
        "Note: AKS is much slower than Miller-Rabin. "
        "Increase --max-primes carefully if you want to process more of the uploaded file."
    )


if __name__ == "__main__":
    main()
