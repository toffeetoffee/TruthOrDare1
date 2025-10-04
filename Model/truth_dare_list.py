import json
import os
from Model.truth_dare import Truth, Dare

class TruthDareList:
    """Manages truths and dares for a player"""
    
    def __init__(self):
        self.truths = []
        self.dares = []
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default truths and dares from file"""
        try:
            # Get the path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, 'default_truths_dares.json')
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Add default truths
            for text in data['truths']:
                self.truths.append(Truth(text, is_default=True))
            
            # Add default dares
            for text in data['dares']:
                self.dares.append(Dare(text, is_default=True))
        except Exception as e:
            print(f"Warning: Could not load default truths/dares: {e}")
    
    def add_truth(self, text):
        """Add a custom truth"""
        self.truths.append(Truth(text, is_default=False))
    
    def add_dare(self, text):
        """Add a custom dare"""
        self.dares.append(Dare(text, is_default=False))
    
    def get_truths(self):
        """Get all truths as list of dicts"""
        return [t.to_dict() for t in self.truths]
    
    def get_dares(self):
        """Get all dares as list of dicts"""
        return [d.to_dict() for d in self.dares]
    
    def get_count(self):
        """Get count of truths and dares"""
        return {
            'truths': len(self.truths),
            'dares': len(self.dares)
        }