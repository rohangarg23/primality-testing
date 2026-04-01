#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "big_int.h"
#include "miller_rabin.h"

using namespace std;

namespace {

struct TimingResult {
    double ordinary_ms;
    double fast_ms;
    bool ordinary_answer;
    bool fast_answer;
};

TimingResult benchmark_number(const big_int& n) {
    auto start = chrono::steady_clock::now();
    bool ordinary = miller_rabin(n, false);
    auto mid = chrono::steady_clock::now();
    bool fast = miller_rabin(n, true);
    auto finish = chrono::steady_clock::now();

    chrono::duration<double, milli> ordinary_ms = mid - start;
    chrono::duration<double, milli> fast_ms = finish - mid;

    return {ordinary_ms.count(), fast_ms.count(), ordinary, fast};
}

big_int generate_candidate(int bits) {
    if (bits <= 0) {
        return big_int(0);
    }

    mt19937_64 rng(1234567ULL + static_cast<unsigned long long>(bits) * 97ULL);
    uniform_int_distribution<int> bit_dist(0, 1);

    string binary(bits, '0');
    for (int i = 0; i < bits; ++i) {
        binary[i] = static_cast<char>('0' + bit_dist(rng));
    }

    big_int candidate(0);
    for (char bit : binary) {
        candidate = candidate * 2;
        if (bit == '1') {
            candidate = candidate + big_int(1);
        }
    }

    return candidate;
}

}  // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const string reference_hex =
        "046fe40ff28041a690af557734e885052b879535574af06db2b787f926e85880060199697023504dd9c0d0e23b7e01e922538c586d676c61c972e1356ff053e78fdb481b7e5909c7dcf82155d713e915d8cb694a2f46320cb10868f03b98566022d225a97f1ee3cc26794b1e481abc61458146c48dd452ba81d06fab826c3ea58585500154d36c9076b0e1fd3d47222d2e8ae28fd5586818db16cc2fb9449a399ec9c22551448bde17c1e752506464424123af8de6b690f9407aaf52d8d279d11292fca1c32d0d9c3adb061f530fe10eca96e2bb2e4be1f6df1d7130aa21f78d31a312af5bdf56660247d6651168088ba0f1a7e4ec202f8efe5eade78726abf365c735736f578a57";

    big_int reference = big_int::from_hex(reference_hex);
    TimingResult reference_result = benchmark_number(reference);

    cout << fixed << setprecision(3);
    cout << "Single dataset case benchmark\n";
    cout << "Bit length: " << reference.bit_length() << '\n';
    cout << "Ordinary modulo time (ms): " << reference_result.ordinary_ms << '\n';
    cout << "Fast modulo time (ms): " << reference_result.fast_ms << '\n';
    cout << "Ordinary result: " << (reference_result.ordinary_answer ? "probably prime" : "composite") << '\n';
    cout << "Fast result: " << (reference_result.fast_answer ? "probably prime" : "composite") << '\n';

    ofstream csv("benchmark_times.csv");
    csv << "bits,ordinary_ms,fast_ms,ordinary_result,fast_result\n";

    vector<int> points;
    for (int bit = 1; bit <= 64; ++bit) {
        points.push_back(bit);
    }
    for (int bit = 100; bit <= 3000; bit += 100) {
        points.push_back(bit);
    }

    cout << "\nRange benchmark\n";
    for (int bits : points) {
        big_int candidate = generate_candidate(bits);
        TimingResult current = benchmark_number(candidate);
        csv << bits << ','
            << current.ordinary_ms << ','
            << current.fast_ms << ','
            << (current.ordinary_answer ? "prime" : "composite") << ','
            << (current.fast_answer ? "prime" : "composite") << '\n';
        cout << "bits=" << setw(4) << bits
             << " ordinary_ms=" << setw(10) << current.ordinary_ms
             << " fast_ms=" << setw(10) << current.fast_ms << '\n';
    }

    return 0;
}
