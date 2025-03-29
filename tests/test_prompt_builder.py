from llm.prompt_builder import build_prompt

def test_prompt_structure():
    prompt = build_prompt("Where's my order?", [], None, None)
    assert "User question" in prompt
    assert "Where's my order?" in prompt
