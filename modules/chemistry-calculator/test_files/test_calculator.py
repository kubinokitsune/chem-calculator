import unittest
from src.calculator import Calculator

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = Calculator()

    def test_calculate_molarity(self):
        self.assertAlmostEqual(self.calculator.calculate_molarity(1, 0.5), 2.0)
        self.assertAlmostEqual(self.calculator.calculate_molarity(0, 1), 0.0)

    def test_calculate_moles(self):
        self.assertAlmostEqual(self.calculator.calculate_moles(1, 18), 0.0555)
        self.assertAlmostEqual(self.calculator.calculate_moles(0, 18), 0.0)

    def test_calculate_mass(self):
        self.assertAlmostEqual(self.calculator.calculate_mass(1, 18), 18.0)
        self.assertAlmostEqual(self.calculator.calculate_mass(0, 18), 0.0)

if __name__ == '__main__':
    unittest.main()