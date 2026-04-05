from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path


DEFAULT_CSV = Path("bit_length_prime_search_benchmark.csv")
DEFAULT_SVG = Path("images/bit_length_prime_search_comparison.svg")
DEFAULT_LOG_SVG = Path("images/bit_length_prime_search_comparison_log.svg")
WITNESSES = (2, 3, 5, 7, 11, 13, 17, 19, 23)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark cumulative time to find one prime for each bit length and plot "
            "square-root search against Miller-Rabin."
        )
    )
    parser.add_argument("--min-bits", type=int, default=1, help="Minimum bit length to process.")
    parser.add_argument("--max-bits", type=int, default=200, help="Maximum bit length to process.")
    parser.add_argument(
        "--sqrt-max-seconds-per-bit",
        type=float,
        default=2.0,
        help="Stop the square-root benchmark when a single bit length exceeds this many seconds.",
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Output CSV path.")
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG, help="Output SVG path.")
    parser.add_argument("--log-svg", type=Path, default=DEFAULT_LOG_SVG, help="Output log-scale SVG path.")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=10,
        help="Print progress after every N processed bit lengths. Use 0 to disable.",
    )
    return parser.parse_args()


def is_prime_square_root(n: int, deadline_ns: int | None = None) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = math.isqrt(n)
    divisor = 3
    iterations = 0
    while divisor <= limit:
        if deadline_ns is not None and iterations % 4096 == 0 and time.perf_counter_ns() > deadline_ns:
            raise TimeoutError("square-root search exceeded the time limit")
        if n % divisor == 0:
            return False
        divisor += 2
        iterations += 1
    return True


def is_probable_prime_miller_rabin(n: int, deadline_ns: int | None = None) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    for p in WITNESSES:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    n_minus_one = n - 1
    for a in WITNESSES:
        if a >= n:
            continue

        x = pow(a, d, n)
        if x == 1 or x == n_minus_one:
            continue

        witness_passed = False
        for _ in range(1, s):
            x = (x * x) % n
            if x == n_minus_one:
                witness_passed = True
                break

        if not witness_passed:
            return False

    return True


def first_candidate_for_bits(bits: int) -> int | None:
    if bits <= 0:
        raise ValueError("Bit length must be positive.")
    if bits == 1:
        return None
    if bits == 2:
        return 2
    return (1 << (bits - 1)) + 1


def search_first_prime(bits: int, primality_fn, time_limit_s: float | None = None) -> dict[str, int | float | str | None]:
    candidate = first_candidate_for_bits(bits)
    if candidate is None:
        return {
            "prime": None,
            "search_ms": 0.0,
            "candidates_tested": 0,
            "status": "no-prime",
        }

    upper_bound = 1 << bits
    tested = 0
    start_ns = time.perf_counter_ns()
    deadline_ns = None if time_limit_s is None else start_ns + int(time_limit_s * 1_000_000_000.0)

    while candidate < upper_bound:
        tested += 1
        try:
            is_prime = primality_fn(candidate, deadline_ns)
        except TimeoutError:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            return {
                "prime": None,
                "search_ms": elapsed_ms,
                "candidates_tested": tested,
                "status": "stopped",
            }

        if is_prime:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            return {
                "prime": candidate,
                "search_ms": elapsed_ms,
                "candidates_tested": tested,
                "status": "ok",
            }

        if candidate == 2:
            candidate = 3
        else:
            candidate += 2

        if deadline_ns is not None:
            if time.perf_counter_ns() > deadline_ns:
                return {
                    "prime": None,
                    "search_ms": (time.perf_counter_ns() - start_ns) / 1_000_000.0,
                    "candidates_tested": tested,
                    "status": "stopped",
                }

    raise RuntimeError(f"No prime found for bit length {bits}.")


