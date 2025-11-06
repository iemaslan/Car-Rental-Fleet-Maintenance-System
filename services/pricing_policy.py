"""
Pricing policy and composable pricing rules for the rental system.
Uses Strategy pattern for flexible pricing computation.
"""
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from domain.models import RentalAgreement, ChargeItem
from domain.value_objects import Money, Kilometers
from domain.clock import Clock


class PricingRule(ABC):
    """Abstract base class for pricing rules."""
    
    @abstractmethod
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        """
        Calculate charges for this rule.
        
        Args:
            rental_agreement: The rental agreement to price
            clock: Clock for time-dependent calculations
            
        Returns:
            List of charge items
        """
        pass


class BaseRateRule(PricingRule):
    """Calculates base daily rate charges."""
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        days = rental_agreement.reservation.duration_in_days()
        base_rate = rental_agreement.vehicle.vehicle_class.base_rate
        total = base_rate * days
        return [ChargeItem(
            description=f"Base rate ({days} days @ {base_rate}/day)",
            amount=total
        )]


class AddOnRule(PricingRule):
    """Calculates add-on service charges."""
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        charges = []
        days = rental_agreement.reservation.duration_in_days()
        
        for addon in rental_agreement.reservation.addons:
            total = addon.daily_fee * days
            charges.append(ChargeItem(
                description=f"{addon.name} ({days} days @ {addon.daily_fee}/day)",
                amount=total
            ))
        
        return charges


class InsuranceRule(PricingRule):
    """Calculates insurance tier charges."""
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        insurance = rental_agreement.reservation.insurance_tier
        if not insurance:
            return []
        
        days = rental_agreement.reservation.duration_in_days()
        total = insurance.daily_fee * days
        return [ChargeItem(
            description=f"{insurance.name} insurance ({days} days @ {insurance.daily_fee}/day)",
            amount=total
        )]


class LateFeeRule(PricingRule):
    """Calculates late return fees with grace period."""
    
    def __init__(self, hourly_rate: Money, grace_period_hours: int = 1):
        self.hourly_rate = hourly_rate
        self.grace_period_hours = grace_period_hours
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        if not rental_agreement.actual_return_time:
            return []
        
        late_hours = rental_agreement.calculate_late_hours(
            rental_agreement.actual_return_time, 
            self.grace_period_hours
        )
        
        if late_hours <= 0:
            return []
        
        total = self.hourly_rate * late_hours
        return [ChargeItem(
            description=f"Late fee ({late_hours} hours @ {self.hourly_rate}/hour)",
            amount=total
        )]


class MileageOverageRule(PricingRule):
    """Calculates mileage overage charges."""
    
    def __init__(self, per_km_rate: Money):
        self.per_km_rate = per_km_rate
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        driven = rental_agreement.driven_distance()
        if not driven:
            return []
        
        days = rental_agreement.reservation.duration_in_days()
        allowance = rental_agreement.vehicle.vehicle_class.daily_mileage_allowance * days
        allowance_km = Kilometers(allowance)
        
        if driven <= allowance_km:
            return []
        
        overage = driven - allowance_km
        total = self.per_km_rate * overage.value
        return [ChargeItem(
            description=f"Mileage overage ({overage.value} km @ {self.per_km_rate}/km)",
            amount=total
        )]


class FuelRefillRule(PricingRule):
    """Calculates fuel refill charges."""
    
    def __init__(self, per_level_charge: Money):
        """
        Args:
            per_level_charge: Charge per 0.1 (10%) fuel level difference
        """
        self.per_level_charge = per_level_charge
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        if not rental_agreement.end_fuel_level:
            return []
        
        if rental_agreement.end_fuel_level >= rental_agreement.start_fuel_level:
            return []
        
        fuel_diff = rental_agreement.start_fuel_level.level - rental_agreement.end_fuel_level.level
        # Convert to units of 10% (0.1)
        units = int(fuel_diff * 10)
        
        if units <= 0:
            return []
        
        total = self.per_level_charge * units
        return [ChargeItem(
            description=f"Fuel refill charge ({units * 10}% @ {self.per_level_charge}/10%)",
            amount=total
        )]


class WeekendMultiplierRule(PricingRule):
    """Applies weekend surcharge multiplier."""
    
    def __init__(self, multiplier: float = 1.2):
        """
        Args:
            multiplier: Multiplier for weekend rates (e.g., 1.2 for 20% increase)
        """
        self.multiplier = multiplier
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        pickup_time = rental_agreement.pickup_time
        
        # Check if pickup is on weekend (Saturday=5, Sunday=6)
        if pickup_time.weekday() not in [5, 6]:
            return []
        
        # Calculate additional charge as percentage of base rate
        base_rate = rental_agreement.vehicle.vehicle_class.base_rate
        days = rental_agreement.reservation.duration_in_days()
        base_total = base_rate * days
        additional = base_total * (self.multiplier - 1.0)
        
        return [ChargeItem(
            description=f"Weekend surcharge ({int((self.multiplier - 1.0) * 100)}%)",
            amount=additional
        )]


