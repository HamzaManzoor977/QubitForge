from agent import generate

def deep_research(prompt, mode="standard"):
    from agent import generate

    if mode == "quick":
        instruction = (
            "Give a concise, clear explanation. "
            "Do NOT include citations or references."
        )

    elif mode == "standard":
        instruction = (
            "Give a structured explanation. "
            "At the END, add a section titled 'SOURCES' "
            "with 2–3 credible references (books, universities, journals). "
            "Do NOT fabricate URLs."
        )

    else:  # deep
        instruction = (
            "Write a deep, academic-style explanation. "
            "Use sections and technical clarity. "
            "At the END, add a section titled 'REFERENCES' "
            "with 4–6 credible sources (journals, textbooks, official sites). "
            "No fake citations."
        )

    system_prompt = f"""
    You are a professional research analyst.

    INSTRUCTION:
    {instruction}

    TOPIC / CONTEXT:
    {prompt}
    """

    return generate(system_prompt)


