#!/usr/bin/env python3
"""
Format for Embedding Utility

This module transforms structured metadata JSON into flat embedding-ready text blocks
that can be sent to OpenAI's Embedding API.
"""

import json
from typing import Dict, Any, List, Optional


def format_metadata_for_embedding(metadata: Dict[str, Any]) -> str:
    """
    Convert structured metadata JSON into a flattened text block suitable for embedding.
    
    Args:
        metadata: A dictionary containing route context metadata
        
    Returns:
        A formatted string ready for embedding
    """
    # Initialize the output text
    output_parts = []
    
    # Add route information
    route = metadata.get("route", "")
    output_parts.append(f"ROUTE: {route}")
    output_parts.append("")  # Empty line for readability
    
    # Add description
    description = metadata.get("description", "")
    if description:
        output_parts.append("DESCRIPTION:")
        output_parts.append(description)
        output_parts.append("")  # Empty line for readability
    
    # Add UI elements
    elements = metadata.get("elements", [])
    if elements:
        output_parts.append("UI ELEMENTS:")
        for element in elements:
            element_id = element.get("id", "")
            element_desc = element.get("description", "")
            output_parts.append(f"- {element_id}: {element_desc}")
        output_parts.append("")  # Empty line for readability
    
    # Add API calls
    api_calls = metadata.get("api_calls", [])
    if api_calls:
        output_parts.append("API CALLS:")
        for api_call in api_calls:
            output_parts.append(f"- {api_call}")
        output_parts.append("")  # Empty line for readability
    
    # Add user actions
    user_actions = metadata.get("user_actions", [])
    if user_actions:
        output_parts.append("USER ACTIONS:")
        for action in user_actions:
            output_parts.append(f"- {action}")
        output_parts.append("")  # Empty line for readability
    
    # Add dependencies if present
    dependencies = metadata.get("dependencies", [])
    if dependencies:
        output_parts.append("DEPENDENCIES:")
        for dependency in dependencies:
            output_parts.append(f"- {dependency}")
        output_parts.append("")  # Empty line for readability
    
    # Join all parts with newlines
    return "\n".join(output_parts).strip()


def load_metadata_file(file_path: str) -> Dict[str, Any]:
    """
    Load a metadata JSON file.
    
    Args:
        file_path: Path to the metadata JSON file
        
    Returns:
        The loaded metadata as a dictionary
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file isn't valid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_file_for_embedding(file_path: str) -> str:
    """
    Load a metadata file and format it for embedding.
    
    Args:
        file_path: Path to the metadata JSON file
        
    Returns:
        A formatted string ready for embedding
    """
    metadata = load_metadata_file(file_path)
    return format_metadata_for_embedding(metadata)


if __name__ == "__main__":
    # Simple test if run directly
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        try:
            formatted = format_file_for_embedding(test_file)
            print(formatted)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python format_for_embedding.py <metadata_file.json>")
