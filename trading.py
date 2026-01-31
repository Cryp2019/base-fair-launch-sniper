#!/usr/bin/env python3
"""
🎯 Automatic Trading Module for Base Fair Launch Sniper Bot
Handles buy/sell execution via Uniswap V3 on Base chain
"""
import os
from web3 import Web3
from eth_account import Account
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Uniswap V3 Router on Base
UNISWAP_V3_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"  # SwapRouter02
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

# Uniswap V3 Router ABI (minimal - just what we need)
ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# ERC20 ABI for approve
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class TradingBot:
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.router = w3.eth.contract(
            address=Web3.to_checksum_address(UNISWAP_V3_ROUTER),
            abi=ROUTER_ABI
        )
    
    def approve_token(self, token_address: str, private_key: str, amount: int = None) -> dict:
        """Approve token for trading on Uniswap"""
        try:
            account = Account.from_key(private_key)
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            
            # Approve max amount if not specified
            if amount is None:
                amount = 2**256 - 1  # Max uint256
            
            # Build transaction
            txn = token_contract.functions.approve(
                UNISWAP_V3_ROUTER,
                amount
            ).build_transaction({
                'from': account.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 8453  # Base mainnet
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"✅ Approval sent: {tx_hash.hex()}")
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'message': 'Token approved for trading'
            }
            
        except Exception as e:
            logger.error(f"❌ Approval failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def buy_token(self, token_address: str, private_key: str, eth_amount: float, slippage: float = 10.0, fee_wallet: str = None, fee_percentage: float = 0.0) -> dict:
        """
        Buy token with ETH via Uniswap V3
        
        Args:
            token_address: Token to buy
            private_key: User's private key
            eth_amount: Amount of ETH to spend
            slippage: Slippage tolerance in percentage (default 10%)
        
        Returns:
            dict with success status, tx_hash, and details
        """
        try:
            account = Account.from_key(private_key)
            token_checksum = Web3.to_checksum_address(token_address)
            weth_checksum = Web3.to_checksum_address(WETH_ADDRESS)

            # Calculate fee if applicable
            fee_amount_eth = 0
            net_eth_amount = eth_amount

            if fee_wallet and fee_percentage > 0:
                fee_amount_eth = eth_amount * (fee_percentage / 100)
                net_eth_amount = eth_amount - fee_amount_eth

                # Send fee to fee wallet
                try:
                    fee_amount_wei = self.w3.to_wei(fee_amount_eth, 'ether')
                    fee_tx = {
                        'from': account.address,
                        'to': Web3.to_checksum_address(fee_wallet),
                        'value': fee_amount_wei,
                        'gas': 21000,
                        'gasPrice': self.w3.eth.gas_price,
                        'nonce': self.w3.eth.get_transaction_count(account.address),
                        'chainId': 8453
                    }
                    signed_fee_tx = self.w3.eth.account.sign_transaction(fee_tx, private_key)
                    fee_tx_hash = self.w3.eth.send_raw_transaction(signed_fee_tx.rawTransaction)
                    logger.info(f"💰 Fee collected: {fee_amount_eth} ETH - TX: {fee_tx_hash.hex()}")
                except Exception as e:
                    logger.error(f"Fee collection failed: {e}")
                    # Continue with trade even if fee fails

            # Convert net ETH amount to Wei
            amount_in = self.w3.to_wei(net_eth_amount, 'ether')
            
            # Calculate minimum output with slippage (set to 0 for now, will calculate properly)
            amount_out_minimum = 0  # We'll accept any amount (high slippage tolerance)
            
            # Build swap parameters
            params = {
                'tokenIn': weth_checksum,
                'tokenOut': token_checksum,
                'fee': 10000,  # 1% fee tier (try 3000 for 0.3% or 500 for 0.05% if this fails)
                'recipient': account.address,
                'amountIn': amount_in,
                'amountOutMinimum': amount_out_minimum,
                'sqrtPriceLimitX96': 0  # No price limit
            }
            
            # Build transaction
            txn = self.router.functions.exactInputSingle(params).build_transaction({
                'from': account.address,
                'value': amount_in,  # Send ETH
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 8453  # Base mainnet
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"✅ Buy transaction sent: {tx_hash.hex()}")
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'eth_spent': eth_amount,
                'message': f'Buy order submitted! TX: {tx_hash.hex()[:10]}...'
            }
            
        except Exception as e:
            logger.error(f"❌ Buy failed: {e}")
            return {
                'success': False,
                'message': f'Buy failed: {str(e)[:100]}'
            }

    def sell_token(self, token_address: str, private_key: str, percentage: float = 100.0, slippage: float = 10.0) -> dict:
        """
        Sell token for ETH via Uniswap V3

        Args:
            token_address: Token to sell
            private_key: User's private key
            percentage: Percentage of balance to sell (default 100%)
            slippage: Slippage tolerance in percentage (default 10%)

        Returns:
            dict with success status, tx_hash, and details
        """
        try:
            account = Account.from_key(private_key)
            token_checksum = Web3.to_checksum_address(token_address)
            weth_checksum = Web3.to_checksum_address(WETH_ADDRESS)

            # Get token balance
            token_contract = self.w3.eth.contract(
                address=token_checksum,
                abi=ERC20_ABI
            )
            balance = token_contract.functions.balanceOf(account.address).call()

            if balance == 0:
                return {
                    'success': False,
                    'message': 'No tokens to sell'
                }

            # Calculate amount to sell based on percentage
            amount_in = int(balance * (percentage / 100.0))

            if amount_in == 0:
                return {
                    'success': False,
                    'message': 'Amount too small to sell'
                }

            # Check if token is approved
            # Note: In production, check allowance first

            # Calculate minimum output with slippage
            amount_out_minimum = 0  # Accept any amount (high slippage tolerance)

            # Build swap parameters
            params = {
                'tokenIn': token_checksum,
                'tokenOut': weth_checksum,
                'fee': 10000,  # 1% fee tier
                'recipient': account.address,
                'amountIn': amount_in,
                'amountOutMinimum': amount_out_minimum,
                'sqrtPriceLimitX96': 0  # No price limit
            }

            # Build transaction
            txn = self.router.functions.exactInputSingle(params).build_transaction({
                'from': account.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 8453  # Base mainnet
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            logger.info(f"✅ Sell transaction sent: {tx_hash.hex()}")

            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'percentage_sold': percentage,
                'message': f'Sell order submitted! TX: {tx_hash.hex()[:10]}...'
            }

        except Exception as e:
            logger.error(f"❌ Sell failed: {e}")
            return {
                'success': False,
                'message': f'Sell failed: {str(e)[:100]}'
            }

    def get_token_balance(self, token_address: str, wallet_address: str) -> dict:
        """Get token balance for a wallet"""
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )

            balance = token_contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()

            decimals = token_contract.functions.decimals().call()
            balance_formatted = balance / (10 ** decimals)

            return {
                'success': True,
                'balance': balance,
                'balance_formatted': balance_formatted,
                'decimals': decimals
            }

        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def get_eth_balance(self, wallet_address: str) -> dict:
        """Get ETH balance for a wallet"""
        try:
            balance = self.w3.eth.get_balance(Web3.to_checksum_address(wallet_address))
            balance_eth = self.w3.from_wei(balance, 'ether')

            return {
                'success': True,
                'balance': balance,
                'balance_eth': float(balance_eth)
            }

        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

