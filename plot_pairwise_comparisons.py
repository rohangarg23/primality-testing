from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_INPUT = Path("prime_cumulative_benchmark.csv")
DEFAULT_OUTPUT_DIR = Path("comparison_plots")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create pairwise cumulative-time comparison plots from prime_cumulative_benchmark.csv."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input benchmark CSV file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the SVG plots will be written.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "index": float(row["index"]),
                    "prime": float(row["prime"]),
                    "sqrt_cumulative_ms": float(row["sqrt_cumulative_ms"]),
                    "ordinary_mr_cumulative_ms": float(row["ordinary_mr_cumulative_ms"]),
                    "fast_mr_cumulative_ms": float(row["fast_mr_cumulative_ms"]),
                    "aks_cumulative_ms": float(row["aks_cumulative_ms"]),
                }
            )
    if not rows:
        raise SystemExit(f"No rows found in {path}")
    return rows


def scale(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max == src_min:
        return dst_min
    return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)


def build_plot(
    rows: list[dict[str, float]],
    title: str,
    subtitle: str,
    series: list[tuple[str, str, str]],
    output_path: Path,
) -> None:
    width = 1200
    height = 720
    left = 90
    right = 40
    top = 90
    bottom = 90

    max_prime = max(row["prime"] for row in rows)
    max_time = max(max(row[key] for row in rows) for key, _, _ in series)
    max_time = max(max_time, 1.0)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="38" text-anchor="middle" font-size="26" font-family="Segoe UI">{title}</text>',
        f'<text x="{width / 2:.1f}" y="64" text-anchor="middle" font-size="13" fill="#555555" font-family="Segoe UI">{subtitle}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#222222" stroke-width="1.5"/>',
        f'<text x="{width / 2:.1f}" y="{height - 25}" text-anchor="middle" font-size="16" font-family="Segoe UI">Prime value (x)</text>',
        f'<text x="28" y="{height / 2:.1f}" text-anchor="middle" font-size="16" font-family="Segoe UI" transform="rotate(-90 28,{height / 2:.1f})">Cumulative time (ms)</text>',
    ]

    y_ticks = 6
    x_ticks = 6

    for tick in range(y_ticks + 1):
        value = max_time * tick / y_ticks
        y = scale(value, 0, max_time, height - bottom, top)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#e7e7e7"/>')
        parts.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="12" font-family="Consolas">{value:.1f}</text>'
        )

    for tick in range(x_ticks + 1):
        value = max_prime * tick / x_ticks
        x = scale(value, 0, max_prime, left, width - right)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" stroke="#f0f0f0"/>')
        parts.append(
            f'<text x="{x:.2f}" y="{height - bottom + 24}" text-anchor="middle" font-size="12" font-family="Consolas">{int(value)}</text>'
        )

    legend_x = width - 320
    legend_y = top + 22
    for idx, (key, label, color) in enumerate(series):
        y = legend_y + idx * 24
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 28}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{legend_x + 38}" y="{y + 4}" font-size="13" font-family="Segoe UI">{label}</text>'
        )

        points = []
        for row in rows:
            x = scale(row["prime"], 0, max_prime, left, width - right)
            y_point = scale(row[key], 0, max_time, height - bottom, top)
            points.append(f"{x:.2f},{y_point:.2f}")
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.4" points="{" ".join(points)}"/>')

    parts.append("</svg>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input CSV not found: {args.input}")

    rows = read_rows(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plots = [
        (
            "Square Root vs AKS",
            "Cumulative time comparison from the generated benchmark CSV.",
            [
                ("sqrt_cumulative_ms", "Square Root", "#111111"),
                ("aks_cumulative_ms", "AKS", "#2e8b57"),
            ],
            args.output_dir / "square_root_vs_aks.svg",
        ),
        (
            "Square Root vs Miller-Rabin",
            "Square root plotted against both Miller-Rabin variants.",
            [
                ("sqrt_cumulative_ms", "Square Root", "#111111"),
                ("ordinary_mr_cumulative_ms", "Miller-Rabin Ordinary", "#c0392b"),
                ("fast_mr_cumulative_ms", "Miller-Rabin Fast", "#1f78b4"),
            ],
            args.output_dir / "square_root_vs_miller_rabin.svg",
        ),
        (
            "Miller-Rabin Fast vs Ordinary",
            "Direct cumulative comparison of the two Miller-Rabin modulo variants.",
            [
                ("ordinary_mr_cumulative_ms", "Miller-Rabin Ordinary", "#c0392b"),
                ("fast_mr_cumulative_ms", "Miller-Rabin Fast", "#1f78b4"),
            ],
            args.output_dir / "miller_rabin_fast_vs_ordinary.svg",
        ),
        (
            "AKS vs Miller-Rabin",
            "AKS plotted against both Miller-Rabin variants.",
            [
                ("aks_cumulative_ms", "AKS", "#2e8b57"),
                ("ordinary_mr_cumulative_ms", "Miller-Rabin Ordinary", "#c0392b"),
                ("fast_mr_cumulative_ms", "Miller-Rabin Fast", "#1f78b4"),
            ],
            args.output_dir / "aks_vs_miller_rabin.svg",
        ),
    ]

    for title, subtitle, series, output_path in plots:
        build_plot(rows, title, subtitle, series, output_path)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
