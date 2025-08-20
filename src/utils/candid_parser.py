"""
Candid Parser - Extracts method information from .did files.

This module parses Candid interface files to automatically discover
available methods for dynamic endpoint generation.
"""

import re
from typing import List, Dict, Tuple

class CandidParser:
    """Parser for Candid interface files."""
    
    @staticmethod
    def parse_did_file(did_content: str) -> List[Dict]:
        """
        Parse a .did file and extract method information.
        
        Args:
            did_content: The content of the .did file
            
        Returns:
            List of method dictionaries with name, type, and parameters
        """
        methods = []
        
        # Look for service definition
        service_match = re.search(r'service\s*:\s*\{([^}]+)\}', did_content, re.DOTALL)
        if not service_match:
            return methods
        
        service_content = service_match.group(1)
        
        # Extract method definitions
        # Pattern: method_name : (args) -> (return_type) query?;
        method_pattern = r'(\w+)\s*:\s*\(([^)]*)\)\s*->\s*\(([^)]*)\)\s*(query|composite_query)?\s*;'
        
        for match in re.finditer(method_pattern, service_content):
            method_name = match.group(1)
            args_str = match.group(2).strip()
            return_type = match.group(3).strip()
            is_query = match.group(4) is not None
            
            # Parse arguments
            args = []
            if args_str:
                # Simple argument parsing (can be enhanced)
                arg_parts = [arg.strip() for arg in args_str.split(',') if arg.strip()]
                for arg in arg_parts:
                    if ':' in arg:
                        arg_name, arg_type = arg.split(':', 1)
                        args.append({
                            "name": arg_name.strip(),
                            "type": arg_type.strip()
                        })
                    else:
                        args.append({
                            "name": f"param_{len(args)}",
                            "type": arg.strip()
                        })
            
            methods.append({
                "name": method_name,
                "args": args,
                "return_type": return_type,
                "is_query": is_query,
                "http_method": "GET" if is_query else "POST"
            })
        
        return methods
    
    @staticmethod
    def get_method_info(methods: List[Dict], method_name: str) -> Dict:
        """Get information about a specific method."""
        for method in methods:
            if method["name"] == method_name:
                return method
        return None