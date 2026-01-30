"""
Rug Hall of Shame - Track and display verified rug pulls caught by the bot
"""
import json
from datetime import datetime
from web3 import Web3

class RugHallOfShame:
    def __init__(self, filename="hall_of_shame.json"):
        self.filename = filename
        self.shame_list = self._load()
    
    def _load(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def add_rug(self, token_address, token_name, rug_type, evidence_url, 
                victims_saved, timestamp=None):
        """Add verified rug to hall of shame"""
        rug_entry = {
            "token_address": token_address,
            "token_name": token_name,
            "rug_type": rug_type,  # "honeypot", "unlocked_liquidity", "high_tax", "fake_renounce"
            "evidence_url": evidence_url,  # Basescan transaction
            "victims_saved": victims_saved,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "verification_status": "pending"  # "verified" after community confirmation
        }
        self.shame_list.append(rug_entry)
        self._save()
        return rug_entry
    
    def verify_rug(self, token_address):
        """Mark a rug as community-verified"""
        for rug in self.shame_list:
            if rug['token_address'].lower() == token_address.lower():
                rug['verification_status'] = 'verified'
                self._save()
                return True
        return False
    
    def _save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.shame_list, f, indent=2)
    
    def get_stats(self):
        """Get statistics for marketing"""
        verified = [r for r in self.shame_list if r['verification_status'] == 'verified']
        total_saved = sum(r['victims_saved'] for r in verified)
        return {
            'total_rugs': len(verified),
            'total_victims_saved': total_saved,
            'by_type': self._count_by_type(verified)
        }
    
    def _count_by_type(self, rugs):
        types = {}
        for rug in rugs:
            rug_type = rug['rug_type']
            types[rug_type] = types.get(rug_type, 0) + 1
        return types
    
    def generate_markdown(self):
        """Generate GitHub-friendly markdown for README"""
        md = "# 🛡️ Rug Hall of Shame\n\n"
        md += "> Verified rugs caught by our bot before major pumps. Updated daily.\n\n"
        
        stats = self.get_stats()
        md += f"**Total Rugs Caught:** {stats['total_rugs']}  \n"
        md += f"**Users Protected:** {stats['total_victims_saved']}+  \n\n"
        
        md += "| Token | Type | Saved Users | Date | Evidence |\n"
        md += "|-------|------|-------------|------|----------|\n"
        
        verified_rugs = [r for r in self.shame_list if r['verification_status'] == 'verified']
        for rug in sorted(verified_rugs, key=lambda x: x['timestamp'], reverse=True)[:20]:
            md += f"| [{rug['token_name']}](https://basescan.org/address/{rug['token_address']}) | `{rug['rug_type']}` | {rug['victims_saved']} | {rug['timestamp'][:10]} | [Tx](https://basescan.org/tx/{rug['evidence_url']}) |\n"
        
        md += "\n⚠️ **Disclaimer**: 99% of new tokens fail. This tool reduces risk but cannot eliminate it. DYOR.\n"
        return md

# Usage in bot.py after catching a rug:
# shame = RugHallOfShame()
# shame.add_rug("0x...", "$RUGTOKEN", "honeypot", "0xTxHash...", 47)
# with open("RUG_HALL_OF_SHAME.md", "w") as f:
#     f.write(shame.generate_markdown())
