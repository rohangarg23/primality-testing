from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import fmean

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "This script requires matplotlib. Install it with:\n"
        "pip install matplotlib"
    ) from exc


DEFAULT_AKS_CSV = Path("aks_runtime_samples.csv")
DEFAULT_MR_CSV = Path("miller_rabin_runtime_samples.csv")
DEFAULT_OUTPUT_DIR = Path("images")

BIT_COLUMNS = ("bit_length", "bits", "bit")
RUNTIME_COLUMNS = (
    "runtime_ms",
    "time_ms",
    "avg_runtime_ms",
    "average_runtime_ms",
    "ms",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the AKS/Miller-Rabin report figures from CSV runtime samples. "
            "The expected default inputs are aks_runtime_samples.csv and "
            "miller_rabin_runtime_samples.csv."
        )
    )
    parser.add_argument(
        "--aks-csv",
        type=Path,
        default=DEFAULT_AKS_CSV,
        help="CSV file containing AKS runtime samples by bit length.",
    )
    parser.add_argument(
        "--mr-csv",
        type=Path,
        default=DEFAULT_MR_CSV,
        help="CSV file containing Miller-Rabin runtime samples by bit length.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the generated PNG figures will be written.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=220,
        help="PNG output DPI. Default: 220.",
    )
    return parser.parse_args()


def pick_column(fieldnames: list[str], candidates: tuple[str, ...], label: str) -> str:
    normalized = {name.strip().lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError(
        f"Could not find a {label} column. Expected one of: {', '.join(candidates)}. "
        f"Found columns: {', '.join(fieldnames)}"
    )


def load_runtime_samples(path: Path) -> list[tuple[int, float]]:
    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {path}\n"
            "Create the file with at least these columns:\n"
            "  bit_length,runtime_ms"
        )

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {path}")

        bit_column = pick_column(reader.fieldnames, BIT_COLUMNS, "bit-length")
        runtime_column = pick_column(reader.fieldnames, RUNTIME_COLUMNS, "runtime")

        samples: list[tuple[int, float]] = []
        for row in reader:
            bit_text = (row.get(bit_column) or "").strip()
            runtime_text = (row.get(runtime_column) or "").strip()
            if not bit_text or not runtime_text:
                continue

            bit_length = int(float(bit_text))
            runtime_ms = float(runtime_text)
            if bit_length <= 0 or runtime_ms < 0:
                continue
            samples.append((bit_length, runtime_ms))

    if not samples:
        raise ValueError(f"No valid runtime rows were found in {path}")

    return samples


def average_by_bit_length(samples: list[tuple[int, float]]) -> dict[int, float]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for bit_length, runtime_ms in samples:
        grouped[bit_length].append(runtime_ms)
    return {bit_length: fmean(values) for bit_length, values in grouped.items()}


def sorted_series(data: dict[int, float]) -> tuple[list[int], list[float]]:
    bits = sorted(data)
    return bits, [data[bit_length] for bit_length in bits]