def format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fieldnames = [
        "bit_length",
        "prime",
        "sqrt_search_ms",
        "sqrt_cumulative_ms",
        "sqrt_candidates_tested",
        "sqrt_status",
        "mr_search_ms",
        "mr_cumulative_ms",
        "mr_candidates_tested",
        "mr_status",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def scale(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max == src_min:
        return dst_min
    return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)


def find_first_crossover(rows: list[dict[str, object]]) -> int | None:
    for row in rows:
        if row["sqrt_cumulative_ms"] == "":
            continue
        if float(row["sqrt_cumulative_ms"]) > float(row["mr_cumulative_ms"]):
            return int(row["bit_length"])
    return None


def format_tick(value: float) -> str:
    if value == 0:
        return "0"
    if value >= 1000:
        return f"{int(value)}"
    if value >= 1:
        return f"{value:.0f}" if float(int(value)) == value else f"{value:.1f}"
    if value >= 0.1:
        return f"{value:.1f}"
    if value >= 0.01:
        return f"{value:.2f}"
    return f"{value:.3f}"


def build_svg(
    rows: list[dict[str, object]],
    svg_path: Path,
    sqrt_cutoff_bits: int | None,
    sqrt_limit_seconds: float,
    *,
    log_scale: bool,
) -> None:
    width = 1280
    height = 760
    left = 90
    right = 40
    top = 90
    bottom = 95

    plotted_rows = [row for row in rows if int(row["bit_length"]) >= 1]
    max_bits = max(int(row["bit_length"]) for row in plotted_rows)
    max_time = max(float(row["mr_cumulative_ms"]) for row in plotted_rows)
    first_crossover_bits = find_first_crossover(plotted_rows)

    sqrt_rows = [row for row in plotted_rows if row["sqrt_cumulative_ms"] != ""]
    if sqrt_rows:
        max_time = max(max_time, max(float(row["sqrt_cumulative_ms"]) for row in sqrt_rows))
    max_time = max(max_time, 1.0)

    if log_scale:
        def y_transform(value: float) -> float:
            return math.log10(1.0 + value)

        transformed_max = y_transform(max_time)
        tick_values = [0.0]
        current = 0.01
        while current < max_time:
            tick_values.append(current)
            current *= 10.0
        tick_values.append(max_time)
        tick_values = sorted(set(tick_values))
        y_axis_label = "Cumulative search time (ms, log scale)"
        subtitle_suffix = "Log scale makes the early crossover visible."
    else:
        def y_transform(value: float) -> float:
            return value

        transformed_max = max_time
        y_ticks = 6
        tick_values = [max_time * tick / y_ticks for tick in range(y_ticks + 1)]
        y_axis_label = "Cumulative search time (ms)"
        subtitle_suffix = "Linear scale emphasizes the later growth."

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="38" text-anchor="middle" font-size="26" font-family="Segoe UI">Cumulative Time To Find One Prime Per Bit Length</text>',
        f'<text x="{width / 2:.1f}" y="64" text-anchor="middle" font-size="13" fill="#555555" font-family="Segoe UI">Bit lengths {int(plotted_rows[0]["bit_length"])} to {max_bits}. {subtitle_suffix}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<text x="{width / 2:.1f}" y="{height - 28}" text-anchor="middle" font-size="16" font-family="Segoe UI">Bit length</text>',
        f'<text x="30" y="{height / 2:.1f}" text-anchor="middle" font-size="16" font-family="Segoe UI" transform="rotate(-90 30,{height / 2:.1f})">{y_axis_label}</text>',
    ]

    x_ticks = 10

    for value in tick_values:
        y = scale(y_transform(value), 0, transformed_max, height - bottom, top)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#e8e8e8"/>')
        parts.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="12" font-family="Consolas">{format_tick(value)}</text>'
        )

    for tick in range(x_ticks + 1):
        value = int(round(max_bits * tick / x_ticks))
        x = scale(value, 1, max_bits, left, width - right)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" stroke="#f1f1f1"/>')
        parts.append(
            f'<text x="{x:.2f}" y="{height - bottom + 25}" text-anchor="middle" font-size="12" font-family="Consolas">{value}</text>'
        )

    series = [
        ("Square Root", "#111111", [row for row in plotted_rows if row["sqrt_cumulative_ms"] != ""], "sqrt_cumulative_ms"),
        ("Miller-Rabin", "#1f78b4", plotted_rows, "mr_cumulative_ms"),
    ]

    legend_x = width - 270
    legend_y = top + 20
    for idx, (label, color, series_rows, key) in enumerate(series):
        y = legend_y + idx * 24
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 28}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{legend_x + 38}" y="{y + 4}" font-size="13" font-family="Segoe UI">{label}</text>'
        )

        if not series_rows:
            continue

        points = []
        for row in series_rows:
            x = scale(float(row["bit_length"]), 1, max_bits, left, width - right)
            y_point = scale(y_transform(float(row[key])), 0, transformed_max, height - bottom, top)
            points.append(f"{x:.2f},{y_point:.2f}")
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(points)}"/>')

    note_y = top + 95
    if sqrt_cutoff_bits is None:
        note = f"Square-root search completed every bit length through {max_bits} bits."
    else:
        note = (
            f"Square-root search halted at {sqrt_cutoff_bits} bits after crossing the "
            f"{sqrt_limit_seconds:.1f}s per-bit limit."
        )
    parts.append(
        f'<text x="{left}" y="{note_y}" font-size="13" fill="#555555" font-family="Segoe UI">{note}</text>'
    )
    if first_crossover_bits is not None:
        parts.append(
            f'<text x="{left}" y="{note_y + 22}" font-size="13" fill="#555555" font-family="Segoe UI">First cumulative crossover: square-root is slower than Miller-Rabin by {first_crossover_bits} bits.</text>'
        )

    parts.append("</svg>")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text("\n".join(parts), encoding="utf-8")


