conversation_memory = ""

def update_memory(new_text: str):
    global conversation_memory
    conversation_memory += "\n" + new_text

def get_memory() -> str:
    return conversation_memory
