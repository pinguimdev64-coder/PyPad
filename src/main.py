import sys, os

## NOTE: Parte para não dar erro

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import readchar, json, shutil
from readchar import key

os.system("clear")
def color_load():
    # Detecta se está rodando como binário (PyInstaller) ou script normal
    if getattr(sys, 'frozen', False):
        # Caminho da pasta onde o executável foi guardado/executado pelo usuário
        diretorio_atual = os.path.dirname(sys.executable)
    else:
        # Caminho tradicional para quando roda o script direto pelo VS Code
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))

    # Define o caminho final do config.json na pasta correta
    caminho_config = os.path.join(diretorio_atual, "config.json")
    
    conf_default = {
        "text_status": "#0F0F1A",
        "text_editor": "#ffffff",
        "global_color": "#ff5555",
    }
    
    if not os.path.exists(caminho_config):
        with open(caminho_config, 'w', encoding='utf-8') as f:
            json.dump(conf_default, f, indent=4, ensure_ascii=False)
        return conf_default
    else:
        with open(caminho_config, 'r', encoding='utf-8') as f:
            conf = json.load(f)
        return conf 

def cur(linha, coluna): #NOTE: Mudar local do cursor
    # O terminal começa em 1, então somamos 1 aos nossos índices base-0
    print(f"\033[{linha + 1};{coluna + 1}H", end="", flush=True)

def prefixo_visivel(num_linha):
    """Tamanho visível do prefixo (sem contar códigos ANSI invisíveis)"""
    return len(f"{num_linha + 1}| ")

