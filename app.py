import json
import os
from flask import Flask, render_template, redirect, request

app = Flask(__name__)
ARQUIVO_DADOS = 'tarefas.json'

def carregar_tarefas():
    if not os.path.exists(ARQUIVO_DADOS): return []
    with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f: return json.load(f)

def salvar_tarefas(lista):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

tarefas = carregar_tarefas()

@app.route('/')
def index():
    # Pegamos todos os nomes de listas únicos que existem
    nomes_listas = sorted(list(set(t.get('lista_nome', 'Geral') for t in tarefas)))
    if 'Geral' not in nomes_listas: nomes_listas.insert(0, 'Geral')
    
    # Filtramos as tarefas por lista (se o usuário escolher uma)
    lista_atual = request.args.get('nome', 'Geral')
    tarefas_filtradas = [t for t in tarefas if t.get('lista_nome', 'Geral') == lista_atual]
    
    return render_template('index.html', lista=tarefas_filtradas, nomes_listas=nomes_listas, atual=lista_atual)

@app.route('/add', methods=['POST'])
def adicionar():
    texto = request.form.get('conteudo')
    nome_lista = request.form.get('lista_nome', 'Geral')
    if texto:
        novo_id = tarefas[-1]['id'] + 1 if tarefas else 1
        tarefas.append({'id': novo_id, 'texto': texto, 'feito': False, 'lista_nome': nome_lista})
        salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

@app.route('/concluir/<int:id_tarefa>')
def concluir(id_tarefa):
    nome_lista = 'Geral'
    for tarefa in tarefas:
        if tarefa['id'] == id_tarefa:
            tarefa['feito'] = True
            nome_lista = tarefa.get('lista_nome', 'Geral')
    salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

@app.route('/deletar/<int:id_tarefa>')
def deletar(id_tarefa):
    global tarefas
    nome_lista = next((t.get('lista_nome', 'Geral') for t in tarefas if t['id'] == id_tarefa), 'Geral')
    tarefas = [t for t in tarefas if t['id'] != id_tarefa]
    salvar_tarefas(tarefas)
    return redirect(f'/?nome={nome_lista}')

if __name__ == '__main__':
    app.run(debug=True)