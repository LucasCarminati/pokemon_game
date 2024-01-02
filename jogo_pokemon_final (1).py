import pygame
from pygame.locals import *
import time
import math
import random
import requests
import io
from urllib.request import urlopen

# Inicializa a biblioteca pygame
pygame.init()

# Cria a janela do jogo
largura_jogo = 500
altura_jogo = 500
tamanho = (largura_jogo, altura_jogo)
jogo = pygame.display.set_mode(tamanho)
pygame.display.set_caption('Batalha Pokémon')

# URL base da API
url_base = 'https://pokeapi.co/api/v2'


class Movimento():

    def __init__(self, url):

        # Chama o endpoint da API de movimentos
        requisicao = requests.get(url)
        self.json = requisicao.json()

        self.nome = self.json['name']
        self.poder = self.json['power']
        self.tipo = self.json['type']['name']


# Define cores
preto = (0, 0, 0)
dourado = (218, 165, 32)
cinza = (200, 200, 200)
verde = (0, 200, 0)
vermelho = (200, 0, 0)
branco = (255, 255, 255)


class Pokemon(pygame.sprite.Sprite):

    def __init__(self, nome, nivel, x, y):

        pygame.sprite.Sprite.__init__(self)

        # Chama o endpoint da API de Pokémon
        requisicao = requests.get(f'{url_base}/pokemon/{nome.lower()}')
        self.json = requisicao.json()

        # Define o nome e o nível do Pokémon
        self.nome = nome
        self.nivel = nivel

        # Define a posição do sprite na tela
        self.x = x
        self.y = y

        # Número de poções restantes
        self.num_pocoes = 3

        # Obtém as estatísticas do Pokémon da API
        estatisticas = self.json['stats']
        for estatistica in estatisticas:
            if estatistica['stat']['name'] == 'hp':
                self.hp_atual = estatistica['base_stat'] + self.nivel
                self.hp_maximo = estatistica['base_stat'] + self.nivel
            elif estatistica['stat']['name'] == 'attack':
                self.ataque = estatistica['base_stat']
            elif estatistica['stat']['name'] == 'defense':
                self.defesa = estatistica['base_stat']
            elif estatistica['stat']['name'] == 'speed':
                self.velocidade = estatistica['base_stat']

        # Define os tipos do Pokémon
        self.tipos = []
        for i in range(len(self.json['types'])):
            tipo = self.json['types'][i]
            self.tipos.append(tipo['type']['name'])

        # Define a largura do sprite
        self.tamanho = 150

        # Define o sprite para a frente
        self.definir_sprite('front_default')

    def realizar_ataque(self, outro, movimento):

        exibir_mensagem(f'{self.nome} usou {movimento.nome}')

        # Pausa por 2 segundos
        time.sleep(2)

        # Calcula o dano
        dano = (2 * self.nivel + 10) / 250 * \
            self.ataque / outro.defesa * movimento.poder

        # Bônus de ataque do mesmo tipo (STAB)
        if movimento.tipo in self.tipos:
            dano *= 1.5

        # Golpe crítico (chance de 6,25%)
        num_aleatorio = random.randint(1, 10000)
        if num_aleatorio <= 625:
            dano *= 1.5

        # Arredonda para baixo o dano
        dano = math.floor(dano)

        outro.receber_dano(dano)

    def receber_dano(self, dano):

        self.hp_atual -= dano

        # O hp não deve ser menor que 0
        if self.hp_atual < 0:
            self.hp_atual = 0

    def usar_pocao(self):

        # Verifica se há poções restantes
        if self.num_pocoes > 0:

            # Adiciona 30 de hp (mas não ultrapassa o hp máximo)
            self.hp_atual += 30
            if self.hp_atual > self.hp_maximo:
                self.hp_atual = self.hp_maximo

            # Diminui o número de poções restantes
            self.num_pocoes -= 1

    def definir_sprite(self, lado):

        # Define o sprite do Pokémon
        imagem = self.json['sprites'][lado]
        fluxo_imagem = urlopen(imagem).read()
        arquivo_imagem = io.BytesIO(fluxo_imagem)
        self.imagem = pygame.image.load(arquivo_imagem).convert_alpha()

        # Redimensiona a imagem
        escala = self.tamanho / self.imagem.get_width()
        nova_largura = self.imagem.get_width() * escala
        nova_altura = self.imagem.get_height() * escala
        self.imagem = pygame.transform.scale(
            self.imagem, (nova_largura, nova_altura))

    def definir_movimentos(self):

        self.movimentos = []

        # Percorre todos os movimentos da API
        for i in range(len(self.json['moves'])):

            # Obtém o movimento de diferentes versões do jogo
            versoes = self.json['moves'][i]['version_group_details']
            for j in range(len(versoes)):

                versao = versoes[j]

                # Apenas obtém movimentos da versão vermelho-azul
                if versao['version_group']['name'] != 'red-blue':
                    continue

                # Apenas obtém movimentos aprendidos ao subir de nível (exclui movimentos de TM)
                metodo_aprendizado = versao['move_learn_method']['name']
                if metodo_aprendizado != 'level-up':
                    continue

                # Adiciona o movimento se o nível do Pokémon for alto o suficiente
                nivel_aprendizado = versao['level_learned_at']
                if self.nivel >= nivel_aprendizado:
                    movimento = Movimento(self.json['moves'][i]['move']['url'])

                    # Inclui apenas movimentos de ataque
                    if movimento.poder is not None:
                        self.movimentos.append(movimento)

        # Seleciona até 4 movimentos aleatórios
        if len(self.movimentos) > 4:
            self.movimentos = random.sample(self.movimentos, 4)

    def desenhar(self, alpha=255):

        sprite = self.imagem.copy()
        transparencia = (255, 255, 255, alpha)
        sprite.fill(transparencia, None, pygame.BLEND_RGBA_MULT)
        jogo.blit(sprite, (self.x, self.y))

    def desenhar_hp(self):

        # Exibe a barra de saúde
        escala_barra = 200 // self.hp_maximo
        for i in range(self.hp_maximo):
            barra = (self.hp_x + escala_barra * i, self.hp_y, escala_barra, 20)
            pygame.draw.rect(jogo, vermelho, barra)

        for i in range(self.hp_atual):
            barra = (self.hp_x + escala_barra * i, self.hp_y, escala_barra, 20)
            pygame.draw.rect(jogo, verde, barra)

        # Exibe o texto "HP"
        fonte = pygame.font.Font(pygame.font.get_default_font(), 16)
        texto = fonte.render(
            f'HP: {self.hp_atual} / {self.hp_maximo}', True, preto)
        rect_texto = texto.get_rect()
        rect_texto.x = self.hp_x
        rect_texto.y = self.hp_y + 30
        jogo.blit(texto, rect_texto)

    def get_rect(self):

        return Rect(self.x, self.y, self.imagem.get_width(), self.imagem.get_height())


