I wrote a Python program in the sandbox to compute the first 1,000,000 terms of the series

1 - 1/3 + 1/5 - 1/7 + ...

and multiply the total by 4.

The program used:
```python
def compute_pi_like_series(terms: int = 1_000_000) -> float:
    total = 0.0
    sign = 1.0
    for n in range(terms):
        total += sign / (2 * n + 1)
        sign = -sign
    return 4 * total


if __name__ == "__main__":
    result = compute_pi_like_series()
    print(result)
```

I ran it successfully, and the output was:
```text
3.1415916535897743
```