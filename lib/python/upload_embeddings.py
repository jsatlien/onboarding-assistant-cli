#!/usr/bin/env python3
"""
Embedding Upload Companion Tool

This CLI tool automates the process of generating and uploading text embeddings to
OpenAI's Embedding API. It converts metadata files into embedding-ready format and
stores the resulting embeddings locally.
"""

import os
import sys
import json
import yaml
import time
import hashlib
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from tqdm import tqdm

import openai
from openai import OpenAI
from openai.types.create_embedding_response import CreateEmbeddingResponse

# Import our formatter utility
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.format_for_embedding import format_file_for_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'errors.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upload_embeddings')

# Constants
DEFAULT_CONFIG_PATH = os.path.join('config', 'assistant_config.yaml')
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
MAX_TOKEN_WARNING = 5000  # Warn if text exceeds this token count (approximate)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate the YAML configuration file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        The loaded configuration as a dictionary
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = ['openai_api_key', 'embedding_model', 'metadata_path']
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValueError(f"Missing required fields in config: {', '.join(missing_fields)}")
    
    # Validate API key format
    api_key = config.get('openai_api_key', '')
    if not api_key.startswith('sk-'):
        raise ValueError("Invalid OpenAI API key format. Should start with 'sk-'")
    
    # Set default values for optional fields
    if 'index_path' not in config:
        config['index_path'] = os.path.join(config['metadata_path'], 'embeddings.json')
    
    if 'embedding_format' not in config:
        config['embedding_format'] = 'openai'
    
    # Ensure paths exist
    metadata_path = config['metadata_path']
    if not os.path.exists(metadata_path):
        raise ValueError(f"Metadata path does not exist: {metadata_path}")
    
    # Check if metadata path contains JSON files
    json_files = list(Path(metadata_path).glob('*.json'))
    if not json_files:
        raise ValueError(f"No JSON files found in metadata path: {metadata_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(config['index_path'])
    os.makedirs(output_dir, exist_ok=True)
    
    return config


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        The SHA-256 hash as a hexadecimal string
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_hash_index(index_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load the hash index file if it exists.
    
    Args:
        index_path: Path to the hash index file
        
    Returns:
        The hash index as a dictionary, or an empty dictionary if the file doesn't exist
    """
    hash_index_path = os.path.join(os.path.dirname(index_path), 'hashes.json')
    if os.path.exists(hash_index_path):
        try:
            with open(hash_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid hash index file: {hash_index_path}. Creating a new one.")
    return {}


def save_hash_index(index_path: str, hash_index: Dict[str, Dict[str, str]]) -> None:
    """
    Save the hash index to a file.
    
    Args:
        index_path: Path to the embedding index file (used to determine hash index path)
        hash_index: The hash index to save
    """
    hash_index_path = os.path.join(os.path.dirname(index_path), 'hashes.json')
    with open(hash_index_path, 'w', encoding='utf-8') as f:
        json.dump(hash_index, f, indent=2)


def load_embedding_index(index_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the embedding index file if it exists.
    
    Args:
        index_path: Path to the embedding index file
        
    Returns:
        The embedding index as a dictionary, or an empty dictionary if the file doesn't exist
    """
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid embedding index file: {index_path}. Creating a new one.")
    return {}


def save_embedding_index(index_path: str, embedding_index: Dict[str, Dict[str, Any]]) -> None:
    """
    Save the embedding index to a file.
    
    Args:
        index_path: Path to the embedding index file
        embedding_index: The embedding index to save
    """
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(embedding_index, f, indent=2)


def create_embedding(client: OpenAI, text: str, model: str, retries: int = MAX_RETRIES) -> Tuple[List[float], Optional[str]]:
    """
    Create an embedding for the given text using the OpenAI API.
    
    Args:
        client: The OpenAI client
        text: The text to embed
        model: The embedding model to use
        retries: Number of retries for failed API calls
        
    Returns:
        A tuple of (embedding vector, error message if any)
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(retries + 1):
        try:
            response = client.embeddings.create(
                input=text,
                model=model
            )
            # Return the embedding vector
            return response.data[0].embedding, None
        except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
            if i < retries:
                # Calculate delay with exponential backoff
                delay = RETRY_DELAYS[min(i, len(RETRY_DELAYS) - 1)]
                logger.warning(f"API error: {str(e)}. Retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
            else:
                # All retries failed
                return [], f"Failed after {retries} retries: {str(e)}"
        except Exception as e:
            # Don't retry other types of errors
            return [], f"Error creating embedding: {str(e)}"


def process_metadata_file(
    file_path: str,
    client: OpenAI,
    model: str,
    embedding_index: Dict[str, Dict[str, Any]],
    hash_index: Dict[str, Dict[str, str]],
    force: bool = False,
    verbose: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Process a single metadata file: format it, create an embedding, and store the result.
    
    Args:
        file_path: Path to the metadata file
        client: The OpenAI client
        model: The embedding model to use
        embedding_index: The current embedding index
        hash_index: The current hash index
        force: Whether to force processing even if the file hasn't changed
        verbose: Whether to print verbose output
        
    Returns:
        A tuple of (success, route, error message if any)
    """
    try:
        # Load and parse the metadata file to extract the route
        with open(file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        route = metadata.get('route', '')
        if not route:
            return False, None, f"No route found in metadata file: {file_path}"
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Check if the file has changed
        if not force and route in hash_index:
            if hash_index[route]['hash'] == file_hash:
                if verbose:
                    logger.info(f"Skipping unchanged file: {file_path}")
                return True, route, None
        
        # Format the metadata for embedding
        formatted_text = format_file_for_embedding(file_path)
        
        # Warn if the text is too long
        if len(formatted_text) > MAX_TOKEN_WARNING:
            logger.warning(f"Text for {route} may be too long ({len(formatted_text)} chars). Consider chunking.")
        
        # Create the embedding
        start_time = time.time()
        embedding, error = create_embedding(client, formatted_text, model)
        end_time = time.time()
        
        if error:
            return False, route, error
        
        # Store the embedding in the index
        embedding_index[route] = {
            'embedding': embedding,
            'text': formatted_text
        }
        
        # Update the hash index
        hash_index[route] = {
            'hash': file_hash,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        if verbose:
            logger.info(f"Created embedding for {route} in {end_time - start_time:.2f}s")
        
        return True, route, None
    
    except Exception as e:
        return False, None, f"Error processing file {file_path}: {str(e)}"


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(description='Upload embeddings for Onboarding Assistant metadata.')
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH, help='Path to the YAML configuration file')
    parser.add_argument('--force', action='store_true', help='Force processing of all files, even if unchanged')
    parser.add_argument('--verbose', action='store_true', help='Print verbose output')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress bar and non-error output')
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    
    try:
        # Load and validate configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Initialize OpenAI client
        client = OpenAI(api_key=config['openai_api_key'])
        
        # Load existing embedding and hash indices
        index_path = config['index_path']
        embedding_index = load_embedding_index(index_path)
        hash_index = load_hash_index(index_path)
        
        # Find all JSON files in the metadata directory
        metadata_path = config['metadata_path']
        json_files = list(Path(metadata_path).glob('*.json'))
        
        if not json_files:
            logger.warning(f"No JSON files found in {metadata_path}")
            return
        
        logger.info(f"Found {len(json_files)} metadata files to process")
        
        # Process each file
        success_count = 0
        error_count = 0
        skipped_count = 0
        errors = []
        
        # Use tqdm for progress bar unless quiet mode is enabled
        file_iterator = tqdm(json_files, disable=args.quiet)
        for file_path in file_iterator:
            if not args.quiet:
                file_iterator.set_description(f"Processing {file_path.name}")
            
            success, route, error = process_metadata_file(
                str(file_path),
                client,
                config['embedding_model'],
                embedding_index,
                hash_index,
                args.force,
                args.verbose
            )
            
            if success:
                if route in hash_index and not args.force:
                    skipped_count += 1
                else:
                    success_count += 1
            else:
                error_count += 1
                errors.append((str(file_path), error))
                logger.error(f"Error processing {file_path}: {error}")
        
        # Save the updated indices
        save_embedding_index(index_path, embedding_index)
        save_hash_index(index_path, hash_index)
        
        # Print summary
        logger.info("\nSummary:")
        logger.info(f"  Processed: {len(json_files)} files")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Skipped (unchanged): {skipped_count}")
        logger.info(f"  Failed: {error_count}")
        
        if errors:
            logger.info("\nErrors:")
            for file_path, error in errors:
                logger.info(f"  {file_path}: {error}")
        
        logger.info(f"\nEmbeddings saved to: {index_path}")
        logger.info(f"Hash index saved to: {os.path.join(os.path.dirname(index_path), 'hashes.json')}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
