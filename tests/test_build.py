import os

def test_phoenix_spec_console():
    spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phoenix.spec")
    
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "console=True" in content, "phoenix.spec deve ter console=True configurado"
