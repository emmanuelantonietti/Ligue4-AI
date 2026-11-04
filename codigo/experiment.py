# experiment.py - o campeonato: faz os agentes jogarem entre si e mede resultado e custo.
# Rodar: python3 experiment.py [N_ABERTURAS]   (padrão 100 aberturas = 200 partidas por confronto)
#
# Como o experimento é justo:
#   - custo medido em NÓS VISITADOS por jogada (o aleatório não busca, custa 0)
#   - os agentes de busca têm a mesma avaliação, a mesma ordenação e o mesmo alfa-beta; só a
#     profundidade muda, e nada foi calibrado
#   - cada abertura (4 lances sorteados) é jogada duas vezes, trocando quem começa
#   - sorteios com semente fixa: rodar de novo dá os mesmos números
import csv
import math
import os
import random
import statistics
import sys
import time
from collections import namedtuple
from multiprocessing import Pool

from game import MAX, MIN, ConnectK
from search import Stats, alphabeta, best_move

NCOLS, NROWS, K = 7, 6, 4   # tabuleiro 7x6, 4 em linha
ABERTURA_PLIES = 4          # lances sorteados no começo de cada partida
SEMENTE_BASE = 20261029

# Cada agente é a profundidade do alfa-beta (um número) ou "aleatorio".
# Cada confronto é (agente A, agente B). O A é o agente "de interesse".
CONFRONTOS = [
    (2, "aleatorio"),   # linha de base: o agente mais fraco já vence o aleatório?
    (4, "aleatorio"),
    (4, 2),             # o próprio agente com profundidade menor (obrigatório)
    (6, 4),             # o que ganha ao aprofundar mais
]

# O que guardamos de cada partida (o resultado é sempre do ponto de vista do agente A)
Partida = namedtuple("Partida", ["confronto", "abertura", "a_e_max", "resultado_a", "jogadas", "nos_a", "nos_b"])


def nome(agente):
    return "Aleatório" if agente == "aleatorio" else f"AB(prof={agente})"


def escolher(game, s, agente, rng):
    """O agente escolhe uma jogada. Devolve (coluna, nós visitados)."""
    if agente == "aleatorio":
        return rng.choice(game.actions(s)), 0
    nos = Stats()
    coluna, _ = best_move(game, s, agente, ordered=True, stats=nos)
    return coluna, nos.nodes


def abertura(game, i):
    """A abertura de número i: 4 lances sorteados. O mesmo i dá sempre a mesma abertura."""
    rng = random.Random(SEMENTE_BASE + i)
    s = game.initial()
    for _ in range(ABERTURA_PLIES):
        s = game.result(s, rng.choice(game.actions(s)))
    return s


def jogar(tarefa):
    """Joga uma partida inteira. O agente A joga como MAX se a_e_max for 1, senão como MIN."""
    confronto, i, a_e_max = tarefa
    game = ConnectK(NCOLS, NROWS, K)
    agente_a, agente_b = CONFRONTOS[confronto]
    cor_a = MAX if a_e_max else MIN
    rng = random.Random(SEMENTE_BASE + 10**6 + confronto * 10**4 + i * 2 + a_e_max)

    s = abertura(game, i)
    nos_a, nos_b = [], []
    while not game.terminal(s):
        if game.player(s) == cor_a:            # é a vez do A
            coluna, nos = escolher(game, s, agente_a, rng)
            nos_a.append(nos)
        else:                                   # é a vez do B
            coluna, nos = escolher(game, s, agente_b, rng)
            nos_b.append(nos)
        s = game.result(s, coluna)

    resultado_a = game.winner(s) * cor_a        # +1 o A ganhou, -1 o A perdeu, 0 empate
    return Partida(confronto, i, a_e_max, resultado_a, game.plies(s), nos_a, nos_b)


def intervalo_de_confianca(placares, repeticoes=4000):
    """Intervalo de 95% do placar médio (bootstrap): sorteia os placares com reposição
    muitas vezes e pega a faixa que contém 95% das médias."""
    rng = random.Random(SEMENTE_BASE)
    n = len(placares)
    medias = sorted(sum(rng.choice(placares) for _ in range(n)) / n for _ in range(repeticoes))
    return medias[int(0.025 * repeticoes)], medias[int(0.975 * repeticoes) - 1]


def descrever(valores):
    """Resume uma lista de custos: média, mediana, p95 e máximo."""
    if not valores:
        return "-"
    valores = sorted(valores)
    p95 = valores[min(len(valores) - 1, math.ceil(0.95 * len(valores)) - 1)]
    return (f"média={statistics.mean(valores):.0f} mediana={statistics.median(valores):.0f} "
            f"p95={p95} máx={valores[-1]}")


