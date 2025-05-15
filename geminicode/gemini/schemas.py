should_continue_schema = {
    "type": "OBJECT",
    "properties": {
        "should_continue": {
            "type": "BOOLEAN"
        }
    },
    "required": ["should_continue"]  # Ensures the "result" field is always present
    # "propertyOrdering": ["result"] # Optional for a single field, but good practice
}