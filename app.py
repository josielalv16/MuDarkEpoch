from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Inicialização do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mudarkepoch.db'  # Usando SQLite para simplicidade
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização das extensões
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# Definição dos modelos
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nome = db.Column(db.String(128), nullable=False)
    ultimo_acesso = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Jogador(db.Model):
    __tablename__ = 'jogador'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    pontuacoes = db.relationship('Pontuacao', backref='jogador', lazy=True)
    historicos = db.relationship('Historico', backref='jogador', lazy=True)

class Item(db.Model):
    __tablename__ = 'item'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), nullable=False)
    entregas_realizadas = db.Column(db.Integer, default=0)
    limite_reset = db.Column(db.Integer, default=10)
    descricao = db.Column(db.Text, nullable=True)
    
    pontuacoes = db.relationship('Pontuacao', backref='item', lazy=True)
    historicos = db.relationship('Historico', backref='item', lazy=True)

class Pontuacao(db.Model):
    __tablename__ = 'pontuacao'
    
    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    reputacao_semanal = db.Column(db.Integer, default=0)
    participacoes_boss = db.Column(db.Integer, default=0)
    participacoes_castelo = db.Column(db.Integer, default=0)
    ja_recebeu = db.Column(db.Boolean, default=False)
    pontuacao_total = db.Column(db.Integer, default=0)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calcular_pontuacao(self):
        pontuacao = (self.reputacao_semanal * 2) + (self.participacoes_boss * 3) + (self.participacoes_castelo * 2.5)
        if not self.ja_recebeu:
            pontuacao += 50
        self.pontuacao_total = int(pontuacao)
        return self.pontuacao_total

class Historico(db.Model):
    __tablename__ = 'historico'
    
    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    data_entrega = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            admin.ultimo_acesso = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('login'))

# Rotas administrativas
@app.route('/dashboard')
@login_required
def dashboard():
    total_jogadores = Jogador.query.filter_by(ativo=True).count()
    total_itens = Item.query.count()
    ultimas_entregas = Historico.query.order_by(Historico.data_entrega.desc()).limit(5).all()
    
    # Contagem de entregas por item
    itens = Item.query.all()
    estatisticas_itens = []
    for item in itens:
        estatisticas_itens.append({
            'nome': item.nome,
            'entregas': item.entregas_realizadas,
            'limite': item.limite_reset
        })
    
    return render_template('dashboard.html', 
                          total_jogadores=total_jogadores,
                          total_itens=total_itens,
                          ultimas_entregas=ultimas_entregas,
                          estatisticas_itens=estatisticas_itens)

# Rotas para jogadores
@app.route('/jogadores')
@login_required
def listar_jogadores():
    jogadores = Jogador.query.all()
    return render_template('jogadores.html', jogadores=jogadores)

@app.route('/jogadores/novo', methods=['GET', 'POST'])
@login_required
def novo_jogador():
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('novo_jogador'))
        
        if Jogador.query.filter_by(nome=nome).first():
            flash('Jogador com este nome já existe', 'danger')
            return redirect(url_for('novo_jogador'))
        
        jogador = Jogador(nome=nome)
        db.session.add(jogador)
        
        # Criar pontuações iniciais para todos os itens
        itens = Item.query.all()
        for item in itens:
            pontuacao = Pontuacao(jogador_id=jogador.id, item_id=item.id)
            db.session.add(pontuacao)
        
        db.session.commit()
        flash('Jogador adicionado com sucesso', 'success')
        return redirect(url_for('listar_jogadores'))
    
    return render_template('novo_jogador.html')

@app.route('/jogadores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_jogador(id):
    jogador = Jogador.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        ativo = 'ativo' in request.form
        
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('editar_jogador', id=id))
        
        jogador_existente = Jogador.query.filter_by(nome=nome).first()
        if jogador_existente and jogador_existente.id != id:
            flash('Jogador com este nome já existe', 'danger')
            return redirect(url_for('editar_jogador', id=id))
        
        jogador.nome = nome
        jogador.ativo = ativo
        db.session.commit()
        
        flash('Jogador atualizado com sucesso', 'success')
        return redirect(url_for('listar_jogadores'))
    
    return render_template('editar_jogador.html', jogador=jogador)

# Rotas para pontuações
@app.route('/pontuacoes')
@login_required
def listar_pontuacoes():
    item_id = request.args.get('item_id', 1, type=int)
    item = Item.query.get_or_404(item_id)
    itens = Item.query.all()
    
    # Buscar jogadores ativos com suas pontuações para o item selecionado
    jogadores_pontuacoes = db.session.query(
        Jogador, Pontuacao
    ).join(
        Pontuacao, Jogador.id == Pontuacao.jogador_id
    ).filter(
        Jogador.ativo == True,
        Pontuacao.item_id == item_id
    ).order_by(
        Pontuacao.pontuacao_total.desc()
    ).all()
    
    return render_template('pontuacoes.html', 
                          jogadores_pontuacoes=jogadores_pontuacoes,
                          item_atual=item,
                          itens=itens)

