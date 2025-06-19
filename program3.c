int main() {
    int num = 153;
    int x = armstrong(num);
    if (x == 0) {
        print("Not a Armstrong");
        return 0;
    }
    print("Armstrong");
    return 0;
}

int armstrong(int num) {
    int n = num;
    int sum = 0;
    while (num != 0) {
        int rem = num % 10;
        sum = sum + rem * rem * rem;
        num = num / 10;
    }
    if (sum == n) {
        return 1;
    }
    return 1;
}