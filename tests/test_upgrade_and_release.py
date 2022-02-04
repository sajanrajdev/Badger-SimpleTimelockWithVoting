import pytest
from brownie import SimpleTimelockWithVoting, accounts, interface
from rich.console import Console

console = Console()


@pytest.fixture()
def old_devProxyAdmin():
    return interface.IProxyAdmin("0x4599F2913a3db4E73aA77A304cCC21516dd7270D")

@pytest.fixture()
def ops_multisig_ops():
    return accounts.at("0x576cD258835C529B54722F84Bb7d4170aA932C64", force=True)

@pytest.fixture()
def dev_multisig():
    return accounts.at("0xB65cef03b9B89f99517643226d76e286ee999e77", force=True)

@pytest.fixture()
def dao_treasury():
    return SimpleTimelockWithVoting.at("0x4441776e6A5D61fA024A5117bfc26b953Ad1f425")

@pytest.fixture()
def BADGER():
    return interface.IBadger("0x3472A5A71965499acd81997a54BBA8D852C6E53d")

def test_migrate_staking_optimizer(
    old_devProxyAdmin,
    ops_multisig_ops,
    dev_multisig,
    dao_treasury,
    BADGER,
):
    '''
    Tests the upgrade of the DAO_treasury (SimpleTimelockWithVoting) and proper
    release of BADGER funds to the devMultisig.
    '''

    treasury_balance = BADGER.balanceOf(dao_treasury.address)
    token = dao_treasury.token()
    releaseTime = dao_treasury.releaseTime()
    # Beneficiary is currently the DAO_Agent
    assert dao_treasury.beneficiary() == "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B"

    # Deploys and upgrades logic
    new_logic = SimpleTimelockWithVoting.deploy({"from": accounts[0]})
    old_devProxyAdmin.upgrade(dao_treasury.address, new_logic, {"from": ops_multisig_ops})
    # Sets new beneficiary
    dao_treasury.setBeneficiary(dev_multisig.address, {"from": dev_multisig.address})

    assert treasury_balance == BADGER.balanceOf(dao_treasury.address)
    assert token == dao_treasury.token()
    assert releaseTime == dao_treasury.releaseTime()
    # Beneficiary is now the devMultisig
    assert dao_treasury.beneficiary() == dev_multisig.address

    # == Release tokens == #
    dev_balance = BADGER.balanceOf(dev_multisig.address)

    dao_treasury.release({"from": dev_multisig.address})

    assert BADGER.balanceOf(dev_multisig.address) == treasury_balance + dev_balance