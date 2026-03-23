import json
import os
from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)
# Chave de segurança para manter você logado
app.secret_key = 'chave_segura_gestao_5352'

ARQUIVO_DADOS = 'tarefas.json'
LISTA_PADRAO = 'Mercado'
PIN_ACESSO = '5352'  # Sua nova senha

def carregar_tarefas():
    if not os.path.exists(ARQUIVO_DADOS):
        return []
    with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_tarefas(lista):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

tarefas = carregar_tarefas()

@app.route('/')
def index():
    if not session.get('autenticado'):
        return redirect('/login')

    nomes_listas = sorted(list(set(t.get('lista_nome', LISTA_PADRAO) for t in tarefas)))
    if LISTA_PADRAO not in nomes_listas:
        nomes_listas.insert(0, LISTA_PADRAO)

    lista_atual = request.args.get('nome', LISTA_PADRAO)
    tarefas_filtradas = [t for t in tarefas if t.get('lista_nome', LISTA_PADRAO) == lista_atual]

    try:
        total_valor = sum(float(t.get('preco', 0) or 0) * int(t.get('qtd', 1) or 1) for t in tarefas_filtradas)
    except Exception:
        total_valor = 0.0

    limite_atual = session.get('limite_gastos')
    if limite_atual is None:
        limite_atual = 100.0
        session['limite_gastos'] = limite_atual

    return render_template('index.html', lista=tarefas_filtradas, nomes_listas=nomes_listas, atual=lista_atual, total=total_valor, limite=limite_atual)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_ACESSO:
            session['autenticado'] = True
            return redirect('/')
    return render_template('login.html')

@app.route('/alternar/<int:id_tarefa>')
def alternar(id_tarefa):
    for t in tarefas:
        if t['id'] == id_tarefa:
            t['feito'] = not t.get('feito', False)
            break
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

@app.route('/resetar_lista')
def resetar_lista():
    nome_lista = request.args.get('nome', LISTA_PADRAO)
    for t in tarefas:
        if t.get('lista_nome', LISTA_PADRAO) == nome_lista:
            t['feito'] = False
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

@app.route('/config_limite', methods=['POST'])
def config_limite():
    novo_limite = request.form.get('novo_limite', '100').replace(',', '.')
    try:
        session['limite_gastos'] = float(novo_limite)
    except ValueError:
        session['limite_gastos'] = 100.0
    return redirect(request.referrer or '/')

@app.route('/add', methods=['POST'])
def adicionar():
    texto = request.form.get('conteudo')
    nome_lista = request.form.get('lista_nome', LISTA_PADRAO)
    quantidade = request.form.get('quantidade', 1)
    preco_raw = request.form.get('preco', '0').replace(',', '.')

    if texto:
        try:
            novo_id = tarefas[-1]['id'] + 1 if tarefas else 1
        except (KeyError, IndexError):
            novo_id = 1
        try:
            qtd_int = int(quantidade)
        except ValueError:
            qtd_int = 1
        try:
            preco_float = float(preco_raw or 0)
        except ValueError:
            preco_float = 0.0
        tarefas.append({
            'id': novo_id,
            'texto': texto,
            'feito': False,
            'lista_nome': nome_lista,
            'qtd': qtd_int,
            'preco': preco_float
        })
        salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

@app.route('/deletar/<int:id_tarefa>')
def deletar(id_tarefa):
    global tarefas
    tarefas = [t for t in tarefas if t['id'] != id_tarefa]
    salvar_tarefas(tarefas)
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)