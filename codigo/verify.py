# verify.py - prova que o alfa-beta dá EXATAMENTE o mesmo valor que o Minimax.
# Rodar: python3 verify.py     (deve terminar com "RESULTADO: TUDO OK")
#   A) tabuleiros pequenos, olhando o jogo inteiro (sem cortar a profundidade)
#   B) tabuleiro 7x6 normal, com profundidade limitada
#   C) controle: um alfa-beta errado de propósito TEM que ser reprovado
import random
import sys
import time

from game import MAX, ConnectK
from search import INF, Stats, alphabeta, minimax, valor_se_folha

SEMENTE = 2026  # sorteio fixo: rodar de novo dá os mesmos números


def posicao_aleatoria(game, rng, jogadas):
    """Joga alguns lances ao acaso a partir do início e devolve a posição (para se o jogo acabar)."""
    s = game.initial()
    for _ in range(jogadas):
        if game.terminal(s):
            break
        s = game.result(s, rng.choice(game.actions(s)))
    return s


def comparar(game, s, depth=INF):
    """Roda os 3 algoritmos na mesma posição: Minimax, alfa-beta com ordenação e alfa-beta sem.
    Devolve os 3 valores e os 3 custos (nós visitados)."""
    nos_mm, nos_ab_ord, nos_ab = Stats(), Stats(), Stats()
    v_mm = minimax(game, s, depth, nos_mm)
    v_ab_ord = alphabeta(game, s, depth, stats=nos_ab_ord, ordered=True)
    v_ab = alphabeta(game, s, depth, stats=nos_ab, ordered=False)
    return v_mm, v_ab_ord, v_ab, nos_mm.nodes, nos_ab_ord.nodes, nos_ab.nodes


def bloco_a():
    print("== A) Profundidade completa, instâncias pequenas ==")
    print(f"{'instância':<12}{'posição':<10}{'minimax':>9}{'ab+ord':>9}{'ab':>9}"
          f"{'nós mm':>12}{'nós ab+ord':>12}{'nós ab':>10}  ok")
    rng = random.Random(SEMENTE)
    falhas = 0
    # (colunas, linhas, quantas em linha, quantos lances sortear antes de testar)
    casos = [(3, 3, 3, [0, 1, 2]), (4, 3, 3, [0, 1, 2]), (4, 4, 3, [0, 3, 5]), (5, 4, 4, [8, 9, 10])]
    for ncols, nrows, k, lances in casos:
        game = ConnectK(ncols, nrows, k)
        for n in lances:
            s = posicao_aleatoria(game, rng, n)
            if game.terminal(s):
                continue
            inicio = time.time()
            v_mm, v_ab_ord, v_ab, nos_mm, nos_ab_ord, nos_ab = comparar(game, s)
            ok = v_mm == v_ab_ord == v_ab  # <- a igualdade que a ficha exige
            falhas += not ok
            print(f"{ncols}x{nrows} k={k:<4}{'lances=' + str(n):<10}{v_mm:>9}{v_ab_ord:>9}{v_ab:>9}"
                  f"{nos_mm:>12}{nos_ab_ord:>12}{nos_ab:>10}  {'OK' if ok else 'FALHOU'}  ({time.time() - inicio:.1f}s)")
    return falhas


def bloco_b():
    print("\n== B) Profundidade limitada (com avaliação) no 7x6 ==")
    game = ConnectK(7, 6, 4)
    rng = random.Random(SEMENTE + 1)
    falhas = total = 0
    for depth in (1, 2, 3, 4, 5):
        nos_mm = nos_ab = 0
        for _ in range(15):
            s = posicao_aleatoria(game, rng, rng.randint(0, 20))
            if game.terminal(s):
                continue
            v_mm, v_ab_ord, v_ab, a, b, _ = comparar(game, s, depth)
            total += 1
            falhas += not (v_mm == v_ab_ord == v_ab)
            nos_mm, nos_ab = nos_mm + a, nos_ab + b
        print(f"profundidade {depth}: nós minimax={nos_mm:>9}  nós alfa-beta(ord)={nos_ab:>9}  "
              f"economia={100 * (1 - nos_ab / nos_mm):.0f}%")
    print(f"{total} posições comparadas, {falhas} divergências")
    return falhas


def alfabeta_defeituoso(game, s, depth, alpha=-INF, beta=INF):
    """Alfa-beta ERRADO de propósito: depois de testar a primeira jogada ele para (poda demais).
    Serve só para provar que o teste de igualdade percebe quando a poda está errada."""
    valor = valor_se_folha(game, s, depth)
    if valor is not None:
        return valor
    maximizando = game.player(s) == MAX
    melhor = -INF if maximizando else INF
    for a in game.ordered_actions(s):
        v = alfabeta_defeituoso(game, game.result(s, a), depth - 1, alpha, beta)
        if maximizando:
            melhor = max(melhor, v)
            if melhor >= beta:
                return melhor
            alpha = max(alpha, melhor)
        else:
            melhor = min(melhor, v)
            if melhor <= alpha:
                return melhor
            beta = min(beta, melhor)
        if depth >= 2:  # <- o defeito
            return melhor
    return melhor


def bloco_c():
    print("\n== C) Controle: alfa-beta defeituoso (poda demais) deve ser pego ==")
    game = ConnectK(4, 4, 3)
    rng = random.Random(SEMENTE + 2)
    pegas = total = 0
    for _ in range(40):
        s = posicao_aleatoria(game, rng, rng.randint(0, 6))
        if game.terminal(s):
            continue
        total += 1
        pegas += minimax(game, s, 4) != alfabeta_defeituoso(game, s, 4)  # o defeito deu valor diferente?
    print(f"o defeito divergiu do Minimax em {pegas} de {total} posições")
    return 0 if pegas > 0 else 1


if __name__ == "__main__":
    problemas = bloco_a() + bloco_b() + bloco_c()
    print("\nRESULTADO:", "TUDO OK" if problemas == 0 else f"{problemas} PROBLEMA(S)")
    sys.exit(1 if problemas else 0)
