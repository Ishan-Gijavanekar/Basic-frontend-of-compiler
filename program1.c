int main() {
    print("Enter the number: ");
    print("Sum = %d", sum(5));
    return 0;
}

int sum(int n) {
    int sum = 0;
    for (int i=0;i<=n;i++) {
        sum = sum + i;
    }
    return sum;
}