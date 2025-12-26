"""
Simple tools for policy analysis
"""
from agno.tools.toolkit import Toolkit
from agno.utils.log import logger


class PolicyTools(Toolkit):
    def __init__(self):
        super().__init__(name="policy_tools")
        self.register(self.step_counter)
        self.register(self.role_lookup)
    
    def step_counter(self, text: str, keyword: str = "approval") -> dict:
        """
        Count the number of steps or occurrences of a keyword in text.
        
        Args:
            text: The text to analyze
            keyword: The keyword to count (default: "approval")
        
        Returns:
            Dictionary with count and details
        """
        lines = text.lower().split('\n')
        count = 0
        matching_lines = []
        
        for i, line in enumerate(lines, 1):
            if keyword.lower() in line:
                count += 1
                matching_lines.append(f"Line {i}: {line.strip()}")
        
        logger.info(f"Counted {count} occurrences of '{keyword}'")
        
        return {
            "keyword": keyword,
            "count": count,
            "matching_lines": matching_lines[:5]
        }
    
    def role_lookup(self, role: str) -> dict:
        """
        Lookup role-based approval rules and permissions.
        
        Args:
            role: The role to lookup (e.g., "manager", "hr", "employee")
        
        Returns:
            Dictionary with role permissions and approval limits
        """
        role_rules = {
            "employee": {
                "can_request": ["hardware", "software", "leave", "training"],
                "can_approve": [],
                "approval_limit": 0,
                "requires_approval_from": ["manager"]
            },
            "manager": {
                "can_request": ["hardware", "software", "leave", "training", "budget"],
                "can_approve": ["hardware", "software", "leave", "training"],
                "approval_limit": 5000,
                "requires_approval_from": ["director"]
            },
            "director": {
                "can_request": ["hardware", "software", "leave", "training", "budget", "hiring"],
                "can_approve": ["hardware", "software", "leave", "training", "budget"],
                "approval_limit": 25000,
                "requires_approval_from": ["ceo"]
            },
            "hr": {
                "can_request": ["hardware", "software", "leave", "training"],
                "can_approve": ["leave", "training", "onboarding"],
                "approval_limit": 10000,
                "requires_approval_from": ["director"]
            },
            "ceo": {
                "can_request": ["all"],
                "can_approve": ["all"],
                "approval_limit": 100000,
                "requires_approval_from": []
            }
        }
        
        role_lower = role.lower()
        if role_lower in role_rules:
            logger.info(f"Retrieved role rules for: {role}")
            return {
                "role": role,
                "found": True,
                "rules": role_rules[role_lower]
            }
        else:
            return {
                "role": role,
                "found": False,
                "error": f"Role '{role}' not found in system",
                "available_roles": list(role_rules.keys())
            }

