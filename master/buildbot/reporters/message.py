from typing import TypedDict

class MessageData(TypedDict):
    id: int
    content: str
    sender: str

class ImmutableContext:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def validate_template(template: str) -> None:
    if not isinstance(template, str) or not template:
        raise ValueError('Template must be a non-empty string.')


def handle_message(data: MessageData, context: ImmutableContext) -> None:
    validate_template(data['content'])
    # Add improved message handling logic here
