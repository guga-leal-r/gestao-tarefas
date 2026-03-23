import json
import os
from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)
# Chave necessária para manter o usuário "logado" na sessão
app.secret_key = 'chave_secreta_para_biometria_123'

ARQUIVO_DADOS = 'tarefas.json'
LISTA_PADRAO = 'Mercado'
PIN_ACESSO = '1234' # Sua senha de acesso (simulando biometria)

def carregar_tarefas():
    if not os.path.exists(ARQUIVO_DADOS): return []
    with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f: return json.load(f)

def salvar_tarefas(lista):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

tarefas = carregar_tarefas()

@app.route('/')
def index():
    # VERIFICAÇÃO DE SEGURANÇA: Se não estiver autenticado, vai para o login
    if not session.get('autenticado'):
        return redirect('/login')

    # Pegamos todos os nomes de listas únicos
    nomes_listas = sorted(list(set(t.get('lista_nome', LISTA_PADRAO) for t in tarefas)))
    if LISTA_PADRAO not in nomes_listas: nomes_listas.insert(0, LISTA_PADRAO)
    
    # Filtramos as tarefas por lista
    lista_atual = request.args.get('nome', LISTA_PADRAO)
    tarefas_filtradas = [t for t in tarefas if t.get('lista_nome', LISTA_PADRAO) == lista_atual]
    
    # Lógica de soma: Quantidade * Preço
    total_valor = 0
    for t in tarefas_filtradas:
        try:
            qtd = int(t.get('qtd', 1))
            preco = float(t.get('preco', 0))
            total_valor += (qtd * preco)
        except:
            continue
    
    return render_template('index.html', 
                           lista=tarefas_filtradas, 
                           nomes_listas=nomes_listas, 
                           atual=lista_atual, 
                           total=total_valor)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = False
    if request.method == 'POST':
        if request.form.get('pin') == PIN_ACESSO:
            session['autenticado'] = True
            return redirect('/')
        else:
            erro = True
    
    # Tela de bloqueio simples e direta
    return f'''
    <body style="font-family:sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <form method="POST" style="background:white; padding:30px; border-radius:20px; box-shadow:0 10px 25px rgba(0,0,0,0.1); text-align:center; width:300px;">
            <div style="font-size:50px; margin-bottom:10px;">🔒</div>
            <h3>App Bloqueado</h3>
            <p style="color:#666; font-size:14px;">Digite o PIN para acessar</p>
            <input type="password" name="pin" placeholder="PIN" maxlength="4" autofocus
                   style="width:100%; padding:15px; font-size:24px; text-align:center; border:1px solid #ddd; border-radius:10px; margin-bottom:15px;">
            { '<p style="color:red; font-size:12px;">PIN Incorreto!</p>' if erro else '' }
            <button type="submit" style="width:100%; padding:15px; background:#1877f2; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">ACESSAR</button>
        </form>
    </body>
    '''

@app.route('/sair')
def sair():
    session.pop('autenticado', None)
    return redirect('/login')

@app.route('/add', methods=['POST'])
def adicionar():
    texto = request.form.get('conteudo')
    nome_lista = request.form.get('lista_nome', LISTA_PADRAO)
    
    # Captura novos campos de Qtd e Preço
    quantidade = request.form.get('quantidade', 1)
    preco_raw = request.form.get('preco', '0').replace(',', '.') # Aceita vírgula ou ponto
    
    if texto:
        novo_id = tarefas[-1]['id'] + 1 if tarefas else 1
        tarefas.append({
            'id': novo_id, 
            'texto': texto, 
            'feito': False, 
            'lista_nome': nome_lista,
            'qtd': int(quantidade) if quantidade else 1,
            'preco': float(preco_raw) if preco_raw else 0.0
        })
        salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

@app.route('/concluir/<int:id_tarefa>')
def concluir(id_tarefa):
    nome_lista = LISTA_PADRAO
    for tarefa in tarefas:
        if tarefa['id'] == id_tarefa:
            tarefa['feito'] = True
            nome_lista = tarefa.get('lista_nome', LISTA_PADRAO)
    salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

@app.route('/deletar/<int:id_tarefa>')
def deletar(id_tarefa):
    global tarefas
    nome_lista = next((t.get('lista_nome', LISTA_PADRAO) for t in tarefas if t['id'] == id_tarefa), LISTA_PADRAO)
    tarefas = [t for t in tarefas if t['id'] != id_tarefa]
    salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

if __name__ == '__main__':
    app.run(debug=True)