#include<stdio.h>

int main() {
    int num = 5;
    int ans = factorial(num);
    print("Factorial = ", ans);
    return 0;
}

int factorial(int num) {
    int fact = 1;
    int i;
    for(i=1;i<=fact;i++) {
        fact = fact * i;
    }
    return fact;
}