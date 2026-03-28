#include <bits/stdc++.h>
#include <boost/multiprecision/cpp_int.hpp>

using namespace std;
using namespace boost::multiprecision;

cpp_int modpow(cpp_int a, cpp_int d, cpp_int mod)
{
    cpp_int r = 1;
    a %= mod;

    while(d > 0)
    {
        if(d & 1) r = (r * a) % mod;
        a = (a * a) % mod;
        d >>= 1;
    }
    return r;
}

bool miller_rabin(cpp_int n, int k)
{
    if(n < 4) return n == 2 || n == 3;
    if(n % 2 == 0) return false;

    cpp_int d = n - 1;
    int s = 0;

    while(d % 2 == 0)
    {
        d /= 2;
        s++;
    }

    for(int i = 0; i < k; i++)
    {
        cpp_int a = 2 + rand() % 1000000;
        cpp_int x = modpow(a, d, n);

        if(x == 1 || x == n - 1) continue;

        bool ok = false;

        for(int j = 0; j < s - 1; j++)
        {
            x = (x * x) % n;
            if(x == n - 1)
            {
                ok = true;
                break;
            }
        }

        if(!ok) return false;
    }

    return true;
}