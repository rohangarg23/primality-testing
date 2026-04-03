#include <chrono>
#include <iostream>
#include <string>

#include "aks.h"
#include "big_int.h"
#include "miller_rabin.h"

using namespace std;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "usage: primality_backend.exe check <dec|hex> <value> | generate <bits>\n";
        return 1;
    }

    string command = argv[1];

    if (command == "generate") {
        if (argc != 3) {
            cerr << "usage: primality_backend.exe generate <bits>\n";
            return 1;
        }

        size_t bits = static_cast<size_t>(stoull(argv[2]));
        auto generate_start = chrono::steady_clock::now();
        big_int prime = generate_probable_prime(bits);
        auto generate_end = chrono::steady_clock::now();
        chrono::duration<double, milli> generate_ms = generate_end - generate_start;

        cout << "number=" << prime.to_string() << '\n';
        cout << "bit_length=" << prime.bit_length() << '\n';
        cout << "generation_ms=" << generate_ms.count() << '\n';
        return 0;
    }

    if (command != "check" || argc != 4) {
        cerr << "usage: primality_backend.exe check <dec|hex> <value> | generate <bits>\n";
        return 1;
    }

    string format = argv[2];
    string value = argv[3];

    big_int n;
    if (format == "hex") {
        n = big_int::from_hex(value);
    } else if (format == "dec") {
        n = big_int(value);
    } else {
        cerr << "invalid format\n";
        return 1;
    }

    auto ordinary_start = chrono::steady_clock::now();
    bool ordinary = miller_rabin(n, false);
    auto ordinary_end = chrono::steady_clock::now();

    auto fast_start = chrono::steady_clock::now();
    bool fast = miller_rabin(n, true);
    auto fast_end = chrono::steady_clock::now();

    auto aks_start = chrono::steady_clock::now();
    bool aks = aks_primality_test(n);
    auto aks_end = chrono::steady_clock::now();

    auto previous_start = chrono::steady_clock::now();
    big_int previous_prime;
    bool has_previous_prime = previous_probable_prime(n, previous_prime, true);
    auto previous_end = chrono::steady_clock::now();

    auto next_start = chrono::steady_clock::now();
    big_int next_prime = next_probable_prime(n, true);
    auto next_end = chrono::steady_clock::now();

    chrono::duration<double, milli> ordinary_ms = ordinary_end - ordinary_start;
    chrono::duration<double, milli> fast_ms = fast_end - fast_start;
    chrono::duration<double, milli> aks_ms = aks_end - aks_start;
    chrono::duration<double, milli> previous_ms = previous_end - previous_start;
    chrono::duration<double, milli> next_ms = next_end - next_start;

    cout << "number=" << n.to_string() << '\n';
    cout << "bit_length=" << n.bit_length() << '\n';
    cout << "ordinary=" << (ordinary ? "prime" : "composite") << '\n';
    cout << "ordinary_ms=" << ordinary_ms.count() << '\n';
    cout << "fast=" << (fast ? "prime" : "composite") << '\n';
    cout << "fast_ms=" << fast_ms.count() << '\n';
    cout << "aks=" << (aks ? "prime" : "composite") << '\n';
    cout << "aks_ms=" << aks_ms.count() << '\n';
    cout << "previous_prime_found=" << (has_previous_prime ? "yes" : "no") << '\n';
    cout << "previous_prime=" << (has_previous_prime ? previous_prime.to_string() : "none") << '\n';
    cout << "previous_prime_ms=" << previous_ms.count() << '\n';
    cout << "next_prime=" << next_prime.to_string() << '\n';
    cout << "next_prime_ms=" << next_ms.count() << '\n';
    cout << "neighbor_method=fast_miller_rabin" << '\n';
    cout << "agree=" << (ordinary == fast ? "yes" : "no") << '\n';
    cout << "all_agree=" << ((ordinary == fast && fast == aks) ? "yes" : "no") << '\n';

    return 0;
}
