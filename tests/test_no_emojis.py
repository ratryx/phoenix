import os
import re

def test_no_emojis_in_source_files():
    """
    Verifica se não existem emojis ou variation selectors nos arquivos fonte do projeto.
    Ignora diretórios irrelevantes e arquivos binários.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    ignore_dirs = {'.git', 'build', 'dist', 'venv', 'env', '__pycache__', 'dados'}
    allowed_extensions = {'.py', '.js', '.html', '.css', '.md', '.json'}
    
    # Regex para capturar Variation Selector-16 (U+FE0F) e a maioria dos blocos de emojis e símbolos
    # U+2600-U+26FF (Símbolos Diversos)
    # U+2700-U+27BF (Dingbats)
    # U+1F300-U+1F5FF (Símbolos e Pictogramas Diversos)
    # U+1F600-U+1F64F (Emoticons)
    # U+1F680-U+1F6FF (Transporte e Mapa)
    emoji_pattern = re.compile(r'[\u2600-\u26ff\u2700-\u27bf\U0001f300-\U0001f5ff\U0001f600-\U0001f64f\U0001f680-\U0001f6ff\ufe0f]')
    
    found_emojis = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
        
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed_extensions:
                continue
                
            filepath = os.path.join(dirpath, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        matches = emoji_pattern.findall(line)
                        if matches:
                            # Filtra falsos positivos se houver, mas a regex é restrita aos blocos de emoji
                            found_emojis.append(f"{filepath}:{line_num} contém {matches}")
            except UnicodeDecodeError:
                # Arquivo binário ou encoding diferente, ignora
                pass
                
    if found_emojis:
        print("\nArquivos com emojis encontrados:")
        for msg in found_emojis:
            print(msg)
        assert False, f"Foram encontrados emojis em {len(found_emojis)} linhas de código. Eles devem ser removidos."