class SeasonMultiplierRule(PricingRule):
    """Applies seasonal surcharge multiplier."""
    
    def __init__(self, peak_months: List[int], multiplier: float = 1.3):
        """
        Args:
            peak_months: List of month numbers (1-12) considered peak season
            multiplier: Multiplier for peak season rates
        """
        self.peak_months = peak_months
        self.multiplier = multiplier
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        pickup_month = rental_agreement.pickup_time.month
        
        if pickup_month not in self.peak_months:
            return []
        
        # Calculate additional charge as percentage of base rate
        base_rate = rental_agreement.vehicle.vehicle_class.base_rate
        days = rental_agreement.reservation.duration_in_days()
        base_total = base_rate * days
        additional = base_total * (self.multiplier - 1.0)
        
        return [ChargeItem(
            description=f"Peak season surcharge ({int((self.multiplier - 1.0) * 100)}%)",
            amount=additional
        )]


class DamageChargeRule(PricingRule):
    """Applies manual damage charges."""
    
    def __init__(self, damage_amount: Money):
        self.damage_amount = damage_amount
    
    def calculate(self, rental_agreement: RentalAgreement, clock: Clock) -> List[ChargeItem]:
        if self.damage_amount.amount <= 0:
            return []
        
        return [ChargeItem(
            description="Damage charge",
            amount=self.damage_amount
        )]


class PricingPolicy:
    """
    Composable pricing policy using Strategy pattern.
    Aggregates multiple pricing rules to calculate total charges.
    """
    
    def __init__(self, clock: Clock):
        self.clock = clock
        self.rules: List[PricingRule] = []

    def add_rule(self, rule: PricingRule) -> 'PricingPolicy':
        """
        Add a pricing rule to the policy.
        
        Args:
            rule: The pricing rule to add
            
        Returns:
            Self for method chaining
        """
        self.rules.append(rule)
        return self

    def calculate_charges(self, rental_agreement: RentalAgreement) -> List[ChargeItem]:
        """
        Calculate all charges for a rental agreement.
        
        Args:
            rental_agreement: The rental agreement to price
            
        Returns:
            List of all charge items from all rules
        """
        all_charges = []
        for rule in self.rules:
            charges = rule.calculate(rental_agreement, self.clock)
            all_charges.extend(charges)
        return all_charges
    
    def calculate_total(self, rental_agreement: RentalAgreement) -> Money:
        """
        Calculate total charge amount.
        
        Args:
            rental_agreement: The rental agreement to price
            
        Returns:
            Total charge amount
        """
        charges = self.calculate_charges(rental_agreement)
        if not charges:
            return Money.zero()
        return sum((charge.amount for charge in charges), Money.zero())


# Factory function for creating a standard pricing policy
def create_standard_pricing_policy(clock: Clock, 
                                   late_fee_per_hour: Money = None,
                                   mileage_overage_per_km: Money = None,
                                   fuel_refill_per_10pct: Money = None,
                                   apply_weekend_surcharge: bool = False,
                                   peak_season_months: List[int] = None) -> PricingPolicy:
    """
    Create a standard pricing policy with common rules.
    
    Args:
        clock: Clock implementation
        late_fee_per_hour: Late fee rate (default: $25/hour)
        mileage_overage_per_km: Overage rate (default: $0.50/km)
        fuel_refill_per_10pct: Fuel refill rate (default: $10/10%)
        apply_weekend_surcharge: Whether to apply weekend surcharge
        peak_season_months: List of peak season months (e.g., [6, 7, 8] for summer)
    
    Returns:
        Configured pricing policy
    """
    from decimal import Decimal
    
    policy = PricingPolicy(clock)
    policy.add_rule(BaseRateRule())
    policy.add_rule(AddOnRule())
    policy.add_rule(InsuranceRule())
    
    late_fee = late_fee_per_hour or Money(Decimal('25.00'))
    policy.add_rule(LateFeeRule(late_fee))
    
    overage_rate = mileage_overage_per_km or Money(Decimal('0.50'))
    policy.add_rule(MileageOverageRule(overage_rate))
    
    fuel_rate = fuel_refill_per_10pct or Money(Decimal('10.00'))
    policy.add_rule(FuelRefillRule(fuel_rate))
    
    if apply_weekend_surcharge:
        policy.add_rule(WeekendMultiplierRule(1.2))
    
    if peak_season_months:
        policy.add_rule(SeasonMultiplierRule(peak_season_months, 1.3))
    
    return policy