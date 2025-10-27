def poly_eval(coeffs, x):
    """
    Evaluate a polynomial using Horner's method.
    coeffs: list of coefficients, highest degree first
    x: the value at which to evaluate the polynomial
    Example: 2x^3 + 3x^2 - 5x + 7 -> coeffs = [2, 3, -5, 7]
    """
    result = 0
    for coef in coeffs:
        result = result * x + coef
    return result

if __name__ == "__main__":
    coeffs = [2, 3, -5, 7]  # 2x^3 + 3x^2 - 5x + 7
    x = 4
    print(f"Polynomial coefficients: {coeffs}")
    print(f"Value of polynomial at x={x}: {poly_eval(coeffs, x)}")
