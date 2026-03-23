import json
import os
from flask import Flask, render_template, redirect, request

app = Flask(__name__)

# Nome do arquivo onde as tarefas serão salvas
ARQUIVO_DADOS = 'tarefas.json'

def carregar_tarefas():
    # Se o arquivo não existir, retorna uma lista vazia
    if not os.path.exists(ARQUIVO_DADOS):
        return []
    # Abre o arquivo e transforma o texto em lista do Python
    with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_tarefas(lista):
    # Transforma a lista do Python em texto e salva no arquivo
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

# Inicializa a lista carregando do arquivo
tarefas = carregar_tarefas()

@app.route('/')
def index():
    return render_template('index.html', lista=tarefas)

@app.route('/add', methods=['POST'])
def adicionar():
    texto = request.form.get('conteudo')
    if texto:
        # Pega o último ID para gerar o próximo
        novo_id = tarefas[-1]['id'] + 1 if tarefas else 1
        tarefas.append({'id': novo_id, 'texto': texto, 'feito': False})
        salvar_tarefas(tarefas) # <-- SALVA NO ARQUIVO
    return redirect('/')

@app.route('/concluir/<int:id_tarefa>')
def concluir(id_tarefa):
    for tarefa in tarefas:
        if tarefa['id'] == id_tarefa:
            tarefa['feito'] = True
            break
    salvar_tarefas(tarefas) # <-- SALVA NO ARQUIVO
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)