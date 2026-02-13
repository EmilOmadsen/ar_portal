"""
Label Detection and Filtering
Identifies indie labels, DistroKid, and major labels
"""
from typing import Optional, Tuple


# Major labels and their subsidiaries
MAJOR_LABELS = {
    "universal", "umg", "universal music",
    "sony", "sony music", "rca", "columbia", "epic",
    "warner", "wmg", "warner music", "atlantic", "elektra",
    "emi", "capitol", "virgin",
    "interscope", "def jam", "republic", "island",
    "polydor", "geffen", "parlophone"
}

# DIY Distribution platforms (indie-friendly)
INDIE_DISTRIBUTORS = {
    "distrokid", "tunecore", "cd baby", "cdbaby",
    "amuse", "ditto", "stem", "routenote",
    "awal", "united masters", "believe", "the orchard"
}

# Known indie labels (can be expanded)
KNOWN_INDIE_LABELS = {
    "secretly canadian", "matador", "sub pop",
    "merge", "domino", "rough trade", "xl recordings",
    "4ad", "warp", "ninja tune", "mute", "fat possum"
}


class LabelDetector:
    """
    Detect whether a track is from a major label or indie/DIY
    """
    
    @staticmethod
    def normalize_label(label: Optional[str]) -> str:
        """Normalize label name for comparison"""
        if not label:
            return ""
        return label.lower().strip()
    
    @staticmethod
    def is_major_label(label: Optional[str]) -> bool:
        """
        Check if label is a major label or subsidiary
        
        Returns:
            True if major label, False otherwise
        """
        if not label:
            return False
        
        label_normalized = LabelDetector.normalize_label(label)
        
        # Check if any major label keyword is in the label name
        for major in MAJOR_LABELS:
            if major in label_normalized:
                return True
        
        return False
    
    @staticmethod
    def is_indie_distributor(label: Optional[str]) -> bool:
        """
        Check if label is a DIY distributor like DistroKid
        
        Returns:
            True if indie distributor
        """
        if not label:
            return False
        
        label_normalized = LabelDetector.normalize_label(label)
        
        for distributor in INDIE_DISTRIBUTORS:
            if distributor in label_normalized:
                return True
        
        return False
    
    @staticmethod
    def is_known_indie(label: Optional[str]) -> bool:
        """
        Check if label is a known indie label
        """
        if not label:
            return False
        
        label_normalized = LabelDetector.normalize_label(label)
        
        for indie in KNOWN_INDIE_LABELS:
            if indie in label_normalized:
                return True
        
        return False
    
    @staticmethod
    def classify_label(label: Optional[str]) -> Tuple[str, bool]:
        """
        Classify a label as major, indie distributor, indie label, or unknown
        
        Returns:
            Tuple of (classification, is_indie_friendly)
            - classification: "major", "indie_distributor", "indie_label", "unknown"
            - is_indie_friendly: True if indie/DIY, False if major
        """
        if not label:
            return ("unknown", False)
        
        if LabelDetector.is_major_label(label):
            return ("major", False)
        
        if LabelDetector.is_indie_distributor(label):
            return ("indie_distributor", True)
        
        if LabelDetector.is_known_indie(label):
            return ("indie_label", True)
        
        # If label is present but not recognized, assume indie
        # (Major labels are usually well-known)
        return ("unknown_indie", True)
    
    @staticmethod
    def should_include_for_discovery(label: Optional[str]) -> bool:
        """
        Determine if track should be included in discovery
        
        Only include:
        - Indie distributors (DistroKid, etc.)
        - Known indie labels
        - Unknown/small labels (likely indie)
        
        Exclude:
        - Major labels and subsidiaries
        """
        classification, is_indie = LabelDetector.classify_label(label)
        return is_indie


def test_label_detection():
    """Test the label detection"""
    test_labels = [
        "DistroKid",
        "Universal Music Group",
        "TuneCore",
        "Sony Music",
        "Small Indie Records",
        "Warner Music",
        "CD Baby",
        "Atlantic Records",
        "Sub Pop",
        None,
        ""
    ]
    
    print("🏷️  LABEL CLASSIFICATION TEST\n")
    print("=" * 60)
    
    for label in test_labels:
        classification, is_indie = LabelDetector.classify_label(label)
        should_include = LabelDetector.should_include_for_discovery(label)
        
        symbol = "✅" if should_include else "❌"
        print(f"{symbol} {label or '(None)'}")
        print(f"   Classification: {classification}")
        print(f"   Include in discovery: {should_include}\n")


if __name__ == "__main__":
    test_label_detection()
