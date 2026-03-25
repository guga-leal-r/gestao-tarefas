import os
from flask import Flask, render_template, redirect, request, session
from pymongo import MongoClient
import certifi

app = Flask(__name__)
app.secret_key = 'chave_mestra_universal_5352_final'

# --- CONEXÃO COM MONGODB (SUBSTITUÍDO PARA NÃO PERDER DADOS) ---
MONGO_URI = "mongodb+srv://gugaleal_db_user:CpUfLIxBJ4iCBfX3@cluster0.d64bn9u.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['organizador_db']
collection = db['tarefas']
# -----------------------------------------------------------

LISTA_PADRAO = 'Mercado'
PIN_ACESSO = '5352'

def carregar_tarefas():
    # Agora busca direto da nuvem
    return list(collection.find({}, {'_id': 0}))

@app.route('/')
def index():
    if not session.get('autenticado'): return redirect('/login')
    tarefas = carregar_tarefas()
    nomes_listas = sorted(list(set(t.get('lista_nome', LISTA_PADRAO) for t in tarefas)))
    if LISTA_PADRAO not in nomes_listas: nomes_listas.insert(0, LISTA_PADRAO)
    
    lista_atual = request.args.get('nome', LISTA_PADRAO)
    tarefas_filtradas = [t for t in tarefas if t.get('lista_nome', LISTA_PADRAO) == lista_atual]
    
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
    nome_lista = request.form.get('lista_nome', LISTA_PADRAO).strip() or LISTA_PADRAO
    id_edicao = request.form.get('id_edicao')
    qtd = request.form.get('quantidade', '')
    preco_ou_desc = request.form.get('preco', '').strip()

    if titulo:
        if id_edicao:
            # Atualiza item existente
            collection.update_one(
                {'id': int(id_edicao)}, 
                {'$set': {'texto': titulo, 'qtd': qtd, 'preco': preco_ou_desc, 'lista_nome': nome_lista}}
            )
        else:
            # Cria novo item com ID incremental
            ultimo = collection.find_one(sort=[("id", -1)])
            novo_id = (ultimo['id'] + 1) if ultimo else 1
            nova_tarefa = {
                'id': novo_id, 'texto': titulo, 'feito': False, 
                'lista_nome': nome_lista, 'qtd': qtd, 'preco': preco_ou_desc
            }
            collection.insert_one(nova_tarefa)
            
    return redirect(f'/?nome={nome_lista}')

@app.route('/alternar/<int:id_tarefa>')
def alternar(id_tarefa):
    t = collection.find_one({'id': id_tarefa})
    if t:
        collection.update_one({'id': id_tarefa}, {'$set': {'feito': not t.get('feito', False)}})
    return redirect(request.referrer or '/')

@app.route('/deletar/<int:id_tarefa>')
def deletar(id_tarefa):
    collection.delete_one({'id': id_tarefa})
    return redirect(request.referrer or '/')

@app.route('/resetar_lista')
def resetar_lista():
    nome_lista = request.args.get('nome', LISTA_PADRAO)
    collection.update_many({'lista_nome': nome_lista}, {'$set': {'feito': False}})
    return redirect(request.referrer or '/')

@app.route('/config_limite', methods=['POST'])
def config_limite():
    novo_limite = request.form.get('novo_limite', '100').replace(',', '.')
    session['limite_gastos'] = float(novo_limite)
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)