def main():
    cor = color_load()
    print("\033[5 q")
    linhas = {i: [] for i in range(999)}
    linha = 0
    coluna = 0
    linha_livre = 0

    # ─ FUNÇÕES AUXILIARES ──
    def complete(tec):
        nonlocal linhas, linha, coluna
        linhas[linha].insert(coluna + 1, tec)

    def deslocar_CIMA():
        """Junta o conteúdo da linha atual no final da linha de cima.
        Se a linha de cima estiver vazia, puxa tudo que está abaixo uma posição para cima."""
        nonlocal linha, linhas, coluna, linha_livre
        
        if not len(linhas[linha + 1]) < 1: 

            # Linha de cima vazia: puxa tudo uma posição para cima
            for i in range(linha, linha_livre):
                linhas[i-1] = linhas[i]
                linhas[i]=[]
            linha -= 1                # Cursor sobe junto
            coluna = len(linhas[linha])
        else:
            # Linha de cima tem texto: junta no final dela
            mov = linhas[linha]
            linhas[linha] = []
            linhas[linha - 1].extend(mov)
            coluna = len(linhas[linha - 1])-len(mov)  # Cursor vai pro final da junção
            linha -= 1                       # Cursor sobe para a linha unida
            

    def deslocar_BAIXO(REP=1):
        """Corta o texto a partir do cursor e joga no início da linha de baixo.
        Empurra as linhas existentes uma posição para baixo antes."""
        nonlocal linha, linhas, coluna, linha_livre
        linha_livre+=1
        # 1. Pega o texto após o cursor
        desloc = linhas[linha][coluna:]
        # 2. Corta a linha atual
        linhas[linha] = linhas[linha][:coluna]
        # 3. Empurra as linhas de baixo uma posição para baixo (de trás pra frente!)
        for i in range(linha_livre, linha, -1):
            linhas[i] = linhas[i - 1]
        # 4. Coloca o texto cortado na nova linha de baixo
        linhas[linha + 1] = desloc
        
        #linha_livre += 1





        coluna = 0
        
    def cor_tp(hexa, e_fundo):
        """Converte hexadecimal → código ANSI. e_fundo=True → fundo, False → texto"""
        h = hexa.lstrip('#')
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        if e_fundo:
            return f"\033[48;2;{r};{g};{b}m"   # ✅ FUNDO: 48;2;R;G;B
        else:
            return f"\033[38;2;{r};{g};{b}m"   # ✅ TEXTO: 38;2;R;G;B    # ── LOOP PRINCIPAL ──
    while True:
        tam = shutil.get_terminal_size()
        area_texto = tam.lines - 1  # Reserva a última linha para a barra
        # Redesenha todas as linhas na tela (limitando à área visível)
        for i in range(min(linha_livre + 1, area_texto)):
            cur(i, 0)
            prefixo = f"{cor_tp(cor["global_color"], True)}{cor_tp(cor["text_status"], False)}{i+1}|\033[0m "
            print(f"{prefixo}{''.join(linhas[i])}\033[K", end="")

        # Limpa linhas restantes na área de texto
        for i in range(linha_livre + 1, area_texto):
            cur(i, 0)
            print("\033[K", end="")

        # ─ Barra de status na última linha ──
        cur(tam.lines - 1, 0)
        largura_blocos = max(0, tam.columns - (6+len(str(linha+1))+len(str(coluna))))
        print(f"{cor_tp(cor["global_color"], True)}{cor_tp(cor["text_status"], False)}PyPad{f"{cor_tp(cor["global_color"], False)}█" * largura_blocos}\033[0m{cor_tp(cor["global_color"], True)}{cor_tp(cor["text_status"], False)}{linha}:{coluna}\033[0m\033[K", end="")

        # Posiciona o cursor de digitação no lugar certo
        cur(linha, coluna + prefixo_visivel(linha))

        # ── Captura de teclas ──
        TECLA = readchar.readkey()

        if TECLA == key.ESC:
            os.system("clear")
            print("Editor fechado!")
            break

        elif TECLA not in [key.BACKSPACE, key.DELETE, key.LEFT, key.RIGHT,
                           key.UP, key.DOWN, key.ENTER, key.ESC, key.END, key.HOME,
                           key.TAB]:
            linhas[linha].insert(coluna, TECLA)
            
            # Auto-complete de aspas
            if TECLA in ["'", '"']:
                linhas[linha].insert(coluna + 1, TECLA)
            
            # Auto-complete de colchetes/parênteses
            if TECLA == "(": complete(")")
            if TECLA == "[": complete("]")
            if TECLA == "{": complete("}")
            
            coluna += 1

        elif TECLA == key.BACKSPACE: 
            if coluna > 0:
                # Lógica para apagar caracteres normais e pares de aspas/colchetes
                if coluna < len(linhas[linha]):
                    if (linhas[linha][coluna-1] in ["'", '"', "{", "[", "("] and 
                        linhas[linha][coluna] in ["'", '"', "}", "]", ")"]):

                        linhas[linha].pop(coluna)
                        linhas[linha].pop(coluna - 1)
                        coluna -= 1
                    else:
                        linhas[linha].pop(coluna-1)
                        coluna -= 1
                    
                else:
                    linhas[linha].pop(coluna - 1)
                    coluna -= 1
            else:
                # Cursor no início da linha (coluna 0)
                if linha > 0:
                    if len(linhas[linha]) == 0:
                        # 1. A linha atual está VAZIA: apaga ela e puxa as de baixo para cima
                        for i in range(linha, linha_livre):
                            linhas[i] = linhas[i + 1]
                        
                        linhas[linha_livre] = []  # Limpa a última linha que foi duplicada
                        linha_livre -= 1          # Avisa que temos uma linha a menos
                        linha -= 1
                        coluna = len(linhas[linha])                 # Cursor continua no início da linha
                        
                    else:
                        if not linha < 0:
                        # 2. A linha atual TEM TEXTO: junta com a linha de cima
                            mov = linhas[linha]       # Guarda o texto da linha atual
                            linhas[linha] = []        # Limpa a linha atual
                            linhas[linha - 1].extend(mov) # Cola o texto no final da linha de cima
                            for i in range(linha, linha_livre):
                                linhas[i] = linhas[i +1]
                            linhas[linha_livre] = []
                            linha -= 1
                            linha_livre -= 1
                            coluna = len(linhas[linha])-len(mov) # Cursor vai para o final da junção
                        else:
                            if coluna > 0:
                                linhas[linha].pop(coluna - 1)
                                coluna -= 1

                            
                        #linha -= 1                      # Cursor sobe para a linha unida        elif TECLA == key.LEFT:
        elif TECLA == key.LEFT:
            if coluna > 0:
                coluna -= 1

        elif TECLA == key.RIGHT:
            if coluna < len(linhas[linha]):
                coluna += 1

        elif TECLA == key.ENTER:
            KEYSNOR = [')', ']', '}']
            if coluna < len(linhas[linha]):
                if linhas[linha][coluna] in KEYSNOR and coluna > 0 and linhas[linha][coluna-1] in ['[', '{', '(']:
                    # Salva o texto que fica após o fechamento
                    recorte_final = linhas[linha][coluna:]
                    linhas[linha] = linhas[linha][:coluna]

                    # Abre 2 espaços no dicionário de linhas empurrando as existentes para baixo
                    linha_livre += 2
                    for i in range(linha_livre, linha + 2, -1):
                        linhas[i] = linhas[i - 2]

                    # Linha intermediária (com indentação de 4 espaços)
                    linhas[linha + 1] = [" "] * 4
                    # Linha inferior (com o caractere de fechamento)
                    linhas[linha + 2] = recorte_final

                    # Move o cursor para a linha do meio indentada
                    linha += 1
                    coluna = 4
                else:
                    deslocar_BAIXO()
                    linha += 1
                    coluna = 0
            else:
                linha_livre += 1
                for i in range(linha_livre, linha, -1):
                    linhas[i] = linhas[i - 1]
                linhas[linha + 1] = []
                
                linha += 1
                coluna = 0
        elif TECLA == key.UP:
            if linha > 0:
                linha -= 1
            coluna = 0

        elif TECLA == key.DOWN:
            if linha < linha_livre:
                linha += 1
            coluna = 0
        elif TECLA == key.END:
            coluna = len(linhas[linha])
        elif TECLA == key.HOME:
            coluna = 0
        elif TECLA == key.TAB:
            TAMTAB = 4
            for tab in range(TAMTAB):
                linhas[linha].insert(coluna+tab, " ")
            coluna += TAMTAB
        if TECLA in [key.CTRL_D]:
            cur(0, 0)
            print("\033[1 q   \nSAINDO")
            break 

# O clássico bug dos underlines faltando foi corrigido aqui embaixo!
if __name__ == '__main__':
    main()