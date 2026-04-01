#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

#include "big_int.h"
#include "miller_rabin.h"

using namespace std;

int main() {
    ifstream in("primes_100_to_200_bits.csv");
    if (!in) {
        cerr << "Could not open primes_100_to_200_bits.csv\n";
        return 1;
    }

    string line;
    getline(in, line);

    int total = 0;
    int ordinary_correct = 0;
    int fast_correct = 0;
    double ordinary_total_ms = 0.0;
    double fast_total_ms = 0.0;

    cout << fixed << setprecision(3);

    while (getline(in, line)) {
        if (line.empty()) {
            continue;
        }

        stringstream ss(line);
        string bits_str;
        string value_str;
        getline(ss, bits_str, ',');
        getline(ss, value_str);

        int bits = stoi(bits_str);
        big_int n(value_str);

        auto ordinary_start = chrono::steady_clock::now();
        bool ordinary = miller_rabin(n, false);
        auto ordinary_end = chrono::steady_clock::now();

        auto fast_start = chrono::steady_clock::now();
        bool fast = miller_rabin(n, true);
        auto fast_end = chrono::steady_clock::now();

        chrono::duration<double, milli> ordinary_ms = ordinary_end - ordinary_start;
        chrono::duration<double, milli> fast_ms = fast_end - fast_start;

        ++total;
        ordinary_correct += ordinary ? 1 : 0;
        fast_correct += fast ? 1 : 0;
        ordinary_total_ms += ordinary_ms.count();
        fast_total_ms += fast_ms.count();

        cout << "bits=" << bits
             << " ordinary_ms=" << ordinary_ms.count()
             << " fast_ms=" << fast_ms.count()
             << " ordinary=" << (ordinary ? "prime" : "composite")
             << " fast=" << (fast ? "prime" : "composite")
             << '\n';
    }

    cout << "\nSummary\n";
    cout << "total_cases=" << total << '\n';
    cout << "ordinary_accuracy=" << ordinary_correct << "/" << total << '\n';
    cout << "fast_accuracy=" << fast_correct << "/" << total << '\n';
    cout << "ordinary_total_ms=" << ordinary_total_ms << '\n';
    cout << "fast_total_ms=" << fast_total_ms << '\n';
    cout << "ordinary_avg_ms=" << (total ? ordinary_total_ms / total : 0.0) << '\n';
    cout << "fast_avg_ms=" << (total ? fast_total_ms / total : 0.0) << '\n';

    return 0;
}
