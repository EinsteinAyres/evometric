import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext
import json
import os
import shutil
import time
from PIL import Image

# Importa a função do outro script. Garanta que ambos estejam na mesma pasta.
try:
    from wallpaper_generator import gerar_wallpaper 
except ImportError:
    messagebox.showerror("Erro de Importação", "Não foi possível encontrar 'wallpaper_generator.py'. Certifique-se de que ambos os scripts estão na mesma pasta.")
    exit()

# --- Constantes ---
# Caminho real do seu projeto (com underscore '_')
JSON_PATH = "C:\\Users\\ayres\\Projetos_Python\\EvoMetric\\progress.json"
LAST_COMPLETION_FILE = os.path.join(os.path.dirname(JSON_PATH), "last_completion.txt")

DIMENSAO_MINIMA_LARGURA = 1280
DIMENSAO_MINIMA_ALTURA = 720
COOLDOWN_SECONDS = 4 * 60 * 60 # 4 horas em segundos

# --- Funções Auxiliares de JSON e Tempo ---

def carregar_dados_json():
    """Carrega os dados do roadmap."""
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        messagebox.showerror("Erro de Arquivo", f"Não foi possível carregar o arquivo {JSON_PATH}. Verifique o caminho e a sintaxe JSON.")
        return None

def salvar_dados_json(dados):
    """Salva os dados atualizados no arquivo JSON."""
    try:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Erro de Escrita", f"Erro ao salvar o arquivo: {e}")
        return False

