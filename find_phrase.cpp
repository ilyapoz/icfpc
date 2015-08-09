#include <cstring>
#include <cstdio>
#include <string>
#include <map>
using namespace std;

const int MOD1 = 1000000007;
const int MOD2 = 1000000009;

const int MAXL = 30000;
const int TARGET = 1332;

char st[MAXL];
int L, pf[MAXL];

map<pair<int, int>, int> dict;
map<pair<int, int>, pair<int, int> > where;

int main()
{
    freopen("test.txt", "r", stdin);
    gets(st); L = strlen(st);

    int P1LEN = 1, P2LEN = 1;

    for (int len = 1; len <= 51; ++len) {
        int H1 = 0, H2 = 0;

        for (int i = 0; i < len - 1; ++i) {
            H1 = (H1 *1LL* 128 + st[i]) % MOD1;
            H2 = (H2 *1LL* 128 + st[i]) % MOD2;
        }

        for (int i = len - 1; i < L; ++i) {
            if (i - len >= 0) {
                H1 = (H1 + MOD1 - (P1LEN *1LL* st[i - len]) % MOD1) % MOD1;
                H2 = (H2 + MOD2 - (P2LEN *1LL* st[i - len]) % MOD2) % MOD2;
            }

            H1 = (H1 *1LL* 128 + st[i]) % MOD1;
            H2 = (H2 *1LL* 128 + st[i]) % MOD2;

            ++dict[make_pair(H1, H2)];
            where[make_pair(H1, H2)] = make_pair(i - len + 1, len);
        }

        P1LEN = (P1LEN *1LL* 128) % MOD1;
        P2LEN = (P2LEN *1LL* 128) % MOD2;
    }

    for (map<pair<int, int>, int>::iterator q = dict.begin(); q != dict.end(); ++q) {
        pair<int, int> word = where[q->first];
        int res = q->second;

        if (2 * res * word.second + 300 == TARGET) {
            printf("%d %d\n", word.second, res);
            for (int i = word.first, j = 0; j < word.second; ++j)
                printf("%c", st[i + j]);
            printf("\n");
        }
    }

    return 0;
}
