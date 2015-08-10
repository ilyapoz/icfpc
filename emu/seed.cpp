#include <iostream>
#include <stdint.h>
#include <stdlib.h>
#include <bitset>

using namespace std;

int main(int argc, char**argv)
{
    uint32_t seed = atoi(argv[1]);
    //cout << "seed: " << seed << endl;
    for (int i = 0; i < 50; ++i) {
        cout << ((0x7fff0000 & seed) >> 16) << endl;
        seed *= 1103515245;
        seed += 12345;
    }
}
