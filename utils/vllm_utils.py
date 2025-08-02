"""
VLLM utilities for automatic detection and integration with CosyVoice2
(Modified to support a wider range of compatible vllm versions)
"""
import sys
import os
import importlib.util
import logging
from typing import Optional, Tuple


def check_vllm_availability() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if vllm is available and compatible for CosyVoice2 usage.
    
    Returns:
        Tuple of (is_available, version, error_message)
    """
    try:
        # Try to import vllm with error suppression for known conflicts
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import vllm
        
        # Get the installed version
        version = getattr(vllm, '__version__', 'unknown')
        
        # --- MODIFICATION START ---
        # The original check rigidly required v0.9.0+, which caused dependency conflicts.
        # This updated check is more flexible and accepts any version that can be imported,
        # relying on the Dockerfile to install a known-good compatible version.
        # We will simply check if the version is parsable and seems valid (e.g., 0.4.0+).
        if version != 'unknown':
            try:
                version_parts = version.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                
                # Accept any reasonably modern version of vllm (e.g., 0.4.0 or newer)
                if major == 0 and minor >= 4:
                    return True, version, None
                else:
                    # This case is unlikely if the Dockerfile is correct, but serves as a safeguard.
                    return False, version, f"vllm version {version} is not compatible. A newer version is required."
            except (ValueError, IndexError):
                # If we can't parse version, log a warning but assume it might work.
                logging.warning(f"Could not parse vllm version: {version}. Assuming compatibility.")
                return True, version, None
        # --- MODIFICATION END ---
        
        return True, version, None
        
    except ImportError as e:
        return False, None, f"vllm not installed: {str(e)}"
    except Exception as e:
        # Handle specific model registration conflicts during import
        error_msg = str(e)
        if "already used by a Transformers config" in error_msg:
            logging.warning(f"VLLM import warning (model name conflict): {error_msg}")
            # Still try to return True as vllm might be functional despite the warning
            try:
                import vllm
                version = getattr(vllm, '__version__', 'unknown')
                return True, version, f"Warning: {error_msg}"
            except:
                return False, None, f"Error checking vllm: {error_msg}"
        return False, None, f"Error checking vllm: {error_msg}"


def register_cosyvoice2_vllm() -> bool:
    """
    Register CosyVoice2 model with VLLM if available.
    
    Returns:
        True if successfully registered, False otherwise
    """
    try:
        is_available, version, error = check_vllm_availability()
        if not is_available:
            return False
            
        # Import and register CosyVoice2 for VLLM
        # This part might need updates if CosyVoice source code changes.
        from vllm import ModelRegistry
        from cosyvoice.vllm.cosyvoice2 import CosyVoice2ForCausalLM
        
        # Check if model is already registered to avoid conflicts
        try:
            ModelRegistry.register_model("CosyVoice2ForCausalLM", CosyVoice2ForCausalLM)
        except ValueError as ve:
            # Model already registered or name conflict
            if "already used" in str(ve) or "already registered" in str(ve):
                logging.info(f"CosyVoice2 model already registered with VLLM: {ve}")
                return True
            else:
                raise ve
        
        return True
        
    except ImportError as e:
        logging.warning(f"Could not import VLLM registration components: {e}")
        return False
    except Exception as e:
        logging.warning(f"Failed to register CosyVoice2 with VLLM: {e}")
        return False


def should_enable_vllm_for_model(model_dir: str) -> bool:
    """
    Determine if VLLM should be enabled for a given model directory.
    
    Args:
        model_dir: Path to the model directory
        
    Returns:
        True if VLLM should be enabled, False otherwise
    """
    is_available, _, _ = check_vllm_availability()
    if not is_available:
        return False
    
    if 'CosyVoice2' in model_dir or os.path.exists(os.path.join(model_dir, 'cosyvoice2.yaml')):
        return True
    
    return False


def get_vllm_status() -> dict:
    """
    Get comprehensive VLLM status information.
    
    Returns:
        Dictionary with VLLM status information
    """
    is_available, version, error = check_vllm_availability()
    
    status = {
        'available': is_available,
        'version': version,
        'error': error,
        'registered': False
    }
    
    if is_available:
        status['registered'] = register_cosyvoice2_vllm()
    
    return status


def log_vllm_status():
    """Log VLLM availability status."""
    status = get_vllm_status()
    
    if status['available']:
        if status['registered']:
            print(f"✅ VLLM v{status['version']} available and CosyVoice2 registered for acceleration")
        else:
            print(f"⚠️  VLLM v{status['version']} available but CosyVoice2 registration failed. Check for compatibility issues.")
    else:
        print(f"❌ VLLM not available: {status['error']}")
        print("💡 To enable VLLM acceleration, ensure a compatible version is installed in the environment.")