def get_cooldown_status(parent_window):
    """Verifica se o cooldown está ativo."""
    if not os.path.exists(LAST_COMPLETION_FILE):
        return False
    try:
        with open(LAST_COMPLETION_FILE, 'r') as f:
            last_timestamp = float(f.read())
        
        tempo_restante = (last_timestamp + COOLDOWN_SECONDS) - time.time()
        
        if tempo_restante > 0:
            horas = int(tempo_restante // 3600)
            minutos = int((tempo_restante % 3600) // 60)
            messagebox.showinfo("Cooldown Ativo", 
                                f"Você só pode marcar a próxima prática após o cooldown. Tempo restante: {horas}h {minutos}m.",
                                parent=parent_window)
            return True
        return False
        
    except Exception:
        return False

def registrar_conclusao():
    """Salva o timestamp da conclusão."""
    try:
        with open(LAST_COMPLETION_FILE, 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        print(f"Erro ao registrar timestamp: {e}")


# --- CLASSE PRINCIPAL DA APLICAÇÃO ---

class EvoMetricApp:
    def __init__(self, master):
        self.master = master
        self.master.title("EvoMetric Task Adder")
        
        # Chama os métodos que definem a aparência e os botões
        self.configure_root_window() 
        self.create_buttons()

    def configure_root_window(self):
        """Configurações da janela flutuante principal."""
        self.master.overrideredirect(True) 
        self.master.wm_attributes("-topmost", True) 

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        button_size_width = 150
        button_size_height = 40
        padding = 20
        # 4 botões + espaçamento
        total_height = (button_size_height * 4) + (5 * 4 * 2) + 10 
        x_pos = screen_width - button_size_width - padding
        y_pos = screen_height - total_height - padding
        self.master.geometry(f'{button_size_width}x{total_height}+{x_pos}+{y_pos}')

    def create_buttons(self):
        """Cria e empacota todos os botões."""
        
        # Estilos base (sem layout)
        base_styles = {
            "font": ("Arial", 12, "bold"),
            "relief": tk.RAISED,
            "bd": 3,
        }
        
        # Parâmetros de layout
        pack_params = {
            "fill": 'x',
            "padx": 5,
            "pady": 5
        }

        # 1. Botão Adicionar Tarefa
        btn_add = tk.Button(self.master, text="+ Tarefa", command=self.adicionar_tarefa_dialog,
                           bg="#00CC66", fg="white", **base_styles)
        btn_add.pack(**pack_params)

        # 2. Botão Marcar Concluído
        btn_done = tk.Button(self.master, text="✅ Concluir Prática", command=self.marcar_concluido_dialog,
                            bg="#FF9900", fg="white", **base_styles)
        btn_done.pack(**pack_params)

        # 3. Botão Configurações
        btn_config = tk.Button(self.master, text="⚙️ Config", command=self.configurar_layout_dialog,
                             bg="#555555", fg="white", **base_styles)
        btn_config.pack(**pack_params)

        # 4. Botão Selecionar Fundo
        btn_fundo = tk.Button(self.master, text="🖼️ Fundo", command=self.selecionar_e_aplicar_fundo,
                            bg="#3366FF", fg="white", **base_styles)
        btn_fundo.pack(**pack_params)

    # --- Funções de Diálogo (Métodos da Classe) ---

    def adicionar_tarefa_dialog(self):
        """Guia o usuário através da hierarquia Módulo > Subtópico para adicionar uma nova Prática."""
        
        dados = carregar_dados_json()
        if dados is None: return
        
        modulos_reais = [m for m in dados['modulos'] if m.get('tipo') != 'FASE']
        
        nomes_modulos_formatados = []
        for m in modulos_reais:
            if ':' in m['nome']:
                nomes_modulos_formatados.append(f"[{m['nome'].split(':')[0].strip()}] {m['nome'].split(':')[1].strip()}")
            else:
                nomes_modulos_formatados.append(m['nome'])
        
        modulo_selecionado_nome = simpledialog.askstring(
            "Nova Tarefa (1/3) - Selecione o Módulo", 
            "Em qual Módulo/Semana deseja adicionar a nova prática?\n\nOpções:\n" + "\n".join(nomes_modulos_formatados),
            parent=self.master
        )
        
        if not modulo_selecionado_nome: return
        
        modulo_obj = next((m for m in modulos_reais if modulo_selecionado_nome in m['nome']), None)
        
        if not modulo_obj:
            messagebox.showerror("Erro", "Módulo inválido ou não encontrado.", parent=self.master)
            return

        subtopicos = modulo_obj.get('subtopicos', [])
        nomes_subtopicos = [s['nome'] for s in subtopicos]
        
        subtopico_selecionado_nome = simpledialog.askstring(
            "Nova Tarefa (2/3) - Selecione o Subtópico", 
            f"Em qual Subtópico de '{modulo_obj['nome']}' deseja adicionar a prática?\n\nOpções:\n" + "\n".join(nomes_subtopicos),
            parent=self.master
        )
        
        if not subtopico_selecionado_nome: return

        subtopico_obj = next((s for s in subtopicos if s['nome'] == subtopico_selecionado_nome), None)
        
        if not subtopico_obj:
            messagebox.showerror("Erro", "Subtópico inválido ou não encontrado.", parent=self.master)
            return
            
        nova_pratica_nome = simpledialog.askstring(
            "Nova Tarefa (3/3) - Nome da Prática", 
            "Digite o nome da nova Prática/Tarefa de código a ser adicionada:", 
            parent=self.master
        )
        
        if not nova_pratica_nome: return

        novo_item = {"nome": nova_pratica_nome, "concluido": False}
        
        if 'praticas' not in subtopico_obj:
            subtopico_obj['praticas'] = [] 

        subtopico_obj['praticas'].append(novo_item)
        
        if salvar_dados_json(dados):
            messagebox.showinfo("Sucesso", f"Prática '{nova_pratica_nome}' adicionada em:\n{modulo_obj['nome']} > {subtopico_obj['nome']}", parent=self.master)
            gerar_wallpaper()

    def marcar_concluido_dialog(self):
        """Abre uma nova janela modal com lista clicável das práticas pendentes."""
        
        if get_cooldown_status(self.master):
            return

        dados = carregar_dados_json()
        if dados is None: return

        praticas_pendentes_flat = []
        
        for modulo in dados['modulos']:
            if modulo.get('tipo') == 'FASE': continue
            for subtopico in modulo.get('subtopicos', []):
                for pratica in subtopico.get('praticas', []):
                    if not pratica.get('concluido', False):
                        # Garante que o split não falhe se não houver ':'
                        nome_modulo_curto = modulo['nome'].split(':')[0].strip() if ':' in modulo['nome'] else modulo['nome']
                        nome_completo = f"[{nome_modulo_curto}] {subtopico['nome']} -> {pratica['nome']}"
                        praticas_pendentes_flat.append({'nome_completo': nome_completo, 'obj': pratica})

        if not praticas_pendentes_flat:
            messagebox.showinfo("Sucesso", "Parabéns! Todas as práticas estão concluídas.", parent=self.master)
            return

        selection_window = tk.Toplevel(self.master)
        selection_window.title("✅ Concluir Prática - Seleção")
        selection_window.geometry("600x400")
        selection_window.grab_set() 

        tk.Label(selection_window, text="Selecione a prática concluída:", padx=10, pady=10).pack()

        list_frame = tk.Frame(selection_window)
        list_frame.pack(padx=10, pady=5, fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        pratica_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        pratica_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=pratica_listbox.yview)

        for item in praticas_pendentes_flat:
            pratica_listbox.insert(tk.END, item['nome_completo'])

        def confirmar_conclusao():
            selected_indices = pratica_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("Atenção", "Selecione uma prática para concluir.", parent=selection_window)
                return

            index = selected_indices[0]
            pratica_selecionada = praticas_pendentes_flat[index]
            pratica_obj_ref = pratica_selecionada['obj']
            
            confirmacao = messagebox.askyesno(
                "Confirmar Conclusão",
                f"Tem certeza que deseja marcar:\n\n{pratica_selecionada['nome_completo']}\n\ncomo CONCLUÍDA?",
                parent=selection_window
            )
            
            if confirmacao:
                pratica_obj_ref['concluido'] = True
                
                if salvar_dados_json(dados):
                    registrar_conclusao()
                    gerar_wallpaper()
                    messagebox.showinfo("Sucesso", "Prática concluída com sucesso! Cooldown de 4 horas iniciado.", parent=selection_window)
                    selection_window.destroy()
            
        tk.Button(selection_window, text="OK - Confirmar", command=confirmar_conclusao, 
                  bg="#00CC66", fg="white", font=("Arial", 12, "bold"), padx=20, pady=5).pack(pady=10)

    def configurar_layout_dialog(self):
        """Permite ao usuário ajustar as cores e a largura do contorno do texto."""
        dados = carregar_dados_json()
        if dados is None: return

        cor_p_str = ', '.join(map(str, dados.get('texto_cor_principal', [255, 255, 255])))
        cor_s_str = ', '.join(map(str, dados.get('contorno_cor', [0, 0, 0])))
        largura_s = dados.get('contorno_largura', 2)

        try:
            nova_cor_p = simpledialog.askstring("Configurar Cores", 
                                                f"Cor Principal do Texto (RGB: 0-255). Atual: ({cor_p_str})", 
                                                parent=self.master)
            if nova_cor_p is None: return

            nova_cor_s = simpledialog.askstring("Configurar Cores", 
                                                f"Cor do Contorno (Stroke) do Texto (RGB: 0-255). Atual: ({cor_s_str})", 
                                                parent=self.master)
            if nova_cor_s is None: return

            nova_largura_s = simpledialog.askinteger("Configurar Cores", 
                                                      f"Largura do Contorno (em pixels). Atual: {largura_s}", 
                                                      parent=self.master, minvalue=0, maxvalue=5)
            if nova_largura_s is None: return

            dados['texto_cor_principal'] = [int(x.strip()) for x in nova_cor_p.split(',')]
            dados['contorno_cor'] = [int(x.strip()) for x in nova_cor_s.split(',')]
            dados['contorno_largura'] = nova_largura_s
            
            if salvar_dados_json(dados):
                messagebox.showinfo("Sucesso", "Configurações de layout salvas e wallpaper atualizado.", parent=self.master)
                gerar_wallpaper()

        except ValueError:
            messagebox.showerror("Erro de Formato", "O formato RGB deve ser 'R, G, B' (ex: 255, 0, 0) com números entre 0 e 255.", parent=self.master)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.master)

    def selecionar_e_aplicar_fundo(self):
        """Abre o explorador de arquivos, copia a imagem e atualiza o JSON."""
        dados = carregar_dados_json()
        if dados is None: return

        caminho_imagem_selecionada = filedialog.askopenfilename(
            parent=self.master,
            title="Selecione a Imagem de Fundo do Wallpaper",
            filetypes=(("Arquivos de Imagem", "*.jpg *.jpeg *.png *.bmp"), ("Todos os arquivos", "*.*"))
        )

        if not caminho_imagem_selecionada: return

        try:
            img = Image.open(caminho_imagem_selecionada)
            largura, altura = img.size
            
            if largura < DIMENSAO_MINIMA_LARGURA or altura < DIMENSAO_MINIMA_ALTURA:
                aviso = (f"A imagem é muito pequena ({largura}x{altura}). "
                         f"O mínimo recomendado é {DIMENSAO_MINIMA_LARGURA}x{DIMENSAO_MINIMA_ALTURA}. "
                         f"Deseja usá-la mesmo assim (ela será esticada/distorcida)?")
                if not messagebox.askyesno("Aviso de Dimensão", aviso, parent=self.master):
                    return
            
            nome_arquivo = os.path.basename(caminho_imagem_selecionada)
            destino = os.path.join(os.path.dirname(JSON_PATH), nome_arquivo)
            
            if caminho_imagem_selecionada != destino:
                 shutil.copy2(caminho_imagem_selecionada, destino)
            
            dados['caminho_fundo'] = nome_arquivo
            
            if salvar_dados_json(dados):
                messagebox.showinfo("Sucesso", f"Imagem de fundo '{nome_arquivo}' configurada.", parent=self.master)
                gerar_wallpaper()
                
        except Exception as e:
            messagebox.showerror("Erro de Imagem", f"Não foi possível processar a imagem. Erro: {e}", parent=self.master)


# --- EXECUÇÃO ---

if __name__ == '__main__':
    root = tk.Tk()
    app = EvoMetricApp(root)
    root.mainloop()