#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>

#include "big_int.h"
#include "miller_rabin.h"

using namespace std;

namespace {

string trim_copy(string s) {
    auto not_space = [](unsigned char ch) { return !isspace(ch); };
    s.erase(s.begin(), find_if(s.begin(), s.end(), not_space));
    s.erase(find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

string extract_json_string(const string& line) {
    size_t first = line.find('"', line.find(':'));
    if (first == string::npos) {
        return "";
    }
    size_t second = line.find('"', first + 1);
    if (second == string::npos) {
        return "";
    }
    return line.substr(first + 1, second - first - 1);
}

void print_single_result(const big_int& n) {
    bool ordinary_result = miller_rabin(n, false);
    bool fast_result = miller_rabin(n, true);

    cout << "Number: " << n << '\n';
    cout << "Bit length: " << n.bit_length() << '\n';
    cout << "Miller-Rabin using ordinary modulo: "
         << (ordinary_result ? "probably prime" : "composite") << '\n';
    cout << "Miller-Rabin using fast modulo: "
         << (fast_result ? "probably prime" : "composite") << '\n';
    cout << "Both methods agree: " << ((ordinary_result == fast_result) ? "yes" : "no") << '\n';
}

void run_decimal_mode() {
    cout << "Enter a decimal number: ";
    string input;
    cin >> input;
    print_single_result(big_int(input));
}

void run_hex_mode() {
    cout << "Enter a hexadecimal number: ";
    string input;
    cin >> input;
    print_single_result(big_int::from_hex(input));
}

void run_dataset_mode() {
    cout << "Enter dataset file path: ";
    string path;
    cin >> path;

    cout << "Enter minimum bit length to test (recommended 2000): ";
    size_t min_bits = 2000;
    cin >> min_bits;

    ifstream in(path);
    if (!in) {
        cout << "Could not open file.\n";
        return;
    }

    string value_hex;
    string result_text;
    int total_cases = 0;
    int tested_cases = 0;
    int skipped_cases = 0;
    int ordinary_correct = 0;
    int fast_correct = 0;
    int agreement_count = 0;
    int expected_primes = 0;
    int expected_composites = 0;
    vector<string> mismatches;

    string line;
    while (getline(in, line)) {
        string trimmed = trim_copy(line);
        if (trimmed.rfind("\"value\"", 0) == 0) {
            value_hex = extract_json_string(trimmed);
        } else if (trimmed.rfind("\"result\"", 0) == 0) {
            result_text = extract_json_string(trimmed);

            if (value_hex.empty()) {
                continue;
            }

            ++total_cases;
            bool expected_prime = (result_text == "valid");
            big_int n = big_int::from_hex(value_hex);
            size_t bits = n.bit_length();

            if (bits < min_bits) {
                ++skipped_cases;
                value_hex.clear();
                result_text.clear();
                continue;
            }

            ++tested_cases;
            if (expected_prime) {
                ++expected_primes;
            } else {
                ++expected_composites;
            }

            bool ordinary = miller_rabin(n, false);
            bool fast = miller_rabin(n, true);

            if (ordinary == expected_prime) {
                ++ordinary_correct;
            }
            if (fast == expected_prime) {
                ++fast_correct;
            }
            if (ordinary == fast) {
                ++agreement_count;
            }

            if (ordinary != expected_prime || fast != expected_prime) {
                string prefix = value_hex.substr(0, min<size_t>(32, value_hex.size()));
                mismatches.push_back(
                    "bits=" + to_string(bits) +
                    ", expected=" + string(expected_prime ? "prime" : "composite") +
                    ", ordinary=" + string(ordinary ? "prime" : "composite") +
                    ", fast=" + string(fast ? "prime" : "composite") +
                    ", hex_prefix=" + prefix + "...");
            }

            value_hex.clear();
            result_text.clear();
        }
    }

    uintmax_t file_size = 0;
    error_code ec;
    file_size = filesystem::file_size(path, ec);

    cout << "\nDataset summary\n";
    cout << "File: " << path << '\n';
    if (!ec) {
        cout << "File size: " << file_size << " bytes\n";
    }
    cout << "Total vectors seen: " << total_cases << '\n';
    cout << "Vectors tested with bit length >= " << min_bits << ": " << tested_cases << '\n';
    cout << "Vectors skipped for being smaller: " << skipped_cases << '\n';
    cout << "Expected primes in tested set: " << expected_primes << '\n';
    cout << "Expected composites in tested set: " << expected_composites << '\n';
    cout << "Ordinary modulo accuracy: " << ordinary_correct << "/" << tested_cases << '\n';
    cout << "Fast modulo accuracy: " << fast_correct << "/" << tested_cases << '\n';
    cout << "Agreement between both methods: " << agreement_count << "/" << tested_cases << '\n';

    if (mismatches.empty()) {
        cout << "No mismatches found in the tested subset.\n";
    } else {
        cout << "Mismatches:\n";
        for (const string& mismatch : mismatches) {
            cout << "  " << mismatch << '\n';
        }
    }
}

}  // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cout << "Choose mode:\n";
    cout << "1. Test one decimal number\n";
    cout << "2. Test one hexadecimal number\n";
    cout << "3. Run batch accuracy test from a Wycheproof JSON file\n";
    cout << "Enter choice: ";

    int choice = 0;
    if (!(cin >> choice)) {
        return 0;
    }

    if (choice == 1) {
        run_decimal_mode();
    } else if (choice == 2) {
        run_hex_mode();
    } else if (choice == 3) {
        run_dataset_mode();
    } else {
        cout << "Invalid choice.\n";
    }

    return 0;
}