def benchmark(args: argparse.Namespace) -> tuple[list[dict[str, object]], int | None]:
    rows: list[dict[str, object]] = []
    sqrt_cumulative_ms = 0.0
    mr_cumulative_ms = 0.0
    sqrt_cutoff_bits: int | None = None
    square_root_active = True

    for bits in range(args.min_bits, args.max_bits + 1):
        mr_result = search_first_prime(bits, is_probable_prime_miller_rabin)
        mr_cumulative_ms += float(mr_result["search_ms"])

        row: dict[str, object] = {
            "bit_length": bits,
            "prime": mr_result["prime"] if mr_result["prime"] is not None else "",
            "sqrt_search_ms": "",
            "sqrt_cumulative_ms": "",
            "sqrt_candidates_tested": "",
            "sqrt_status": "skipped_after_cutoff" if not square_root_active else "",
            "mr_search_ms": f'{float(mr_result["search_ms"]):.6f}',
            "mr_cumulative_ms": f"{mr_cumulative_ms:.6f}",
            "mr_candidates_tested": mr_result["candidates_tested"],
            "mr_status": mr_result["status"],
        }

        if square_root_active:
            sqrt_result = search_first_prime(bits, is_prime_square_root, args.sqrt_max_seconds_per_bit)
            row["sqrt_search_ms"] = f'{float(sqrt_result["search_ms"]):.6f}'
            row["sqrt_candidates_tested"] = sqrt_result["candidates_tested"]
            row["sqrt_status"] = sqrt_result["status"]

            if sqrt_result["status"] == "ok" or sqrt_result["status"] == "no-prime":
                sqrt_cumulative_ms += float(sqrt_result["search_ms"])
                row["sqrt_cumulative_ms"] = f"{sqrt_cumulative_ms:.6f}"
            else:
                square_root_active = False
                sqrt_cutoff_bits = bits

        rows.append(row)

        if args.progress_every > 0 and (bits - args.min_bits + 1) % args.progress_every == 0:
            sqrt_state = (
                "active"
                if square_root_active
                else f"stopped_at_{sqrt_cutoff_bits}"
            )
            print(
                f"processed_bits={bits} mr_cumulative_ms={mr_cumulative_ms:.3f} "
                f"sqrt_state={sqrt_state}"
            )

    return rows, sqrt_cutoff_bits


def main() -> None:
    args = parse_args()
    if args.min_bits <= 0:
        raise SystemExit("--min-bits must be positive.")
    if args.max_bits < args.min_bits:
        raise SystemExit("--max-bits must be greater than or equal to --min-bits.")
    if args.sqrt_max_seconds_per_bit <= 0:
        raise SystemExit("--sqrt-max-seconds-per-bit must be positive.")

    rows, sqrt_cutoff_bits = benchmark(args)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.csv)
    build_svg(rows, args.svg, sqrt_cutoff_bits, args.sqrt_max_seconds_per_bit, log_scale=False)
    build_svg(rows, args.log_svg, sqrt_cutoff_bits, args.sqrt_max_seconds_per_bit, log_scale=True)

    print(f"Wrote CSV: {args.csv}")
    print(f"Wrote SVG: {args.svg}")
    print(f"Wrote log SVG: {args.log_svg}")
    if sqrt_cutoff_bits is None:
        print("Square-root benchmark completed for the full requested bit-length range.")
    else:
        print(
            "Square-root benchmark stopped early at "
            f"{sqrt_cutoff_bits} bits because the per-bit time cap was exceeded."
        )


if __name__ == "__main__":
    main()
