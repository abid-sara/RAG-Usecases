"""Patch for transformers library."""

import logging

logger = logging.getLogger("arabic_qa")

def find_tied_parameters(model):
    """
    Find tied parameters in the model.
    
    Args:
        model: PyTorch model
        
    Returns:
        List of tuples with tied parameter references
    """
    tied_params = []
    seen_params = {}
    
    for name, param in model.named_parameters():
        param_id = id(param.data_ptr())
        if param_id in seen_params:
            tied_params.append((name, seen_params[param_id]))
        else:
            seen_params[param_id] = name
    
    return tied_params

def patch_transformers():
    """
    Patch transformers library to add the missing init_empty_weights function.
    """
    try:
        # Try importing the function first to see if it's already defined
        from transformers.utils import init_empty_weights
        logger.info("init_empty_weights already exists, no patching needed")
        return
    except ImportError:
        pass
    
    logger.info("Patching transformers to add init_empty_weights")
    
    try:
        import torch
        from contextlib import contextmanager
        
        # Define the missing function
        @contextmanager
        def init_empty_weights():
            """Context manager that sets the weights to empty during initialization."""
            old_instantiate = torch.nn.Linear.__init__
            
            def new_instantiate(self, *args, **kwargs):
                old_instantiate(self, *args, **kwargs)
                self.weight.fill_(0)
                if self.bias is not None:
                    self.bias.fill_(0)
            
            torch.nn.Linear.__init__ = new_instantiate
            yield
            torch.nn.Linear.__init__ = old_instantiate
        
        # Add function to transformers namespace
        import transformers.modeling_utils
        transformers.modeling_utils.init_empty_weights = init_empty_weights
        transformers.modeling_utils.find_tied_parameters = find_tied_parameters
        
        # Also add to transformers.utils if it exists
        try:
            import transformers.utils
            transformers.utils.init_empty_weights = init_empty_weights
            transformers.utils.find_tied_parameters = find_tied_parameters
        except:
            pass
            
        logger.info("Successfully patched transformers library")
        
    except Exception as e:
        logger.error(f"Error patching transformers: {e}")