# Cria os Pokémon iniciais
nivel = 30
bulbasaur = Pokemon('Bulbasaur', nivel, 25, 100)
charmander = Pokemon('Charmander', nivel, 175, 100)
squirtle = Pokemon('Squirtle', nivel, 325, 100)
pikachu = Pokemon('Pikachu', nivel, 25, 300)
eevee = Pokemon('Eevee', nivel, 175, 300)
psyduck = Pokemon('Psyduck', nivel, 325, 300)
# gengar = Pokemon('Gengar', nivel, 325, 300)
pokemons = [bulbasaur, charmander, squirtle,
            pikachu, eevee, psyduck]  # Lista atualizada

# Pokémon selecionados pelo jogador e pelo rival
pokemon_jogador = None
pokemon_rival = None


def exibir_mensagem(mensagem):

    # Desenha uma caixa branca com borda preta
    pygame.draw.rect(jogo, branco, (10, 350, 480, 140))
    pygame.draw.rect(jogo, preto, (10, 350, 480, 140), 3)

    # Exibe a mensagem
    fonte = pygame.font.Font(pygame.font.get_default_font(), 20)
    texto = fonte.render(mensagem, True, preto)
    rect_texto = texto.get_rect()
    rect_texto.x = 30
    rect_texto.y = 410
    jogo.blit(texto, rect_texto)

    pygame.display.update()


def criar_botao(largura, altura, esquerda, topo, texto_cx, texto_cy, rotulo):

    # Posição do cursor do mouse
    cursor_mouse = pygame.mouse.get_pos()

    botao = Rect(esquerda, topo, largura, altura)

    # Destaca o botão se o mouse estiver sobre ele
    if botao.collidepoint(cursor_mouse):
        pygame.draw.rect(jogo, dourado, botao)
    else:
        pygame.draw.rect(jogo, branco, botao)

    # Adiciona o rótulo ao botão
    fonte = pygame.font.Font(pygame.font.get_default_font(), 16)
    texto = fonte.render(f'{rotulo}', True, preto)
    rect_texto = texto.get_rect(center=(texto_cx, texto_cy))
    jogo.blit(texto, rect_texto)

    return botao


