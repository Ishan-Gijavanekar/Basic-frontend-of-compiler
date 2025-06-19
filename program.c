#include<stdio.h>

int main() {
    int num = 5;
    print("Enter the number: ");
    print("%d", fact(5));
    int x = 2*5+3*5+(5*(5+60));
}

int fact(int n) {
    int fact = 1;
    for (int i=0; i<n; i++) {
        fact = fact * i;
    }
    return fact;
}