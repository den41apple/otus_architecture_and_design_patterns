import math

import pytest

from homeworks.homework_1.solver import solve


def test_no_roots():
    """
    Тест, который проверяет, что для уравнения x^2+1 = 0
    корней нет (возвращается пустой массив)
    """
    assert solve(1, 0, 1) == []


def test_two_roots():
    """
    Тест, который проверяет, что для уравнения x^2-1 = 0
    есть два корня кратности 1 (x1=1, x2=-1)
    """
    roots = solve(1, 0, -1)
    assert set(roots) == {1, -1}


def test_one_double_root():
    """
    Тест, который проверяет, что для уравнения x^2+2x+1 = 0
    есть один корень кратности 2 (x1= x2 = -1).
    """
    roots = solve(1, 2, 1)
    assert roots == [-1]


def test_zero_a_raises():
    """
    Тест, который проверяет, что коэффициент a не может быть равен 0.
    В этом случае solve выбрасывает исключение.

    Примечание:
        Учесть, что a имеет тип double и сравнивать с 0 через == нельзя
    """
    with pytest.raises(ValueError):
        try:
            solve(0, 1, 1)
        except ValueError as err:
            assert err.args[0] == "'a' coefficient must not be zero"
            raise


def test_discriminant_almost_zero():
    """
    С учетом того, что дискриминант тоже нельзя сравнивать с 0 через знак равенства,
    подобрать такие коэффициенты квадратного уравнения для случая одного корня кратности два,
    чтобы дискриминант был отличный от нуля, но меньше заданного эпсилон.
    Эти коэффициенты должны заменить коэффициенты в тесте из п. 7.
    """
    a = 1
    b = 2.0000000001
    c = 1.00000000005
    roots = solve(a, b, c)
    assert len(roots) == 1
    assert abs(roots[0] + 1) < 1e-6


@pytest.mark.parametrize(
    ("a", "b", "c"),
    [
        (math.nan, 1, 1),
        (1, math.inf, 1),
        (1, 1, -math.inf),
    ],
)
def test_non_finite_coeffs(a: float, b: float, c: float):
    """
    Посмотреть какие еще значения могут принимать числа типа double,
    кроме числовых и написать тест с их использованием на все коэффициенты.
    solve должен выбрасывать исключение.
    """
    with pytest.raises(ValueError):
        try:
            solve(a, b, c)
        except ValueError as err:
            assert err.args[0] == "All coefficients must be finite numbers"
            raise
