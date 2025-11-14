import json
import os
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter 

# --- Constantes do Windows API ---
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE    = 0x02

def carregar_dados(caminho_json="progress.json"):
    """
    Carrega os dados de progresso a partir do arquivo JSON.
    Retorna None em caso de erro (FileNotFound ou JSONDecode) para manter a interface gráfica ativa.
    """
    try:
        # Tenta carregar o JSON do diretório de trabalho atual
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {caminho_json} não encontrado. Certifique-se de que o caminho JSON_PATH em task_adder.py está correto.")
        return None
    except json.JSONDecodeError:
        print("Erro: Arquivo JSON inválido. Verifique a sintaxe.")
        return None

def aplicar_wallpaper(caminho_imagem):
    """Define a imagem gerada como papel de parede do Windows."""
    print(f"Aplicando novo wallpaper: {caminho_imagem}")
    if not os.path.exists(caminho_imagem):
        print(f"Erro: Imagem de saída não encontrada em {caminho_imagem}")
        return

    sucesso = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        caminho_imagem,
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    
    if sucesso:
        print("Wallpaper aplicado com sucesso.")
    else:
        print("Erro ao aplicar o wallpaper. (Verifique permissões ou o caminho da imagem)")

def desenhar_texto_com_contorno(draw, pos, text, font, cor_principal, cor_contorno, largura_contorno):
    """Desenha texto com um contorno simples (stroke) ao redor."""
    x, y = pos
    
    # 1. Desenha o contorno (deslocando a posição em 8 direções)
    for dx in range(-largura_contorno, largura_contorno + 1):
        for dy in range(-largura_contorno, largura_contorno + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=cor_contorno)
                
    # 2. Desenha o texto principal por cima
    draw.text(pos, text, font=font, fill=cor_principal)

