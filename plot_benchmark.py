from pathlib import Path
import csv


def scale(value, src_min, src_max, dst_min, dst_max):
    if src_max == src_min:
        return dst_min
    return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)


rows = []
with Path("benchmark_times.csv").open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(
            {
                "bits": int(row["bits"]),
                "ordinary_ms": float(row["ordinary_ms"]),
                "fast_ms": float(row["fast_ms"]),
            }
        )

if not rows:
    raise SystemExit("No benchmark data found.")

width = 1000
height = 600
left = 80
right = 40
top = 40
bottom = 70

max_bits = max(row["bits"] for row in rows)
max_time = max(max(row["ordinary_ms"], row["fast_ms"]) for row in rows)
max_time = max(max_time, 1.0)

ordinary_points = []
fast_points = []

for row in rows:
    x = scale(row["bits"], 1, max_bits, left, width - right)
    y1 = scale(row["ordinary_ms"], 0, max_time, height - bottom, top)
    y2 = scale(row["fast_ms"], 0, max_time, height - bottom, top)
    ordinary_points.append(f"{x:.2f},{y1:.2f}")
    fast_points.append(f"{x:.2f},{y2:.2f}")

y_ticks = 5
x_ticks = 6

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" fill="white"/>',
    f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="black" />',
    f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="black" />',
    f'<text x="{width/2:.1f}" y="24" text-anchor="middle" font-size="20">Miller-Rabin Runtime vs Bit Length</text>',
    f'<text x="{width/2:.1f}" y="{height - 20}" text-anchor="middle" font-size="16">Bit length</text>',
    f'<text x="24" y="{height/2:.1f}" text-anchor="middle" font-size="16" transform="rotate(-90 24,{height/2:.1f})">Time (ms)</text>',
]

for i in range(y_ticks + 1):
    value = max_time * i / y_ticks
    y = scale(value, 0, max_time, height - bottom, top)
    parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" stroke="#dddddd" />')
    parts.append(f'<text x="{left - 10}" y="{y + 5:.2f}" text-anchor="end" font-size="12">{value:.1f}</text>')

for i in range(x_ticks + 1):
    value = 1 + (max_bits - 1) * i / x_ticks
    x = scale(value, 1, max_bits, left, width - right)
    parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" stroke="#f0f0f0" />')
    parts.append(f'<text x="{x:.2f}" y="{height - bottom + 20}" text-anchor="middle" font-size="12">{int(value)}</text>')

parts.append(f'<polyline fill="none" stroke="#cc3333" stroke-width="2" points="{" ".join(ordinary_points)}" />')
parts.append(f'<polyline fill="none" stroke="#2255cc" stroke-width="2" points="{" ".join(fast_points)}" />')

parts.append(f'<circle cx="{width - 210}" cy="{top + 12}" r="5" fill="#cc3333" />')
parts.append(f'<text x="{width - 195}" y="{top + 16}" font-size="13">Ordinary modulo</text>')
parts.append(f'<circle cx="{width - 210}" cy="{top + 34}" r="5" fill="#2255cc" />')
parts.append(f'<text x="{width - 195}" y="{top + 38}" font-size="13">Fast modulo</text>')
parts.append("</svg>")

Path("benchmark_plot.svg").write_text("\n".join(parts), encoding="utf-8")
print("Wrote benchmark_plot.svg")