def resumo(confronto, partidas, texto):
    """Escreve no texto o resultado de um confronto."""
    agente_a, agente_b = CONFRONTOS[confronto]
    jogos = [p for p in partidas if p.confronto == confronto]
    n = len(jogos)
    vitorias = sum(p.resultado_a == 1 for p in jogos)
    empates = sum(p.resultado_a == 0 for p in jogos)
    derrotas = sum(p.resultado_a == -1 for p in jogos)

    # placar de cada abertura = média das duas partidas dela (vitória 1, empate 0,5, derrota 0)
    por_abertura = {}
    for p in jogos:
        por_abertura.setdefault(p.abertura, []).append((p.resultado_a + 1) / 2)
    placares = [sum(v) / len(v) for v in por_abertura.values()]
    baixo, alto = intervalo_de_confianca(placares)

    texto.append(f"\n### {nome(agente_a)} (A) contra {nome(agente_b)} (B) - {n} partidas, {len(por_abertura)} aberturas pareadas")
    texto.append(f"- A: {vitorias}V {empates}E {derrotas}D | placar (V+E/2)/N = {(vitorias + empates / 2) / n:.3f}  "
                 f"IC95% [{baixo:.3f}, {alto:.3f}]")
    for rotulo, a_e_max in (("A jogando como MAX (joga primeiro após a abertura)", 1), ("A jogando como MIN", 0)):
        lado = [p for p in jogos if p.a_e_max == a_e_max]
        texto.append(f"- {rotulo}: {sum(p.resultado_a == 1 for p in lado)}V "
                     f"{sum(p.resultado_a == 0 for p in lado)}E {sum(p.resultado_a == -1 for p in lado)}D")
    texto.append(f"- nós por jogada de A: {descrever([nos for p in jogos for nos in p.nos_a])}")
    texto.append(f"- nós por jogada de B: {descrever([nos for p in jogos for nos in p.nos_b])}")
    texto.append(f"- nós por PARTIDA de A: {descrever([sum(p.nos_a) for p in jogos])}")
    texto.append(f"- duração (jogadas totais): {descrever([p.jogadas for p in jogos])}")


def efeito_da_ordenacao(texto, n_posicoes=60):
    """Mede quanto a ordenação (centro primeiro) economiza de nós, com o mesmo valor (profundidade 5)."""
    game = ConnectK(NCOLS, NROWS, K)
    rng = random.Random(SEMENTE_BASE + 7)
    nos_com = nos_sem = achadas = 0
    while achadas < n_posicoes:
        s = game.initial()
        for _ in range(rng.randint(4, 20)):
            if game.terminal(s):
                break
            s = game.result(s, rng.choice(game.actions(s)))
        if game.terminal(s):
            continue
        achadas += 1
        com, sem = Stats(), Stats()
        valor_com = alphabeta(game, s, 5, stats=com, ordered=True)
        valor_sem = alphabeta(game, s, 5, stats=sem, ordered=False)
        assert valor_com == valor_sem  # a ordenação muda o custo, nunca o valor
        nos_com += com.nodes
        nos_sem += sem.nodes
    texto.append(f"\n### Ablação da ordenação de jogadas (alfa-beta, prof=5, {n_posicoes} posições sorteadas)")
    texto.append(f"- nós SEM ordenação: {nos_sem}  | COM ordenação (centro primeiro): {nos_com}  "
                 f"| redução: {100 * (1 - nos_com / nos_sem):.0f}%  (valores idênticos nas {n_posicoes} posições)")


if __name__ == "__main__":
    n_aberturas = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    # uma tarefa por partida: (confronto, abertura, A joga como MAX?). Cada abertura é jogada dos dois lados.
    tarefas = [(c, i, lado) for c in range(len(CONFRONTOS)) for i in range(n_aberturas) for lado in (1, 0)]

    inicio = time.time()
    with Pool(os.cpu_count()) as pool:  # reparte as partidas entre os núcleos do computador
        partidas = pool.map(jogar, tarefas, chunksize=2)

    texto = [f"# Resultados - Ligue 4 {NCOLS}x{NROWS}, {K} em linha",
             f"{n_aberturas} aberturas x 2 lados = {2 * n_aberturas} partidas por confronto; "
             f"abertura = {ABERTURA_PLIES} lances sorteados; semente base {SEMENTE_BASE}; "
             f"tempo total {time.time() - inicio:.0f}s"]
    for c in range(len(CONFRONTOS)):
        resumo(c, partidas, texto)
    efeito_da_ordenacao(texto)
    texto = "\n".join(texto)
    print(texto)

    open("resultados.md", "w", encoding="utf8").write(texto + "\n")
    with open("partidas.csv", "w", newline="", encoding="utf8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["confronto", "A", "B", "abertura", "A_e_MAX", "resultado_A", "jogadas", "nos_A", "nos_B"])
        for p in partidas:
            agente_a, agente_b = CONFRONTOS[p.confronto]
            escritor.writerow([p.confronto, nome(agente_a), nome(agente_b), p.abertura, p.a_e_max,
                               p.resultado_a, p.jogadas, sum(p.nos_a), sum(p.nos_b)])
