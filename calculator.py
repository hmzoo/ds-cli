def add(a, b):
    """
    Additionne deux nombres.
    
    Args:
        a: Premier nombre
        b: Deuxième nombre
        
    Returns:
        La somme de a et b
    """
    return a + b


def subtract(a, b):
    """
    Soustrait deux nombres.
    
    Args:
        a: Premier nombre
        b: Deuxième nombre
        
    Returns:
        La différence de a et b (a - b)
    """
    return a - b


def multiply(a, b):
    """
    Multiplie deux nombres.
    
    Args:
        a: Premier nombre
        b: Deuxième nombre
        
    Returns:
        Le produit de a et b
    """
    return a * b


def divide(a, b):
    """
    Divise deux nombres.
    
    Args:
        a: Numérateur
        b: Dénominateur
        
    Returns:
        Le quotient de a divisé par b
        
    Raises:
        ValueError: Si b est égal à 0 (division par zéro)
    """
    if b == 0:
        raise ValueError("Division par zéro n'est pas autorisée")
    return a / b


if __name__ == "__main__":
    # Exemple d'utilisation
    result = add(5, 3)
    print(f"5 + 3 = {result}")
    
    # Test avec des nombres négatifs
    result2 = add(-2, 7)
    print(f"-2 + 7 = {result2}")
    
    # Test avec des nombres décimaux
    result3 = add(3.14, 2.86)
    print(f"3.14 + 2.86 = {result3}")
    
    # Test de la fonction subtract
    result4 = subtract(10, 4)
    print(f"10 - 4 = {result4}")
    
    result5 = subtract(5, 8)
    print(f"5 - 8 = {result5}")
    
    result6 = subtract(7.5, 2.3)
    print(f"7.5 - 2.3 = {result6}")
    
    # Test de la fonction multiply
    result7 = multiply(4, 5)
    print(f"4 * 5 = {result7}")
    
    result8 = multiply(-3, 6)
    print(f"-3 * 6 = {result8}")
    
    result9 = multiply(2.5, 4)
    print(f"2.5 * 4 = {result9}")
    
    # Test de la fonction divide
    result10 = divide(10, 2)
    print(f"10 / 2 = {result10}")
    
    result11 = divide(7, 3)
    print(f"7 / 3 = {result11:.2f}")
    
    result12 = divide(5.5, 2)
    print(f"5.5 / 2 = {result12}")
    
    # Test division par zéro (avec gestion d'erreur)
    try:
        result13 = divide(10, 0)
        print(f"10 / 0 = {result13}")
    except ValueError as e:
        print(f"Erreur: {e}")