def configure_style() -> None:
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.style.use("default")

    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "axes.titlesize": 15,
            "axes.labelsize": 12,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def finalize_plot(fig, ax, output_path: Path, dpi: int) -> None:
    ax.set_xlabel("Bit length")
    ax.set_ylabel("Runtime (ms)")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_runtime_with_average(
    samples: list[tuple[int, float]],
    averages: dict[int, float],
    title: str,
    subtitle: str,
    output_path: Path,
    dpi: int,
) -> None:
    sample_bits = [bit_length for bit_length, _ in samples]
    sample_times = [runtime_ms for _, runtime_ms in samples]
    average_bits, average_times = sorted_series(averages)

    fig, ax = plt.subplots()
    ax.scatter(
        sample_bits,
        sample_times,
        s=20,
        alpha=0.35,
        color="#4C72B0",
        edgecolors="none",
        label="Measured samples",
    )
    ax.plot(
        average_bits,
        average_times,
        color="#C44E52",
        linewidth=2.5,
        label="Average runtime",
    )
    ax.set_title(title)
    ax.text(
        0.5,
        1.01,
        subtitle,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    ax.legend(loc="upper left")
    finalize_plot(fig, ax, output_path, dpi)


def plot_direct_comparison(
    aks_averages: dict[int, float],
    mr_averages: dict[int, float],
    output_path: Path,
    dpi: int,
) -> None:
    common_bits = sorted(set(aks_averages) & set(mr_averages))
    if not common_bits:
        raise ValueError("AKS and Miller-Rabin CSV files do not share any common bit lengths.")

    aks_values = [aks_averages[bit_length] for bit_length in common_bits]
    mr_values = [mr_averages[bit_length] for bit_length in common_bits]

    fig, ax = plt.subplots()
    ax.plot(common_bits, aks_values, color="#2E8B57", linewidth=2.5, label="AKS average runtime")
    ax.plot(common_bits, mr_values, color="#1F77B4", linewidth=2.5, label="Miller-Rabin average runtime")
    ax.set_title("AKS vs Miller-Rabin Runtime (Shared Bit-Length Range)")
    ax.text(
        0.5,
        1.01,
        "Both curves are plotted on the common bit-length range present in both CSV files.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    ax.legend(loc="upper left")
    finalize_plot(fig, ax, output_path, dpi)


def plot_ratio(
    aks_averages: dict[int, float],
    mr_averages: dict[int, float],
    output_path: Path,
    dpi: int,
) -> None:
    common_bits = sorted(set(aks_averages) & set(mr_averages))
    if not common_bits:
        raise ValueError("AKS and Miller-Rabin CSV files do not share any common bit lengths.")

    ratio_bits: list[int] = []
    ratio_values: list[float] = []
    for bit_length in common_bits:
        mr_runtime = mr_averages[bit_length]
        if mr_runtime <= 0:
            continue
        ratio_bits.append(bit_length)
        ratio_values.append(aks_averages[bit_length] / mr_runtime)

    if not ratio_bits:
        raise ValueError("No valid AKS/Miller-Rabin ratios could be computed from the CSV data.")

    fig, ax = plt.subplots()
    ax.plot(ratio_bits, ratio_values, color="#7A5195", linewidth=2.5)
    ax.fill_between(ratio_bits, ratio_values, color="#7A5195", alpha=0.12)
    ax.set_title("AKS-to-Miller-Rabin Average Runtime Ratio")
    ax.text(
        0.5,
        1.01,
        "Each point shows average AKS runtime divided by average Miller-Rabin runtime.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    ax.set_xlabel("Bit length")
    ax.set_ylabel("AKS average / Miller-Rabin average")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_extended_comparison(
    aks_averages: dict[int, float],
    mr_averages: dict[int, float],
    output_path: Path,
    dpi: int,
) -> None:
    aks_bits, aks_values = sorted_series(aks_averages)
    mr_bits, mr_values = sorted_series(mr_averages)

    fig, ax = plt.subplots()
    ax.plot(aks_bits, aks_values, color="#2E8B57", linewidth=2.5, label="AKS average runtime")
    ax.plot(mr_bits, mr_values, color="#1F77B4", linewidth=2.5, label="Miller-Rabin average runtime")
    ax.set_title("Extended AKS vs Miller-Rabin Runtime Comparison")
    ax.text(
        0.5,
        1.01,
        "AKS and Miller-Rabin are shown on the full ranges present in their respective CSV files.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    ax.legend(loc="upper left")
    finalize_plot(fig, ax, output_path, dpi)


def main() -> None:
    args = parse_args()
    configure_style()

    aks_samples = load_runtime_samples(args.aks_csv)
    mr_samples = load_runtime_samples(args.mr_csv)

    aks_averages = average_by_bit_length(aks_samples)
    mr_averages = average_by_bit_length(mr_samples)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    outputs = [
        args.output_dir / "aks_runtime_plot.png",
        args.output_dir / "miller_rabin_runtime_plot.png",
        args.output_dir / "aks_vs_miller_rabin_plot.png",
        args.output_dir / "aks_miller_rabin_ratio_plot.png",
        args.output_dir / "aks_vs_miller_rabin_extended_plot.png",
    ]

    plot_runtime_with_average(
        aks_samples,
        aks_averages,
        title="AKS Runtime vs Bit Length",
        subtitle="Scatter points are measured samples; the red curve is the average runtime at each bit length.",
        output_path=outputs[0],
        dpi=args.dpi,
    )
    plot_runtime_with_average(
        mr_samples,
        mr_averages,
        title="Miller-Rabin Runtime vs Bit Length",
        subtitle="Scatter points are measured samples; the red curve is the average runtime at each bit length.",
        output_path=outputs[1],
        dpi=args.dpi,
    )
    plot_direct_comparison(aks_averages, mr_averages, outputs[2], args.dpi)
    plot_ratio(aks_averages, mr_averages, outputs[3], args.dpi)
    plot_extended_comparison(aks_averages, mr_averages, outputs[4], args.dpi)

    for output_path in outputs:
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
