from typing import TypedDict, Dict, Any

# Define TypedDict for BuildContext
class BuildContext(TypedDict):
    # Define fields here as per requirements
    pass

# Define TypedDict for MessageDict
class MessageDict(TypedDict):
    # Define fields here as per requirements
    pass

# Valid template types
VALID_TEMPLATE_TYPES = {"type1", "type2", "type3"}  # Example template types

class MessageFormatterEmpty:
    def __init__(self):
        self.extra_info = {}  # Initialize the extra_info key

    def format(self):
        # Formatting logic here
        pass

# Existing code from buildbot/buildbot master branch with improvements:
# (Include the original content of the message.py file here with updates)

# Example of how to handle the immutable context
def handle_context(context: BuildContext) -> None:
    # Instead of context.update(new_context), use dictionary unpacking
    new_context = {...context, "new_field": "new_value"}
    # Use new_context for further processing here
