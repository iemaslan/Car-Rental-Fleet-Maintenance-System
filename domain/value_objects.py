"""
Value objects for the Car Rental & Fleet Maintenance System.
These are immutable objects that represent measurements and monetary values.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass(frozen=True)
class Money:
    """Immutable value object for currency arithmetic."""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __radd__(self, other):
        """Support for sum() function which starts with 0."""
        if other == 0:
            return self
        return self.__add__(other)
    
    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Money':
        return Money(self.amount * Decimal(str(multiplier)), self.currency)
    
    def __truediv__(self, divisor: Union[int, float, Decimal]) -> 'Money':
        return Money(self.amount / Decimal(str(divisor)), self.currency)
    
    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount
    
    def __le__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount <= other.amount
    
    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount
    
    def __ge__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount >= other.amount
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
    
    @classmethod
    def zero(cls, currency: str = "USD") -> 'Money':
        """Create a Money object with zero amount."""
        return cls(Decimal('0'), currency)


@dataclass(frozen=True)
class FuelLevel:
    """Immutable value object for fuel level measurements (0.0 to 1.0)."""
    level: float
    
    def __post_init__(self):
        if not 0.0 <= self.level <= 1.0:
            raise ValueError(f"Fuel level must be between 0.0 and 1.0, got {self.level}")
    
    def __sub__(self, other: 'FuelLevel') -> float:
        """Return the difference in fuel levels."""
        return self.level - other.level
    
    def __lt__(self, other: 'FuelLevel') -> bool:
        return self.level < other.level
    
    def __le__(self, other: 'FuelLevel') -> bool:
        return self.level <= other.level
    
    def __gt__(self, other: 'FuelLevel') -> bool:
        return self.level > other.level
    
    def __ge__(self, other: 'FuelLevel') -> bool:
        return self.level >= other.level
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FuelLevel):
            return False
        return abs(self.level - other.level) < 0.001  # Allow small floating point differences
    
    def __str__(self) -> str:
        return f"{self.level * 100:.1f}%"
    
    @classmethod
    def full(cls) -> 'FuelLevel':
        """Create a FuelLevel object representing a full tank."""
        return cls(1.0)
    
    @classmethod
    def empty(cls) -> 'FuelLevel':
        """Create a FuelLevel object representing an empty tank."""
        return cls(0.0)


@dataclass(frozen=True)
class Kilometers:
    """Immutable value object for distance measurements in kilometers."""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Kilometers must be non-negative, got {self.value}")
    
    def __add__(self, other: 'Kilometers') -> 'Kilometers':
        return Kilometers(self.value + other.value)
    
    def __sub__(self, other: 'Kilometers') -> 'Kilometers':
        result = self.value - other.value
        if result < 0:
            raise ValueError(f"Resulting kilometers cannot be negative: {result}")
        return Kilometers(result)
    
    def __mul__(self, multiplier: Union[int, float]) -> 'Kilometers':
        return Kilometers(int(self.value * multiplier))
    
    def __lt__(self, other: 'Kilometers') -> bool:
        return self.value < other.value
    
    def __le__(self, other: 'Kilometers') -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: 'Kilometers') -> bool:
        return self.value > other.value
    
    def __ge__(self, other: 'Kilometers') -> bool:
        return self.value >= other.value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Kilometers):
            return False
        return self.value == other.value
    
    def __str__(self) -> str:
        return f"{self.value} km"
    
    @classmethod
    def zero(cls) -> 'Kilometers':
        """Create a Kilometers object with zero distance."""
        return cls(0)
