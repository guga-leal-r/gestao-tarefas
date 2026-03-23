import json
import os
from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)
app.secret_key = 'chave_universal_5352_final'

ARQUIVO_DADOS = 'tarefas.json'
LISTA_PADRAO = 'Mercado'
PIN_ACESSO = '5352'

def carregar_tarefas():
    try:
        if os.path.exists(ARQUIVO_DADOS):
            with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return []

def salvar_tarefas(lista):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

tarefas = carregar_tarefas()

@app.route('/')
def index():
    if not session.get('autenticado'): return redirect('/login')
    global tarefas
    tarefas = carregar_tarefas()
    nomes_listas = sorted(list(set(t.get('lista_nome', LISTA_PADRAO) for t in tarefas)))
    if LISTA_PADRAO not in nomes_listas: nomes_listas.insert(0, LISTA_PADRAO)
    
    lista_atual = request.args.get('nome', LISTA_PADRAO)
    tarefas_filtradas = [t for t in tarefas if t.get('lista_nome', LISTA_PADRAO) == lista_atual]
    
    # SOMA APENAS SE FOR A LISTA MERCADO
    total_valor = 0
    if lista_atual == LISTA_PADRAO:
        for t in tarefas_filtradas:
            try:
                preco = float(str(t.get('preco', 0)).replace(',', '.'))
                qtd_raw = str(t.get('qtd', '1'))
                qtd_num = int(''.join(filter(str.isdigit, qtd_raw))) if any(c.isdigit() for c in qtd_raw) else 1
                total_valor += (preco * qtd_num)
            except: continue
            
    limite_atual = session.get('limite_gastos', 100.0)
    return render_template('index.html', lista=tarefas_filtradas, nomes_listas=nomes_listas, atual=lista_atual, total=total_valor, limite=limite_atual)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN_ACESSO:
        session['autenticado'] = True
        return redirect('/')
    return render_template('login.html')

@app.route('/add', methods=['POST'])
def adicionar():
    titulo = request.form.get('conteudo')
    nome_lista = request.form.get('lista_nome', LISTA_PADRAO).strip()
    id_edicao = request.form.get('id_edicao')
    qtd = request.form.get('quantidade', '')
    
    # Pega o valor do campo de preço ou da descrição (dependendo da lista)
    preco_ou_desc = request.form.get('preco', '').strip()

    if titulo:
        if id_edicao: # EDIÇÃO
            for t in tarefas:
                if str(t['id']) == id_edicao:
                    t['texto'] = titulo
                    t['qtd'] = qtd
                    t['preco'] = preco_ou_desc
                    t['lista_nome'] = nome_lista if nome_lista else LISTA_PADRAO
        else: # NOVO ITEM
            novo_id = tarefas[-1]['id'] + 1 if tarefas else 1
            tarefas.append({
                'id': novo_id, 'texto': titulo, 'feito': False, 
                'lista_nome': nome_lista if nome_lista else LISTA_PADRAO,
                'qtd': qtd, 'preco': preco_ou_desc
            })
        salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista if nome_lista else LISTA_PADRAO}')

@app.route('/alternar/<int:id_tarefa>')
def alternar(id_tarefa):
    for t in tarefas:
        if t['id'] == id_tarefa: t['feito'] = not t.get('feito', False)
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

@app.route('/deletar/<int:id_tarefa>')
def deletar(id_tarefa):
    global tarefas
    tarefas = [t for t in tarefas if t['id'] != id_tarefa]
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

@app.route('/config_limite', methods=['POST'])
def config_limite():
    novo_limite = request.form.get('novo_limite', '100').replace(',', '.')
    session['limite_gastos'] = float(novo_limite)
    return redirect(request.referrer or '/')

@app.route('/resetar_lista')
def resetar_lista():
    nome_lista = request.args.get('nome', LISTA_PADRAO)
    for t in tarefas:
        if t.get('lista_nome') == nome_lista: t['feito'] = False
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)