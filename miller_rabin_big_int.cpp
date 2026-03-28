#include <bits/stdc++.h>
using namespace std;

class big_int {
    static const int base = 1000000000;
    static const int digits = 9;
    vector<int> a;

    void trim() {
        while (a.size() > 1 && a.back() == 0) {
            a.pop_back();
        }
        if (a.empty()) {
            a.push_back(0);
        }
    }

    static int block_to_int(const string& s) {
        int num = 0;
        for (char ch : s) {
            num = num * 10 + (ch - '0');
        }
        return num;
    }

public:
    big_int() : a(1, 0) {}

    big_int(long long value) {
        if (value == 0) {
            a.push_back(0);
            return;
        }
        while (value > 0) {
            a.push_back(static_cast<int>(value % base));
            value /= base;
        }
    }

    big_int(const string& s) {
        a.clear();
        for (int i = static_cast<int>(s.size()); i > 0; i -= digits) {
            int l = max(0, i - digits);
            a.push_back(block_to_int(s.substr(l, i - l)));
        }
        trim();
    }

    bool is_zero() const {
        return a.size() == 1 && a[0] == 0;
    }

    bool is_odd() const {
        return a[0] & 1;
    }

    string to_string() const {
        stringstream ss;
        ss << a.back();
        for (int i = static_cast<int>(a.size()) - 2; i >= 0; --i) {
            ss << setw(digits) << setfill('0') << a[i];
        }
        return ss.str();
    }

    friend ostream& operator<<(ostream& out, const big_int& value) {
        out << value.to_string();
        return out;
    }

    int compare(const big_int& other) const {
        if (a.size() != other.a.size()) {
            return a.size() < other.a.size() ? -1 : 1;
        }
        for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
            if (a[i] != other.a[i]) {
                return a[i] < other.a[i] ? -1 : 1;
            }
        }
        return 0;
    }

    bool operator<(const big_int& other) const { return compare(other) < 0; }
    bool operator>(const big_int& other) const { return compare(other) > 0; }
    bool operator<=(const big_int& other) const { return compare(other) <= 0; }
    bool operator>=(const big_int& other) const { return compare(other) >= 0; }
    bool operator==(const big_int& other) const { return a == other.a; }
    bool operator!=(const big_int& other) const { return !(*this == other); }

    big_int operator+(const big_int& other) const {
        big_int res;
        int n = max(a.size(), other.a.size());
        res.a.assign(n, 0);

        long long carry = 0;
        for (int i = 0; i < n; ++i) {
            long long sum = carry;
            if (i < static_cast<int>(a.size())) sum += a[i];
            if (i < static_cast<int>(other.a.size())) sum += other.a[i];
            res.a[i] = static_cast<int>(sum % base);
            carry = sum / base;
        }
        if (carry) {
            res.a.push_back(static_cast<int>(carry));
        }
        res.trim();
        return res;
    }

    big_int operator-(const big_int& other) const {
        big_int res;
        res.a.assign(a.size(), 0);

        long long borrow = 0;
        for (int i = 0; i < static_cast<int>(a.size()); ++i) {
            long long cur = a[i] - borrow - (i < static_cast<int>(other.a.size()) ? other.a[i] : 0LL);
            if (cur < 0) {
                cur += base;
                borrow = 1;
            } else {
                borrow = 0;
            }
            res.a[i] = static_cast<int>(cur);
        }
        res.trim();
        return res;
    }

    big_int operator*(int m) const {
        if (m == 0 || is_zero()) {
            return big_int(0);
        }

        big_int res;
        res.a.assign(a.size(), 0);
        long long carry = 0;
        for (int i = 0; i < static_cast<int>(a.size()); ++i) {
            long long cur = 1LL * a[i] * m + carry;
            res.a[i] = static_cast<int>(cur % base);
            carry = cur / base;
        }
        while (carry > 0) {
            res.a.push_back(static_cast<int>(carry % base));
            carry /= base;
        }
        res.trim();
        return res;
    }

    big_int operator*(const big_int& other) const {
        if (is_zero() || other.is_zero()) {
            return big_int(0);
        }

        big_int res;
        res.a.assign(a.size() + other.a.size(), 0);
        for (int i = 0; i < static_cast<int>(a.size()); ++i) {
            long long carry = 0;
            for (int j = 0; j < static_cast<int>(other.a.size()) || carry > 0; ++j) {
                long long cur = res.a[i + j] + carry;
                if (j < static_cast<int>(other.a.size())) {
                    cur += 1LL * a[i] * other.a[j];
                }
                res.a[i + j] = static_cast<int>(cur % base);
                carry = cur / base;
            }
        }
        res.trim();
        return res;
    }

    big_int div2() const {
        big_int res;
        res.a.assign(a.size(), 0);
        long long carry = 0;
        for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
            long long cur = a[i] + carry * base;
            res.a[i] = static_cast<int>(cur / 2);
            carry = cur % 2;
        }
        res.trim();
        return res;
    }

    int mod_int(int m) const {
        long long rem = 0;
        for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
            rem = (rem * base + a[i]) % m;
        }
        return static_cast<int>(rem);
    }

    pair<big_int, big_int> divmod(const big_int& v) const {
        if (v.is_zero()) {
            throw runtime_error("division by zero");
        }

        big_int res;
        big_int cur(0);
        res.a.assign(a.size(), 0);

        for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
            cur.a.insert(cur.a.begin(), a[i]);
            cur.trim();

            int l = 0;
            int r = base - 1;
            int x = 0;
            while (l <= r) {
                int m = l + (r - l) / 2;
                big_int t = v * m;
                if (t <= cur) {
                    x = m;
                    l = m + 1;
                } else {
                    r = m - 1;
                }
            }

            res.a[i] = x;
            cur = cur - (v * x);
        }

        res.trim();
        cur.trim();
        return {res, cur};
    }

    big_int operator/(const big_int& other) const {
        return divmod(other).first;
    }

    big_int ordinary_mod(const big_int& other) const {
        return divmod(other).second;
    }

    static big_int fast_mod(const big_int& value, const big_int& mod) {
        if (mod.is_zero()) {
            throw runtime_error("modulo by zero");
        }

        big_int result = value;
        while (result >= mod) {
            int shift = static_cast<int>(result.a.size()) - static_cast<int>(mod.a.size());
            big_int candidate;
            candidate.a.assign(shift, 0);
            candidate.a.insert(candidate.a.end(), mod.a.begin(), mod.a.end());
            candidate.trim();

            if (candidate > result) {
                --shift;
                candidate.a.assign(shift, 0);
                candidate.a.insert(candidate.a.end(), mod.a.begin(), mod.a.end());
                candidate.trim();
            }

            long long low = 1;
            long long high = base - 1;
            long long best = 1;
            while (low <= high) {
                long long mid = (low + high) / 2;
                big_int scaled = candidate * static_cast<int>(mid);
                if (scaled <= result) {
                    best = mid;
                    low = mid + 1;
                } else {
                    high = mid - 1;
                }
            }

            result = result - (candidate * static_cast<int>(best));
        }
        result.trim();
        return result;
    }
};

