    def _log_wallet_access(self, cursor, user_id: int, wallet_address: str, action: str):
        """
        Internal helper to log wallet access
        
        Args:
            cursor: Active database cursor
            user_id: User ID
            wallet_address: Wallet address
            action: Action type (created, retrieved, exported, transaction)
        """
        cursor.execute('''
            INSERT INTO wallet_access_log (user_id, wallet_address, action)
            VALUES (?, ?, ?)
        ''', (user_id, wallet_address, action))
        logger.info(f"📝 Logged wallet access: user={user_id}, action={action}")
