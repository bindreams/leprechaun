from leprechaun.base import InvalidConfigError
from .xmr import XmrMiner
from .eth import EthMiner


def cpuminer(name, data, config):
    if "currency" not in data:
        raise InvalidConfigError("missing property 'currency'")
    
    currency = data["currency"]
    if currency == "XMR":
        return XmrMiner(name, data, config)
    else:
        raise InvalidConfigError(f"no known CPU miners for currency '{currency}'")


def gpuminer(name, data, config):
    if "currency" not in data:
        raise InvalidConfigError("missing property 'currency'")
    
    currency = data["currency"]
    if currency == "ETH":
        return EthMiner(name, data, config)
    # elif currency == "GRLC":
    #     return GrlcMiner(name, data, config)
    else:
        raise InvalidConfigError(f"no known GPU miners for currency '{currency}'")
