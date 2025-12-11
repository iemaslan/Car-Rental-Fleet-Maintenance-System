"""
Compressed file operations for CRFMS snapshots.
Supports gzip compression for both JSON and Protocol Buffers.
"""

import gzip
import json
from pathlib import Path
from typing import Dict, Any

from persistence import crfms_pb2


def save_json_compressed(snapshot: Dict[str, Any], filename: str) -> int:
    """
    Save snapshot to compressed JSON file (.json.gz).
    
    Args:
        snapshot: The snapshot dictionary to save
        filename: Output filename (will add .gz if not present)
        
    Returns:
        Size of compressed file in bytes
    """
    if not filename.endswith('.gz'):
        filename += '.gz'
    
    json_str = json.dumps(snapshot, indent=2, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    with gzip.open(filename, 'wb', compresslevel=9) as f:
        f.write(json_bytes)
    
    return Path(filename).stat().st_size


def load_json_compressed(filename: str) -> Dict[str, Any]:
    """
    Load snapshot from compressed JSON file (.json.gz).
    
    Args:
        filename: Input filename
        
    Returns:
        Loaded snapshot dictionary
    """
    with gzip.open(filename, 'rb') as f:
        json_bytes = f.read()
    
    json_str = json_bytes.decode('utf-8')
    return json.load(json_str)


def save_proto_compressed(snapshot_msg: crfms_pb2.CrfmsSnapshot, filename: str) -> int:
    """
    Save Protocol Buffers snapshot to compressed file (.pb.gz).
    
    Args:
        snapshot_msg: The CrfmsSnapshot protobuf message to save
        filename: Output filename (will add .gz if not present)
        
    Returns:
        Size of compressed file in bytes
    """
    if not filename.endswith('.gz'):
        filename += '.gz'
    
    proto_bytes = snapshot_msg.SerializeToString()
    
    with gzip.open(filename, 'wb', compresslevel=9) as f:
        f.write(proto_bytes)
    
    return Path(filename).stat().st_size


def load_proto_compressed(filename: str) -> crfms_pb2.CrfmsSnapshot:
    """
    Load Protocol Buffers snapshot from compressed file (.pb.gz).
    
    Args:
        filename: Input filename
        
    Returns:
        Loaded CrfmsSnapshot protobuf message
    """
    snapshot = crfms_pb2.CrfmsSnapshot()
    
    with gzip.open(filename, 'rb') as f:
        proto_bytes = f.read()
    
    snapshot.ParseFromString(proto_bytes)
    return snapshot


def get_compression_stats(original_file: str, compressed_file: str) -> Dict[str, Any]:
    """
    Get compression statistics for a file.
    
    Args:
        original_file: Path to original file
        compressed_file: Path to compressed file
        
    Returns:
        Dictionary with compression statistics
    """
    original_size = Path(original_file).stat().st_size
    compressed_size = Path(compressed_file).stat().st_size
    
    ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'savings_bytes': original_size - compressed_size,
        'compression_ratio': ratio
    }


# Convenience function for auto-detection
def save_compressed(data: Any, filename: str, format: str = 'json') -> int:
    """
    Save data with automatic compression.
    
    Args:
        data: Data to save (dict for JSON, CrfmsSnapshot for proto)
        filename: Output filename
        format: 'json' or 'proto'
        
    Returns:
        Size of compressed file in bytes
    """
    if format == 'json':
        return save_json_compressed(data, filename)
    elif format == 'proto':
        return save_proto_compressed(data, filename)
    else:
        raise ValueError(f"Unknown format: {format}")


def load_compressed(filename: str, format: str = None):
    """
    Load compressed data with automatic format detection.
    
    Args:
        filename: Input filename
        format: 'json' or 'proto' (auto-detected from extension if None)
        
    Returns:
        Loaded data (dict for JSON, CrfmsSnapshot for proto)
    """
    if format is None:
        # Auto-detect from filename
        if '.json' in filename:
            format = 'json'
        elif '.pb' in filename or '.protobuf' in filename:
            format = 'proto'
        else:
            raise ValueError(f"Cannot determine format from filename: {filename}")
    
    if format == 'json':
        return load_json_compressed(filename)
    elif format == 'proto':
        return load_proto_compressed(filename)
    else:
        raise ValueError(f"Unknown format: {format}")
