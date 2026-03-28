import json
import sys
import time
from pathlib import Path


def miller_rabin(n: int, bases=(2, 3, 5, 7, 11, 13, 17, 19, 23)) -> bool:
    if n in (2, 3):
        return True
    if n < 2 or n % 2 == 0:
        return False

    for p in bases:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        witness_passed = False
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                witness_passed = True
                break
        if not witness_passed:
            return False
    return True


def parse_value(item: dict) -> int:
    if item["format"] == "hex":
        return int(item["value"], 16)
    if item["format"] == "dec":
        return int(item["value"], 10)
    raise ValueError(f"Unsupported format: {item['format']}")


def main() -> int:
    dataset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("prime_dataset.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    correct = 0
    total = 0

    print(f"Dataset: {dataset_path}")
    print()

    for item in dataset:
        n = parse_value(item)
        expected = item["expected_is_prime"]
        start = time.perf_counter()
        actual = miller_rabin(n)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        total += 1
        correct += int(actual == expected)

        print(
            f"{item['name']}: bits={n.bit_length()} "
            f"expected={'prime' if expected else 'composite'} "
            f"actual={'prime' if actual else 'composite'} "
            f"time_ms={elapsed_ms:.3f}"
        )

    print()
    print(f"Accuracy: {correct}/{total}")
    return 0 if correct == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
