#include<stdio.h>

int main() {
    int num = 1234;
    int x = sumOfDigits(num);
    print("Reversed Digits: ", x);
    return 0;
}

int sumOfDigits(int num) {
    int s = 0;
    while (num != 0) {
        int rem = num % 10;
        s = s*10 + rem;
        num = num / 10;
    }
    return 0;
}