big_int modular_multiply_ordinary(const big_int& a, const big_int& b, const big_int& mod) {
    return (a * b).ordinary_mod(mod);
}

big_int modular_multiply_fast(const big_int& a, const big_int& b, const big_int& mod) {
    return big_int::fast_mod(a * b, mod);
}

big_int modular_power(big_int base, big_int exponent, const big_int& mod, bool use_fast_mod) {
    big_int result(1);
    base = use_fast_mod ? big_int::fast_mod(base, mod) : base.ordinary_mod(mod);

    while (!exponent.is_zero()) {
        if (exponent.is_odd()) {
            result = use_fast_mod ? modular_multiply_fast(result, base, mod)
                                  : modular_multiply_ordinary(result, base, mod);
        }
        exponent = exponent.div2();
        if (!exponent.is_zero()) {
            base = use_fast_mod ? modular_multiply_fast(base, base, mod)
                                : modular_multiply_ordinary(base, base, mod);
        }
    }

    return result;
}

bool miller_rabin(const big_int& n, bool use_fast_mod) {
    static const int witnesses[] = {2, 3, 5, 7, 11, 13, 17, 19, 23};

    if (n == big_int(2) || n == big_int(3)) {
        return true;
    }
    if (n < big_int(2) || !n.is_odd()) {
        return false;
    }

    for (int p : witnesses) {
        if (n == big_int(p)) {
            return true;
        }
        if (n.mod_int(p) == 0) {
            return false;
        }
    }

    big_int d = n - big_int(1);
    int s = 0;
    while (!d.is_odd()) {
        d = d.div2();
        ++s;
    }

    big_int n_minus_one = n - big_int(1);
    for (int a : witnesses) {
        big_int base(a);
        if (base >= n) {
            continue;
        }

        big_int x = modular_power(base, d, n, use_fast_mod);
        if (x == big_int(1) || x == n_minus_one) {
            continue;
        }

        bool witness_passed = false;
        for (int r = 1; r < s; ++r) {
            x = use_fast_mod ? modular_multiply_fast(x, x, n)
                             : modular_multiply_ordinary(x, x, n);
            if (x == n_minus_one) {
                witness_passed = true;
                break;
            }
        }

        if (!witness_passed) {
            return false;
        }
    }

    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string input;
    if (!(cin >> input)) {
        return 0;
    }

    big_int n(input);
    bool ordinary_result = miller_rabin(n, false);
    bool fast_result = miller_rabin(n, true);

    cout << "Number: " << n << '\n';
    cout << "Miller-Rabin using ordinary modulo: "
         << (ordinary_result ? "probably prime" : "composite") << '\n';
    cout << "Miller-Rabin using fast modulo: "
         << (fast_result ? "probably prime" : "composite") << '\n';

    return 0;
}