@app.route('/pontuacoes/atualizar', methods=['GET', 'POST'])
@login_required
def atualizar_pontuacoes():
    if request.method == 'POST':
        item_id = request.form.get('item_id', type=int)
        tipo = request.form.get('tipo')  # reputacao, boss, castelo
        
        for key, value in request.form.items():
            if key.startswith('jogador_'):
                try:
                    jogador_id = int(key.split('_')[1])
                    valor = int(value) if value else 0
                    
                    pontuacao = Pontuacao.query.filter_by(
                        jogador_id=jogador_id, 
                        item_id=item_id
                    ).first()
                    
                    if pontuacao:
                        if tipo == 'reputacao':
                            pontuacao.reputacao_semanal = valor
                        elif tipo == 'boss':
                            pontuacao.participacoes_boss = valor
                        elif tipo == 'castelo':
                            pontuacao.participacoes_castelo = valor
                        
                        pontuacao.calcular_pontuacao()
                except ValueError:
                    continue
        
        db.session.commit()
        flash('Pontuações atualizadas com sucesso', 'success')
        return redirect(url_for('listar_pontuacoes', item_id=item_id))
    
    item_id = request.args.get('item_id', 1, type=int)
    tipo = request.args.get('tipo', 'reputacao')
    item = Item.query.get_or_404(item_id)
    itens = Item.query.all()
    
    jogadores = Jogador.query.filter_by(ativo=True).all()
    pontuacoes = {}
    
    for jogador in jogadores:
        pontuacao = Pontuacao.query.filter_by(
            jogador_id=jogador.id, 
            item_id=item_id
        ).first()
        
        if pontuacao:
            if tipo == 'reputacao':
                pontuacoes[jogador.id] = pontuacao.reputacao_semanal
            elif tipo == 'boss':
                pontuacoes[jogador.id] = pontuacao.participacoes_boss
            elif tipo == 'castelo':
                pontuacoes[jogador.id] = pontuacao.participacoes_castelo
    
    return render_template('atualizar_pontuacoes.html',
                          jogadores=jogadores,
                          pontuacoes=pontuacoes,
                          item=item,
                          itens=itens,
                          tipo=tipo)

# Rotas para entregas
@app.route('/entregas/confirmar/<int:jogador_id>/<int:item_id>', methods=['POST'])
@login_required
def confirmar_entrega(jogador_id, item_id):
    jogador = Jogador.query.get_or_404(jogador_id)
    item = Item.query.get_or_404(item_id)
    
    # Registrar entrega no histórico
    historico = Historico(
        jogador_id=jogador_id,
        item_id=item_id,
        admin_id=current_user.id
    )
    db.session.add(historico)
    
    # Atualizar pontuação do jogador
    pontuacao = Pontuacao.query.filter_by(
        jogador_id=jogador_id,
        item_id=item_id
    ).first()
    
    if pontuacao:
        pontuacao.ja_recebeu = True
        pontuacao.reputacao_semanal = 0
        pontuacao.participacoes_boss = 0
        pontuacao.participacoes_castelo = 0
        pontuacao.calcular_pontuacao()
    
    # Incrementar contador de entregas do item
    item.entregas_realizadas += 1
    
    db.session.commit()
    
    # Verificar se atingiu limite para reset
    if item.entregas_realizadas >= item.limite_reset:
        flash(f'Atenção: O item {item.nome} atingiu o limite de entregas ({item.limite_reset}). Considere resetar o ranking.', 'warning')
    
    flash(f'Entrega do item {item.nome} para {jogador.nome} confirmada com sucesso!', 'success')
    return redirect(url_for('listar_pontuacoes', item_id=item_id))

@app.route('/entregas/historico')
@login_required
def historico_entregas():
    item_id = request.args.get('item_id', type=int)
    jogador_id = request.args.get('jogador_id', type=int)
    
    query = db.session.query(
        Historico, Jogador, Item
    ).join(
        Jogador, Historico.jogador_id == Jogador.id
    ).join(
        Item, Historico.item_id == Item.id
    )
    
    if item_id:
        query = query.filter(Historico.item_id == item_id)
    
    if jogador_id:
        query = query.filter(Historico.jogador_id == jogador_id)
    
    historicos = query.order_by(Historico.data_entrega.desc()).all()
    
    itens = Item.query.all()
    jogadores = Jogador.query.all()
    
    return render_template('historico.html',
                          historicos=historicos,
                          itens=itens,
                          jogadores=jogadores,
                          item_id_filtro=item_id,
                          jogador_id_filtro=jogador_id)