# Loop do jogo
status_jogo = 'selecionar pokemon'
while status_jogo != 'sair':

    for evento in pygame.event.get():
        if evento.type == QUIT:
            status_jogo = 'sair'

        # Detecta pressionamento de tecla
        if evento.type == KEYDOWN:

            # Jogar novamente
            if evento.key == K_y:
                # Reseta os Pokémon
                bulbasaur = Pokemon('Bulbasaur', nivel, 25, 150)
                charmander = Pokemon('Charmander', nivel, 175, 150)
                squirtle = Pokemon('Squirtle', nivel, 325, 150)
                pokemons = [bulbasaur, charmander, squirtle]
                status_jogo = 'selecionar pokemon'

            # Sair
            elif evento.key == K_n:
                status_jogo = 'sair'

        # Detecta clique do mouse
        if evento.type == MOUSEBUTTONDOWN:

            # Coordenadas do clique do mouse
            clique_mouse = evento.pos

            # Para selecionar um Pokémon
            if status_jogo == 'selecionar pokemon':

                # Verifica qual Pokémon foi clicado
                for i in range(len(pokemons)):

                    if pokemons[i].get_rect().collidepoint(clique_mouse):

                        # Atribui os Pokémon ao jogador e ao rival
                        pokemon_jogador = pokemons[i]
                        pokemon_rival = pokemons[(i + 1) % len(pokemons)]

                        # Diminui o nível do Pokémon rival para facilitar a batalha
                        pokemon_rival.nivel = int(pokemon_rival.nivel * .75)

                        # Define as coordenadas das barras de hp
                        pokemon_jogador.hp_x = 275
                        pokemon_jogador.hp_y = 250
                        pokemon_rival.hp_x = 50
                        pokemon_rival.hp_y = 50

                        status_jogo = 'prebatalha'

            # Para selecionar lutar ou usar poção
            elif status_jogo == 'turno jogador':

                # Verifica se o botão de luta foi clicado
                if botao_luta.collidepoint(clique_mouse):
                    status_jogo = 'movimento jogador'

                # Verifica se o botão de poção foi clicado
                if botao_pocao.collidepoint(clique_mouse):

                    # Força o ataque se não houver mais poções
                    if pokemon_jogador.num_pocoes == 0:
                        exibir_mensagem('Sem mais poções')
                        time.sleep(2)
                        status_jogo = 'movimento jogador'
                    else:
                        pokemon_jogador.usar_pocao()
                        exibir_mensagem(f'{pokemon_jogador.nome} usou poção')
                        time.sleep(2)
                        status_jogo = 'turno rival'

            # Para selecionar um movimento
            elif status_jogo == 'movimento jogador':

                # Verifica qual botão de movimento foi clicado
                for i in range(len(botoes_movimento)):
                    botao = botoes_movimento[i]

                    if botao.collidepoint(clique_mouse):
                        movimento = pokemon_jogador.movimentos[i]
                        pokemon_jogador.realizar_ataque(
                            pokemon_rival, movimento)

                        # Verifica se o Pokémon do rival desmaiou
                        if pokemon_rival.hp_atual == 0:
                            status_jogo = 'desmaiado'
                        else:
                            status_jogo = 'turno rival'

    # Tela de seleção de Pokémon
    if status_jogo == 'selecionar pokemon':
        jogo.fill(branco)

    # Desenhando todos os Pokémon (incluindo os novos)
        for pokemon in pokemons:
            pokemon.desenhar()

        # Desenha uma caixa ao redor do Pokémon sobre o qual o mouse está apontando
            cursor_mouse = pygame.mouse.get_pos()
            if pokemon.get_rect().collidepoint(cursor_mouse):
                pygame.draw.rect(jogo, preto, pokemon.get_rect(), 2)

        pygame.display.update()

    # Obtém movimentos da API e reposiciona os Pokémon
    if status_jogo == 'prebatalha':

        # Desenha o Pokémon selecionado
        jogo.fill(branco)
        pokemon_jogador.desenhar()
        pygame.display.update()

        pokemon_jogador.definir_movimentos()
        pokemon_rival.definir_movimentos()

        # Reposiciona os Pokémon
        pokemon_jogador.x = -50
        pokemon_jogador.y = 100
        pokemon_rival.x = 250
        pokemon_rival.y = -50

        # Redimensiona os sprites
        pokemon_jogador.tamanho = 300
        pokemon_rival.tamanho = 300
        pokemon_jogador.definir_sprite('back_default')
        pokemon_rival.definir_sprite('front_default')

        status_jogo = 'iniciar batalha'

    # Animação de início de batalha
    if status_jogo == 'iniciar batalha':

        # O rival envia seu Pokémon
        alpha = 0
        while alpha < 255:

            jogo.fill(branco)
            pokemon_rival.desenhar(alpha)
            exibir_mensagem(f'O rival enviou {pokemon_rival.nome}!')
            alpha += .4

            pygame.display.update()

        # Pausa por 1 segundo
        time.sleep(1)

        # O jogador envia seu Pokémon
        alpha = 0
        while alpha < 255:

            jogo.fill(branco)
            pokemon_rival.desenhar()
            pokemon_jogador.desenhar(alpha)
            exibir_mensagem(f'Vai {pokemon_jogador.nome}!')
            alpha += .4

            pygame.display.update()

        # Desenha as barras de hp
        pokemon_jogador.desenhar_hp()
        pokemon_rival.desenhar_hp()

        # Determina quem começa
        if pokemon_rival.velocidade > pokemon_jogador.velocidade:
            status_jogo = 'turno rival'
        else:
            status_jogo = 'turno jogador'

        pygame.display.update()

        # Pausa por 1 segundo
        time.sleep(1)

    # Exibe os botões de luta e uso de poção
    if status_jogo == 'turno jogador':

        jogo.fill(branco)
        pokemon_jogador.desenhar()
        pokemon_rival.desenhar()
        pokemon_jogador.desenhar_hp()
        pokemon_rival.desenhar_hp()

        # Cria os botões de luta e uso de poção
        botao_luta = criar_botao(240, 140, 10, 350, 130, 412, 'Lutar')
        botao_pocao = criar_botao(
            240, 140, 250, 350, 370, 412, f'Usar Poção ({pokemon_jogador.num_pocoes})')

        # Desenha a borda preta
        pygame.draw.rect(jogo, preto, (10, 350, 480, 140), 3)

        pygame.display.update()

    # Exibe os botões de movimento
    if status_jogo == 'movimento jogador':

        jogo.fill(branco)
        pokemon_jogador.desenhar()
        pokemon_rival.desenhar()
        pokemon_jogador.desenhar_hp()
        pokemon_rival.desenhar_hp()

        # Cria um botão para cada movimento
        botoes_movimento = []
        for i in range(len(pokemon_jogador.movimentos)):
            movimento = pokemon_jogador.movimentos[i]
            largura_botao = 240
            altura_botao = 70
            esquerda = 10 + i % 2 * largura_botao
            topo = 350 + i // 2 * altura_botao
            centro_texto_x = esquerda + 120
            centro_texto_y = topo + 35
            botao = criar_botao(largura_botao, altura_botao, esquerda,
                                topo, centro_texto_x, centro_texto_y, movimento.nome.capitalize())
            botoes_movimento.append(botao)

        # Desenha a borda preta
        pygame.draw.rect(jogo, preto, (10, 350, 480, 140), 3)

        pygame.display.update()

    # O rival seleciona um movimento aleatório para atacar
    if status_jogo == 'turno rival':

        jogo.fill(branco)
        pokemon_jogador.desenhar()
        pokemon_rival.desenhar()
        pokemon_jogador.desenhar_hp()
        pokemon_rival.desenhar_hp()

        # Esvazia a caixa de exibição e pausa por 2 segundos antes de atacar
        exibir_mensagem('')
        time.sleep(2)

        # Seleciona um movimento aleatório
        movimento = random.choice(pokemon_rival.movimentos)
        pokemon_rival.realizar_ataque(pokemon_jogador, movimento)

        # Verifica se o Pokémon do jogador desmaiou
        if pokemon_jogador.hp_atual == 0:
            status_jogo = 'desmaiado'
        else:
            status_jogo = 'turno jogador'

        pygame.display.update()

    # Um dos Pokémon desmaiou
    if status_jogo == 'desmaiado':

        alpha = 255
        while alpha > 0:

            jogo.fill(branco)
            pokemon_jogador.desenhar_hp()
            pokemon_rival.desenhar_hp()

            # Determina qual Pokémon desmaiou
            if pokemon_rival.hp_atual == 0:
                pokemon_jogador.desenhar()
                pokemon_rival.desenhar(alpha)
                exibir_mensagem(f'{pokemon_rival.nome} desmaiou!')
            else:
                pokemon_jogador.desenhar(alpha)
                pokemon_rival.desenhar()
                exibir_mensagem(f'{pokemon_jogador.nome} desmaiou!')
            alpha -= .4

            pygame.display.update()

        status_jogo = 'fim de jogo'

    # Tela de fim de jogo
    if status_jogo == 'fim de jogo':

        exibir_mensagem('Jogar novamente (S/N)?')

pygame.quit()
