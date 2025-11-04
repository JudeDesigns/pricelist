"""
Vendor-specific parsing modules for PDF price list extraction.

Each vendor has its own module with custom parsing logic.
"""

from .rw_zant import RWZantParser
from .glen_rose import GlenRoseParser
from .kruse_sons import KruseSonsParser
from .quirch_foods import QuirchFoodsParser
from .purcell import PurcellParser
from .laras_meat import LarasMeatParser
from .maui_prices import MauiPricesParser
from .cd_international import CDInternationalParser
from .royalty_distribution import RoyaltyDistributionParser
from .la_poultry import LAPoultryParser
from .apsic_wholesale import APSICWholesaleParser
from .delmar_cow import DelMarCowParser
from .delmar_steer import DelMarSteerParser
from .gladway import GladwayParser
from .union_fish import UnionFishParser
from .solomon_wholesale import SolomonWholesaleParser
from .da_price import DAPriceParser
from .broadleaf import BroadleafParser
from .cofoods import CofoodsParser
from .monarch_trading import MonarchTradingParser
from .generic import GenericParser

# Vendor registry - maps vendor codes to parser classes
VENDOR_PARSERS = {
    'rw_zant': RWZantParser,
    'glen_rose': GlenRoseParser,
    'kruse_sons': KruseSonsParser,
    'quirch_foods': QuirchFoodsParser,
    'purcell': PurcellParser,
    'laras_meat': LarasMeatParser,
    'maui_prices': MauiPricesParser,
    'cd_international': CDInternationalParser,
    'royalty_distribution': RoyaltyDistributionParser,
    'la_poultry': LAPoultryParser,
    'apsic_wholesale': APSICWholesaleParser,
    'delmar_cow': DelMarCowParser,
    'delmar_steer': DelMarSteerParser,
    'gladway': GladwayParser,
    'union_fish': UnionFishParser,
    'solomon_wholesale': SolomonWholesaleParser,
    'da_price': DAPriceParser,
    'broadleaf': BroadleafParser,
    'cofoods': CofoodsParser,
    'monarch_trading': MonarchTradingParser,
    'unknown': GenericParser,
}

def get_parser(vendor_code='rw_zant'):
    """
    Get the appropriate parser for a vendor.
    
    Args:
        vendor_code: Vendor code (e.g., 'rw_zant', 'glen_rose')
    
    Returns:
        Parser instance for the vendor
    """
    parser_class = VENDOR_PARSERS.get(vendor_code, RWZantParser)
    return parser_class()