@app.route('/entregas/reset/<int:item_id>', methods=['POST'])
@login_required
def reset_ranking(item_id):
    item = Item.query.get_or_404(item_id)
    
    # Resetar status "já recebeu" para todos os jogadores
    pontuacoes = Pontuacao.query.filter_by(item_id=item_id).all()
    for pontuacao in pontuacoes:
        pontuacao.ja_recebeu = False
        pontuacao.calcular_pontuacao()
    
    # Resetar contador de entregas do item
    item.entregas_realizadas = 0
    
    db.session.commit()
    
    flash(f'Ranking do item {item.nome} foi resetado com sucesso!', 'success')
    return redirect(url_for('listar_pontuacoes', item_id=item_id))

# Rotas para itens
@app.route('/itens')
@login_required
def listar_itens():
    itens = Item.query.all()
    return render_template('itens.html', itens=itens)

@app.route('/itens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        limite_reset = request.form.get('limite_reset', type=int)
        descricao = request.form.get('descricao')
        
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('editar_item', id=id))
        
        item_existente = Item.query.filter_by(nome=nome).first()
        if item_existente and item_existente.id != id:
            flash('Item com este nome já existe', 'danger')
            return redirect(url_for('editar_item', id=id))
        
        item.nome = nome
        item.limite_reset = limite_reset if limite_reset else 10
        item.descricao = descricao
        db.session.commit()
        
        flash('Item atualizado com sucesso', 'success')
        return redirect(url_for('listar_itens'))
    
    return render_template('editar_item.html', item=item)

# Rota principal para visualização pública
@app.route('/')
def index():
    return render_template('index.html')

# Rota para visualização de ranking público
@app.route('/ranking/<int:item_id>')
def ranking(item_id):
    item = Item.query.get_or_404(item_id)
    itens = Item.query.all()
    
    # Buscar jogadores ativos com suas pontuações para o item selecionado
    jogadores_pontuacoes = db.session.query(
        Jogador, Pontuacao
    ).join(
        Pontuacao, Jogador.id == Pontuacao.jogador_id
    ).filter(
        Jogador.ativo == True,
        Pontuacao.item_id == item_id
    ).order_by(
        Pontuacao.pontuacao_total.desc()
    ).all()
    
    return render_template('ranking.html', 
                          jogadores_pontuacoes=jogadores_pontuacoes,
                          item_atual=item,
                          itens=itens)

# Inicialização do banco de dados e dados iniciais
with app.app_context():
    db.create_all()
    
    # Verificar se existe pelo menos um admin
    if not Admin.query.first():
        admin = Admin(username='admin', nome='Administrador')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Verificar se existem itens padrão
    if not Item.query.first():
        itens_padrao = [
            {'nome': 'COC', 'limite_reset': 10, 'descricao': 'Colar of Covenant'},
            {'nome': 'Pena', 'limite_reset': 10, 'descricao': 'Pena da Fênix'},
            {'nome': 'Condor', 'limite_reset': 10, 'descricao': 'Condor Flame'},
            {'nome': 'Baú', 'limite_reset': 8, 'descricao': 'Baú do Tesouro'}
        ]
        
        for item_data in itens_padrao:
            item = Item(**item_data)
            db.session.add(item)
        
        db.session.commit()
        
    # Adicionar alguns jogadores de exemplo se não existirem
    if not Jogador.query.first():
        jogadores_exemplo = [
            {'nome': 'Player1'},
            {'nome': 'Player2'},
            {'nome': 'Player3'},
            {'nome': 'Player4'},
            {'nome': 'Player5'}
        ]
        
        for jogador_data in jogadores_exemplo:
            jogador = Jogador(**jogador_data)
            db.session.add(jogador)
        
        db.session.commit()
        
        # Criar pontuações iniciais para todos os jogadores e itens
        jogadores = Jogador.query.all()
        itens = Item.query.all()
        
        for jogador in jogadores:
            for item in itens:
                pontuacao = Pontuacao(
                    jogador_id=jogador.id,
                    item_id=item.id,
                    reputacao_semanal=5 + (jogador.id % 5),
                    participacoes_boss=3 + (jogador.id % 4),
                    participacoes_castelo=2 + (jogador.id % 3),
                    ja_recebeu=False
                )
                pontuacao.calcular_pontuacao()
                db.session.add(pontuacao)
        
        db.session.commit()

# Iniciar o servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
