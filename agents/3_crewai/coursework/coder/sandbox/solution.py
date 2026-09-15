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
