import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path



BACKEND_PATH = Path(__file__).with_name("primality_backend.exe")


def normalize_number(raw: str) -> str:
    text = "".join(raw.split())
    if not text:
        raise ValueError("Please enter a number.")
    return text


def run_backend_command(args: list[str]) -> dict[str, str]:
    if not BACKEND_PATH.exists():
        raise RuntimeError(
            "C++ backend not found. Build it with:\n"
            "g++ -std=c++17 -O2 -Wall -Wextra -pedantic "
            "primality_backend.cpp big_int.cpp miller_rabin.cpp aks.cpp -o primality_backend.exe"
        )

    completed = subprocess.run(
        [str(BACKEND_PATH), *args],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or "Backend failed."
        raise RuntimeError(error_text)

    data: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        data[key.strip()] = val.strip()
    return data


def call_cpp_backend(raw: str, fmt: str) -> dict[str, str]:
    value = normalize_number(raw)
    return run_backend_command(["check", fmt, value])


def call_cpp_prime_generator(bit_count: str) -> dict[str, str]:
    value = "".join(bit_count.split())
    if not value:
        raise ValueError("Please enter a bit length.")
    return run_backend_command(["generate", value])


class PrimalityApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Primality Checker")
        self.root.geometry("760x520")

        self.number_format = tk.StringVar(value="dec")
        self.bit_length_var = tk.StringVar(value="128")

        container = ttk.Frame(root, padding=16)
        container.pack(fill="both", expand=True)

        title = ttk.Label(container, text="Primality Checker", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        format_row = ttk.Frame(container)
        format_row.pack(fill="x", pady=(0, 10))

        ttk.Label(format_row, text="Input format:").pack(side="left")
        ttk.Radiobutton(format_row, text="Decimal", variable=self.number_format, value="dec").pack(side="left", padx=(10, 0))
        ttk.Radiobutton(format_row, text="Hexadecimal", variable=self.number_format, value="hex").pack(side="left", padx=(10, 0))

        ttk.Label(container, text="Enter number:").pack(anchor="w")

        self.input_box = tk.Text(container, height=8, wrap="word", font=("Consolas", 11))
        self.input_box.pack(fill="both", expand=False, pady=(6, 12))

        button_row = ttk.Frame(container)
        button_row.pack(fill="x", pady=(0, 12))

        ttk.Button(button_row, text="Check Prime", command=self.check_prime).pack(side="left")
        ttk.Button(button_row, text="Clear", command=self.clear_all).pack(side="left", padx=(10, 0))

        generate_row = ttk.Frame(container)
        generate_row.pack(fill="x", pady=(0, 12))

        ttk.Label(generate_row, text="Generate probable prime with bit length:").pack(side="left")
        ttk.Entry(generate_row, textvariable=self.bit_length_var, width=10).pack(side="left", padx=(10, 10))
        ttk.Button(generate_row, text="Generate Prime", command=self.generate_prime).pack(side="left")

        self.summary_var = tk.StringVar(
            value="Enter a number and click Check Prime. The app also shows previous and next probable primes."
        )
        ttk.Label(container, textvariable=self.summary_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        self.result_box = tk.Text(container, height=14, wrap="word", font=("Consolas", 11))
        self.result_box.pack(fill="both", expand=True)
        self.result_box.configure(state="disabled")

    def clear_all(self) -> None:
        self.input_box.delete("1.0", "end")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")
        self.summary_var.set("Enter a number and click Check Prime. The app also shows previous and next probable primes.")

    def write_result(self, text: str) -> None:
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", text)
        self.result_box.configure(state="disabled")

    def check_prime(self) -> None:
        raw = self.input_box.get("1.0", "end")
        try:
            result = call_cpp_backend(raw, self.number_format.get())
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        summary = (
            "All methods agree. Neighbor search uses fast Miller-Rabin."
            if result["all_agree"] == "yes"
            else "At least one method disagrees. Neighbor search uses fast Miller-Rabin."
        )
        self.summary_var.set(summary)

        previous_prime_line = (
            result["previous_prime"]
            if result.get("previous_prime_found") == "yes"
            else "None below 2"
        )

        result_text = (
            f"Number:\n{result['number']}\n\n"
            f"Bit length: {result['bit_length']}\n\n"
            f"Ordinary modulo Miller-Rabin:\n"
            f"  Result: {'probably prime' if result['ordinary'] == 'prime' else 'composite'}\n"
            f"  Time: {float(result['ordinary_ms']):.3f} ms\n\n"
            f"Fast modulo Miller-Rabin:\n"
            f"  Result: {'probably prime' if result['fast'] == 'prime' else 'composite'}\n"
            f"  Time: {float(result['fast_ms']):.3f} ms\n\n"
            f"AKS primality test:\n"
            f"  Result: {'prime' if result['aks'] == 'prime' else 'composite'}\n"
            f"  Time: {float(result['aks_ms']):.3f} ms\n\n"
            f"Neighbor search using fast Miller-Rabin:\n"
            f"  Previous probable prime: {previous_prime_line}\n"
            f"  Previous search time: {float(result['previous_prime_ms']):.3f} ms\n"
            f"  Next probable prime: {result['next_prime']}\n"
            f"  Next search time: {float(result['next_prime_ms']):.3f} ms\n\n"
            f"Miller-Rabin agreement: {result['agree']}\n"
            f"All methods agree: {result['all_agree']}\n"
        )
        self.write_result(result_text)

    def generate_prime(self) -> None:
        try:
            result = call_cpp_prime_generator(self.bit_length_var.get())
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Generation failed", str(exc))
            return

        self.summary_var.set("Probable prime generated by the C++ backend.")
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", result["number"])

        result_text = (
            f"Generated probable prime:\n{result['number']}\n\n"
            f"Bit length: {result['bit_length']}\n"
            f"Generation time: {float(result['generation_ms']):.3f} ms\n"
        )
        self.write_result(result_text)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = PrimalityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
