def build_royalties(payload):
    royalty_percent = payload.get("royalty_percent", 50)
    
    # Publishing splits
    publishing_same_as_recording = payload.get("publishing_same_as_recording", True)
    
    if publishing_same_as_recording:
        # Writer gets same as recording royalty, publisher gets the rest
        writer_share = royalty_percent
        publisher_share = 100 - royalty_percent
    else:
        # Custom split
        writer_share = payload.get("writer_share", 50)
        publisher_share = 100 - writer_share

    return {
        "royalty_percentage": royalty_percent,
        "writer_share": writer_share,
        "publisher_share": publisher_share,
    }