def gerar_wallpaper():
    """Gera a imagem do wallpaper com base nos dados do JSON, desenhando 3 níveis com contorno."""
    dados = carregar_dados()
    
    if dados is None:
        return
        
    # 1. Configuração da Imagem
    largura_str, altura_str = dados['resolucao'].split('x')
    largura = int(largura_str)
    altura = int(altura_str)
    
    # Carregando cores
    cor_fundo = tuple(dados['fundo_cor'])
    cor_principal = tuple(dados['texto_cor_principal']) 
    cor_concluido = tuple(dados['texto_cor_concluido'])
    cor_contorno = tuple(dados['contorno_cor'])        
    largura_contorno = dados['contorno_largura']       

    # Lógica para carregar imagem de fundo
    caminho_fundo_relativo = dados.get('caminho_fundo')
    
    # Se o caminho de fundo não for absoluto (sem disco/raiz), tentamos resolver a partir da pasta do script
    if caminho_fundo_relativo and not os.path.isabs(caminho_fundo_relativo):
        caminho_fundo_relativo = os.path.join(os.path.dirname(dados['caminho_saida']), caminho_fundo_relativo)
        
    if caminho_fundo_relativo and os.path.exists(caminho_fundo_relativo):
        try:
            img = Image.open(caminho_fundo_relativo).resize((largura, altura))
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo. Usando cor sólida. Erro: {e}")
            img = Image.new('RGB', (largura, altura), color=cor_fundo)
    else:
        img = Image.new('RGB', (largura, altura), color=cor_fundo)
    
    draw = ImageDraw.Draw(img)

    # Tenta carregar fontes
    try:
        fonte_titulo = ImageFont.truetype("arialbd.ttf", 60)
        fonte_fase = ImageFont.truetype("arialbd.ttf", 36)
        fonte_modulo = ImageFont.truetype("arial.ttf", 30)
        fonte_pratica = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        print("Aviso: Fontes não encontradas, usando fonte padrão.")
        fonte_titulo = ImageFont.load_default()
        fonte_fase = ImageFont.load_default()
        fonte_modulo = ImageFont.load_default()
        fonte_pratica = ImageFont.load_default()

    # 2. Desenho do Título
    margin_x = largura // 20 
    margin_y = altura // 20
    
    desenhar_texto_com_contorno(draw, (margin_x, margin_y), dados['titulo'], 
                                fonte_titulo, cor_principal, cor_contorno, largura_contorno)
    y_pos = margin_y + 100
    
    # 3. Desenho dos Módulos (Roadmap Três Níveis)
    total_praticas_global = 0
    praticas_concluidas_global = 0

    for modulo in dados['modulos']:
        
        # Tipo FASE (Separador)
        if modulo.get('tipo') == 'FASE':
            desenhar_texto_com_contorno(draw, (margin_x, y_pos), modulo['nome'], 
                                        fonte_fase, cor_concluido, cor_contorno, largura_contorno)
            y_pos += 50
            continue

        # Nível 1: Módulo (Semana)
        mod_cor = cor_principal
        desenhar_texto_com_contorno(draw, (margin_x, y_pos), f"▶ {modulo['nome']}", 
                                    fonte_modulo, mod_cor, cor_contorno, largura_contorno)
        y_pos += 35

        # Nível 2: Subtópicos
        for subtopico in modulo.get('subtopicos', []):
            sub_cor = cor_principal
            desenhar_texto_com_contorno(draw, (margin_x + 20, y_pos), f"  • {subtopico['nome']}", 
                                        fonte_pratica, sub_cor, cor_contorno, largura_contorno)
            y_pos += 30

            # Nível 3: Práticas (Checklist)
            for pratica in subtopico.get('praticas', []):
                total_praticas_global += 1
                prat_concluido = pratica.get('concluido', False)
                
                if prat_concluido:
                    praticas_concluidas_global += 1
                    prefixo = "✅"
                    prat_cor = cor_concluido
                else:
                    prefixo = "☐"
                    prat_cor = cor_principal
                
                # Desenha a Prática com recuo duplo e o ícone de checklist
                desenhar_texto_com_contorno(draw, (margin_x + 40, y_pos), f"    {prefixo} {pratica['nome']}", 
                                            fonte_pratica, prat_cor, cor_contorno, largura_contorno)
                y_pos += 25
            
            y_pos += 10
        y_pos += 20

    # 4. Desenho da Barra de Progresso (Com correção de métricas de texto)
    progresso_percentual = (praticas_concluidas_global / total_praticas_global) * 100 if total_praticas_global > 0 else 0
    
    bar_altura = altura - (altura // 10)
    margin_bar = largura // 20
    bar_largura = largura - (2 * margin_bar)
    bar_height = 30
    
    # Fundo da barra
    draw.rectangle(
        (margin_bar, bar_altura, largura - margin_bar, bar_altura + bar_height),
        fill=(50, 50, 50), 
        outline=(200, 200, 200)
    )
    
    # Progresso
    progresso_largura = int(bar_largura * (progresso_percentual / 100))
    draw.rectangle(
        (margin_bar, bar_altura, margin_bar + progresso_largura, bar_altura + bar_height),
        fill=cor_concluido 
    )
    
    # Texto de progresso 
    texto_progresso = f"Progresso Global: {praticas_concluidas_global} de {total_praticas_global} Práticas ({progresso_percentual:.1f}%)"
    
    # CORREÇÃO: Utiliza getlength() e getmetrics() no objeto da fonte
    text_w = fonte_modulo.getlength(texto_progresso)
    try:
        text_h = fonte_modulo.getmetrics()[0]
    except AttributeError:
        text_h = 30 
        
    text_x = margin_bar + (bar_largura - text_w) // 2
    text_y = bar_altura + (bar_height - text_h) // 2
    
    draw.text((text_x, text_y), texto_progresso, fill=(0, 0, 0), font=fonte_modulo)

    # 5. Salvar e Aplicar
    caminho_saida = dados['caminho_saida']
    img.save(caminho_saida)
    aplicar_wallpaper(caminho_saida)

if __name__ == "__main__":
    gerar_wallpaper()